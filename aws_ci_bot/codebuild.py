# -*- coding: utf-8 -*-

import dataclasses

from aws_codecommit import better_boto

from aws_codebuild import (
    CodeBuildEvent,
    BuildJobRun,
)
from boto_session_manager import BotoSesManager

from . import logger
from .ci_data import CIData
from .codebuild_rule import CodeBuildHandlerActionEnum, check_what_to_do


@dataclasses.dataclass
class CodeBuildEventHandler:
    """
    Handle CodeBuild event. Determine whether we should post a comment to
    CodeCommit, what is the message content?

    :param bsm: where the original event is stored.
    :param cb_event: the CodeBuild event object.
    :param s3_console_url: where the original event is stored.
    :param build_job_run: the CodeBuild job run object.
    """

    bsm: BotoSesManager = dataclasses.field()
    cb_event: CodeBuildEvent = dataclasses.field()
    s3_console_url: str = dataclasses.field()
    build_job_run: BuildJobRun = dataclasses.field()

    def log_cb_event(self):
        logger.header("Handle CodeBuild event", "-", 60)
        logger.info(f"- is it a BATCH build = {self.build_job_run.is_batch}")
        logger.info(f"- detected event type = {self.cb_event.event_type!r}")
        logger.info(f"- build job run url = {self.cb_event.console_url}")

    def post_build_status_to_comment(self):
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
            logger.info(
                f"  post status {self.cb_event.build_status!r} to comment {ci_data.comment_id!r}"
            )
            better_boto.post_comment_reply(
                bsm=self.bsm,
                in_reply_to=ci_data.comment_id,
                content=comment,
            )

    def action_post_status_to_comment(self):
        logger.header("Post job run status", "-", 60)
        self.post_build_status_to_comment()

    def execute(self):
        self.log_cb_event()
        action = check_what_to_do(self.cb_event)
        if action == CodeBuildHandlerActionEnum.nothing:
            return
        elif action == CodeBuildHandlerActionEnum.post_status_to_comment:
            self.action_post_status_to_comment()
