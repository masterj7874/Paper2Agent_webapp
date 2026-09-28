"""Exercise stream parsing and stopping an actual subprocess, without model requests."""
import asyncio
import json
import os
from pathlib import Path

import pytest

from app.paper_worker import ClaudeWorker, WorkerError


def executable(tmp_path, source):
    script = tmp_path / 'worker'
    script.write_text('#!/usr/bin/env python3\n' + source)
    script.chmod(0o700)
    worker = ClaudeWorker()
    worker.executable = str(script)
    return worker


def test_structured_response_from_stream(tmp_path):
    payload = {'type': 'result', 'subtype': 'success', 'is_error': False, 'structured_output': {'title': 'paper'}}
    worker = executable(tmp_path, 'import sys\nsys.stdin.read()\nprint(' + repr(json.dumps(payload)) + ')\n')
    assert asyncio.run(worker.run('test', tmp_path, schema={'type': 'object'})) == {'title': 'paper'}


def test_model_error_never_counts_as_success(tmp_path):
    payload = {'type': 'result', 'subtype': 'error_max_budget_usd', 'is_error': True}
    worker = executable(tmp_path, 'import sys\nsys.stdin.read()\nprint(' + repr(json.dumps(payload)) + ')\n')
    with pytest.raises(WorkerError, match='한도'):
        asyncio.run(worker.run('test', tmp_path))


def test_safety_block_with_success_subtype_is_reported_as_policy_error(tmp_path):
    # Observed CLI failure: subtype is success even though is_error is true.
    payload = {
        'type': 'result', 'subtype': 'success', 'is_error': True,
        'result': "API Error: Opus 5.5 (1M context)'s safeguards flagged this session. Details: `[bio]`",
        'permission_denials': [],
    }
    worker = executable(tmp_path, 'import sys\nsys.stdin.read()\nprint(' + repr(json.dumps(payload)) + ')\n')
    with pytest.raises(WorkerError, match='안전 정책') as error:
        asyncio.run(worker.run('test', tmp_path, schema={'type': 'object'}))
    assert '로그인' not in str(error.value)
    assert 'Anthropic 지원팀' in str(error.value)


@pytest.mark.parametrize('fields,stderr,message', [
    ({'errors': ['OAuth token expired']}, '', '로그인'),
    ({'api_error_status': 401}, '', '로그인'),
    ({'result': 'API Error'}, 'rate_limit_error: Too many requests', '계정의 사용량'),
    ({'api_error_status': 429}, '', '계정의 사용량'),
    ({'errors': ["You've hit your limit"]}, '', '계정의 사용량'),
    ({'subtype': 'error_max_budget_usd'}, '', '설정된 생성 한도'),
    ({'subtype': 'error_max_turns'}, '', '설정된 생성 한도'),
    ({'permission_denials': [{'tool_name': 'Bash'}]}, '', '작업 권한'),
    ({'errors': ['Permission denied']}, '', '작업 권한'),
    ({'errors': ['Prompt is too long']}, '', '입력 길이'),
    ({'subtype': 'error_max_structured_output_retries'}, '', '분석 결과'),
    ({'errors': ['Unknown option --permission-mode']}, '', '실행 옵션'),
    ({'api_error_status': 529}, '', '서비스 오류'),
    ({'result': 'API Error'}, 'fetch failed: ECONNRESET', '서비스 오류'),
    ({'errors': ['Blocked by safety policy']}, '', '안전 정책'),
])
def test_failure_causes_use_all_error_channels(tmp_path, fields, stderr, message):
    payload = {'type': 'result', 'subtype': 'error_during_execution', 'is_error': True, **fields}
    worker = executable(tmp_path, 'import sys\nsys.stdin.read()\n'
                        'print(' + repr(json.dumps(payload)) + ')\n'
                        'print(' + repr(stderr) + ', file=sys.stderr)\nsys.exit(1)\n')
    with pytest.raises(WorkerError, match=message):
        asyncio.run(worker.run('test', tmp_path))


def test_startup_failure_with_large_prompt_reports_stderr(tmp_path):
    worker = executable(tmp_path, 'import sys\n'
                        'print("error: unknown option --json-schema", file=sys.stderr)\nsys.exit(2)\n')
    with pytest.raises(WorkerError, match='실행 옵션'):
        asyncio.run(worker.run('x' * 1_000_000, tmp_path))


def test_unclassified_failure_hides_raw_output(tmp_path):
    payload = {'type': 'result', 'is_error': True, 'result': 'private-document-content sk-secret-token'}
    worker = executable(tmp_path, 'import sys\nsys.stdin.read()\n'
                        'print(' + repr(json.dumps(payload)) + ')\nsys.exit(7)\n')
    with pytest.raises(WorkerError, match='종료 코드: 7') as error:
        asyncio.run(worker.run('test', tmp_path))
    assert 'private-document-content' not in str(error.value)
    assert 'sk-secret-token' not in str(error.value)


def test_missing_result_is_not_success(tmp_path):
    worker = executable(tmp_path, 'import sys\nsys.stdin.read()\nprint("null")\nprint("[]")\n')
    with pytest.raises(WorkerError, match='원인을 분류하지 못했습니다'):
        asyncio.run(worker.run('test', tmp_path))


@pytest.mark.parametrize('cancel', [True, False])
def test_cancel_and_timeout_stop_process_tree(tmp_path, monkeypatch, cancel):
    worker = executable(tmp_path, '''import json, os, pathlib, subprocess, sys, time
sys.stdin.read()
child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
pathlib.Path('pids.json').write_text(json.dumps([os.getpid(), child.pid]))
time.sleep(60)
''')
    monkeypatch.setenv('PAPER2AGENT_ANALYSIS_TIMEOUT', '10' if cancel else '.3')
    async def check():
        task = asyncio.create_task(worker.run('test', tmp_path))
        for _ in range(100):
            if (tmp_path / 'pids.json').exists():
                break
            await asyncio.sleep(.01)
        assert (tmp_path / 'pids.json').exists()
        if cancel:
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
        else:
            with pytest.raises(WorkerError, match='제한 시간'):
                await task
        for pid in json.loads((tmp_path / 'pids.json').read_text()):
            stat = Path(f'/proc/{pid}/stat')
            # A killed orphan may briefly remain a zombie until init reaps it.
            assert not stat.exists() or stat.read_text().split()[2] == 'Z'
    asyncio.run(check())
