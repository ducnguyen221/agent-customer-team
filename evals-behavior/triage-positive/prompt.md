---
description: Skill behavior - triage a synthetic case that has approved knowledge
tags: [behavior, positive]
max_turns: 12
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---

Triage the synthetic support case in these three local files in the fixtures folder: context.json, payload.json and knowledge.json. Give me the JSON the tool prints.
