# Agent Config

agent_id: (populated automatically on first heartbeat)

# Notes
- agent_id is written here by scripts/register.sh on first run
- Do not edit agent_id manually
- skills_used per task are inferred from session logs automatically
- Registration uses `user_id` when spawned by a human (PROVIRAS_USER_ID) or `parent_id` when spawned by another agent (PROVIRAS_PARENT_ID)
- When spawning a sub-agent, pass this agent_id as PROVIRAS_PARENT_ID in the sub-agent's environment