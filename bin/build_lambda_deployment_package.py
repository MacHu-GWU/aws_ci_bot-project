# -*- coding: utf-8 -*-

import os
import glob
import shutil
import subprocess
from pathlib import Path


dir_project_root = Path(__file__).absolute().parent.parent
path_requirements = dir_project_root / "requirements.txt"
path_lambda_handler_py = dir_project_root / "lambda_function.py"

dir_build = dir_project_root / "build"
dir_build_lambda = dir_build / "lambda"
dir_build_deployment_package = dir_build_lambda / "deploy"
path_lambda_handler_in_deployment_package = (
    dir_build_deployment_package / "lambda_function.py"
)

bin_pip = "pip"

if dir_build_deployment_package.exists():
    shutil.rmtree(dir_build_deployment_package)
else:
    dir_build_deployment_package.mkdir(parents=True)


def get_aws_ci_bot_version():
    path_version_file = dir_project_root / "aws_ci_bot" / "_version.py"
    args = ["python", f"{path_version_file}"]
    res = subprocess.run(args, capture_output=True)
    return res.stdout.decode("utf-8").strip()


__version__ = get_aws_ci_bot_version()

path_lambda_deployment_package = (
    dir_build_lambda / f"aws_ci_bot-lambda-{__version__}.zip"
)


def install_aws_ci_bot_dependencies():
    for line in path_requirements.read_text().strip().split("\n"):
        args = [
            f"{bin_pip}",
            "install",
            f"{line}",
            "--no-deps",
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
        "--target",
        f"{dir_build_deployment_package}",
    ]
    subprocess.run(args)

    path_lambda_handler_in_deployment_package.write_text(
        path_lambda_handler_py.read_text()
    )


def zip_deployment_package():
    os.chdir(dir_build_deployment_package)

    args = [
        "zip",
        f"{path_lambda_deployment_package}",
        "-r",
        "-9",
        "-q",
    ] + glob.glob("*")
    subprocess.run(args, check=True)


install_aws_ci_bot_dependencies()
install_aws_ci_bot()
zip_deployment_package()
