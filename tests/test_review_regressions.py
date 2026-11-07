import json
import os
from pathlib import Path
import subprocess
import sys
import pytest
from agent_customer_team.cli import main
from case_helpers import CTX, D, P, doc
ROOT = Path(__file__).resolve().parents[1]

def execute(paths):
    env = os.environ.copy()
    env['PYTHONPATH'] = str(ROOT / 'src')
    args = [sys.executable, '-B', '-m', 'agent_customer_team.cli']
    for name, path in zip(('context', 'payload', 'knowledge'), paths):
        args.extend(('--' + name, str(path)))
    return subprocess.run(args, capture_output=True, env=env)

def files(tmp_path):
    objects = [CTX, P, {'documents': [D]}]
    paths = [tmp_path / str(i) for i in range(3)]
    for path, value in zip(paths, objects):
        path.write_text(json.dumps(value), encoding='utf-8')
    return paths

def test_locator_c1_eligible_and_inaccessible(tmp_path):
    paths = files(tmp_path)
    baseline = execute(paths)
    assert baseline.returncode == 0
    for control in ('\x80', '\x85', '\x9b', '\x9f'):
        bad = doc(locator='x' + control)
        paths[2].write_text(json.dumps({'documents': [bad]}), encoding='utf-8')
        result = execute(paths)
        assert result.returncode == 0
        assert json.loads(result.stdout)['handoff']['reason'] == 'invalid_scoped_knowledge'
        assert json.loads(result.stdout)['evidence'] == []
        for extra in (dict(bad, acl=['other']), dict(bad, status='draft'), dict(bad, effective_from='2024-01-01', expires_at='2025-01-01')):
            paths[2].write_text(json.dumps({'documents': [D, extra]}), encoding='utf-8')
            assert execute(paths).stdout == baseline.stdout

def test_huge_numeric_values_do_not_cross_boundaries(tmp_path):
    paths = files(tmp_path)
    baseline = execute(paths)
    number = '9' * 4301
    filtered = json.dumps(doc(tenant_id='other', answer='MARKER')).replace('"MARKER"', number)
    eligible = json.dumps(doc(answer='MARKER')).replace('"MARKER"', number)
    paths[2].write_text('{"documents":[' + json.dumps(D) + ',' + filtered + ']}', encoding='utf-8')
    assert execute(paths).stdout == baseline.stdout
    paths[2].write_text('{"documents":[' + eligible + ']}', encoding='utf-8')
    result = execute(paths)
    assert result.returncode == 0
    assert json.loads(result.stdout)['handoff']['reason'] == 'invalid_scoped_knowledge'
    paths = files(tmp_path)
    paths[1].write_text(json.dumps(dict(P, case_id='MARKER')).replace('"MARKER"', number), encoding='utf-8')
    assert execute(paths).returncode == 2

@pytest.mark.parametrize('index', range(3))
def test_duplicate_keys_in_each_valid_file(tmp_path, index):
    paths = files(tmp_path)
    assert execute(paths).returncode == 0
    raw = paths[index].read_text(encoding='utf-8')
    value = json.loads(raw)
    key = next(iter(value))
    repeated = json.dumps(key) + ":" + json.dumps(value[key])
    paths[index].write_text(raw[:-1] + "," + repeated + "}", encoding="utf-8")
    assert execute(paths).returncode == 2

@pytest.mark.parametrize('index', range(3))
def test_file_byte_limit_with_valid_json(tmp_path, index):
    paths = files(tmp_path)
    raw = paths[index].read_bytes()
    paths[index].write_bytes(raw + b' ' * (65536 - len(raw)))
    assert execute(paths).returncode == 0
    paths[index].write_bytes(raw + b' ' * (65537 - len(raw)))
    assert execute(paths).returncode == 2

@pytest.mark.parametrize('constant', ['NaN', 'Infinity', '-Infinity'])
def test_nonstandard_constant_in_denied_record_rejected(tmp_path, constant):
    paths = files(tmp_path)
    denied = json.dumps(doc(acl=['other'], answer='MARKER')).replace('"MARKER"', constant)
    paths[2].write_text('{"documents":[' + json.dumps(D) + ',' + denied + ']}', encoding='utf-8')
    assert execute(paths).returncode == 2

def test_unc_is_rejected_before_open(no_open, capsysbinary):
    with no_open():
        result = main(['--context', '\\\\server\\share', '--payload', 'a', '--knowledge', 'b'])
    assert result == 3
    assert json.loads(capsysbinary.readouterr().out) == {'error': {'code': 'read_error'}}

def test_duplicate_keys_inside_denied_record(tmp_path):
    paths = files(tmp_path)
    denied = json.dumps(doc(acl=['other']))
    denied = denied[:-1] + ',"answer":"second"}'
    paths[2].write_text('{"documents":[' + json.dumps(D) + ',' + denied + ']}', encoding='utf-8')
    assert execute(paths).returncode == 2

@pytest.mark.parametrize('path', ['/\\example.invalid/test/unused', '\\/example.invalid/test/unused', '/\\./pipe/unopened'])
def test_mixed_unc_rejected_before_open(path, no_open, capsysbinary):
    with no_open():
        result = main(['--context', path, '--payload', 'a', '--knowledge', 'b'])
    captured = capsysbinary.readouterr()

    assert result == 3
    assert captured.out == b'{"error":{"code":"read_error"}}\n'
    assert captured.err == b''
    assert path.encode() not in captured.out
