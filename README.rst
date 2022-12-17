.. .. image:: https://readthedocs.org/projects/aws_ci_bot/badge/?version=latest
    :target: https://aws_ci_bot.readthedocs.io/index.html
    :alt: Documentation Status

.. .. image:: https://github.com/MacHu-GWU/aws_ci_bot-project/workflows/CI/badge.svg
    :target: https://github.com/MacHu-GWU/aws_ci_bot-project/actions?query=workflow:CI

.. .. image:: https://codecov.io/gh/MacHu-GWU/aws_ci_bot-project/branch/main/graph/badge.svg
    :target: https://codecov.io/gh/MacHu-GWU/aws_ci_bot-project

.. .. image:: https://img.shields.io/pypi/v/aws_ci_bot.svg
    :target: https://pypi.python.org/pypi/aws_ci_bot

.. .. image:: https://img.shields.io/pypi/l/aws_ci_bot.svg
    :target: https://pypi.python.org/pypi/aws_ci_bot

.. .. image:: https://img.shields.io/pypi/pyversions/aws_ci_bot.svg
    :target: https://pypi.python.org/pypi/aws_ci_bot

.. image:: https://img.shields.io/badge/STAR_Me_on_GitHub!--None.svg?style=social
    :target: https://github.com/MacHu-GWU/aws_ci_bot-project

------

.. .. image:: https://img.shields.io/badge/Link-Document-blue.svg
    :target: https://aws_ci_bot.readthedocs.io/index.html

.. .. image:: https://img.shields.io/badge/Link-API-blue.svg
    :target: https://aws_ci_bot.readthedocs.io/py-modindex.html

.. .. image:: https://img.shields.io/badge/Link-Source_Code-blue.svg
    :target: https://aws_ci_bot.readthedocs.io/py-modindex.html

.. .. image:: https://img.shields.io/badge/Link-Install-blue.svg
    :target: `install`_

.. image:: https://img.shields.io/badge/Link-GitHub-blue.svg
    :target: https://github.com/MacHu-GWU/aws_ci_bot-project

.. image:: https://img.shields.io/badge/Link-Submit_Issue-blue.svg
    :target: https://github.com/MacHu-GWU/aws_ci_bot-project/issues

.. image:: https://img.shields.io/badge/Link-Request_Feature-blue.svg
    :target: https://github.com/MacHu-GWU/aws_ci_bot-project/issues

.. .. image:: https://img.shields.io/badge/Link-Download-blue.svg
    :target: https://pypi.org/pypi/aws_ci_bot#files


Welcome to ``aws_ci_bot`` Documentation
==============================================================================
🤖 ``aws_ci_bot`` is a open source solution that allow you to create an CI/CD platform that is similar to "Jenkins", "GitHub Action", "CircleCI", "GitLab CI" in 30 minutes, in an empty "AWS Account" using AWS CodeCommit as the git repository, AWS CodeBuild as the CI build runtime, and the AWS Lambda Function as the CI-Bot.

It comes with a lot more advanced features that is highly customizable:

1. Automatically post comment, reply to your Pull Request activity about your CI job run status, code artifacts you just put, applications you just deployed.
2. Highly customizable trigger rules, allow you to use ``branch name``, ``commit message`` and everything to write your own rules to define "**when to trigger build and what exactly to build**", in pure python IF ELSE syntax.
3. Allow to use a Human-in-loop GUI to approve, deny build job run, from your browser or your cell phone, please see my ``aws_cicd_hil-project`` repo.

.. image:: ./images/comment-bot.png

.. contents::
    :class: this-will-duplicate-information-and-it-is-still-useful-here
    :depth: 1
    :local:


1. How it Work
------------------------------------------------------------------------------
Below is a sample workflow for Pull Request and Code Review.

.. image:: ./images/pr-workflow.drawio.png

1. Developer created a branch and started a Pull request to merge the ``feature`` branch to ``main``, the CodeCommit sent the PR event to SNS topic.
2. The SNS topic send the CodeCommit event to the Lambda Function CI-Bot.
3. The CI-Bot analyze the event, find out that it is a PR event and it should trigger a code build (This logic can be customized), so it post a comment to the PR about the build job link.
4. The CI-Bot triggers the CodeBuild job run.
5. Everytime the CI bot job run changed Phase, failed or succeeded, it send the CodeBuild event to the SNS topic.
6. The SNS topic send the CodeBuild event to the Lambda Function CI-Bot.
7. The CI-Bot post a reply to the PR comment to tell the developer the build job progress.


2. How to Deploy
------------------------------------------------------------------------------
In average, it usually takes 5 minutes to deploy using the Infrastructure as Code

- `How-to-Deploy-the-Infrastructure-as-Code-Way <./How-to-Deploy-the-Infrastructure-as-Code-Way.rst>`_
- `How-to-Deploy-the-Manual-Way <./How-to-Deploy-the-Manual-Way.rst>`_


3. Test This Solution
------------------------------------------------------------------------------
.. contents::
    :class: this-will-duplicate-information-and-it-is-still-useful-here
    :depth: 1
    :local:


3.1 Prepare necessary config file in your CodeCommit repo
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. Find your repo in `AWS CodeCommit Repositories Console <https://console.aws.amazon.com/codesuite/codecommit/repositories?#>`_.
2. Add the ``codebuild-config.json`` file, so the CI-Bot knows that which CodeBuild project you want to use to run CI for this repo.
    - Click "Add File", "Create File"
    - Post the following JSON body, make sure you entered the correct value for ``${codebuild_project_name}::

        {
            "jobs": [
                {
                    "project_name": "${codebuild_project_name}",
                    "is_batch_job": false,
                    "buildspec": "",
                    "env_var": {}
                }
            ]
        }
    - Set "File name": ``codebuild-config.json``
    - Put your "Author name" and "Email address", then click "Commit Changes"
3. Add the ``buildspec.yml`` file, so the CodeBuild knows what to run in build job. In this example, it is just a dummy build job that runs a lot of ``echo``.
    - Click "Add File", "Create File"
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


4. How to Customize
------------------------------------------------------------------------------
- go `codecommit_rule.py <./aws_ci_bot/codecommit_rule.py>`_ to customize when, on what git event, on what branch, on what commit message, you want to run what build.
- go `codebuild_rule.py <./aws_ci_bot/codebuild_rule.py>`_ to customize when do you want to post comment to CodeCommit repo.
