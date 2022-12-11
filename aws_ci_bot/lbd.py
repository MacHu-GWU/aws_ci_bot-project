# -*- coding: utf-8 -*-

import os

from aws_codecommit import CodeCommitEvent
from aws_codebuild import CodeBuildEvent
from boto_session_manager import BotoSesManager, AwsServiceEnum

from .console import get_s3_console_url
from .sns_event import (
    extract_sns_message_dict,
    upload_ci_event,
)
from .codecommit_and_codebuild import (
    CodeCommitEventHandler,
    CodeBuildEventHandler,
    BuildJobRun,
)
from . import logger

S3_BUCKET = os.environ["S3_BUCKET"]
S3_PREFIX = os.environ["S3_PREFIX"]

bsm = BotoSesManager()


def lambda_handler(event: dict, context: dict):
    logger.header("START", "=", 60)

    logger.header("Parse SNS message", "-", 60)
    message_dict = extract_sns_message_dict(event)

    try:
        event["Records"][0]["Sns"]["Message"] = message_dict
    except:
        pass

    if message_dict["source"] == "aws.codecommit":
        ci_event = CodeCommitEvent.from_event(message_dict)
        ci_event.bsm = bsm
    elif message_dict["source"] == "aws.codebuild":
        ci_event = CodeBuildEvent.from_codebuid_notification_event(message_dict)
    else:  # pragma: no cover
        raise NotImplementedError

    s3_uri = upload_ci_event(
        s3_client=bsm.get_client(AwsServiceEnum.S3),
        event_dict=event,
        event_obj=ci_event,
        bucket=S3_BUCKET,
        prefix=S3_PREFIX,
    )
    s3_console_url = get_s3_console_url(s3_uri=s3_uri)

    if isinstance(ci_event, CodeCommitEvent):
        cc_event_handler = CodeCommitEventHandler(
            bsm=bsm,
            cc_event=ci_event,
            s3_console_url=s3_console_url,
        )
        cc_event_handler.execute()
    elif isinstance(ci_event, CodeBuildEvent):
        cb_event_handler = CodeBuildEventHandler(
            bsm=bsm,
            cb_event=ci_event,
            s3_console_url=s3_console_url,
            build_job_run=BuildJobRun.from_arn(ci_event.build_arn),
        )
        cb_event_handler.execute()
    else:  # pragma: no cover
        raise NotImplementedError
