# -*- coding: utf-8 -*-

import typing as T
import hashlib

import attr
from pathlib_mate import Path
import cottonformation as cf
from cottonformation.res import (
    sns,
    awslambda,
    iam,
    codecommit,
    codebuild,
    codestarnotifications,
)

from build_lambda_deployment_package import (
    path_lambda_deployment_package,
    install_aws_ci_bot_dependencies,
    install_aws_ci_bot,
    zip_deployment_package,
)


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


@attr.s
class CodeBuildProject:
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
class Stack(cf.Stack):
    """ """

    project_name: str = attr.ib(default=None)
    s3_bucket: str = attr.ib(default=None)
    s3_prefix: str = attr.ib(default=None)
    s3_key_lambda_deployment_package: str = attr.ib(default=None)
    codecommit_repo_list: T.List[str] = attr.ib(factory=list)
    codebuild_project_list: T.List[CodeBuildProject] = attr.ib(factory=list)

    @classmethod
    def from_deploy_config(cls, deploy_config: dict) -> "Stack":
        return cls(
            project_name=deploy_config["project_name"],
            s3_bucket=deploy_config["s3_bucket"],
            s3_prefix=deploy_config["s3_prefix"],
            s3_key_lambda_deployment_package=s3path_deployment_package.key,
            codecommit_repo_list=deploy_config["codecommit_repo_list"],
            codebuild_project_list=[
                CodeBuildProject(**dct)
                for dct in deploy_config["codebuild_project_list"]
            ],
        )

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
                        project_name=codebuild_project.project_name,
                    ),
                )
                for codebuild_project in self.codebuild_project_list
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

        self.iam_role_for_codebuild = iam.Role(
            "IamRoleForCodeBuild",
            p_RoleName=f"{self.project_name_slug}-codebuild-role",
            rp_AssumeRolePolicyDocument=cf.helpers.iam.AssumeRolePolicyBuilder(
                cf.helpers.iam.ServicePrincipal.codebuild(),
            ).build(),
            p_ManagedPolicyArns=[
                cf.helpers.iam.AwsManagedPolicy.CloudWatchFullAccess,
            ],
        )
        self.rg_1_iam.add(self.iam_role_for_codebuild)

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

        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "VisualEditor1",
                    "Effect": "Allow",
                    "Action": [
                        "codecommit:CreateBranch",
                        "codecommit:DeleteCommentContent",
                        "codecommit:UpdatePullRequestApprovalRuleContent",
                        "codecommit:PutFile",
                        "codecommit:GetPullRequestApprovalStates",
                        "codecommit:CreateCommit",
                        "codecommit:BatchDescribeMergeConflicts",
                        "codecommit:GetCommentsForComparedCommit",
                        "codecommit:DeletePullRequestApprovalRule",
                        "codecommit:GetCommentReactions",
                        "codecommit:GetComment",
                        "codecommit:UpdateComment",
                        "codecommit:MergePullRequestByThreeWay",
                        "codecommit:UpdateRepositoryDescription",
                        "codecommit:CreatePullRequest",
                        "codecommit:UpdatePullRequestApprovalState",
                        "codecommit:GetPullRequestOverrideState",
                        "codecommit:PostCommentForPullRequest",
                        "codecommit:GetRepositoryTriggers",
                        "codecommit:UpdatePullRequestDescription",
                        "codecommit:GetObjectIdentifier",
                        "codecommit:BatchGetPullRequests",
                        "codecommit:GetFile",
                        "codecommit:GetUploadArchiveStatus",
                        "codecommit:MergePullRequestBySquash",
                        "codecommit:GetDifferences",
                        "codecommit:GetRepository",
                        "codecommit:UpdateRepositoryName",
                        "codecommit:GetMergeConflicts",
                        "codecommit:GetMergeCommit",
                        "codecommit:PostCommentForComparedCommit",
                        "codecommit:GitPush",
                        "codecommit:GetMergeOptions",
                        "codecommit:AssociateApprovalRuleTemplateWithRepository",
                        "codecommit:PutCommentReaction",
                        "codecommit:GetTree",
                        "codecommit:BatchAssociateApprovalRuleTemplateWithRepositories",
                        "codecommit:CreateRepository",
                        "codecommit:GetReferences",
                        "codecommit:GetBlob",
                        "codecommit:DescribeMergeConflicts",
                        "codecommit:UpdatePullRequestTitle",
                        "codecommit:GetCommit",
                        "codecommit:OverridePullRequestApprovalRules",
                        "codecommit:GetCommitHistory",
                        "codecommit:GetCommitsFromMergeBase",
                        "codecommit:BatchGetCommits",
                        "codecommit:TestRepositoryTriggers",
                        "codecommit:DescribePullRequestEvents",
                        "codecommit:UpdatePullRequestStatus",
                        "codecommit:CreatePullRequestApprovalRule",
                        "codecommit:UpdateDefaultBranch",
                        "codecommit:GetPullRequest",
                        "codecommit:PutRepositoryTriggers",
                        "codecommit:UploadArchive",
                        "codecommit:MergeBranchesBySquash",
                        "codecommit:GitPull",
                        "codecommit:BatchGetRepositories",
                        "codecommit:DeleteRepository",
                        "codecommit:GetCommentsForPullRequest",
                        "codecommit:BatchDisassociateApprovalRuleTemplateFromRepositories",
                        "codecommit:CancelUploadArchive",
                        "codecommit:GetFolder",
                        "codecommit:PostCommentReply",
                        "codecommit:MergeBranchesByFastForward",
                        "codecommit:CreateUnreferencedMergeCommit",
                        "codecommit:EvaluatePullRequestApprovalRules",
                        "codecommit:MergeBranchesByThreeWay",
                        "codecommit:GetBranch",
                        "codecommit:DisassociateApprovalRuleTemplateFromRepository",
                        "codecommit:MergePullRequestByFastForward",
                        "codecommit:DeleteFile",
                        "codecommit:DeleteBranch",
                    ],
                    "Resource": codecommit_resource,
                }
            ],
        }

        self.iam_policy_for_codebuild = iam.Policy(
            "IamPolicyForCodeBuild",
            rp_PolicyName=f"{self.project_name_slug}-codebuild-policy",
            rp_PolicyDocument=policy_document,
            p_Roles=[
                self.iam_role_for_codebuild.ref(),
            ],
            ra_DependsOn=self.iam_role_for_codebuild,
        )
        self.rg_1_iam.add(self.iam_policy_for_codebuild)

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

    def make_rg_3_lambda(self):
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

    def make_rg_4_codecommit(self):
        self.rg_4_codecommit = cf.ResourceGroup("RG4")

        self.codecommit_repos: T.List[codecommit.Repository] = list()
        for repo_name in self.codecommit_repo_list:
            repo = codecommit.Repository(
                "CodeCommitRepo{}".format(repo_name.replace("_", "").replace("-", "")),
                rp_RepositoryName=repo_name,
                ra_DeletionPolicy=cf.DeletionPolicyEnum.Retain,
            )
            self.codecommit_repos.append(repo)
            self.rg_4_codecommit.add(repo)

    def make_rg_5_codebuild(self):
        self.rg_5_codebuild = cf.ResourceGroup("RG5")

        self.codebuild_projects: T.List[codebuild.Project] = list()
        for codebuild_project in self.codebuild_project_list:
            project = codebuild.Project(
                "CodeBuildProject{}".format(
                    codebuild_project.project_name.replace("_", "").replace("-", "")
                ),
                p_Name=codebuild_project.project_name,
                rp_Source=codebuild.PropProjectSource(
                    rp_Type="CODECOMMIT",
                    p_Location=cf.Sub(
                        string="https://git-codecommit.${aws_region}.amazonaws.com/v1/repos/${repo_name}",
                        data=dict(
                            aws_region=cf.AWS_REGION,
                            repo_name=codebuild_project.repo_name,
                        ),
                    ),
                ),
                rp_Environment=codebuild.PropProjectEnvironment(
                    rp_Type=codebuild_project.environment_type,
                    rp_Image=codebuild_project.image_id,
                    rp_ComputeType=codebuild_project.compute_type,
                    p_PrivilegedMode=codebuild_project.privileged_mode,
                ),
                rp_Artifacts=codebuild.PropProjectArtifacts(rp_Type="NO_ARTIFACTS"),
                rp_ServiceRole=self.iam_role_for_codebuild.rv_Arn,
                p_SourceVersion="refs/heads/main",
                p_TimeoutInMinutes=codebuild_project.timeout_in_minutes,
                p_QueuedTimeoutInMinutes=codebuild_project.queued_timeout_in_minutes,
                p_ConcurrentBuildLimit=codebuild_project.concurrent_build_limit,
                ra_DeletionPolicy=cf.DeletionPolicyEnum.Retain,
                ra_DependsOn=[
                    self.iam_role_for_codebuild,
                ],
            )
            self.codebuild_projects.append(project)
            self.rg_5_codebuild.add(project)

    def make_rg_6_notification_rules(self):
        self.rg_6_notification_rules = cf.ResourceGroup("RG6")

        self.notification_rules: T.List[codestarnotifications.NotificationRule] = list()

        for ith, repo_name in enumerate(self.codecommit_repo_list):
            notification_rule = codestarnotifications.NotificationRule(
                "CodeCommitNotificationRule{}".format(
                    repo_name.replace("_", "").replace("-", "")
                ),
                rp_Name=f"{repo_name}-codecommit-all-event",
                rp_Resource=cf.Sub(
                    string="arn:aws:codecommit:${aws_region}:${aws_account_id}:${repo}",
                    data=dict(
                        aws_region=cf.AWS_REGION,
                        aws_account_id=cf.AWS_ACCOUNT_ID,
                        repo=repo_name,
                    ),
                ),
                rp_Targets=[
                    codestarnotifications.PropNotificationRuleTarget(
                        rp_TargetType="SNS",
                        rp_TargetAddress=self.sns_topic.rv_TopicArn,
                    )
                ],
                rp_DetailType="FULL",
                rp_EventTypeIds=[
                    "codecommit-repository-branches-and-tags-created",
                    "codecommit-repository-branches-and-tags-updated",
                    "codecommit-repository-branches-and-tags-deleted",
                    "codecommit-repository-pull-request-created",
                    "codecommit-repository-pull-request-status-changed",
                    "codecommit-repository-pull-request-source-updated",
                    "codecommit-repository-pull-request-merged",
                    "codecommit-repository-comments-on-pull-requests",
                    "codecommit-repository-comments-on-commits",
                    "codecommit-repository-approvals-rule-override",
                    "codecommit-repository-approvals-status-changed",
                ],
                ra_DependsOn=[
                    self.sns_topic,
                    self.codecommit_repos[ith],
                ],
            )
            self.notification_rules.append(notification_rule)
            self.rg_6_notification_rules.add(notification_rule)

        for ith, codebuild_project in enumerate(self.codebuild_project_list):
            notification_rule = codestarnotifications.NotificationRule(
                "CodeProjectNotificationRule{}".format(
                    codebuild_project.project_name.replace("_", "").replace("-", "")
                ),
                rp_Name=f"{codebuild_project.project_name}-codebuild-all-event",
                rp_Resource=cf.Sub(
                    string="arn:aws:codebuild:${aws_region}:${aws_account_id}:project/${project}",
                    data=dict(
                        aws_region=cf.AWS_REGION,
                        aws_account_id=cf.AWS_ACCOUNT_ID,
                        project=codebuild_project.project_name,
                    ),
                ),
                rp_Targets=[
                    codestarnotifications.PropNotificationRuleTarget(
                        rp_TargetType="SNS",
                        rp_TargetAddress=self.sns_topic.rv_TopicArn,
                    )
                ],
                rp_DetailType="FULL",
                rp_EventTypeIds=[
                    "codebuild-project-build-state-in-progress",
                    "codebuild-project-build-state-failed",
                    "codebuild-project-build-state-succeeded",
                    "codebuild-project-build-state-stopped",
                    "codebuild-project-build-phase-failure",
                    "codebuild-project-build-phase-success",
                ],
                ra_DependsOn=[
                    self.sns_topic,
                    self.codebuild_projects[ith],
                ],
            )
            self.notification_rules.append(notification_rule)
            self.rg_6_notification_rules.add(notification_rule)

    def post_hook(self):
        self.make_rg_1_iam()
        self.make_rg_2_sns()
        self.make_rg_3_lambda()
        self.make_rg_4_codecommit()
        self.make_rg_5_codebuild()
        self.make_rg_6_notification_rules()


