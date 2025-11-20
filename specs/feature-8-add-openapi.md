# Feature 8: Add OpenApi Spec for application

## Process
- git pull main
- create new branch from main
- complete tasks
- regress test in docker-compose
- Update Readme.md
- run pylint and ruff against code
-- if issues are found
---fix issues one at a time; git add,commit after each issue
- push branch to github
- create pull request to main with cli via gh
-- for more informaton on gh use https://github.com/cli/cli

## Tasks
- Create an OpenAPI specification document for the application
-- Use for reference: https://spec.openapis.org/oas/latest.html
-- Make sure it is a secure specification.
-- Make sure the API key is not sent over in cleartext in the openapi.yaml file.

## Requirements Per Task
- Think, validate, and test all work inside docker-compose environment do not run tests locally for the fastapi application
- Make sure all data and endpoints are secure
- git add, commit after each task with comments

## Clean Up Work
- Verify all work completed.
- If anything is updated, push updates to github.