# -*- coding: utf-8 -*-

import typing as T
import sys
import hashlib
import subprocess
from pathlib import Path

import attr
import cottonformation as cf
from cottonformation.res import (
    sns,
    awslambda,
    iam,
)

from build_lambda_deployment_package import (
    path_lambda_deployment_package,
    install_aws_ci_bot_dependencies,
    install_aws_ci_bot,
    zip_deployment_package,
)


def get_md5(path: Path) -> str:
    m = hashlib.md5()
    m.update(path.read_bytes())
    return m.hexdigest()


@attr.s
class Stack(cf.Stack):
    """ """

    project_name: str = attr.ib(default=None)
    s3_bucket: str = attr.ib(default=None)
    s3_prefix: str = attr.ib(default=None)
    s3_key_lambda_deployment_package: str = attr.ib(default=None)
    codecommit_repo_list: T.List[str] = attr.ib(factory=list)
    codebuild_project_list: T.List[str] = attr.ib(factory=list)

    @property
    def project_name_slug(self) -> str:
        return self.project_name.replace("_", "-")

    @property
    def stack_name(self) -> str:
        return self.project_name_slug

    def make_rg_1_iam(self):
        self.rg_1_iam = cf.ResourceGroup("RG1")

        self.iam_role_for_lambda = iam.Role(
            "IamRoleForLambda",
            p_RoleName=f"{self.project_name_slug}-lambda-role",
            rp_AssumeRolePolicyDocument=cf.helpers.iam.AssumeRolePolicyBuilder(
                cf.helpers.iam.ServicePrincipal.awslambda(),
            ).build(),
        )
        self.rg_1_iam.add(self.iam_role_for_lambda)

        s3_statement = {
            "Sid": "VisualEditor2",
            "Effect": "Allow",
            "Action": ["s3:PutObject"],
            "Resource": [f"arn:aws:s3:::{self.s3_bucket}/*"],
        }

        if len(self.codecommit_repo_list):
            codecommit_resource = [
                cf.Sub(
                    string="arn:aws:codecommit:${aws_region}:${aws_account_id}:${repo_name}",
                    data=dict(
                        aws_region=cf.AWS_REGION,
                        aws_account_id=cf.AWS_ACCOUNT_ID,
                        repo_name=repo_name,
                    ),
                )
                for repo_name in self.codecommit_repo_list
            ]
        else:
            codecommit_resource = [
                cf.Sub(
                    string="arn:aws:codecommit:${aws_region}:${aws_account_id}:*",
                    data=dict(
                        aws_region=cf.AWS_REGION,
                        aws_account_id=cf.AWS_ACCOUNT_ID,
                    ),
                )
            ]

        codecommit_statement = {
            "Sid": "VisualEditor3",
            "Effect": "Allow",
            "Action": [
                "codecommit:GetCommit",
                "codecommit:GetFile",
                "codecommit:PostCommentForPullRequest",
                "codecommit:PostCommentForComparedCommit",
                "codecommit:PostCommentReply",
                "codecommit:UpdateComment",
            ],
            "Resource": codecommit_resource,
        }

        if len(self.codebuild_project_list):
            codebuild_resource = [
                cf.Sub(
                    string="arn:aws:codebuild:${aws_region}:${aws_account_id}:project/${project_name}",
                    data=dict(
                        aws_region=cf.AWS_REGION,
                        aws_account_id=cf.AWS_ACCOUNT_ID,
                        project_name=project_name,
                    ),
                )
                for project_name in self.codebuild_project_list
            ]
        else:
            codebuild_resource = [
                cf.Sub(
                    string="arn:aws:codebuild:${aws_region}:${aws_account_id}:project/*",
                    data=dict(
                        aws_region=cf.AWS_REGION,
                        aws_account_id=cf.AWS_ACCOUNT_ID,
                    ),
                )
            ]

        codebuild_statement = {
            "Sid": "VisualEditor4",
            "Effect": "Allow",
            "Action": [
                "codebuild:StartBuild",
                "codebuild:StartBuildBatch",
                "codebuild:BatchGetBuilds",
                "codebuild:BatchGetBuildBatches",
            ],
            "Resource": codebuild_resource,
        }

        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "VisualEditor1",
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogStream",
                        "logs:CreateLogGroup",
                        "logs:PutLogEvents",
                    ],
                    "Resource": "*",
                },
                s3_statement,
                codecommit_statement,
                codebuild_statement,
            ],
        }

        self.iam_policy_for_lambda = iam.Policy(
            "IamPolicyForLambda",
            rp_PolicyName=f"{self.project_name_slug}-lambda-policy",
            rp_PolicyDocument=policy_document,
            p_Roles=[
                self.iam_role_for_lambda.ref(),
            ],
            ra_DependsOn=self.iam_role_for_lambda,
        )
        self.rg_1_iam.add(self.iam_policy_for_lambda)

    def make_rg_2_sns(self):
        self.rg_2_sns = cf.ResourceGroup("RG2")

        self.sns_topic = sns.Topic(
            "SNSTopic",
            p_TopicName=f"{self.project_name_slug}",
            p_FifoTopic=False,
        )
        self.rg_2_sns.add(self.sns_topic)

        self.output_sns_topic_arn = cf.Output(
            "SNSTopicArn",
            Value=self.sns_topic.rv_TopicArn,
        )
        self.rg_2_sns.add(self.output_sns_topic_arn)

        self.sns_topic_policy = sns.TopicPolicy(
            "SNSTopicPolicy",
            rp_PolicyDocument={
                "Version": "2008-10-17",
                "Statement": [
                    {
                        "Sid": "CodeNotification_publish",
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "codestar-notifications.amazonaws.com"
                        },
                        "Action": "SNS:Publish",
                        "Resource": cf.Sub(
                            string="arn:aws:sns:${aws_region}:${aws_account_id}:${sns_topic_name}",
                            data=dict(
                                aws_region=cf.AWS_REGION,
                                aws_account_id=cf.AWS_ACCOUNT_ID,
                                sns_topic_name=self.sns_topic.rv_TopicName,
                            ),
                        ),
                    }
                ],
            },
            rp_Topics=[
                self.sns_topic.rv_TopicArn,
            ],
            ra_DependsOn=self.sns_topic,
        )
        self.rg_2_sns.add(self.sns_topic_policy)

    def make_rg3_lambda(self):
        self.rg_3_lambda = cf.ResourceGroup("RG3")

        self.lbd_func = awslambda.Function(
            "LambdaFunction",
            rp_Code=awslambda.PropFunctionCode(
                p_S3Bucket=self.s3_bucket,
                p_S3Key=self.s3_key_lambda_deployment_package,
            ),
            rp_Role=self.iam_role_for_lambda.rv_Arn,
            p_FunctionName=f"{self.project_name_slug}",
            p_Runtime="python3.8",
            p_Handler="lambda_function.lambda_handler",
            p_Timeout=10,
            p_MemorySize=128,
            p_Environment=awslambda.PropFunctionEnvironment(
                p_Variables=dict(
                    S3_BUCKET=self.s3_bucket,
                    S3_PREFIX=self.s3_prefix,
                ),
            ),
            p_PackageType="Zip",
            ra_DependsOn=[
                self.iam_role_for_lambda,
                self.sns_topic,
            ],
        )
        self.rg_3_lambda.add(self.lbd_func)

        self.sns_subscription = sns.Subscription(
            "SNSSubscriptionForLambda",
            rp_Protocol="lambda",
            rp_TopicArn=self.sns_topic.rv_TopicArn,
            p_Endpoint=self.lbd_func.rv_Arn,
            ra_DependsOn=[
                self.sns_topic,
                self.lbd_func,
            ],
        )
        self.rg_3_lambda.add(self.sns_subscription)

        self.lambda_permission_for_sns_topic = (
            cf.helpers.awslambda.create_permission_for_sns(
                logic_id="LambdaPermissionForSNSTopic",
                func=self.lbd_func,
                topic=self.sns_topic,
            )
        )
        self.rg_3_lambda.add(self.lambda_permission_for_sns_topic)

    def post_hook(self):
        self.make_rg_1_iam()
        self.make_rg_2_sns()
        self.make_rg3_lambda()


