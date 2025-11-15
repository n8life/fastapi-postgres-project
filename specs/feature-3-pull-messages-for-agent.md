# Pull Messages for Agent

## Process
- git checkout new branch
- Per task
-- make a commit after each task completion
-- create a test for each task
- Remove any unneeded dependencies
- Validate updates by running all tests; Including regression testing; Test using docker-compose environment not local environment
- git push after all steps completed and tested

## Tasks
- Add endpoint to pull all messages by looking up by recipient_id in message_recipients for an agent
- Add endpoint to pull all messages by looking up by recipient_id in message_recipients that have not been read for an agent
- Add endpoint to pull by a message_id metadata and from agent information for a given message
- Add endpoint to update all message_recipients records up to a given date by recipient_id

### Requirements for task
- Agents should only be able to read their own messages and ones assigned in message_recipients; same applys for message_metadata
- No end point should allow multiple agents' information to be returned 
- Only one agent's information can be returned
