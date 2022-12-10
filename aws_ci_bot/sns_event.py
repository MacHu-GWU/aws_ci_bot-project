# -*- coding: utf-8 -*-

import typing as T
import json
from datetime import datetime

from aws_lambda_event import SNSTopicNotificationEvent
from aws_codebuild import CodeBuildEvent
from aws_codecommit import CodeCommitEvent

from .console import get_s3_console_url
from . import logger


def extract_sns_message_dict(event: dict) -> dict:
    """
    :param event: the original lambda function input payload
    :return: the sns message data in dict
    """
    sns_event = SNSTopicNotificationEvent(event)
    return json.loads(sns_event.records[0].message)


def encode_partition_key(dt: datetime) -> str:
    """
    Figure out the s3 partition part based on the given datetime.
    """
    return "/".join(
        [
            f"year={dt.year}/"
            f"month={str(dt.month).zfill(2)}/"
            f"day={str(dt.day).zfill(2)}/"
        ]
    )


def upload_ci_event(
    s3_client,
    event_dict: dict,
    event_obj: T.Union[CodeCommitEvent, CodeBuildEvent],
    bucket: str,
    prefix: str,
    verbose: bool = True,
) -> str:
    """
    Upload CI/CD lambda event to S3 as a backup.

    :param s3_client:
    :param event_dict:
    :param event_obj:
    :param bucket:
    :param prefix:
    :param verbose:
    :return: S3 uri
    """
    if verbose:
        logger.info("Upload CI event to S3")

    if prefix.endswith("/"):
        prefix = prefix[:-1]

    utc_now = datetime.utcnow()
    time_str = utc_now.strftime("%Y-%m-%dT%H-%M-%S.%f")

    if isinstance(event_obj, CodeCommitEvent):
        s3_key = (
            f"{prefix}/codecommit/{event_obj.repo_name}/"
            f"{encode_partition_key(utc_now)}/"
            f"{time_str}_{event_obj.repo_name}.json"
        )
    elif isinstance(event_obj, CodeBuildEvent):
        s3_key = (
            f"{prefix}/codebuild/{event_obj.buildProject}/"
            f"{encode_partition_key(utc_now)}/"
            f"{time_str}_{event_obj.buildId}.json"
        )
    else:  # pragma: no cover
        raise NotImplementedError

    s3_client.put_object(
        Bucket=bucket,
        Key=s3_key,
        Body=json.dumps(event_dict, indent=4),
    )

    console_url = get_s3_console_url(bucket=bucket, prefix=s3_key)
    if verbose:
        logger.info(f"preview event at: {console_url}", 1)

    return f"s3://{bucket}/{s3_key}"
