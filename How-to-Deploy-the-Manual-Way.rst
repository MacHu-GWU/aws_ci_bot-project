How to Deploy, the Manual Way
==============================================================================

.. contents::
    :class: this-will-duplicate-information-and-it-is-still-useful-here
    :depth: 1
    :local:


1. Create SNS Topic
------------------------------------------------------------------------------
1. Go to `AWS SNS Topic Console <https://console.aws.amazon.com/sns/v3/home?#/topics>`_, click "Create Topic".
2. Check the following configuration:
    - Type: Standard
    - Name: put your SNS topic name ``${sns_topic_name}``
    - Access Policy (choose advanced) and put the following Policy document, make sure you replaced the variable ``${aws_region}``, ``${aws_account_id}``, ``${sns_topic_name}`` with the right value. It has to allow CodeCommit and CodeBuild to publish notification event to the Topic.::

        {
            "Version": "2008-10-17",
            "Statement": [
                {
                    "Sid": "CodeNotification_publish",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "codestar-notifications.amazonaws.com"
                    },
                    "Action": "SNS:Publish",
                    "Resource": "arn:aws:sns:${aws_region}:${aws_account_id}:${sns_topic_name}"
                }
            ]
        }

3. Click "Create Topic" to confirm.


2. Create CodeCommit Repository
------------------------------------------------------------------------------
**Create CodeCommit Repository**

This will be your git repo to put your code.

1. Go to `AWS CodeCommit Repositories Console <https://console.aws.amazon.com/codesuite/codecommit/repositories?#>`_, click "Create repository".
2. Check the following configuration:
    - Repository name: put your git repo name ``${repo_name}``

**Configure CodeCommit Notification**

This step will allow CodeCommit repo to send lots of ``git`` events such as ``commit``, ``pr created``, ``pr updated`` to SNS topic.

1. Go to the repo you just created, click "Notify" button (the one with a little "bell" icon), then click "Create notification rule"
2. Check the following configuration:
    - Notification name: I recommend ``${repo_name}-codecommit-all-event``
    - Detail type: Full
    - Events that trigger notifications: click "Select All"
    - Target: choose the SNS topic you just created
3. Click "Submit"


3. Create CodeBuild Project
------------------------------------------------------------------------------
**Create IAM Role for CodeBuild**

1. Go to `AWS IAM Role Console <https://console.aws.amazon.com/iamv2/home?#/roles>`_, click "Create role"
2. Check the following configuration:
    - Use case: "CodeBuild"
    - Permissions: use the following AWS managed policies. You may need additional permissions to allow your build job to do more works, such as publish artifacts to S3, deploy applications:
        - ``AWSCodeCommitPowerUser``: allow build job to pull code from and make change to your CodeCommit repo.
        - ``CloudWatchFullAccess``: allow build job to post CloudWatch log
    - Name: I recommend ``${repo_name}-codebuild-project``, because this project is only for this CodeCommit repo.

**Create CodeBuild Project**

This will be where you run your CI/CD job.

1. Go to `AWS CodeBuild Build Projects Console <https://console.aws.amazon.com/codesuite/codebuild/projects>`_, click "Create build project".
2. Check the following configuration:
    - Project name: I recommend ``${repo_name}``, because this project is only for this CodeCommit repo.
    - Source: choose AWS CodeCommit and your ``${repo_name}`` repo
    - Reference type: use "Branch" and set Branch = main. This is the branch you want to build from when you manually click the button "Build". However, in this solution, we never manually trigger build, but let the CI Bot to trigger it. So it doesn't matter.
    - Environment: this is just for demo, you can always use your own build environment
        - Environment image: check "Managed image"
        - Operating system: check "Amazon Linux2"
        - Runtime: check "Standard"
        - Image: in this demo, I use ``aws/codebuild/amazonlinux2-x84_64-standard:3.0`` because it has Python3.8, which is the version I used in this project. If you are using different Python version, check `this document <https://docs.aws.amazon.com/codebuild/latest/userguide/available-runtimes.html>`_ and figure out the what built in runtime is available in different image.
        - Image version: always use the latest
        - Environment type: Linux
    - Service role: the IAM role you just created.
    - Buildspec:
        - Build specifications: check "Use a buildspec file"
