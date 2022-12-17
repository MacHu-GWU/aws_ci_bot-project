# -*- coding: utf-8 -*-

from boto_session_manager import BotoSesManager
from aws_ci_bot.bootstrap import (
    create_codecommit_repos,
    create_codebuild_projects,
    create_notifications,
)

bsm = BotoSesManager(profile_name="aws_data_lab_open_source_us_east_1")

repos = [
    "aws_ci_bot_test-project",
]
codebuild_iam_role = "arn:aws:iam::501105007192:role/codebuild-power-user"
sns_topic_arn = "arn:aws:sns:us-east-1:501105007192:aws-ci-bot"

create_codecommit_repos(bsm, repos)
create_codebuild_projects(bsm, repos, codebuild_iam_role)
create_notifications(bsm, repos, sns_topic_arn)
