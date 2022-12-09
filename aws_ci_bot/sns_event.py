# -*- coding: utf-8 -*-

import typing as T
import json
from datetime import datetime

from aws_lambda_event import SNSTopicNotificationEvent
from aws_codebuild import CodeBuildEvent
from aws_codecommit import CodeCommitEvent

from .console import get_s3_console_url


def parse_sns_event(event: dict) -> T.Union[CodeCommitEvent, CodeBuildEvent]:
    sns_event = SNSTopicNotificationEvent(event)
    ci_event: dict = json.loads(sns_event.records[0].message)
    if ci_event["source"] == "aws.codecommit":
        return CodeCommitEvent.from_event(ci_event)
    elif ci_event["source"] == "aws.codebuild":
        return CodeBuildEvent.from_event(ci_event)
    else:  # pragma: no cover
        raise NotImplementedError


def encode_partition_key(dt: datetime) -> str:
    """
    Figure out the s3 partition part based on the given datetime.
    """
    return "/".join([
        f"year={dt.year}/"
        f"month={str(dt.month).zfill(2)}/"
        f"day={str(dt.day).zfill(2)}/"
    ])


def upload_ci_event(
    event_dict: dict,
    event_obj: T.Union[CodeCommitEvent, CodeBuildEvent],
    s3_client,
    bucket: str,
    prefix: str,
    logger,
    verbose: bool = True,
) -> str:
    """

    :param ci_event:
    :param event_obj:
    :param verbose:
    :return: S3 uri
    """

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
    else: # pragma: no cover
        raise NotImplementedError

    s3_client.put_object(
        Bucket=bucket,
        Key=s3_key,
        Body=json.dumps(event_dict, indent=4),
    )

    console_url = get_s3_console_url(bucket=bucket, prefix=s3_key)
    if verbose:
        logger.info(f"  preview event at: {console_url}")

    return f"s3://{bucket}/{s3_key}"