3. Click "Create build project"

**Configure CodeBuild Notification**

This step will allow CodeBuild job run to send lots of events such as ``build success``, ``build failed`` to SNS topic.

1. Go to the build project you just created, click "Notify" button (the one with a little "bell" icon), then click "Create notification rule"
2. Check the following configuration:
    - Notification name: I recommend ``${repo_name}-codebuild-all-event``
    - Detail type: Full
    - Events that trigger notifications: click "Select All"
    - Target: choose the SNS topic you just created
3. Click "Submit"


4. Create the Lambda Function CI-BOT
------------------------------------------------------------------------------
**Create IAM Role for Lambda Function**

1. Go to `AWS IAM Role Console <https://console.aws.amazon.com/iamv2/home?#/roles>`_, click "Create role"
2. Check the following configuration:
    - Use case: "Lambda"
    - Permissions: don't use AWS managed IAM policy, we will create a inline policy later.
    - Name: I recommend ``ci-bot-lambda``, because this lambda can be reused for other CodeCommit repo and other CodeBuild project.
3. Go to the IAM role you just created, go to "Permissions policies" card, click "Add permission" drop down menu, click "Create inline policy", and use put the following Policy document, make sure you replaced the variable ``${aws_region}``, ``${aws_account_id}``, ``${bucket}``, ``${prefix}`` with the right value. The ``${bucket}`` and ``${prefix}`` is the S3 location to store all your CI-Bot events. You have to create this bucket yourself. This allow the CI-Bot Lambda function to put CI events to S3, get codebuild project commit from CodeCommit repo, and automatically put comment to Pull Request activities, and start CodeBuild job run::

    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "VisualEditor0",
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogStream",
                    "logs:CreateLogGroup",
                    "logs:PutLogEvents"
                ],
                "Resource": "*"
            },
            {
                "Sid": "VisualEditor1",
                "Effect": "Allow",
                "Action": [
                    "s3:PutObject",
                    "codecommit:GetCommit",
                    "codecommit:GetFile",
                    "codecommit:PostCommentForPullRequest",
                    "codecommit:PostCommentForComparedCommit",
                    "codecommit:PostCommentReply",
                    "codecommit:UpdateComment",
                    "codebuild:StartBuild",
                    "codebuild:StartBuildBatch",
                    "codebuild:BatchGetBuilds",
                    "codebuild:BatchGetBuildBatches"
                ],
                "Resource": [
                    "arn:aws:codecommit:${aws_region}:${aws_account_id}:*",
                    "arn:aws:codebuild:${aws_region}:${aws_account_id}:project/*",
                    "arn:aws:s3:::${bucket}/${prefix}*"
                ]
            }
        ]
    }

**Create CI-Bot Lambda Function**

1. Go to the `aws_ci_bot Release <https://github.com/MacHu-GWU/aws_ci_bot-project/releases>`_, download the latest ``aws_ci_bot-${version}-lambda-deployment-package.zip`` file.
2. Go to `AWS Lambda Function Console <https://console.aws.amazon.com/lambda/home?#/functions>`_, click "Create function".
3. Check the following configuration:
    - Function name: ``ci-bot``
    - Runtime: I recommend ``Python3.8``, because it is the version I used to build this solution.
    - Permissions: check "Use an existing role" and choose the IAM role you just created.
4. Go to the ``ci-bot`` Lambda Function details, do additional configuration:
    - Upload source code, click "Upload from", check ".zip File", and select the ``aws_ci_bot-${version}-lambda-deployment-package.zip`` file you just downloaded.
    - Go to the "Configuration" tab
        - General configuration: set timeout 10 seconds.
        - Environment variables: create two environment variable ``S3_BUCKET`` and ``S3_PREFIX``, it should match the one you put in step "Create IAM Role for Lambda Function" #3, it is the S3 location to store all your CI-Bot events.
5. Add SNS topic as the trigger:
    - Go to the "Function overview" card on top, click "Add trigger".
    - select "SNS", and select the SNS topic you created.
    - click "Add".
