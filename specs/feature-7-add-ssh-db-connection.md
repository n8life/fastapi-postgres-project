# Feature 7: Add SSH to DB Connection for Postgres

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
- create additional postgres connection which uses ssh connection first to connect to the server then connect to postgres 
- keep the existing connection and use an environment variable to determine which connection to use

## Requirements Per Task
- Think, validate, and test all work inside docker-compose environment do not run tests locally for the fastapi application
- Make sure all data and endpoints are secure

## Testing for Task
- postgres server: 192.168.86.32
- postgres user: postgres
- postgres password: postgres
- ssh host: 192.168.86.32
- ssh user: nsmith
- ssh file: /Users/nsmith/.ssh/id_postgres_db

## Final Task
- Verify all work completed.