# Credential scrub canary

One case run by the `eval-behavior` workflow before the behavior eval. With Bash granted and
`CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1`, the agent runs `printenv ANTHROPIC_API_KEY | wc -c`; the case passes only when the
reply is `0`. The command prints a length, never the value. If it fails, the workflow skips the behavior eval and the job
fails. The canary checks `ANTHROPIC_API_KEY` only; a run that authenticates with `CLAUDE_CODE_OAUTH_TOKEN` is not covered.
