# -*- coding: utf-8 -*-

"""
An automation script that build the deployment package for Lambda Function.

This script requires Python3.7 + and no other dependencies.
"""

from pathlib_mate import Path


dir_project_root = Path.dir_here(__file__).parent.parent

dir_python_lib = dir_project_root / "aws_ci_bot"
path_requirements = dir_project_root / "requirements.txt"
path_lambda_handler_py = dir_project_root / "lambda_function.py"

dir_build = dir_project_root / "build"
dir_build_lambda = dir_build / "lambda"
dir_build_deployment_package = dir_build_lambda / "deploy"
path_lambda_handler_in_deployment_package = (
    dir_build_deployment_package / "lambda_function.py"
)

bin_pip = "pip"
