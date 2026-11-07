# agent-customer-team

> Version `0.1.0`, not released. Vietnamese version: [README.vi.md](README.vi.md).

## What it is

A local, deterministic prototype for synthetic support cases. It validates three JSON inputs (context, payload,
knowledge), selects approved fixture knowledge, and returns an exact grounded draft or a pending internal handoff. The
repository is also an OpcOS plugin: the skill `customer-support-offline` wraps the command-line tool for Claude
Code, Codex and Antigravity. Details of the tool: [offline guide](docs/offline-guide.md).

## Limits

- Synthetic data only; no real customer data.
- No network, LLM, CRM or sending of any message; a draft is never sent and a handoff is never accepted.
- Not production-ready: no production privacy or tenant authorization guarantee.
- License not chosen: the plugin declares `UNLICENSED` (all rights reserved) until the owner decides.

Python 3.11 or newer is required; the runtime uses only the standard library.

## Install

Give the prompt at the end of [INSTALL.md](INSTALL.md) to your agent; it follows that file and asks before it touches
anything. Per-harness steps: [hosts/](hosts/README.md). The repository has no remote yet, so install from a local
checkout.

## Test

From the repository root:

```bash
python -m pytest
```

No environment variable is needed; `pyproject.toml` puts `src` on the path. `pytest-cov` is optional, for coverage; when you use it, point `COVERAGE_FILE` at a path outside the tree so no `.coverage` file lands in the repository.

## Layout

| Path | What |
|---|---|
| `src/agent_customer_team/` | the offline tool (standard library only) |
| `skills/customer-support-offline/` | the skill that wraps the tool |
| `evals/` | trigger cases for the skill (not run yet) |
| `tests/` | unit tests, runtime lock, packaging and documentation gates |
| `.claude-plugin/`, `.codex-plugin/`, `plugin.json` | plugin manifests |
| `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` | repository rules |
| `hosts/`, `INSTALL.md` | install guides |
