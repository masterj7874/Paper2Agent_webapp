"""Headless coding-agent adapter with cancellation, bounded output and time limits."""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import signal
from pathlib import Path


class WorkerError(RuntimeError):
    pass


def failure_message(result: dict | None, stderr: str, returncode: int | None) -> str:
    """Classify provider/CLI failures without exposing raw output or credentials."""
    result = result or {}
    detail = '\n'.join(str(value) for value in (
        result.get('result', ''), result.get('errors', ''), result.get('subtype', ''), stderr,
    )).lower()
    status = result.get('api_error_status')
    if any(word in detail for word in (
        'safeguards flagged', 'safety policy', 'safety filter', 'content policy',
        'content_filter', 'content filtering', 'usage policy', 'safety refusal',
        'blocked by safety', 'output blocked',
    )):
        return ('Claude의 안전 정책에 따라 요청이 차단되었습니다. 논문과 요청 내용을 검토하고, '
                '오탐이 의심되면 Anthropic 지원팀에 문의해 주세요.')
    if status == 401 or any(word in detail for word in (
        'login', 'log in', 'logged in', 'authentication', 'oauth', 'invalid api key', 'invalid_api_key',
    )):
        return 'Claude 로그인이 필요합니다. 서버에서 claude auth login 후 재시도해 주세요.'
    if any(word in detail for word in ('budget', 'max_turns')):
        return '설정된 생성 한도에 도달했습니다. 범위를 줄이거나 서버 한도를 조정한 뒤 재시도해 주세요.'
    if status == 429 or any(word in detail for word in (
        'rate_limit', 'rate limit', 'usage limit', 'hit your limit', 'reached your limit',
        'too many requests', 'quota', 'credit balance', 'insufficient credits',
    )):
        return 'Claude 계정의 사용량 또는 요청 한도에 도달했습니다. 계정의 한도와 갱신 시간을 확인한 뒤 재시도해 주세요.'
    if result.get('permission_denials') or status == 403 or any(word in detail for word in (
        'permission denied', 'permission_denied', 'permission_error',
        'auto mode is not available', 'auto mode is unavailable',
    )):
        return '자동 실행에 필요한 작업 권한을 받지 못했습니다. 서버의 Claude 권한 설정을 확인해 주세요.'
    if any(word in detail for word in (
        'prompt is too long', 'prompt too long', 'context window', 'context length',
        'too many tokens', 'request too large',
    )):
        return 'Claude가 처리할 수 있는 입력 길이를 초과했습니다. 논문이나 추가 자료를 나누어 다시 시도해 주세요.'
    if any(word in detail for word in ('json_schema', 'json schema', 'structured_output', 'structured output')):
        return 'Claude가 요청한 구조의 분석 결과를 생성하지 못했습니다. 서버의 분석 형식과 CLI 호환성을 확인해 주세요.'
    if any(word in detail for word in ('unknown option', 'unrecognized option', 'invalid argument')):
        return '설치된 Claude Code가 실행 옵션을 지원하지 않습니다. 서버의 Claude Code 버전과 실행 설정을 확인해 주세요.'
    if status in (500, 502, 503, 504, 529) or any(word in detail for word in (
        'overloaded', 'service unavailable', 'internal server error', 'api_connection_error',
        'connection error', 'connection refused', 'connection reset', 'econnrefused',
        'econnreset', 'enotfound', 'fetch failed', 'network error', 'timed out', 'timeout',
    )):
        return 'Claude 서버에 연결하지 못했거나 일시적인 서비스 오류가 발생했습니다. 네트워크와 서비스 상태를 확인한 뒤 재시도해 주세요.'
    suffix = f' (종료 코드: {returncode})' if returncode else ''
    return f'Claude가 작업 실패를 반환했지만 원인을 분류하지 못했습니다.{suffix} 서버의 Claude 실행 상태를 확인해 주세요.'


