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
- Add endpoint to pull all tasks for an agent
- Add endpoint to pull all tasks that have not been read for an agent
- Add endpoint to pull metadata and from agent information for a given message
- Add endpoint to update all messages up to a given date, status='read'

### Requirements for task
- Agents should only be able to read their own messages
- No end point should allow multiple agents' information to be returned 
- Only one agent's information can be returned
- Agent information will be pulled by agent_id