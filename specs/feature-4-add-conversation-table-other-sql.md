# Feature 4: Add Conversation Table and Other SQL Updates

## Process
- Create new branch 
- Create SQL Scripts
- Test SQL Scripts
- Fix scripts
- Repeat tests for sql script
- Create new api endpoints in fastapi application
- Test new api endpoints
- Regression tests
- Fix and issues and repeat previous 2 steps
- Commit branch, push to github, create pull request to main

## Tasks
- Add new table called conversation which relates to the messages table through the conversation id in messages table
-- Columns for new table id, create date, conversation archived, title, description, metadata
- Create endpoints to create, update and list
- Create endpoint to pull all informaton for a conversation by conversation id including agents, agent_message_metadata, message_recipients, messages
- Update messages code to include conversation information  

## Requirements
- Think, validate, and test all work inside docker-compose environment do not run tests locally for the fastapi application
- Make sure all data and endpoints are secure

