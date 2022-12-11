# -*- coding: utf-8 -*-

import typing as T
import json
import enum
import dataclasses

from aws_codecommit import (
    CodeCommitEvent,
    better_boto as cc_boto,
    is_certain_semantic_commit,
    SemanticCommitEnum,
)

from aws_codebuild import (
    CodeBuildEvent,
    BuildJobRun,
    start_build,
    start_build_batch,
)
from boto_session_manager import BotoSesManager

from . import logger


@dataclasses.dataclass
class BuildJobConfig:
    project_name: str = dataclasses.field()
    is_batch_job: bool = dataclasses.field()
    buildspec: T.Optional[str] = dataclasses.field(default=None)
    env_var: dict = dataclasses.field(default_factory=dict)

    @classmethod
    def from_dict(cls, dct: dict) -> "BuildJobConfig":
        return cls(
            project_name=dct["project_name"],
            is_batch_job=dct["is_batch_job"],
            buildspec=dct.get("buildspec"),
            env_var=dct.get("env_var", {}),
        )


@dataclasses.dataclass
class CodebuildConfig:
    """
    The codebuild-config.json file that defines which CodeBuild project
    it should use to run CI job.
    """

    jobs: T.List[BuildJobConfig] = dataclasses.field(default_factory=list)

    @classmethod
    def from_dict(cls, dct: dict) -> "CodebuildConfig":
        return cls(jobs=[BuildJobConfig.from_dict(d) for d in dct["jobs"]])


CI_DATA_PREFIX = "CI_DATA_"


@dataclasses.dataclass
class CIData:
    """
    CI related data, will be available in environment variable.

    It is a simple data container that allow you to pass data into
    codebuild job run, or read CIData from env var when you are running
    automation script in job run.

    :param comment_id: the comment is the thread created when received
        CodeCommit event. it will send to the Environment Variable for CodeBuild
        job run, and all of sub-sequence CodeBuild event will reply
        to this comment.
    """

    event_s3_console_url: str = dataclasses.field(default=None)
    commit_message: T.Optional[str] = dataclasses.field(default=None)
    comment_id: T.Optional[str] = dataclasses.field(default=None)

    def to_env_var(
        self,
        prefix: str = CI_DATA_PREFIX,
    ) -> dict:
        env_var = dict()
        for attr, value in dataclasses.asdict(self).items():
            if value is not None:
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


class CodeCommitHandlerActionEnum(str, enum.Enum):
    nothing = "nothing"
    start_build = "start_build"


