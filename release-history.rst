.. _release_history:

Release and Version History
==============================================================================


Backlog
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

**Minor Improvements**

**Bugfixes**

**Miscellaneous**


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
