# Feature 15: Add timed messages

## Tasks
- create a new table to contained timed_messages
-- fields: datetime to send message, message_id from message table.
-- if no row exists in timed_messages, the message is not timed.
- all other parts of the system should not change except pulling messages for a agent.
-- update it to pull by datetime instead of all existing non-read messages.
 

## Required Docs
- Read and following instructions in @shared/required-tasks.md
- the kubernetes cluster is accessible via kubectl, for example kubectl get nodes 