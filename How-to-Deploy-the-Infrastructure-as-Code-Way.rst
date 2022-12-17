How to Deploy, the Infrastructure as Code Way
==============================================================================
This method does nothing different than `How-to-Deploy-the-Manual-Way <./How-to-Deploy-the-Manual-Way.rst>`_ but automate each manual step using Infrastructure as Code tool `cottonformation <https://pypi.org/project/cottonformation/>`_.

1. Ensure that you have Python3.7 +

.. code-block:: bash

    python --version

2. Pip install necessary dependencies to run the automation script:

.. code-block:: bash

    pip install -r requirements-dev.txt

3. Update the `deploy-config.json <./deploy/deploy-config.json>`_ file to define which AWS Account and what to create using this solution.

4. Ensure that your default aws profile has the permission to do the following:
    - Create / Update CloudFormation Stack
    - Create / Update IAM Role and Policy
    - Create / Update SNS Topic
    - Create / Update Lambda Function
    - Read / Write deployment artifacts to the S3 bucket you defined
    - Create CodeCommit repositories
    - Create / Update CodeBuild projects
    - Create / Update CodeStarNotificationRules

5. Run the `deploy_solution.py <./deploy/deploy_solution.py>`_ script to deploy this solution to your AWS Account.

.. code-block:: bash

    python ./deploy/deploy_solution.py

Then you should see the following:

.. code-block:: bash

    ================== Deploy stack: aws-ci-bot ==================
      preview stack in AWS CloudFormation console: https://console.aws.amazon.com/cloudformation/home?#/stacks?filteringStatus=active&filteringText=aws-ci-bot&viewNested=true&hideStacks=false
      preview change set details at: https://us-east-1.console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/changesets/changes?stackId=arn:aws:cloudformation:us-east-1:111122223333:stack/aws-ci-bot/17a98f80-7e5d-11ed-a200-0ecf505780af&changeSetId=arn:aws:cloudformation:us-east-1:111122223333:changeSet/aws-ci-bot-2022-12-17-22-49-41-019/b3635494-3e90-40da-9aae-21e2c4a1536a
      wait for change set creation to finish ...
        on 2 th attempt, elapsed 10 seconds, remain 50 seconds ...
        reached status CREATE_COMPLETE
                        >>> Change for stack aws-ci-bot <<<
    stack id = arn:aws:cloudformation:us-east-1:111122223333:stack/aws-ci-bot/17a98f80-7e5d-11ed-a200-0ecf505780af
    change set id = arn:aws:cloudformation:us-east-1:111122223333:changeSet/aws-ci-bot-2022-12-17-22-49-41-019/b3635494-3e90-40da-9aae-21e2c4a1536a
    +---------------------------- Change Set Statistics -----------------------------
    | 🟢 Add        13 Resources
    |
    +--------------------------------------------------------------------------------
    +----------------------------------- Changes ------------------------------------
    | 🟢 📦 Add Resource:        CodeBuildProjectawscibottestproject               AWS::CodeBuild::Project
    | 🟢 📦 Add Resource:        CodeCommitNotificationRuleawscibottestproject     AWS::CodeStarNotifications::NotificationRule
    | 🟢 📦 Add Resource:        CodeCommitRepoawscibottestproject                 AWS::CodeCommit::Repository
    | 🟢 📦 Add Resource:        CodeProjectNotificationRuleawscibottestproject    AWS::CodeStarNotifications::NotificationRule
    | 🟢 📦 Add Resource:        IamPolicyForCodeBuild                             AWS::IAM::Policy
    | 🟢 📦 Add Resource:        IamPolicyForLambda                                AWS::IAM::Policy
    | 🟢 📦 Add Resource:        IamRoleForCodeBuild                               AWS::IAM::Role
    | 🟢 📦 Add Resource:        IamRoleForLambda                                  AWS::IAM::Role
    | 🟢 📦 Add Resource:        LambdaFunction                                    AWS::Lambda::Function
    | 🟢 📦 Add Resource:        LambdaPermissionForSNSTopic                       AWS::Lambda::Permission
    | 🟢 📦 Add Resource:        SNSSubscriptionForLambda                          AWS::SNS::Subscription
    | 🟢 📦 Add Resource:        SNSTopicPolicy                                    AWS::SNS::TopicPolicy
    | 🟢 📦 Add Resource:        SNSTopic                                          AWS::SNS::Topic
    |
    +--------------------------------------------------------------------------------
        need to execute the change set to apply those changes.
      preview create stack progress at: https://us-east-1.console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/stackinfo?filteringText=aws-ci-bot&viewNested=true&hideStacks=false&stackId=arn:aws:cloudformation:us-east-1:111122223333:stack/aws-ci-bot/17a98f80-7e5d-11ed-a200-0ecf505780af&filteringStatus=active
     wait for deploy to finish ...
        on 11 th attempt, elapsed 55 seconds, remain 5 seconds ...
        reached status 🟢 'CREATE_COMPLETE'
      done

6. ⭐ Enjoy!
