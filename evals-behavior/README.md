# Behavior eval

Same four cases as `evals/`, but the run grants Bash, so graders also check the CLI command and the final reply. Bash
runs only inside the OS sandbox, which native Windows lacks: run it on Linux (macOS is untested), normally through the
`eval-behavior` GitHub Actions workflow (labels `run-behavior-eval-smoke` / `run-behavior-eval`, or manual run).

Each run calls the model and costs money (estimate 1-3 USD for 4 cases x 3 runs; not measured yet). Command on Linux,
from a copy of the plugin **outside your home directory** (with Bash granted the sandbox cannot read the home directory):

```
claude plugin eval /opt/acs --eval-dir evals-behavior --allow-tools Bash --trust-plugin --no-publish --ablation none \
  --max-cost-usd 5 --model claude-sonnet-5-5 --judge-model claude-haiku-5-5
```

Bash is granted broadly: the skill's command spans several lines and sets `PYTHONPATH=`, and Bash allow rules cannot
match past such an assignment, so no narrow rule fits. The fences are the OS sandbox, `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1`,
the canary in `evals-scrub/`, the negative cases' "no Bash" graders, and the credential scan of the results.

Exit 1 under the default threshold 1.0 is expected when a positive case passes 2 of 3 runs; read the scores in
`result.json`.

`evals/` stays the activation-only suite that runs on Windows; this folder does not replace it.

Job steps (workflow `eval-behavior`):

```
run size (label or inputs, checked) -> credential secret present? --no--> fail, no model called
  -> sandbox prerequisites (bubblewrap, socat, user namespaces)
  -> Claude Code 2.1.310 from .github/eval/package-lock.json (npm ci, audit signatures)
  -> copy tracked files to /opt/acs (the sandbox cannot read the home directory)
  -> canary evals-scrub: Bash must see no credential --fail--> skip the eval, job fails
  -> behavior eval evals-behavior (exit code kept, job continues)
  -> always: scan out/ for the credential --found--> delete out/, job fails
  -> keep out/ as artifact for 7 days (only if the scan is clean)
  -> job exits with the eval's exit code
```

Start a run:

- Label a pull request opened from this repository: `run-behavior-eval-smoke` (case `triage-positive`, 1 run, 1 USD
  ceiling) or `run-behavior-eval` (4 cases, 3 runs, 5 USD). Remove and re-add the label to run again. Pull requests from
  forks are skipped.
- After the workflow is on the default branch: Actions -> eval-behavior -> Run workflow (case glob, runs 1-5, ceiling 1-10
  USD).

Credential: create the repository secret `ANTHROPIC_API_KEY` (an API key from a dedicated Console workspace with a spend
limit). Never paste the value anywhere else. Without it the job stops before any model call. Only this secret is
accepted, because the canary measures exactly this variable.

`evals/customer-support-offline/cases.json` says `status: evaluated` because the activation cases have run; the
behavior graders in this folder have not run yet, so its `expected_behaviors` are not all graded.
