# -*- coding: utf-8 -*-

import json
import dataclasses

from aws_codecommit import (
    CodeCommitEvent,
    better_boto,
    is_certain_semantic_commit,
    SemanticCommitEnum,
)
from aws_codebuild import BuildJobRun, start_build, start_build_batch
from boto_session_manager import BotoSesManager, AwsServiceEnum

from .. import logger
from ..ci.codebuild import BuildJobConfig, CodebuildConfig

CI_DATA_PREFIX = "CI_DATA_"


@dataclasses.dataclass
class CIData:
    """
    CI related data, will be available in environment variable.
    """

    commit_message: str = ""
    comment_id: str = ""

    def to_env_var(
        self,
        prefix: str = CI_DATA_PREFIX,
    ) -> dict:
        env_var = dict()
        for attr, value in dataclasses.asdict(self).items():
            key = (prefix + attr).upper()
            env_var[key] = value
        return env_var

    @classmethod
    def from_env_var(
        cls,
        env_var: dict,
        prefix: str = CI_DATA_PREFIX,
    ) -> "CIData":
        field_set = {field.name for field in dataclasses.fields(cls)}
        kwargs = dict()
        for field_name in field_set:
            key = (prefix + field_name).upper()
            if key in env_var:
                kwargs[field_name] = env_var[key]
        return cls(**kwargs)


@dataclasses.dataclass
class CodeCommitEventHandler:
    bsm: BotoSesManager = dataclasses.field()
    cc_event: CodeCommitEvent = dataclasses.field()

    def log_cc_event(self):
        logger.info("Received CodeCommit event")
        logger.info(f"- detected event type = {self.cc_event.event_type!r}")
        logger.info(f"- event description = {self.cc_event.event_description!r}")

    def do_we_trigger_build(self) -> bool:
        """
        This function defines whether we should trigger an AWS CodeBuild build job.
        This solution designed for any type of project for any programming language
        and for any Git Workflow. This function allow you to customize your own
        git branching rule and git commit rule, decide when to trigger the build.
        """
        # won't trigger build direct commit
        if self.cc_event.is_commit_event:
            logger.info(
                f"we don't trigger build job for "
                f"event type {self.cc_event.event_type!r} on {self.cc_event.source_branch}"
            )
            return False
        # run build job if it is a Pull Request related event
        elif self.cc_event.is_pr_created_event or self.cc_event.is_pr_update_event:
            # we don't trigger if commit message has 'NO BUILD'
            if is_certain_semantic_commit(
                self.cc_event.commit_message,
                stub=SemanticCommitEnum.chore.value,
            ):
                logger.info(
                    f"we DO NOT trigger build job for "
                    f"commit message {SemanticCommitEnum.chore.value!r}"
                )
                return False

            # we don't trigger if source branch is not valid branch
            if not (
                self.cc_event.source_is_feature_branch
                or self.cc_event.source_is_develop_branch
                or self.cc_event.source_is_fix_branch
                or self.cc_event.source_is_build_branch
                or self.cc_event.source_is_doc_branch
                or self.cc_event.source_is_release_branch
            ):
                logger.info(
                    "we DO NOT trigger build job "
                    f"if PR source branch is {self.cc_event.target_branch!r}"
                )
                return False

            # we don't trigger if target branch is not main
            if not self.cc_event.target_is_main_branch:
                logger.info(
                    "we DO NOT trigger build job "
                    "if PR target branch is not 'main' "
                    f"it is {self.cc_event.target_branch!r}"
                )
                return False
            return True
        # always trigger on PR merge event
        elif self.cc_event.is_pr_merged_event:
            return True
        # we don't trigger on other event
        elif (
            self.cc_event.is_create_branch_event
            or self.cc_event.is_delete_branch_event
            or self.cc_event.is_comment_event
            or self.cc_event.is_approve_pr_event
        ):
            return False
        else:
            return False

    def get_codebuild_config(self) -> CodebuildConfig:
        file = better_boto.get_file(
            bsm=self.bsm,
            repo_name=self.cc_event.repo_name,
            file_path="codebuild-config.json",
        )
        return CodebuildConfig.from_dict(json.loads(file.get_text()))

    @property
    def pr_commit_console_url(self) -> str:
        """
        It only works when the codecommit event is a PR event.
        """
        return (
            f"https://{self.bsm.aws_region}.console.aws.amazon.com/"
            f"codesuite/codecommit/repositories/{self.cc_event.repo_name}/"
            f"pull-requests/{self.cc_event.pr_id}/"
            f"commit/{self.cc_event.source_commit}?region={self.bsm.aws_region}"
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
        cb_client = self.bsm.get_client(AwsServiceEnum.CodeBuild)
        kwargs = dict(
            cb_client=cb_client,
            projectName=build_job_config.project_name,
        )
        if build_job_config.buildspec:
            kwargs["buildspecOverride"] = build_job_config.buildspec
        kwargs["sourceVersion"] = self.cc_event.source_commit
        env_var = build_job_config.env_var.copy()
        env_var.update(additional_env_var)
        kwargs["environmentVariablesOverride"] = [
            {
                "name": key,
                "value": value,
                "type": "PLAINTEXT",
            }
            for key, value in env_var.items()
        ]
        if build_job_config.is_batch_job:
            res = start_build_batch(**kwargs)
        else:
            res = start_build(**kwargs)
        build_job_run = BuildJobRun.from_start_build_response(res)
        return build_job_run

    def run_build_job_for_pr_event(
        self,
        build_job_config: BuildJobConfig,
    ):
        # post an initial comment to the PR
        comment = better_boto.post_comment_for_pull_request(
            bsm=self.bsm,
            pr_id=self.cc_event.pr_id,
            repo_name=self.cc_event.repo_name,
            before_commit_id=self.cc_event.source_commit,
            after_commit_id=self.cc_event.target_commit,
            content=self.comment_body_before_run_build_job,
        )
        ci_data = CIData(
            commit_message=self.cc_event.commit_message,
            comment_id=comment.comment_id,
        )

        # start build
        build_job_run = self.run_build_job(
            build_job_config=build_job_config,
            additional_env_var=ci_data.to_env_var(),
        )

        # update the first comment with build job run console url
        better_boto.update_comment(
            bsm=self.bsm,
            comment_id=comment.comment_id,
            content=self.get_comment_body_after_run_build_job(build_job_run),
        )

    def run_build_job_for_non_pr_event(
        self,
        build_job_config: BuildJobConfig,
    ):
        self.run_build_job(
            build_job_config=build_job_config,
            additional_env_var={},
        )

    def execute(self):
        self.log_cc_event()

        if self.do_we_trigger_build() is False:
            return

        cb_config = self.get_codebuild_config()

        for job in cb_config.jobs:
            if self.cc_event.is_pr_event:
                self.run_build_job_for_pr_event(job)
            else:
                self.run_build_job_for_non_pr_event(job)
