# -*- coding: utf-8 -*-

"""
This module defines how to response to CodeBuild event in different situations.
"""

import enum
from aws_codebuild import CodeBuildEvent
from . import logger


class CodeBuildHandlerActionEnum(str, enum.Enum):
    nothing = "nothing"
    post_status_to_comment = "post_status_to_pr_comment"


def check_what_to_do(cb_event: CodeBuildEvent) -> CodeBuildHandlerActionEnum:
    """
    Analyze the CodeBuild event, check what to do.

    This function should take a ``CodeBuildEvent`` object, and return
    a ``CodeBuildHandlerActionEnum`` object.
    """
    logger.header("Check what to do", "-", 60)

    # Ignore all phase change event
    if cb_event.is_phase_change_event():
        logger.info("  do nothing for Phase Change")
        return CodeBuildHandlerActionEnum.nothing

    if cb_event.is_state_change_event():
        # Ignore when it is state change event, but IN PROGRESS
        if cb_event.is_build_status_IN_PROGRESS():
            logger.info("  do nothing for State Change IN_PROGRESS")
            return CodeBuildHandlerActionEnum.nothing
        # Post comment only when the state change event is the failed, succeeded, stopped
        else:
            logger.info("  post status to Comment")
            return CodeBuildHandlerActionEnum.post_status_to_comment
