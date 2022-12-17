# -*- coding: utf-8 -*-

"""
Allow user to quickly set up CodeCommit repo and CodeBuild project to use
along with aws_ci_bot solution
"""

import typing as T
from boto_session_manager import BotoSesManager


def _create_one_codecommit_repo(
    bsm: BotoSesManager,
    name: str,
):
    """
    Ref: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/codecommit.html#CodeCommit.Client.create_repository
    """
    return bsm.codecommit_client.create_repository(
        repositoryName=name,
    )


def create_codecommit_repos(
    bsm: BotoSesManager,
    repos: T.List[str],
):
    for repo in repos:
        try:
            print(f"Create CodeCommit Repository {repo!r}")
            _create_one_codecommit_repo(bsm, repo)
        except Exception as e:
            if f"Repository named {repo} already exists" in str(e):
                print(f"  already exists, skip")
            else:
                raise e


def _create_one_codebuild_project(
    bsm: BotoSesManager,
    repo: str,
    project: str,
    iam_role: str,
):
    """
    Ref: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/codebuild.html#CodeBuild.Client.create_project
    """
    bsm.codebuild_client.create_project(
        name=project,
        source=dict(
            type="CODECOMMIT",
            location=f"https://git-codecommit.{bsm.aws_region}.amazonaws.com/v1/repos/{repo}",
        ),
        sourceVersion="refs/heads/main",
        environment=dict(
            type="LINUX_CONTAINER",
            image="aws/codebuild/amazonlinux2-x86_64-standard:3.0",
            computeType="BUILD_GENERAL1_MEDIUM",
            privilegedMode=True,
        ),
        artifacts=dict(
            type="NO_ARTIFACTS",
        ),
        serviceRole=iam_role,
        timeoutInMinutes=15,
        queuedTimeoutInMinutes=30,
        concurrentBuildLimit=20,
    )


def create_codebuild_projects(
    bsm: BotoSesManager,
    repos: T.List[str],
    codebuild_iam_role: str,
):
    for repo in repos:
        project = repo
        try:
            print(f"Create CodeBuild Project {project!r}")
            _create_one_codebuild_project(
                bsm,
                repo=repo,
                project=project,
                iam_role=codebuild_iam_role,
            )
        except Exception as e:
            if f"Project already exists" in str(e):
                print(f"  already exists, skip")
            else:
                raise e


def create_notifications(
    bsm: BotoSesManager,
    repos: T.List[str],
    sns_topic_arn: str,
):

    for repo in repos:
        project = repo
        try:
            name = f"{repo}-codecommit-all-event"
            print(f"Create Notification event {name}")
            bsm.codestar_notifications_client.create_notification_rule(
                Name=name,
                Resource=f"arn:aws:codecommit:{bsm.aws_region}:{bsm.aws_account_id}:repo",
                Targets=[
                    dict(
                        TargetType="SNS",
                        TargetAddress=sns_topic_arn,
                    )
                ],
                DetailType="FULL",
                EventTypeIds=[
                    "codecommit-repository-branches-and-tags-created",
                    "codecommit-repository-branches-and-tags-updated",
                    "codecommit-repository-branches-and-tags-deleted",
                    "codecommit-repository-pull-request-created",
                    "codecommit-repository-pull-request-status-changed",
                    "codecommit-repository-pull-request-source-updated",
                    "codecommit-repository-pull-request-merged",
                    "codecommit-repository-comments-on-pull-requests",
                    "codecommit-repository-comments-on-commits",
                    "codecommit-repository-approvals-rule-override",
                    "codecommit-repository-approvals-status-changed",
                ],
            )
        except Exception as e:
            if "already exists" in str(e):
                print("  already exists, skip")
            else:
                raise e

        try:
            name = f"{project}-codebuild-all-event"
            print(f"Create Notification event {name}")
            bsm.codestar_notifications_client.create_notification_rule(
                Name=name,
                Resource=f"arn:aws:codebuild:{bsm.aws_region}:{bsm.aws_account_id}:project/{project}",
                Targets=[
                    dict(
                        TargetType="SNS",
                        TargetAddress=sns_topic_arn,
                    )
                ],
                DetailType="FULL",
                EventTypeIds=[
                    "codebuild-project-build-state-in-progress",
                    "codebuild-project-build-state-failed",
                    "codebuild-project-build-state-succeeded",
                    "codebuild-project-build-state-stopped",
                    "codebuild-project-build-phase-failure",
                    "codebuild-project-build-phase-success",
                ],
            )
        except Exception as e:
            if "already exists" in str(e):
                print("  already exists, skip")
            else:
                raise e
