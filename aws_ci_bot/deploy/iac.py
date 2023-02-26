# -*- coding: utf-8 -*-

import typing as T
import sys
import copy

import attr
import cottonformation as cf
from cottonformation.res import (
    sns,
    awslambda,
    iam,
    codecommit,
    codebuild,
    codestarnotifications,
)

if T.TYPE_CHECKING:
    from .script import DeployConfig

py_ver = f"{sys.version_info.major}.{sys.version_info.minor}"


def encode_policy_document(statement: T.List[dict]) -> dict:
    policy_document = {
        "Version": "2012-10-17",
    }
    new_statement = list()
    for ith, stat in enumerate(statement, start=1):
        new_stat = copy.deepcopy(stat)
        new_stat["Sid"] = f"Sid{str(ith).zfill(3)}"
        new_statement.append(new_stat)

    policy_document["Statement"] = new_statement
    return policy_document


@attr.s
class Stack(cf.Stack):
    """
    The CloudFormation stack definition for this solution.
    """

    deploy_config: "DeployConfig" = attr.ib(default=None)
    s3_key_lambda_deployment_package: str = attr.ib(default=None)

    @property
    def project_name_slug(self) -> str:
        return self.deploy_config.project_name.replace("_", "-")

    @property
    def stack_name(self) -> str:
        return self.project_name_slug

    def make_rg_1_iam(self):
        self.rg_1_iam = cf.ResourceGroup("RG1")

        self.iam_role_for_lambda = iam.Role(
            "IamRoleForLambda",
            p_RoleName=cf.Sub(
                string="${project_name}-${aws_region}-lambda-role",
                data=dict(
                    project_name=self.project_name_slug,
                    aws_region=cf.AWS_REGION,
                ),
            ),
            rp_AssumeRolePolicyDocument=cf.helpers.iam.AssumeRolePolicyBuilder(
                cf.helpers.iam.ServicePrincipal.awslambda(),
            ).build(),
        )
        self.rg_1_iam.add(self.iam_role_for_lambda)

        self.stat_s3 = {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
            ],
            "Resource": [
                f"arn:aws:s3:::{self.deploy_config.s3_bucket}/*",
            ],
        }

        if len(self.deploy_config.codecommit_repo_list):
            codecommit_resource = [
                cf.Sub(
                    string="arn:aws:codecommit:${aws_region}:${aws_account_id}:${repo_name}",
                    data=dict(
                        aws_region=cf.AWS_REGION,
                        aws_account_id=cf.AWS_ACCOUNT_ID,
                        repo_name=repo_name,
                    ),
                )
                for repo_name in self.deploy_config.codecommit_repo_list
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

        self.stat_codecommit_permissin_for_lambda = {
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

        if len(self.deploy_config.codebuild_project_list):
            codebuild_resource = [
                cf.Sub(
                    string="arn:aws:codebuild:${aws_region}:${aws_account_id}:project/${project_name}",
                    data=dict(
                        aws_region=cf.AWS_REGION,
                        aws_account_id=cf.AWS_ACCOUNT_ID,
                        project_name=codebuild_project.project_name,
                    ),
                )
                for codebuild_project in self.deploy_config.codebuild_project_list
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

        self.stat_codebuild_permission_for_lambda = {
            "Effect": "Allow",
            "Action": [
                "codebuild:StartBuild",
                "codebuild:StartBuildBatch",
                "codebuild:BatchGetBuilds",
                "codebuild:BatchGetBuildBatches",
            ],
            "Resource": codebuild_resource,
        }

        self.iam_policy_for_lambda = iam.Policy(
            "IamPolicyForLambda",
            rp_PolicyName=cf.Sub(
                string="${project_name}-${aws_region}-lambda-policy",
                data=dict(
                    project_name=self.project_name_slug,
                    aws_region=cf.AWS_REGION,
                ),
            ),
            rp_PolicyDocument=encode_policy_document(
                [
                    self.stat_s3,
                    self.stat_codecommit_permissin_for_lambda,
                    self.stat_codebuild_permission_for_lambda,
                ]
            ),
            p_Roles=[
                self.iam_role_for_lambda.ref(),
            ],
            ra_DependsOn=self.iam_role_for_lambda,
        )
        self.rg_1_iam.add(self.iam_policy_for_lambda)

        self.iam_role_for_codebuild = iam.Role(
            "IamRoleForCodeBuild",
            p_RoleName=cf.Sub(
                string="${project_name}-${aws_region}-codebuild-role",
                data=dict(
                    project_name=self.project_name_slug,
                    aws_region=cf.AWS_REGION,
                ),
            ),
            rp_AssumeRolePolicyDocument=cf.helpers.iam.AssumeRolePolicyBuilder(
                cf.helpers.iam.ServicePrincipal.codebuild(),
            ).build(),
            p_ManagedPolicyArns=[
                cf.helpers.iam.AwsManagedPolicy.AdministratorAccess,
            ],
        )
        self.rg_1_iam.add(self.iam_role_for_codebuild)

        if len(self.deploy_config.codecommit_repo_list):
            codecommit_resource = [
                cf.Sub(
                    string="arn:aws:codecommit:${aws_region}:${aws_account_id}:${repo_name}",
                    data=dict(
                        aws_region=cf.AWS_REGION,
                        aws_account_id=cf.AWS_ACCOUNT_ID,
                        repo_name=repo_name,
                    ),
                )
                for repo_name in self.deploy_config.codecommit_repo_list
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

        self.stat_codecommit_many_permissions = {
            "Effect": "Allow",
            "Action": [
                "codecommit:AssociateApprovalRuleTemplateWithRepository",
                "codecommit:BatchAssociateApprovalRuleTemplateWithRepositories",
                "codecommit:BatchDescribeMergeConflicts",
                "codecommit:BatchDisassociateApprovalRuleTemplateFromRepositories",
                "codecommit:BatchGetCommits",
                "codecommit:BatchGetPullRequests",
                "codecommit:BatchGetRepositories",
                "codecommit:CancelUploadArchive",
                "codecommit:CreateCommit",
                "codecommit:CreatePullRequest",
                "codecommit:CreatePullRequestApprovalRule",
                "codecommit:CreateRepository",
                "codecommit:CreateUnreferencedMergeCommit",
                "codecommit:DeleteBranch",
                "codecommit:DeleteCommentContent",
                "codecommit:DeleteFile",
                "codecommit:DeletePullRequestApprovalRule",
                "codecommit:DeleteRepository",
                "codecommit:DescribeMergeConflicts",
                "codecommit:DescribePullRequestEvents",
                "codecommit:DisassociateApprovalRuleTemplateFromRepository",
                "codecommit:EvaluatePullRequestApprovalRules",
                "codecommit:GetBlob",
                "codecommit:GetBranch",
                "codecommit:GetComment",
                "codecommit:GetCommentReactions",
                "codecommit:GetCommentsForComparedCommit",
                "codecommit:GetCommentsForPullRequest",
                "codecommit:GetCommit",
                "codecommit:GetCommitHistory",
                "codecommit:GetCommitsFromMergeBase",
                "codecommit:GetDifferences",
                "codecommit:GetFile",
                "codecommit:GetFolder",
                "codecommit:GetMergeCommit",
                "codecommit:GetMergeConflicts",
                "codecommit:GetMergeOptions",
                "codecommit:GetObjectIdentifier",
                "codecommit:GetPullRequest",
                "codecommit:GetPullRequestApprovalStates",
                "codecommit:GetPullRequestOverrideState",
                "codecommit:GetReferences",
                "codecommit:GetRepository",
                "codecommit:GetRepositoryTriggers",
                "codecommit:GetTree",
                "codecommit:GetUploadArchiveStatus",
                "codecommit:GitPull",
                "codecommit:GitPush",
                "codecommit:MergeBranchesByFastForward",
                "codecommit:MergeBranchesBySquash",
                "codecommit:MergeBranchesByThreeWay",
                "codecommit:MergePullRequestByFastForward",
                "codecommit:MergePullRequestBySquash",
                "codecommit:MergePullRequestByThreeWay",
                "codecommit:OverridePullRequestApprovalRules",
                "codecommit:PostCommentForComparedCommit",
                "codecommit:PostCommentForPullRequest",
                "codecommit:PostCommentReply",
                "codecommit:PutCommentReaction",
                "codecommit:PutFile",
                "codecommit:PutRepositoryTriggers",
                "codecommit:TestRepositoryTriggers",
                "codecommit:UpdateComment",
                "codecommit:UpdateDefaultBranch",
                "codecommit:UpdatePullRequestApprovalRuleContent",
                "codecommit:UpdatePullRequestApprovalState",
                "codecommit:UpdatePullRequestDescription",
                "codecommit:UpdatePullRequestStatus",
                "codecommit:UpdatePullRequestTitle",
                "codecommit:UpdateRepositoryDescription",
                "codecommit:UpdateRepositoryName",
                "codecommit:UploadArchive",
                "codecommit:CreateBranch",
            ],
            "Resource": codecommit_resource,
        }

        self.iam_policy_for_codebuild = iam.Policy(
            "IamPolicyForCodeBuild",
            rp_PolicyName=cf.Sub(
                string="${project_name}-${aws_region}-codebuild-policy",
                data=dict(
                    project_name=self.project_name_slug,
                    aws_region=cf.AWS_REGION,
                ),
            ),
            rp_PolicyDocument=encode_policy_document(
                [self.stat_codecommit_many_permissions]
            ),
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
                p_S3Bucket=self.deploy_config.s3_bucket,
                p_S3Key=self.s3_key_lambda_deployment_package,
            ),
            rp_Role=self.iam_role_for_lambda.rv_Arn,
            p_FunctionName=f"{self.project_name_slug}",
            p_Runtime=f"python{py_ver}",
            p_Handler="lambda_function.lambda_handler",
            p_Timeout=10,
            p_MemorySize=128,
            p_Environment=awslambda.PropFunctionEnvironment(
                p_Variables=dict(
                    S3_BUCKET=self.deploy_config.s3_bucket,
                    S3_PREFIX=self.deploy_config.s3_prefix,
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
        for repo_name in self.deploy_config.codecommit_repo_list:
            repo = codecommit.Repository(
                "CodeCommitRepo{}".format(repo_name.replace("_", "").replace("-", "")),
                rp_RepositoryName=repo_name,
                # don't delete repo when you delete CloudFormation stack
                ra_DeletionPolicy=cf.DeletionPolicyEnum.Retain,
            )
            self.codecommit_repos.append(repo)
            self.rg_4_codecommit.add(repo)

    def make_rg_5_codebuild(self):
        self.rg_5_codebuild = cf.ResourceGroup("RG5")

        self.codebuild_projects: T.List[codebuild.Project] = list()
        for codebuild_project in self.deploy_config.codebuild_project_list:
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
                # don't delete build project when you delete CloudFormation stack
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

        for ith, repo_name in enumerate(self.deploy_config.codecommit_repo_list):
            notification_rule = codestarnotifications.NotificationRule(
                "CodeCommitNotificationRule{}".format(
                    repo_name.replace("_", "").replace("-", "")
                ),
                rp_Name=cf.Sub(
                    string="${repo_name}-${aws_region}-codecommit-all-event",
                    data=dict(
                        repo_name=repo_name,
                        aws_region=cf.AWS_REGION,
                    ),
                ),
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

        for ith, codebuild_project in enumerate(
            self.deploy_config.codebuild_project_list
        ):
            notification_rule = codestarnotifications.NotificationRule(
                "CodeProjectNotificationRule{}".format(
                    codebuild_project.project_name.replace("_", "").replace("-", "")
                ),
                rp_Name=cf.Sub(
                    string="${project_name}-${aws_region}-codebuild-all-event",
                    data=dict(
                        project_name=codebuild_project.project_name,
                        aws_region=cf.AWS_REGION,
                    ),
                ),
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
