# Feature 7: Add k8s deployment

## Process
- git checkout main and git pull 
- git checkout new branch from main
- complete tasks
- update any existing third-party libraries
- remove any third-party libraries no longer used
- regression testing in docker-compose
- update Readme
- git commmit and git push origin new branch

## Tasks
- create namespace to deploy containers
- create storage for the deployment
-- options for storage: open-ebs, nfs, local (choose the most efficient)
- create deployment file for application
- create deployment for postgres application
- test using k8s cluster that is accessible via kubectl via cli
- include instructions on how to access after deployment is completed.

## Requirements per Task
- git add / git commit after each task is complete
- document work in task
- make sure efficient and secure
- think and validate task work
- create tests to validate work

## Wrap Up
- Validate all work is done
-- create pull request to main with cli via gh
-- for more informaton on gh use https://github.com/cli/cli