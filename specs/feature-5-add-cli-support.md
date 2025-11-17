# Feature 5: Add CLI Support

## Process 
- git pull main
- create new branch from main
- complete tasks
- regress test in docker-compose
- Update Readme.md
- push branch to github
- create pull request to main with cli via gh
-- for more informaton on gh use https://github.com/cli/cli

## Tasks
- create an endpoint that will receive a message
-- next the endpoint will echo it to the command line via a subprocess command
- create unit test for endpoint
- only test echo command 

## Requirements Per Task
- Think, validate, and test all work inside docker-compose environment do not run tests locally for the fastapi application
- Make sure all data and endpoints are secure