@dataclasses.dataclass
class CodeCommitEventHandler:
    """
    :param s3_console_url: where the original event is stored.
    """

    bsm: BotoSesManager = dataclasses.field()
    cc_event: CodeCommitEvent = dataclasses.field()
    s3_console_url: str = dataclasses.field()

    def log_cc_event(self):
        logger.header("Handle CodeCommit event", "-", 60)
        logger.info(f"- detected event type = {self.cc_event.event_type!r}")
        logger.info(f"- event description = {self.cc_event.event_description!r}")

    def check_what_to_do(self) -> CodeCommitHandlerActionEnum:
        """
        Analyze the CodeBuild event, check what to do.

        This function defines whether we should trigger an AWS CodeBuild build job.
        This solution designed for any type of project for any programming language
        and for any Git Workflow. This function allow you to customize your own
        git branching rule and git commit rule, decide when to trigger the build.
        """
        logger.header("Detect whether we should trigger build", "-", 60)

        # won't trigger build direct commit
        if self.cc_event.is_commit_event:
            logger.info(
                f"we don't trigger build job for "
                f"event type {self.cc_event.event_type!r} on {self.cc_event.source_branch}"
            )
            return CodeCommitHandlerActionEnum.nothing
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
                return CodeCommitHandlerActionEnum.nothing

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
                return CodeCommitHandlerActionEnum.nothing

            # we don't trigger if target branch is not main
            if not self.cc_event.target_is_main_branch:
                logger.info(
                    "we DO NOT trigger build job "
                    "if PR target branch is not 'main' "
                    f"it is {self.cc_event.target_branch!r}"
                )
                return CodeCommitHandlerActionEnum.nothing

            logger.info(
                f"we don't trigger build job for "
                f"event type {self.cc_event.event_type!r} on {self.cc_event.source_branch}"
            )
            return CodeCommitHandlerActionEnum.start_build
        # always trigger on PR merge event
        elif self.cc_event.is_pr_merged_event:
            logger.info(
                f"trigger build job for PR merged event, from branch "
                f"{self.cc_event.source_branch!r} to {self.cc_event.target_branch!r}"
            )
            return CodeCommitHandlerActionEnum.start_build
        # we don't trigger on other event
        elif (
            self.cc_event.is_create_branch_event
            or self.cc_event.is_delete_branch_event
            or self.cc_event.is_comment_event
            or self.cc_event.is_approve_pr_event
        ):
            logger.info(
                f"we don't trigger build job for "
                f"event type {self.cc_event.event_type!r}."
            )
            return CodeCommitHandlerActionEnum.nothing
        else:
            logger.info(
                f"we don't trigger build job for "
                f"event type {self.cc_event.event_type!r}."
            )
            return CodeCommitHandlerActionEnum.nothing

    def get_codebuild_config(self) -> CodebuildConfig:
        """
        Get the CodebuildConfig json file from the CodeCommit repo.
        """
        file_path = "codebuild-config.json"
        logger.info(f"Get codebuild config from {file_path!r}")

        file = cc_boto.get_file(
            bsm=self.bsm,
            repo_name=self.cc_event.repo_name,
            file_path=file_path,
            commit_id=self.cc_event.source_commit,
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
            function = start_build_batch
            env_var[f"{CI_DATA_PREFIX}BUILD_TYPE"] = "batch build"
        else:
            logger.info(
                f"invoke codebuild.start_build API, "
                f"source version = {self.cc_event.source_commit!r}"
            )
            function = start_build
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
        res = function(**kwargs)

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
                before_commit_id= self.cc_event.target_commit,
                after_commit_id= self.cc_event.source_commit,
            )
            if self.cc_event.pr_id:
                kwargs["pr_id"] = self.cc_event.pr_id
                logger.info(f"post comment on PR {self.cc_event.pr_id}")
            else:
                logger.info(f"post comment on Commit {self.cc_event.source_commit}")
            comment = thread.post_comment(**kwargs)

            ci_data = CIData(
                event_s3_console_url=self.s3_console_url,
                commit_message=self.cc_event.commit_message,
                comment_id=comment.comment_id,
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
        cb_config = self.get_codebuild_config()
        for job in cb_config.jobs:
            self.run_build_job_and_post_comment(job)

    def execute(self):
        self.log_cc_event()

        action = self.check_what_to_do()
        if action == CodeCommitHandlerActionEnum.nothing:
            return
        elif action == CodeCommitHandlerActionEnum.start_build:
            self.action_start_build()


class CodeBuildHandlerActionEnum(str, enum.Enum):
    nothing = "nothing"
    post_status_to_comment = "post_status_to_pr_comment"


@dataclasses.dataclass
class CodeBuildEventHandler:
    bsm: BotoSesManager = dataclasses.field()
    cb_event: CodeBuildEvent = dataclasses.field()
    s3_console_url: str = dataclasses.field()
    build_job_run: BuildJobRun = dataclasses.field()

    def log_cb_event(self):
        logger.header("Handle CodeBuild event", "-", 60)
        logger.info(f"- is it a BATCH build = {self.build_job_run.is_batch}")
        logger.info(f"- detected event type = {self.cb_event.event_type!r}")
        logger.info(f"- build job run url = {self.cb_event.console_url}")

    def check_what_to_do(self) -> CodeBuildHandlerActionEnum:
        """
        Analyze the CodeBuild event, check what to do.
        """
        logger.header("Check what to do", "-", 60)
        logger.info("  do nothing for State Change IN_PROGRESS")
        # Ignore when it is state change event, but IN PROGRESS
        # we only care the failed, succeeded, stopped
        if (
            self.cb_event.is_state_change_event()
            and self.cb_event.is_build_status_IN_PROGRESS()
        ):
            logger.info("  do nothing for State Change IN_PROGRESS")
            return CodeBuildHandlerActionEnum.nothing
        # Ignore all phase change event
        elif self.cb_event.is_phase_change_event():
            logger.info("  do nothing for Phase Change")
            return CodeBuildHandlerActionEnum.nothing
        else:
            logger.info("  post status to Comment")
            return CodeBuildHandlerActionEnum.post_status_to_comment

    def get_build_job_run_details(self) -> dict:  # pragma: no cover
        """
        Call ``batch_get_builds`` or ``batch_get_build_batches`` API to get
        build job run details. Primarily it is to get the environment variable.

        Reference:

        - https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/codebuild.html#CodeBuild.Client.batch_get_builds
        - https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/codebuild.html#CodeBuild.Client.batch_get_build_batches

        NOTE:

            this function is not used ...
        """
        if self.build_job_run.is_batch:
            return self.bsm.codebuild_client.batch_get_build_batches(
                ids=[
                    self.cb_event.build_arn,
                ]
            )
        else:
            return self.bsm.codebuild_client.batch_get_builds(
                ids=[
                    self.cb_event.build_arn,
                ]
            )

    def post_build_status_to_comment(self):
        # env_var = {
        #     dct["name"]: dct["value"]
        #     for dct in build_job_run_details["builds"][0]["environment"][
        #         "environmentVariables"
        #     ]
        # }
        # ci_data = CIData.from_env_var(env_var)

        ci_data = CIData.from_env_var(self.cb_event.plain_text_env_var)
        if ci_data.comment_id:
            if self.cb_event.is_build_status_SUCCEEDED():
                comment = "🟢 Build Run SUCCEEDED"
            elif self.cb_event.is_build_status_FAILED():
                comment = "🔴 Build Run FAILED"
            elif self.cb_event.is_build_status_STOPPED():
                comment = "⚫ Build Run STOPPED"
            else:  # pragma: no cover
                raise NotImplementedError
            logger.info(f"  post status {self.cb_event.build_status!r} to comment {ci_data.comment_id!r}")
            cc_boto.post_comment_reply(
                bsm=self.bsm,
                in_reply_to=ci_data.comment_id,
                content=comment,
            )

    def action_post_status_to_comment(self):
        logger.header("Post job run status", "-", 60)
        # build_job_run_details = self.get_build_job_run_details()
        self.post_build_status_to_comment()

    def execute(self):
        self.log_cb_event()
        action = self.check_what_to_do()
        if action == CodeBuildHandlerActionEnum.nothing:
            return
        elif action == CodeBuildHandlerActionEnum.post_status_to_comment:
            self.action_post_status_to_comment()
