How to Deploy
==============================================================================
In this tutorial, we will use an empty, newly created AWS Account as an example to deploy this solution.

.. contents::
    :class: this-will-duplicate-information-and-it-is-still-useful-here
    :depth: 1
    :local:


Pre-requisites
------------------------------------------------------------------------------
1. This solution is developed and tested on Python3.8, but it should works for Python3.7+ as well. You should have Python3.7+ installed on your laptop.
2. AWS CLI Credentials configured on your laptop, make sure you have the following permissions. The easiest way to get these permissions is to attach the following AWS Managed Policies to your IAM user. Of course, you can also create your own custom IAM policy, but it takes more time to develop one.
    - ``arn:aws:iam::aws:policy/IAMFullAccess``: we need this permission to create IAM role and policy.
    - ``arn:aws:iam::aws:policy/AmazonS3FullAccess``: we need this permission to read and write the CloudFormation template in S3 bucket.
    - ``arn:aws:iam::aws:policy/AWSCodeCommitFullAccess``: we need this permission to create and configure CodeCommit repository.
    - ``arn:aws:iam::aws:policy/AWSCodeBuildAdminAccess``: we need this permission to create and configure CodeBuild project.
    - ``arn:aws:iam::aws:policy/AWSCodeStarFullAccess``: we need this permission to create CodeCommit and CodeBuild Notification rules.
    - ``arn:aws:iam::aws:policy/AWSLambda_FullAccess``: we need this permission to create AWS Lambda function.
    - ``arn:aws:iam::aws:policy/AmazonSNSFullAccess``: we need this permission to create
    - ``arn:aws:iam::aws:policy/AWSCloudFormationFullAccess``: we need this permission to deploy the solution via AWS CloudFormation.
    - ``sts:GetCallerIdentity``: we need this permission to figure out the AWS Account ID.


Deploy the Solution
------------------------------------------------------------------------------
1. Run the following command to clone the specific version of this solution to your laptop. You can find the release history in the `release-history.rst <https://github.com/MacHu-GWU/aws_ci_bot-project/blob/main/release-history.rst>`_ file. The ``${version}`` has to match the release version.

.. code-block:: bash

    # Command
    git clone --depth 1 --branch ${version} https://github.com/MacHu-GWU/aws_ci_bot-project.git

    # Example
    git clone --depth 1 --branch 0.3.1 https://github.com/MacHu-GWU/aws_ci_bot-project.git

2. Create an Python virtual environment and install the required Python dependencies:

.. code-block:: bash

    # CD to the project root directory
    cd /path/to/aws_ci_bot-project

    # Create a Python virtual environment
    virtualenv -p python3.8

2. Edit the ``deploy-config.json``.
