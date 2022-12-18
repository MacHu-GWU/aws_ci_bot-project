# -*- coding: utf-8 -*-

import dataclasses

from aws_codecommit import (
    CodeCommitEvent,
    better_boto as cc_boto,
    console,
)

from aws_codebuild import (
    BuildJobRun,
    start_build,
    start_build_batch,
)
from boto_session_manager import BotoSesManager

from . import logger
from .ci_data import CIData, CI_DATA_PREFIX
from .code_build_config import CodebuildConfig, BuildJobConfig
from .codecommit_rule import CodeCommitHandlerActionEnum, check_what_to_do


@dataclasses.dataclass
class CodeCommitEventHandler:
    """
    Handle CodeCommit event. Determine whether we should trigger a CodeBuild job?
    trigger what build project? how to trigger it? include what env var?

    :param bsm: where the original event is stored.
    :param cc_event: the CodeCommit event object.
    :param s3_console_url: where the original event is stored.
    :param s3_uri: where the original event is stored.
    """

    bsm: BotoSesManager = dataclasses.field()
    cc_event: CodeCommitEvent = dataclasses.field()
    s3_console_url: str = dataclasses.field()
    s3_uri: str = dataclasses.field()

    def log_cc_event(self):
        logger.header("Handle CodeCommit event", "-", 60)
        logger.info(f"- detected event type = {self.cc_event.event_type!r}")
        logger.info(f"- event description = {self.cc_event.event_description!r}")

    @property
    def pr_commit_console_url(self) -> str:
        """
        Return the link can jump to AWS CodeCommit Pull Request commit console.

        It only works when the CodeCommit event is a PR event.
        """
        return console.browse_pr(
            aws_region=self.bsm.aws_region,
            repo_name=self.cc_event.repo_name,
            pr_id=self.cc_event.pr_id,
            commits_tab=True,
        )

    @property
    def comment_body_before_run_build_job(self) -> str:
        lines = [
            "## 🌴 A build run is triggered, let's relax.",
            "",
            f"- commit id: [{self.cc_event.source_commit[:7]}]({self.pr_commit_console_url})",
            f'- commit message: "{self.cc_event.commit_message.strip()}"',
            f'- committer name: "{self.cc_event.committer_name.strip()}"',
        ]
        return "\n".join(lines)

    def get_comment_body_after_run_build_job(self, build_job_run: BuildJobRun) -> str:
        lines = [
            "## 🌴 A build run is triggered, let's relax.",
            "",
            f"- build run id: [{build_job_run.project_name}:{build_job_run.run_id}]({build_job_run.console_url})",
            f"- commit id: [{self.cc_event.source_commit[:7]}]({self.pr_commit_console_url})",
            f'- commit message: "{self.cc_event.commit_message.strip()}"',
            f'- committer name: "{self.cc_event.committer_name.strip()}"',
        ]
        return "\n".join(lines)

    def run_build_job(
        self,
        build_job_config: BuildJobConfig,
        additional_env_var: dict,
    ) -> BuildJobRun:
        """
        Based on build job config from the ``codebuild-config.json`` file,
        run the CodeBuild job.

        :param build_job_config:
        :param additional_env_var:
        :return:
        """
        # prepare argument
        kwargs = dict(
            bsm=self.bsm,
            projectName=build_job_config.project_name,
        )
        if build_job_config.buildspec:
            kwargs["buildspecOverride"] = build_job_config.buildspec
        kwargs["sourceVersion"] = self.cc_event.source_commit

        # use the env var defined in ``codebuild-config.json`` file
        env_var = build_job_config.env_var.copy()

        # merge additional env var
        env_var.update(additional_env_var)

        # add additional env var based on the build type
        if build_job_config.is_batch_job:
            logger.info(
                f"invoke codebuild.start_build_batch API, "
                f"source version = {self.cc_event.source_commit!r}"
            )
            start_build_function = start_build_batch
            env_var[f"{CI_DATA_PREFIX}BUILD_TYPE"] = "batch build"
        else:
            logger.info(
                f"invoke codebuild.start_build API, "
                f"source version = {self.cc_event.source_commit!r}"
            )
            start_build_function = start_build
            env_var[f"{CI_DATA_PREFIX}BUILD_TYPE"] = "single build"

        # set env var in kwargs
        kwargs["environmentVariablesOverride"] = [
            {
                "name": key,
                "value": value,
                "type": "PLAINTEXT",
            }
            for key, value in env_var.items()
        ]

        # run build job
        res = start_build_function(**kwargs)

        # parse API response
        build_job_run = BuildJobRun.from_start_build_response(res)
        return build_job_run

    def run_build_job_and_post_comment(
        self,
        build_job_config: BuildJobConfig,
    ):
        with cc_boto.CommentThread(bsm=self.bsm) as thread:
            kwargs = dict(
                repo_name=self.cc_event.repo_name,
                content=self.comment_body_before_run_build_job,
                before_commit_id=self.cc_event.target_commit,
                after_commit_id=self.cc_event.source_commit,
            )
            if self.cc_event.pr_id:
                kwargs["pr_id"] = self.cc_event.pr_id
                logger.info(f"post comment on PR {self.cc_event.pr_id}")
            else:
                logger.info(f"post comment on Commit {self.cc_event.source_commit}")
            comment = thread.post_comment(**kwargs)

            ci_data = CIData(
                event_s3_console_url=self.s3_console_url,
                event_s3_uri=self.s3_uri,
                event_type=self.cc_event.event_type,
                comment_id=comment.comment_id,
                commit_id=self.cc_event.source_commit,
                commit_message=self.cc_event.commit_message,
                committer_name=self.cc_event.committer_name,
                branch_name=self.cc_event.source_branch,
                pr_from_branch=self.cc_event.source_branch,
                pr_to_branch=self.cc_event.target_branch,
                pr_from_commit_id=self.cc_event.source_commit,
                pr_to_commit_id=self.cc_event.target_commit,
            )

            # start build
            build_job_run = self.run_build_job(
                build_job_config=build_job_config,
                additional_env_var=ci_data.to_env_var(),
            )

            # update the first comment with build job run console url
            cc_boto.update_comment(
                bsm=self.bsm,
                comment_id=comment.comment_id,
                content=self.get_comment_body_after_run_build_job(build_job_run),
            )

    def action_start_build(self):
        logger.header("Trigger build jobs", "-", 60)
        cb_config = CodebuildConfig.from_codecommit_repo(
            bsm=self.bsm,
            repo_name=self.cc_event.repo_name,
            commit_id=self.cc_event.source_commit,
        )
        for job in cb_config.jobs:
            self.run_build_job_and_post_comment(job)

    def execute(self):
        self.log_cc_event()

        action = check_what_to_do(self.cc_event)
        if action == CodeCommitHandlerActionEnum.nothing:
            return
        elif action == CodeCommitHandlerActionEnum.start_build:
            self.action_start_build()
