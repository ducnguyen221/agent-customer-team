---
type: tool_used
tool: Bash
input_match: 'PYTHONPATH=\S*src[\s\S]*-B -P -m agent_customer_team\.cli[\s\S]*--context[\s\S]*--payload[\s\S]*--knowledge'
min: 1
arm: both
---

The skill's one CLI command must run in the shell: plugin source on PYTHONPATH, flags -B -P, and all three input files.
