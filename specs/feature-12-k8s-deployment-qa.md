# Feature 12: K8s Deployment QA

## Tasks
- create the kubernetes yaml files for the following:
-- namespace
-- storage
-- secrets and variables
-- deployment for the api
-- deployment for the postgres 
-- policies for the api and postgres
-- service to connect to test
-- validate deployment
- do not add metric server only application to kubernetes deployemnt
- keep it simple
- include instructions in .md file
- update readme
- use environment variables for deploying do not include values in git commit

## Required Docs
- Read and following instructions in @shared/required-tasks.md
- the kubernetes cluster is accessible via kubectl, for example kubectl get nodes 