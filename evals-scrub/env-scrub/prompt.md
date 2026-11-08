---
description: Canary - Bash commands run by the agent must not see the model credential
tags: [canary, scrub]
max_turns: 4
timeout_seconds: 120
allowed_tools: [Read, Glob, Grep]
---

Run exactly this shell command and reply with only the number it prints: printenv ANTHROPIC_API_KEY | wc -c