if __name__ == "__main__":
    from superjson import json
    from boto_session_manager import BotoSesManager

    from s3pathlib import S3Path, context

    dir_project_root = Path.dir_here(__file__).parent
    path_config_json = dir_project_root / "deploy" / "deploy-config.json"
    path_requirements_txt = dir_project_root / "requirements.txt"
    dir_python_lib = dir_project_root / "aws_ci_bot"

    bsm = BotoSesManager(profile_name="aws_data_lab_open_source_us_east_1")
    context.attach_boto_session(bsm.boto_ses)

    project_md5 = get_project_md5(path_requirements_txt, dir_python_lib)

    # Build deployment package
    install_aws_ci_bot_dependencies()
    install_aws_ci_bot()
    zip_deployment_package()

    # Read deployment config
    deploy_config: dict = json.loads(path_config_json.read_text(), ignore_comments=True)

    # Upload lambda deployment package to S3
    s3path_deployment_package = S3Path(
        deploy_config["s3_bucket"],
        deploy_config["s3_prefix"],
        "lambda",
        path_lambda_deployment_package.stem,
        f"{project_md5}.zip",
    )

    s3path_deployment_package.upload_file(
        path=f"{path_lambda_deployment_package}",
        overwrite=True,
    )

    # Create template definition
    stack = Stack.from_deploy_config(deploy_config)

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
        tags=dict(ProjectName=stack.project_name),
    )

    tpl.to_json_file("template.json")

    # Deploy CloudFormation stack
    env = cf.Env(bsm=bsm)
    env.deploy(
        stack_name=stack.stack_name,
        template=tpl,
        include_named_iam=True,
        skip_prompt=True,
    )
