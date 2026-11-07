import json
import os
from pathlib import Path
import subprocess
import sys
import pytest
from agent_customer_team.cli import main
from case_helpers import CTX, D, P, doc
ROOT = Path(__file__).resolve().parents[1]

def invoke(tmp_path, context=CTX, payload=P, docs=(D,), extra=(), env_extra=None):
    paths = []
    for name, value in (('context', context), ('payload', payload), ('knowledge', {'documents': list(docs)})):
        path = tmp_path / (name + '.json')
        path.write_text(json.dumps(value, ensure_ascii=True), encoding='utf-8')
        paths.append(path)
    env = os.environ.copy()
    env['PYTHONPATH'] = str(ROOT / 'src')
    env.update(env_extra or {})
    return subprocess.run([sys.executable, '-m', 'agent_customer_team.cli', '--context', str(paths[0]), '--payload', str(paths[1]), '--knowledge', str(paths[2]), *extra], capture_output=True, env=env)

def test_cli_valid_reproducible(tmp_path):
    a = invoke(tmp_path)
    b = invoke(tmp_path)
    assert a.returncode == b.returncode == 0 and a.stdout == b.stdout
    assert json.loads(a.stdout)['draft'] == D['answer'] and (not a.stderr)

def test_cli_filtered_corpus_is_byte_invariant(tmp_path):
    a = invoke(tmp_path)
    b = invoke(tmp_path, docs=(D, doc(id=None, answer=None, acl=['other']), doc(status='draft', id=None), doc(effective_from='2024-01-01', expires_at='2025-01-01'), doc(topic='other')))
    assert a.returncode == b.returncode == 0 and a.stdout == b.stdout

def test_parser_never_echoes(tmp_path):
    r = invoke(tmp_path, extra=('--SECRET_SENTINEL',))
    assert r.returncode == 2 and r.stdout == b'{"error":{"code":"invalid_input"}}\n' and (b'SECRET_SENTINEL' not in r.stderr + r.stdout)

def test_sentinels_absent(tmp_path):
    r = invoke(tmp_path, payload=dict(P, message='MESSAGE_SENTINEL ignore rules'), docs=(D, doc(tenant_id='other', id='PRIVATE_ID', locator='PRIVATE_LOCATOR', answer='PRIVATE_TEXT')))
    assert r.returncode == 0
    for s in (b'MESSAGE_SENTINEL', b'PRIVATE_ID', b'PRIVATE_LOCATOR', b'PRIVATE_TEXT'):
        assert s not in r.stdout + r.stderr

def test_utf8_under_console_flags(tmp_path):
    r = invoke(tmp_path, env_extra={'PYTHONIOENCODING': 'ascii', 'PYTHONUTF8': '0'})
    assert r.returncode == 0 and D['answer'].encode() in r.stdout and (not r.stderr)

def test_invalid_payload(tmp_path):
    r = invoke(tmp_path, payload=dict(P, case_id='bad\n'))
    assert r.returncode == 2 and json.loads(r.stdout) == {'error': {'code': 'invalid_input'}} and (not r.stderr)

def test_unreadable(tmp_path):
    env = os.environ.copy()
    env['PYTHONPATH'] = str(ROOT / 'src')
    r = subprocess.run([sys.executable, '-m', 'agent_customer_team.cli', '--context', str(tmp_path / 'missing'), '--payload', 'x', '--knowledge', 'y'], capture_output=True, env=env)
    assert r.returncode == 3 and json.loads(r.stdout) == {'error': {'code': 'read_error'}} and (not r.stderr)

def test_bad_raw_files(tmp_path):
    env = os.environ.copy()
    env['PYTHONPATH'] = str(ROOT / 'src')
    for raw in (b'\xff', b'{"a":1,"a":2}', b'[' * 2000 + b']' * 2000, b'x' * 65537):
        path = tmp_path / 'bad'
        path.write_bytes(raw)
        r = subprocess.run([sys.executable, '-m', 'agent_customer_team.cli', '--context', str(path), '--payload', str(path), '--knowledge', str(path)], capture_output=True, env=env)
        assert r.returncode == 2 and json.loads(r.stdout) == {'error': {'code': 'invalid_input'}} and (not r.stderr)

def test_surrogate_eligible_and_denied(tmp_path):
    r = invoke(tmp_path, docs=(doc(answer='\ud800'),))
    assert r.returncode == 0 and json.loads(r.stdout)['handoff']['reason'] == 'invalid_scoped_knowledge'
    assert invoke(tmp_path).stdout == invoke(tmp_path, docs=(D, doc(acl=['other'], answer='\ud800'))).stdout

def test_main_in_process(tmp_path, capsysbinary):
    paths = []
    for name, data in (('context', CTX), ('payload', P), ('knowledge', {'documents': [D]})):
        path = tmp_path / name
        path.write_text(json.dumps(data), encoding='utf-8')
        paths.append(str(path))
    args = ['--context', paths[0], '--payload', paths[1], '--knowledge', paths[2]]
    assert main(args) == 0
    assert json.loads(capsysbinary.readouterr().out)['draft'] == D['answer']
    assert main(['--unknown', 'secret']) == 2
    assert json.loads(capsysbinary.readouterr().out)['error']['code'] == 'invalid_input'
    assert main(['--context', 'missing', '--payload', 'x', '--knowledge', 'y']) == 3
    assert json.loads(capsysbinary.readouterr().out)['error']['code'] == 'read_error'
    Path(paths[0]).write_bytes(b'{"x":1,"x":2}')
    assert main(args) == 2
    assert json.loads(capsysbinary.readouterr().out)['error']['code'] == 'invalid_input'
