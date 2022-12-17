# -*- coding: utf-8 -*-

import typing as T
import dataclasses

from superjson import json
from aws_codecommit import better_boto
from boto_session_manager import BotoSesManager

from . import logger


@dataclasses.dataclass
class BuildJobConfig:
    project_name: str = dataclasses.field()
    is_batch_job: bool = dataclasses.field()
    buildspec: T.Optional[str] = dataclasses.field(default=None)
    env_var: dict = dataclasses.field(default_factory=dict)

    @classmethod
    def from_dict(cls, dct: dict) -> "BuildJobConfig":
        return cls(
            project_name=dct["project_name"],
            is_batch_job=dct["is_batch_job"],
            buildspec=dct.get("buildspec"),
            env_var=dct.get("env_var", {}),
        )


@dataclasses.dataclass
class CodebuildConfig:
    """
    The ``codebuild-config.json`` file that defines which CodeBuild project
    it should use to run CI job. By default, it is at the root folder of the
    git repo.

    The data structure looks like this:

    .. code-block:: javascript

        {
            "jobs": [
                {
                    "project_name": "my-codebuild-project-name",
                    "is_batch_job": false,
                    "buildspec": "the path to the buildspec.yml file",
                    "env_var": {
                        "key1": "value1",
                        "key2": "value2"
                    }
                },
                {
                    ...
                },
                ...
            ]
    """

    jobs: T.List[BuildJobConfig] = dataclasses.field(default_factory=list)

    @classmethod
    def from_dict(cls, dct: dict) -> "CodebuildConfig":
        return cls(jobs=[BuildJobConfig.from_dict(d) for d in dct["jobs"]])

    @classmethod
    def from_codecommit_repo(
        cls,
        bsm: BotoSesManager,
        repo_name: str,
        commit_id: str,
    ) -> "CodebuildConfig":
        """
        Get the ``codebuild-config.json`` file from the CodeCommit repo.

        Read more about the :class:`~aws_ci_bot.code_build_config.CodebuildConfig`
        file.
        """
        file_path = "codebuild-config.json"
        logger.info(f"Get codebuild config from {file_path!r}")

        file = better_boto.get_file(
            bsm=bsm,
            repo_name=repo_name,
            file_path=file_path,
            commit_id=commit_id,
        )
        return CodebuildConfig.from_dict(
            json.loads(file.get_text(), ignore_comments=True)
        )
