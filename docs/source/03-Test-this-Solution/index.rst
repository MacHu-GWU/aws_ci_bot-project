Test This Solution
==============================================================================
In the previous document, we successfully deployed the ``aws_ci_bot`` solution to your AWS Account. Now let's use a dummy CodeCommit repository to test this solution. The deployment created a CodeCommit repository ``aws_ci_bot_test-project`` and a CodeBuild project ``aws_ci_bot_test-project``. Now let's use them to test the solution.


Add necessary files to your CodeCommit repository
------------------------------------------------------------------------------
Now, the ``aws_ci_bot_test-project`` is an empty repo, we need to add some files to it. AWS CodeCommit Console allows you to do that via the console without installing any git client. In this document, we will use the AWS CodeCommit Console. However, feel free to do it via your favorite git client.

1. Find your repo in `AWS CodeCommit Repositories Console <https://console.aws.amazon.com/codesuite/codecommit/repositories?#>`_.

2. Add the ``codebuild-config.json`` file, so the CI-Bot knows that which CodeBuild project you want to use to run CI for this repo.
    - Click "Add File", "Create File"

    .. image:: ./images/create-file.png

    - Post the following JSON body and add the file::

        {
            "jobs": [
                {
                    "project_name": "aws_ci_bot_test-project",
                    "is_batch_job": false,
                    "buildspec": "",
                    "env_var": {}
                }
            ]
        }
    - Set "File name": ``codebuild-config.json``
    - Put your "Author name" and "Email address", then click "Commit Changes"

    .. image:: ./images/add-codebuild-config.png

3. Add the ``buildspec.yml`` file, so the CodeBuild knows what to run in build job. In this example, it is just a dummy build job that runs a lot of ``echo``.
    - Click "Add File", "Create File"

    .. image:: ./images/add-file.png

    - Put the following content::

        # Ref: https://docs.aws.amazon.com/codebuild/latest/userguide/build-spec-ref.html
        version: 0.2

        phases:
          install:
            runtime-versions:
              python: 3.8
            commands:
              - echo "install phase"
          pre_build:
            commands:
              - echo "pre_build phase"
          build:
            commands:
              - echo "build phase"
          post_build:
            commands:
              - echo "post_build phase"
    - Set "File name": ``buildspec.yml``.
    - Put your "Author name" and "Email address", then click "Commit Changes".
4. Add a ``chore.txt`` file. Because this is an example repo, we just update the content of the ``chore.txt`` to simulate that we are adding new features.
    - Click "Add File", "Create File".
    - Put ``hello world`` to the content.
    - Set "File name": ``chore.txt``.
    - Put your "Author name" and "Email address", then click "Commit Changes".

    .. image:: ./images/add-buildspec-yml.png

Now the repo is all set. In production, we should also do this before checking in any real application code.


3.2 Test the CI Bot in a Pull Request
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Now we want to simulate a scenario that a developer created a new branch, and started a Pull Request to merge to the ``main`` branch.

In this solution, the trigger rules are defined in the `do_we_trigger_build <https://github.com/MacHu-GWU/aws_ci_bot-project/blob/main/aws_ci_bot/codecommit_and_codebuild.py>`_ function (click this link and search it). It only triggers a CI build job when it is a event of:
    - commit directly to main branch
    - Pull request from ``X`` branch to ``main``, if ``X`` is:
        - feature branch
        - dev branch
        - fix branch
        - build branch
        - doc branch
        - release branch
And it won't trigger build if the commit message starts with semantic commit word ``chore``.

You can easily define your own rules to customize this behavior by chaging this ``do_we_trigger_build`` python function.

**Pull Request Experiment**

1. Find your repo in `AWS CodeCommit Repositories Console <https://console.aws.amazon.com/codesuite/codecommit/repositories?#>`_, enter your repo, then click "Branches" on the side bar.
2. Click "Create branch" button and give it a name called ``feature/1``.
3. Switch to ``feature/1`` branch, and edit the ``chore.txt`` file, and commit the change.
4. Click "Create pull request" button, choose to merge from ``feature/1`` to ``main``, give it a random title and click the "Create pull request" button.
5. **Switch to** "Activity" Tab, **you will see the CI bot just triggered a CodeBuild job run and automatically posted a comment to the PR**, you can click on the link to jump to the CodeBuild job run, or to the detailed changes for the commit. **After a while, when the job run Success or Failed, the CI bot will automatically reply to the comment and tell your the result**.

**Sample Comment**

    🌴 A build run is triggered, let's relax.

    - build run id: `aws_ci_bot-test:cd78cc7e-f538-405e-b4a0-5dddf96fe0f7 <https://us-east-2.console.aws.amazon.com/codesuite/codebuild/111122223333/projects/aws_ci_bot-test/build/aws_ci_bot-test:cd78cc7e-f538-405e-b4a0-5dddf96fe0f7/?region=us-east-2>`_
    - commit id: `c9f2463 <https://us-east-2.console.aws.amazon.com/codesuite/codecommit/repositories/aws_ci_bot-test/pull-requests/1/commit/c9f246376b88d6d63dc02e61059f31d3fc3227c4?region=us-east-2>`_
    - commit message: "Edited chore.txt"
    - committer name: "alice"

    🟢 Build Run SUCCEEDED