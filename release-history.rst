.. _release_history:

Release and Version History
==============================================================================


Backlog
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

**Minor Improvements**

- use `wait condition <https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-waitcondition.html>`_ to deploy this solution in one shot.

**Bugfixes**

**Miscellaneous**


0.5.1 (2023-03-28)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- Prompt to ask user to type "y" to proceed the deployment.

**Minor Improvements**

- Allow user to customize the CloudFormation timeout time.

**Bugfixes**

- Fix a bug that the Lambda function IAM role doesn't have the permission to create Cloudwatch log group.

**Miscellaneous**

- Improve documentation.


0.4.1 (2022-02-26)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- greatly simplifies the deployment process.

**Miscellaneous**

- add dedicated documentation website, greatly improves the documentations.


0.3.1 (2022-12-18)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- Add a lot environment variable to show git event details for CI build environment to use.

**Default CodeCommit git event handler**

- No change

**Default CodeBuild event handler**

- No change


0.2.1 (2022-12-17)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- Add the infrastructure as code deployment option.
- Can setup multiple CodeCommit repositories and CodeBuild projects using infrastructure as code deployment option.

**Default CodeCommit git event handler**

- No change

**Default CodeBuild event handler**

- No change


0.1.1 (2022-12-09)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- First release
- Add the manual deployment option

**Default CodeCommit git event handler**

- Trigger build job only when:
    - PR created on semantic feature | develop | fix | build | doc | release branch
    - PR merged

**Default CodeBuild event handler**

- Post comment to the Pull Request when:
    - Build status change when failed | succeeded
