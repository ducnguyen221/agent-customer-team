# Local synthetic case

Python 3.11 or newer is required; runtime uses only the standard library. From the repository root set the package path, then run the CLI (`-P` keeps the current directory off the import path, so a look-alike package there cannot replace the tool):

PowerShell:

```powershell
$env:PYTHONPATH = Join-Path (Get-Location).Path 'src'
python -B -P -m agent_customer_team.cli --context tests/fixtures/context.json --payload tests/fixtures/payload.json --knowledge tests/fixtures/knowledge.json
```

POSIX shell:

```sh
export PYTHONPATH="$(pwd)/src"
python -B -P -m agent_customer_team.cli --context tests/fixtures/context.json --payload tests/fixtures/payload.json --knowledge tests/fixtures/knowledge.json
```

To run the tests, use `python -m pytest` from the repository root; `pyproject.toml` puts `src` on the path, so no `PYTHONPATH` is needed. With pytest-cov also available, add `--cov --cov-report=term-missing` (set `COVERAGE_FILE` to a path outside the tree so no `.coverage` file lands in the repository).

Exit 0 means an internal result (draft, human-owned or pending handoff); 2 means invalid input or flags; 3 means an input file could not be read. No message is sent or handoff accepted. The context is trusted only as a local test fixture, not authenticated. Use synthetic data only. This prototype provides no production privacy or tenant authorization guarantee.

Inputs must be regular local files already present on storage managed by the operator. Do not supply UNC paths, network drives, or cloud placeholders. The CLI refuses, by lexical check only, UNC paths, device and NT object prefixes (such as the double-backslash-question-mark and backslash-question-question-backslash forms) and Windows device names (CON, PRN, AUX, NUL, COM1-9, LPT1-9) in any path component. This is not a filesystem sandbox: mapped drives, junctions and symlinks are not resolved, and it is no guarantee that mounted storage is offline. `-B` avoids interpreter bytecode writes.
