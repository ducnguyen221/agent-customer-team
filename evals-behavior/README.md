# Behavior eval

Same four cases as `evals/`, but the run grants Bash, so graders also check the CLI command and the final reply. Bash
runs only inside the OS sandbox, which native Windows lacks: run it on Linux or macOS, normally through the
`eval-behavior` GitHub Actions workflow (labels `run-behavior-eval-smoke` / `run-behavior-eval`, or manual run).

Command (Linux or macOS, from the plugin root):

```
claude plugin eval . --eval-dir evals-behavior --allow-tools Bash
```

Exit 1 under the default threshold 1.0 is expected when a positive case passes 2 of 3 runs; read the scores in
`result.json`.

`evals/` stays the activation-only suite that runs on Windows; this folder does not replace it.

Job steps (workflow `eval-behavior`):

```
TK2 fills in the job diagram.
```
