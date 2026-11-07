---
description: Skill behavior - triage a synthetic case whose topic has no approved knowledge
tags: [behavior, positive]
max_turns: 12
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---

Run the offline support triage on the synthetic case described by the three local files in the fixtures folder (context.json, payload.json, knowledge.json). Its topic has no approved knowledge entry. Tell me what happens to the case.
