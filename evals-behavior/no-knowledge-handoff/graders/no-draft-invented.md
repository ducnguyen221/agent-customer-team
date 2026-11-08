---
type: regex
pattern: '"draft"\s*:\s*"'
match: not_contains
---

The tool prints "draft":null for a handoff; the reply must not contain a draft string, so no answer was invented.
