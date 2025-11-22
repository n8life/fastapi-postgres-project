# Feature 11: Assign tasks to agent

## Tasks
- create new environment variable called AGENT_NAME
-- use this for inserting records into messages table
--- AGENT_NAME will be the sender by the id from the agent table
- create new api endpoint to use the api endpoint to read the most recent file
-- start a new conversation 
-- insert the information into the messages table
--- insert a record into message-recipient
---- assign to an agent other than the one refenced by AGENT_NAME
-- once the information is inserted into the table delete the file from issues folder

## Required Docs
- Read and following instructions in @shared/required-tasks.md