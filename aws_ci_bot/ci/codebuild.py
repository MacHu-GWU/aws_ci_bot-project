# -*- coding: utf-8 -*-

import typing as T
import dataclasses


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
    jobs: T.List[BuildJobConfig] = dataclasses.field(default_factory=list)

    @classmethod
    def from_dict(cls, dct: dict) -> "CodebuildConfig":
        return cls(jobs=[BuildJobConfig.from_dict(d) for d in dct["jobs"]])
