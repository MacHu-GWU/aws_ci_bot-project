# -*- coding: utf-8 -*-

"""
An automation script that build the deployment package for Lambda Function.

This script requires Python3.7 + and no other dependencies.
"""

import os
import glob
import shutil
import subprocess

from pathlib_mate import Path

from .paths import (
    dir_project_root,
    path_requirements,
    path_lambda_handler_py,
    dir_build_lambda,
    dir_build_deployment_package,
    path_lambda_handler_in_deployment_package,
    bin_pip,
)


def clear_build_dir():
    if dir_build_lambda.exists():
        shutil.rmtree(dir_build_lambda)
    else:
        dir_build_lambda.mkdir(parents=True)


def get_aws_ci_bot_version() -> str:
    """
    Read the semantic version number from the ``aws_ci_bot/_version.py`` file.
    """
    path_version_file = dir_project_root / "aws_ci_bot" / "_version.py"
    args = ["python", f"{path_version_file}"]
    res = subprocess.run(args, capture_output=True)
    return res.stdout.decode("utf-8").strip()


def install_aws_ci_bot_dependencies():
    for line in path_requirements.read_text().strip().split("\n"):
        args = [
            f"{bin_pip}",
            "install",
            f"{line}",
            "--no-deps",
            "--disable-pip-version-check",
            "--target",
            f"{dir_build_deployment_package}",
        ]
        subprocess.run(args)


def install_aws_ci_bot():
    args = [
        f"{bin_pip}",
        "install",
        f"{dir_project_root}",
        "--no-deps",
        "--disable-pip-version-check",
        "--target",
        f"{dir_build_deployment_package}",
    ]
    subprocess.run(args)

    path_lambda_handler_in_deployment_package.write_text(
        path_lambda_handler_py.read_text()
    )


def zip_deployment_package() -> Path:
    """
    :return: the local file path to the lambda deployment package zip file
    """
    __version__ = get_aws_ci_bot_version()
    basename = f"aws_ci_bot-{__version__}-lambda-deployment-package.zip"
    path_lambda_deployment_package = dir_build_lambda.joinpath(basename)

    with dir_build_deployment_package.temp_cwd():
        args = [
            "zip",
            f"{path_lambda_deployment_package}",
            "-r",
            "-9",
            "-q",
        ] + glob.glob("*")
        subprocess.run(args, check=True)

    return path_lambda_deployment_package


def build_deployment_package() -> Path:
    """

    :return: the local file path to the lambda deployment package zip file
    """
    clear_build_dir()
    install_aws_ci_bot_dependencies()
    install_aws_ci_bot()
    return zip_deployment_package()