if __name__ == "__main__":
    import json
    from pathlib import Path
    from boto_session_manager import BotoSesManager

    from s3pathlib import S3Path, context

    dir_project_root = Path(__file__).absolute().parent.parent
    path_config_json = dir_project_root / "deploy" / "deploy-config.json"

    bsm = BotoSesManager(profile_name="aws_data_lab_open_source_us_east_1")
    context.attach_boto_session(bsm.boto_ses)

    # Build deployment package
    install_aws_ci_bot_dependencies()
    install_aws_ci_bot()
    zip_deployment_package()

    # Read deployment config
    deploy_config: dict = json.loads(path_config_json.read_text())

    # Upload lambda deployment package to S3
    s3path_deployment_package = S3Path(
        deploy_config["s3_bucket"],
        deploy_config["s3_prefix"],
        "lambda",
        path_lambda_deployment_package.stem,
        f"{get_md5(path_lambda_deployment_package)}.zip",
    )

    s3path_deployment_package.upload_file(
        path=f"{path_lambda_deployment_package}",
        overwrite=True,
    )

    # Create template definition
    stack = Stack(
        project_name=deploy_config["project_name"],
        s3_bucket=deploy_config["s3_bucket"],
        s3_prefix=deploy_config["s3_prefix"],
        s3_key_lambda_deployment_package=s3path_deployment_package.key,
        codecommit_repo_list=deploy_config["codecommit_repo_list"],
        codebuild_project_list=deploy_config["codebuild_project_list"],
    )

    tpl = cf.Template(
        Description="AWS CI Bot solution stack",
    )
    tpl.add(stack.rg_1_iam)
    tpl.add(stack.rg_2_sns)
    tpl.add(stack.rg_3_lambda)

    tpl.batch_tagging(
        tags=dict(ProjectName=stack.project_name),
    )

    # Deploy CloudFormation stack
    env = cf.Env(bsm=bsm)
    env.deploy(
        stack_name=stack.stack_name,
        template=tpl,
        include_named_iam=True,
        skip_prompt=True,
    )
