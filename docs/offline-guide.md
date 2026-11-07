# Local synthetic case

Python 3.11 or newer is required; runtime uses only the standard library. From the repository root set the package path, then run the CLI:

PowerShell:

```powershell
$env:PYTHONPATH = Join-Path (Get-Location).Path 'src'
python -B -m agent_customer_team.cli --context tests/fixtures/context.json --payload tests/fixtures/payload.json --knowledge tests/fixtures/knowledge.json
```

POSIX shell:

```sh
export PYTHONPATH="$(pwd)/src"
python -B -m agent_customer_team.cli --context tests/fixtures/context.json --payload tests/fixtures/payload.json --knowledge tests/fixtures/knowledge.json
```

With pytest and pytest-cov already available, run `python -m pytest -q --cov=agent_customer_team --cov-report=term-missing --cov-fail-under=80`.

Exit 0 means an internal result (draft, human-owned or pending handoff); 2 means invalid input or flags; 3 means an input file could not be read. No message is sent or handoff accepted. The context is trusted only as a local test fixture, not authenticated. Use synthetic data only. This prototype provides no production privacy or tenant authorization guarantee.

Inputs must be regular local files already present on storage managed by the operator. Do not supply UNC paths, network drives, or cloud placeholders. The CLI rejects lexical UNC/device prefixes; this is not a filesystem sandbox or a guarantee that mounted storage is offline. `-B` avoids interpreter bytecode writes.
