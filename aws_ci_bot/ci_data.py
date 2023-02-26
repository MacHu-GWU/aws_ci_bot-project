# -*- coding: utf-8 -*-

import typing as T
import dataclasses

CI_DATA_PREFIX = "CI_DATA_"


@dataclasses.dataclass
class CIData:
    """
    CI related data, will be available in environment variable.

    It is a simple data container that allow you to pass data into
    codebuild job run, or read CIData from env var when you are running
    automation script in job run.

    :param comment_id: the comment is the thread created when received
        CodeCommit event. it will send to the Environment Variable for CodeBuild
        job run, and all of sub-sequence CodeBuild event will reply
        to this comment.

    All attributes have a default value None, because if it is None,
    it won't be used in environment variable
    """
    event_s3_console_url: T.Optional[str] = dataclasses.field(default=None)
    event_s3_uri: T.Optional[str] = dataclasses.field(default=None)
    event_type: T.Optional[str] = dataclasses.field(default=None)
    comment_id: T.Optional[str] = dataclasses.field(default=None)
    commit_id: T.Optional[str] = dataclasses.field(default=None)
    commit_message: T.Optional[str] = dataclasses.field(default=None)
    committer_name: T.Optional[str] = dataclasses.field(default=None)
    branch_name: T.Optional[str] = dataclasses.field(default=None)
    pr_id: T.Optional[str] = dataclasses.field(default=None)
    pr_from_branch: T.Optional[str] = dataclasses.field(default=None)
    pr_to_branch: T.Optional[str] = dataclasses.field(default=None)
    pr_from_commit_id: T.Optional[str] = dataclasses.field(default=None)
    pr_to_commit_id: T.Optional[str] = dataclasses.field(default=None)

    def to_env_var(
        self,
        prefix: str = CI_DATA_PREFIX,
    ) -> dict:
        """
        env_var is a dict of environment variable key value pair.
        """
        env_var = dict()
        for attr, value in dataclasses.asdict(self).items():
            if bool(value):
                key = (prefix + attr).upper()
                env_var[key] = value
        return env_var

    @classmethod
    def from_env_var(
        cls,
        env_var: dict,
        prefix: str = CI_DATA_PREFIX,
    ) -> "CIData":
        """
        env_var is a dict of environment variable key value pair.
        """
        field_set = {field.name for field in dataclasses.fields(cls)}
        kwargs = dict()
        for field_name in field_set:
            key = (prefix + field_name).upper()
            if key in env_var:
                kwargs[field_name] = env_var[key]
        return cls(**kwargs)
