---
type: tool_used
tool: Bash
input_match: 'printenv ANTHROPIC_API_KEY \| wc -c'
min: 1
arm: both
---

The canary command must actually run in Bash; it prints only a length, never the value.
