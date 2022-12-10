# -*- coding: utf-8 -*-

import os

from aws_codecommit import CodeCommitEvent
from aws_codebuild import CodeBuildEvent
from boto_session_manager import BotoSesManager, AwsServiceEnum

from .sns_event import (
    extract_sns_message_dict,
    upload_ci_event,
)
from .codecommit_and_codebuild import (
    CodeCommitEventHandler,
    CodeBuildEventHandler,
)
from . import logger


S3_BUCKET = os.environ["S3_BUCKET"]
S3_PREFIX = os.environ["S3_PREFIX"]

bsm = BotoSesManager()


def lambda_handler(event: dict, context: dict):
    logger.header("START", "=", 60)

    logger.header("Parse SNS message", "-", 60)
    message_dict = extract_sns_message_dict(event)

    if message_dict["source"] == "aws.codecommit":
        ci_event = CodeCommitEvent.from_event(message_dict)
        ci_event.bsm = bsm
    elif message_dict["source"] == "aws.codebuild":
        ci_event = CodeBuildEvent.from_event(message_dict)
    else:  # pragma: no cover
        raise NotImplementedError

    upload_ci_event(
        s3_client=bsm.get_client(AwsServiceEnum.S3),
        event_dict=event,
        event_obj=ci_event,
        bucket=S3_BUCKET,
        prefix=S3_PREFIX,
    )

    if isinstance(ci_event, CodeCommitEvent):
        cc_event_handler = CodeCommitEventHandler(
            bsm=bsm,
            cc_event=ci_event,
        )
        cc_event_handler.execute()
    elif isinstance(ci_event, CodeBuildEvent):
        cc_event_handler = CodeBuildEventHandler(
            bsm=bsm,
            cb_event=ci_event,
        )
        cc_event_handler.execute()
    else:  # pragma: no cover
        raise NotImplementedError
