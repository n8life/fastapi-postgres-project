# Feature 9: Pull File from S3

## Process
- git pull main
- create new branch from main
- to set the environment variables, run the following bash command: source set_env.sh 
- complete tasks
- regress test in docker-compose
- Update Readme.md
- run pylint and ruff against code
-- if issues are found
---fix issues one at a time; git add,commit after each issue
- verify third party libraries to determine if still needed for application
-- if updated, retest
- push branch to github
- create pull request to main with cli via gh
-- for more informaton on gh use https://github.com/cli/cli

## Tasks
- Create two new end point
-- one to read a file from a given s3 bucket, and write it to the issues_folder with uuid created name with a file type of .sarif
-- one to read the latest file from issues and return the content in a response


## Requirements Per Task
- Think, validate, and test all work inside docker-compose environment do not run tests locally for the fastapi application
- Make sure all data and endpoints are secure
- git add, commit after each task with comments

## Clean Up Work
- Verify all work completed.
- If anything is updated, push updates to github.