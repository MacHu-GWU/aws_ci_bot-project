# -*- coding: utf-8 -*-

import typing as T
import hashlib

import attr
from attrs_mate import AttrsClass
from pathlib_mate import Path
from s3pathlib import S3Path, context
from boto_session_manager import BotoSesManager
import cottonformation as cf

from .paths import (
    dir_python_lib,
    path_requirements,
)
from .package import build_deployment_package
from .iac import Stack


@attr.s
class CodeBuildProject(AttrsClass):
    project_name: str = attr.ib()
    repo_name: str = attr.ib()
    environment_type: str = attr.ib()
    image_id: str = attr.ib()
    compute_type: str = attr.ib()
    privileged_mode: bool = attr.ib()
    timeout_in_minutes: int = attr.ib()
    queued_timeout_in_minutes: int = attr.ib()
    concurrent_build_limit: int = attr.ib()


@attr.s
class DeployConfig(AttrsClass):
    project_name: str = attr.ib()
    aws_profile: T.Optional[str] = attr.ib()
    aws_region: T.Optional[str] = attr.ib()
    s3_bucket: str = attr.ib()
    s3_prefix: str = attr.ib()
    codecommit_repo_list: T.List[str] = attr.ib(factory=list)
    codebuild_project_list: T.List[
        CodeBuildProject
    ] = CodeBuildProject.ib_list_of_nested(factory=list)


def get_project_md5(
    path_requirements_txt: Path,
    dir_python_lib: Path,
) -> str:
    """
    Get the aws_ci_bot deployment package md5 check sum.

    The md5 file is calculated based on the requirements.txt and the source code.
    """
    md5_list = list()
    md5_list.append(path_requirements_txt.md5)
    for p in Path.sort_by_abspath(dir_python_lib.select_by_ext(".py")):
        md5_list.append(p.md5)
    md5 = hashlib.md5()
    md5.update("-".join(md5_list).encode("utf-8"))
    return md5.hexdigest()


class UserAbortError(Exception):
    pass


def deploy_aws_ci_bot(
    deploy_config: DeployConfig,
):
    kwargs = dict()
    if deploy_config.aws_profile is not None:
        kwargs["profile_name"] = deploy_config.aws_profile
    if deploy_config.aws_region is not None:
        kwargs["region_name"] = deploy_config.aws_region
    bsm = BotoSesManager(**kwargs)
    context.attach_boto_session(bsm.boto_ses)

    print(f"❗ you are trying to deploy aws ci bot to {bsm.aws_account_id!r} {bsm.aws_region!r}")
    try:
        res = bsm.iam_client.list_account_aliases()
        account_alias = res["AccountAliases"][0]
        print(f"  the account alias is {account_alias!r}")
        decision = input("  continue? [y/n]: ").strip()
        if decision != "y":
            raise UserAbortError("🛑 user abort!")
    except UserAbortError as e:
        raise e
    except Exception:
        pass

    # build and upload lambda deployment package to S3
    # build
    path_lambda_deployment_package = build_deployment_package()
    # upload
    project_md5 = get_project_md5(path_requirements, dir_python_lib)
    s3path_deployment_package = S3Path(
        deploy_config.s3_bucket,
        deploy_config.s3_prefix,
        "lambda",
        path_lambda_deployment_package.stem,
        f"{project_md5}.zip",
    )
    s3path_deployment_package.upload_file(
        path=f"{path_lambda_deployment_package}",
        overwrite=True,
    )

    # Create CloudFormation template definition
    stack = Stack(
        deploy_config=deploy_config,
        s3_key_lambda_deployment_package=s3path_deployment_package.key,
    )

    tpl = cf.Template(
        Description="AWS CI Bot solution stack",
    )
    tpl.add(stack.rg_1_iam)
    tpl.add(stack.rg_2_sns)
    tpl.add(stack.rg_3_lambda)
    tpl.add(stack.rg_4_codecommit)
    tpl.add(stack.rg_5_codebuild)
    tpl.add(stack.rg_6_notification_rules)

    tpl.batch_tagging(
        tags=dict(ProjectName=deploy_config.project_name),
    )

    tpl.to_json_file("template.json")

    # Deploy CloudFormation stack
    env = cf.Env(bsm=bsm)
    env.deploy(
        stack_name=stack.stack_name,
        template=tpl,
        bucket=f"{bsm.aws_account_id}-{bsm.aws_region}-artifacts",
        include_named_iam=True,
        skip_prompt=True,
        timeout=180,
        change_set_timeout=180,
    )
