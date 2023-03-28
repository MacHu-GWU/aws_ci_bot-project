# -*- coding: utf-8 -*-

from pathlib_mate import Path
from superjson import json

from aws_ci_bot.deploy.script import DeployConfig, deploy_aws_ci_bot


path_deploy_config_json = Path.dir_here(__file__).joinpath("deploy-config.json")
deploy_config = DeployConfig.from_dict(
    json.loads(path_deploy_config_json.read_text(), ignore_comments=True)
)
deploy_aws_ci_bot(deploy_config, timeout=180)
