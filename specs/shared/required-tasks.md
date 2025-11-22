# Required Steps to follow for tasks

## Process
- run git pull main
- run git branch -b "feature-9/read-issue-files" from main
- run source @set_env.sh 
- complete all Tasks
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

## Requirements Per Task
- Think, validate, and test all work inside docker-compose environment do not run tests locally for the fastapi application
- Make sure all data and endpoints are secure
- git add, commit after each task with comments

## Clean Up Work
- Verify all work completed.
- If anything is updated, push updates to github.