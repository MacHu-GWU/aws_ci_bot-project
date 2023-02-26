# -*- coding: utf-8 -*-

"""
An automation script automatically configure CodeCommit repositories and
CodeBuild projects to use ``aws_ci_bot`` solution.

Use this only when you DON't use the infrastructure as code way to deploy the solution.
"""

from boto_session_manager import BotoSesManager
from aws_ci_bot.bootstrap import (
    create_codecommit_repos,
    create_codebuild_projects,
    create_notifications,
    delete_notification_rules,
)

# please manually enter the following parameters
repos = [
    "aws_ci_bot_test-project",
]
codebuild_iam_role = "arn:aws:iam::111122223333:role/codebuild-power-user"
sns_topic_arn = "arn:aws:sns:us-east-1:111122223333:aws-ci-bot"

bsm = BotoSesManager()

# create_codecommit_repos(bsm, repos)
# create_codebuild_projects(bsm, repos, codebuild_iam_role)
# create_notifications(bsm, repos, sns_topic_arn)
# delete_notification_rules(bsm, repos)
