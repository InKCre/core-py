- To develop the InKCre/core-py, following resources are required for you to test and debug so as to verify your changes:
  - PostgreSQL database
    - A Github Action is configured to checkout a database branch (NeonDB) for each PR with branch name `pr/<branch-name>`. 
      The checked out branch's parent branch is `pr/<pr-target-branch-name>` and schema only, 
      if no target branch, use `pr/develop` instead.
    - `copilot-setup-steps` also checked out a database branch for Github Copilot Agent and configure the DATABASE_URL in `.env`.