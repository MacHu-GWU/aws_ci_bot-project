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

6. ⭐ Enjoy!