async def stop_process(process):
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        await process.wait()
        return
    try:
        await asyncio.wait_for(process.wait(), timeout=5)
    except asyncio.TimeoutError:
        pass
    # The group can outlive its leader (e.g. a child holding stdout open).
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    await process.wait()


class ClaudeWorker:
    def __init__(self):
        self.executable = os.environ.get('PAPER2AGENT_CLAUDE_BIN', 'claude')

    async def run(self, prompt: str, cwd: Path, *, schema=None, build=False, on_event=None, skill=None, profile=None):
        executable = shutil.which(self.executable)
        if not executable:
            raise WorkerError('Claude Code를 찾을 수 없습니다. 설치하고 claude auth login으로 로그인해 주세요.')
        command = [executable, '-p', '--output-format', 'stream-json', '--verbose',
                   '--no-session-persistence', '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}',
                   '--setting-sources', 'user', '--settings', '{"disableAllHooks":true,"autoMemoryEnabled":false}',
                   '--permission-mode', 'auto' if build else 'dontAsk']
        if build:
            command += ['--tools', 'Read,Write,Edit,Glob,Grep,Bash,Agent,Skill,WebFetch,WebSearch',
                        '--add-dir', str(skill.parent)]
        else:
            command += ['--tools', '', '--disable-slash-commands']
        if schema:
            command += ['--json-schema', json.dumps(schema)]
        prefix = 'BUILD' if build else 'MANUSCRIPT' if profile == 'manuscript' else 'ANALYSIS'
        budget = os.environ.get(f'PAPER2AGENT_{prefix}_BUDGET_USD',
                                '15' if build else '6' if profile == 'manuscript' else '2')
        command += ['--max-budget-usd', budget]
        env = dict(os.environ)
        env.pop('CLAUDECODE', None)  # a separate app worker, not a nested interactive session
        process = await asyncio.create_subprocess_exec(
            *command, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE, cwd=str(cwd), env=env, start_new_session=True, limit=2**21)

        async def stderr_tail():
            tail = b''
            while chunk := await process.stderr.read(4096):
                tail = (tail + chunk)[-4000:]
            return tail.decode('utf-8', 'replace')

        async def consume():
            try:
                process.stdin.write(prompt.encode('utf-8'))
                await process.stdin.drain()
            except (BrokenPipeError, ConnectionResetError):
                # Read the CLI error even if startup fails before it accepts the prompt.
                pass
            finally:
                process.stdin.close()
            result = None
            while line := await process.stdout.readline():
                try:
                    event = json.loads(line)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
                if not isinstance(event, dict):
                    continue
                if event.get('type') == 'result':
                    result = event
                if event.get('type') == 'assistant' and on_event:
                    for block in event.get('message', {}).get('content', []):
                        if block.get('type') == 'tool_use':
                            # Do not expose commands, secrets or raw tool outputs in the UI.
                            name = block.get('name', 'tool')
                            on_event(f'생성 작업 중 · {name}')
            await process.wait()
            return result

        stderr_task = asyncio.create_task(stderr_tail())
        try:
            timeout = float(os.environ.get(f'PAPER2AGENT_{prefix}_TIMEOUT',
                                           '3600' if build else '900' if profile == 'manuscript' else '240'))
            result = await asyncio.wait_for(consume(), timeout=timeout)
            stderr = await stderr_task
            if process.returncode or not result or result.get('is_error') or result.get('subtype', 'success') != 'success':
                raise WorkerError(failure_message(result, stderr, process.returncode))
            if schema:
                value = result.get('structured_output')
                if not isinstance(value, dict):
                    raise WorkerError('분석 결과를 올바른 형식으로 받지 못했습니다. 다시 시도해 주세요.')
                return value
            return result
        except asyncio.TimeoutError:
            raise WorkerError('작업 제한 시간을 초과했습니다. 생성 범위를 줄이고 다시 시도해 주세요.')
        finally:
            await stop_process(process)
            if not stderr_task.done():
                stderr_task.cancel()
            await asyncio.gather(stderr_task, return_exceptions=True)
