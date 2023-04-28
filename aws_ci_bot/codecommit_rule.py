# -*- coding: utf-8 -*-

"""
This module defines how to response to CodeCommit event in different situations.
"""

import enum

from aws_codecommit import (
    CodeCommitEvent,
    is_certain_semantic_branch,
    is_certain_semantic_commit,
    SemanticCommitEnum,
)

from . import logger


class CodeCommitHandlerActionEnum(str, enum.Enum):
    nothing = "nothing"
    start_build = "start_build"


def check_what_to_do(cc_event: CodeCommitEvent) -> CodeCommitHandlerActionEnum:
    """
    Analyze the CodeCommit event, check what to do.

    This function determines when to trigger an AWS CodeBuild build job based
    on your custom Git branching and commit rules, as well as
    which branch, tag, or commit to build from. The default settings are suitable
    for most use cases, but you can customize the function by following
    the comments provided.

    This solution designed for any type of project for any programming language
    and for any Git Workflow.

    This function should take a ``CodeCommitEvent`` object as input, and return
    a ``CodeCommitHandlerActionEnum`` object.
    """
    logger.header("Detect whether we should trigger build", "-", 60)

    # ----------------------------------------------------------------------
    # We don't build if commit message has 'chore'
    # ----------------------------------------------------------------------
    if is_certain_semantic_commit(
        cc_event.commit_message,
        stub=SemanticCommitEnum.chore.value,
    ):
        logger.info(
            f"we DO NOT trigger build job for "
            f"commit message {SemanticCommitEnum.chore.value!r}"
        )
        return CodeCommitHandlerActionEnum.nothing

    # ==========================================================================
    # Case 1: direct commit to any branch
    #
    # either you write your own if/else logic here,
    # either you uncomment one and only one of the following block of code:
    # 1.1 (default), 1.2, 1.3
    # ==========================================================================
    if cc_event.is_commit_event:
        # ----------------------------------------------------------------------
        # 1.1 Don't build for direct commit
        # ----------------------------------------------------------------------

        logger.info(
            f"we don't trigger build job for "
            f"event type {cc_event.event_type!r} on {cc_event.source_branch}"
        )
        return CodeCommitHandlerActionEnum.nothing

        # ----------------------------------------------------------------------
        # 1.2 Only build for direct commit to main branch
        # ----------------------------------------------------------------------

        # if cc_event.source_is_main_branch:
        #     logger.info(f"trigger build for direct commit to main branch.")
        #     return CodeCommitHandlerActionEnum.start_build
        # else:
        #     logger.info(
        #         f"we don't trigger build job for: "
        #         f"event type is {cc_event.event_type!r}, "
        #         f"branch is {cc_event.source_branch!r}."
        #     )
        #     return CodeCommitHandlerActionEnum.nothing

        # ----------------------------------------------------------------------
        # 1.3 Only build for direct commit to the following pre-defined branch
        # ----------------------------------------------------------------------

        # if (
        #     cc_event.source_is_main_branch
        #     or is_certain_semantic_branch(cc_event.source_branch, ["dev",])
        #     or is_certain_semantic_branch(cc_event.source_branch, ["test", ])
        #     or is_certain_semantic_branch(cc_event.source_branch, ["prod", ])
        # ):
        #     logger.info(
        #         f"trigger build for direct commit to main, dev, test, prod branch."
        #     )
        #     return CodeCommitHandlerActionEnum.start_build
        # else:
        #     logger.info(
        #         f"we don't trigger build job for: "
        #         f"event type is {cc_event.event_type!r}, "
        #         f"branch is {cc_event.source_branch!r}."
        #     )
        #     return CodeCommitHandlerActionEnum.nothing

    # ==========================================================================
    # Case 2: Pull Request create / update event
    #
    # either you write your own if/else logic here,
    # either you uncomment one and only one of the following block of code:
    # 2.1, 2.2, 2.3 (default)
    # ==========================================================================
    elif cc_event.is_pr_created_event or cc_event.is_pr_update_event:
        # ----------------------------------------------------------------------
        # 2.1 Build for all Pull Request create / update event
        # ----------------------------------------------------------------------

        # return CodeCommitHandlerActionEnum.start_build

        # ----------------------------------------------------------------------
        # 2.2 Build for Pull Request create / update event only if the target
        # branch is 'main'.
        # ----------------------------------------------------------------------

        # if cc_event.target_is_main_branch:
        #     logger.info(f"trigger build for Pull request to main branch.")
        #     return CodeCommitHandlerActionEnum.start_build
        # else:
        #     logger.info(
        #         f"we don't trigger build for Pull request to a branch that is not 'main'."
        #     )
        #     return CodeCommitHandlerActionEnum.nothing

        # ----------------------------------------------------------------------
        # 2.3 Build for Pull Request create / update event only if the source
        # branch is the following pre-defined branch, regardless of the target branch
        # ----------------------------------------------------------------------
        if (
            # based on purpose
            cc_event.source_is_feature_branch
            or cc_event.source_is_fix_branch
            or cc_event.source_is_build_branch
            or cc_event.source_is_doc_branch
            or cc_event.source_is_release_branch
            or is_certain_semantic_branch(cc_event.source_branch, ["clean", "cleanup"])
            # based on environment
            or cc_event.source_is_develop_branch
            or is_certain_semantic_branch(cc_event.source_branch, ["test"])
            or is_certain_semantic_branch(cc_event.source_branch, ["int"])
            or is_certain_semantic_branch(cc_event.source_branch, ["stage", "staging"])
            or is_certain_semantic_branch(cc_event.source_branch, ["qa"])
            or is_certain_semantic_branch(cc_event.source_branch, ["preprod"])
            or is_certain_semantic_branch(cc_event.source_branch, ["prod"])
            or is_certain_semantic_branch(cc_event.source_branch, ["blue"])
            or is_certain_semantic_branch(cc_event.source_branch, ["green"])
            # based on semantic branch
            or is_certain_semantic_branch(cc_event.source_branch, ["dev"])
            or is_certain_semantic_branch(cc_event.source_branch, ["layer"])
            or is_certain_semantic_branch(cc_event.source_branch, ["lambda"])
            or is_certain_semantic_branch(cc_event.source_branch, ["glue"])
            or is_certain_semantic_branch(cc_event.source_branch, ["hil"])
            or is_certain_semantic_branch(cc_event.source_branch, ["ecr"])
            or is_certain_semantic_branch(cc_event.source_branch, ["batch"])
        ):
            logger.info(
                f"trigger build for pull request from {cc_event.source_branch!r} branch."
            )
            return CodeCommitHandlerActionEnum.start_build
        else:
            logger.info(
                "we DO NOT trigger build job "
                f"if PR source branch is {cc_event.target_branch!r}"
            )
            return CodeCommitHandlerActionEnum.nothing
    # ==========================================================================
    # Case 3: Pull Request merge event
    #
    # either you write your own if/else logic here,
    # either you uncomment one and only one of the following block of code:
    # 3.1 (default), 3.2
    # ==========================================================================
    elif cc_event.is_pr_merged_event:
        # ----------------------------------------------------------------------
        # 3.1 Build for all Pull Request merge event
        # ----------------------------------------------------------------------

        logger.info(
            f"trigger build job for PR merged event, from branch "
            f"{cc_event.source_branch!r} to {cc_event.target_branch!r}"
        )
        return CodeCommitHandlerActionEnum.start_build

        # ----------------------------------------------------------------------
        # 3.2 Build for Pull Request merge event only if the target branch is 'main'.
        # regardless of the source branch
        # ----------------------------------------------------------------------

        # if cc_event.target_is_main_branch:
        #     logger.info(
        #         f"trigger build job for PR merged event, from branch "
        #         f"{cc_event.source_branch!r} to {cc_event.target_branch!r}"
        #     )
        #     return CodeCommitHandlerActionEnum.start_build
        # else:
        #     logger.info(
        #         f"we don't trigger build job for PR merged event, from branch "
        #         f"{cc_event.source_branch!r} to {cc_event.target_branch!r}"
        #     )
        #     return CodeCommitHandlerActionEnum.nothing

    # ==========================================================================
    # Case 4: Other event
    #
    # either you write your own if/else logic here, either use the default
    # ==========================================================================
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
