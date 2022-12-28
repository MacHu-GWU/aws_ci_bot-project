# -*- coding: utf-8 -*-

import enum

from aws_codecommit import (
    CodeCommitEvent,
    is_certain_semantic_branch,
    SemanticBranchEnum,
    is_certain_semantic_commit,
    SemanticCommitEnum,
)

from . import logger


class CodeCommitHandlerActionEnum(str, enum.Enum):
    nothing = "nothing"
    start_build = "start_build"


def check_what_to_do(cc_event: CodeCommitEvent) -> CodeCommitHandlerActionEnum:
    """
    Analyze the CodeBuild event, check what to do.

    This function defines whether we should trigger an AWS CodeBuild build job.
    This solution designed for any type of project for any programming language
    and for any Git Workflow. This function allow you to customize your own
    git branching rule and git commit rule, decide when to trigger the build.
    """
    logger.header("Detect whether we should trigger build", "-", 60)

    # won't trigger build direct commit
    if cc_event.is_commit_event:
        logger.info(
            f"we don't trigger build job for "
            f"event type {cc_event.event_type!r} on {cc_event.source_branch}"
        )
        return CodeCommitHandlerActionEnum.nothing
    # run build job if it is a Pull Request related event
    elif cc_event.is_pr_created_event or cc_event.is_pr_update_event:
        # we don't trigger if commit message has 'NO BUILD'
        if is_certain_semantic_commit(
            cc_event.commit_message,
            stub=SemanticCommitEnum.chore.value,
        ):
            logger.info(
                f"we DO NOT trigger build job for "
                f"commit message {SemanticCommitEnum.chore.value!r}"
            )
            return CodeCommitHandlerActionEnum.nothing

        # we don't trigger if source branch is not valid branch
        if not (
            cc_event.source_is_feature_branch
            or cc_event.source_is_develop_branch
            or cc_event.source_is_fix_branch
            or cc_event.source_is_build_branch
            or is_certain_semantic_branch(cc_event.source_branch, ["lbd", "lambda"])  # do Lambda Function stuff
            or is_certain_semantic_branch(cc_event.source_branch, ["layer",]) # build Lambda Layer
            or is_certain_semantic_branch(cc_event.source_branch, ["cf", "cft", "cloudformation"]) # deploy CloudFormation stack
            or cc_event.source_is_doc_branch
            or cc_event.source_is_release_branch
        ):
            logger.info(
                "we DO NOT trigger build job "
                f"if PR source branch is {cc_event.target_branch!r}"
            )
            return CodeCommitHandlerActionEnum.nothing

        # we don't trigger if target branch is not main
        if not cc_event.target_is_main_branch:
            logger.info(
                "we DO NOT trigger build job "
                "if PR target branch is not 'main' "
                f"it is {cc_event.target_branch!r}"
            )
            return CodeCommitHandlerActionEnum.nothing

        logger.info(
            f"we don't trigger build job for "
            f"event type {cc_event.event_type!r} on {cc_event.source_branch}"
        )
        return CodeCommitHandlerActionEnum.start_build
    # always trigger on PR merge event
    elif cc_event.is_pr_merged_event:
        logger.info(
            f"trigger build job for PR merged event, from branch "
            f"{cc_event.source_branch!r} to {cc_event.target_branch!r}"
        )
        return CodeCommitHandlerActionEnum.start_build
    # we don't trigger on other event
    elif (
        cc_event.is_create_branch_event
        or cc_event.is_delete_branch_event
        or cc_event.is_comment_event
        or cc_event.is_approve_pr_event
    ):
        logger.info(
            f"we don't trigger build job for " f"event type {cc_event.event_type!r}."
        )
        return CodeCommitHandlerActionEnum.nothing
    else:
        logger.info(
            f"we don't trigger build job for " f"event type {cc_event.event_type!r}."
        )
        return CodeCommitHandlerActionEnum.nothing
