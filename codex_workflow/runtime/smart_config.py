"""Small, lossless-at-other-keys TOML update for the global Smart bootstrap."""
from __future__ import annotations
import json
import re
from pathlib import Path
from ._toml import tomllib
from .errors import ValidationError
from .markers import Marker, extract, replace

SMART = Marker('<!-- smart-orchestration-start -->', '<!-- smart-orchestration-end -->')


def bootstrap(home: Path) -> str:
    policy = str(home / 'codex_workflow' / 'smart_orchestration.md')
    return f'''Smart Orchestration 3.1.1. For substantive work Main reads {json.dumps(policy, ensure_ascii=False)} once; named workers follow their role/task and relevant project rules, not the full Main policy.
Optimize accepted quality, elapsed time and total work. Main owns product/architecture/design judgment and acceptance. Main may implement tiny understood fixes or context-heavy critical-path work. Delegate coherent work without pre-solving the patch.
Luna Max handles ordinary work; Sol Low/Medium/High handles moderate/deep/serious work. Tester/Luna Medium executes approved tests, never semantic sign-off. Independent Reviewer handles required semantic gates. Follow the installed policy for exact presets and evidence-based recovery; no silent downgrade or repeated stalled attempt.
Run useful independent work in parallel within actual capacity, at most five owned open workers excluding Main. Declare scopes/resources, freeze verification inputs, preserve review capacity and observe native closure. Main may work on a disjoint path.
Reuse applicable evidence, never waive mandatory fresh/full gates. Missing proof is UNVERIFIED; drift STALE. Main inspects actual visuals. No duplicate suites or status polling on timeout.
Preserve owner/project, approval, no-agent, read-only, sandbox and speed settings. No ungranted writes or automatic restart. Disk checks are not live proof. Do not audit or retune the workflow during ordinary tasks.'''


def _statements(text: str):
    """Yield validated TOML statement spans without reserializing other settings."""
    start = i = depth = 0
    quote = None
    comment = False
    while i < len(text):
        ch = text[i]
        if comment:
            if ch == '\n':
                comment = False
                if depth == 0:
                    yield start, i + 1
                    start = i + 1
            i += 1
        elif quote:
            if quote[0] == '"' and ch == '\\':
                i += 2
            elif text.startswith(quote, i):
                i += len(quote)
                quote = None
            else:
                i += 1
        elif ch == '#':
            comment = True
            i += 1
        elif ch in "\"'":
            quote = ch * 3 if text.startswith(ch * 3, i) else ch
            i += len(quote)
        else:
            if ch in '[{':
                depth += 1
            elif ch in ']}':
                depth -= 1
            elif ch == '\n' and depth == 0:
                yield start, i + 1
                start = i + 1
            i += 1
    if start < len(text):
        yield start, len(text)


def patch_config(text: str, home: Path) -> str:
    try:
        parsed = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise ValidationError(f'Codex configuration is not valid TOML: {exc}') from exc
    existing = parsed.get('developer_instructions', '')
    if not isinstance(existing, str):
        raise ValidationError('developer_instructions must be a string; configuration unchanged')
    if SMART.start in existing or SMART.end in existing:
        extract(existing, SMART)
        desired = replace(existing, SMART, bootstrap(home))
    else:
        desired = (existing + '\n\n' if existing else '') + SMART.start + '\n' + bootstrap(home) + '\n' + SMART.end
    if desired == existing:
        return text
    assignment = 'developer_instructions = ' + json.dumps(desired, ensure_ascii=False) + '\n'
    match_span = None
    pattern = re.compile(r'''\s*(?:developer_instructions|"developer_instructions"|'developer_instructions')\s*=''')
    for start, end in _statements(text):
        statement = text[start:end]
        if statement.lstrip().startswith('['):
            break
        if pattern.match(statement):
            if match_span:
                raise ValidationError('Ambiguous root developer_instructions assignment')
            match_span = (start, end)
    if 'developer_instructions' in parsed and match_span is None:
        raise ValidationError('Unsupported developer_instructions spelling; refusing a lossy TOML rewrite')
    if match_span:
        start, end = match_span
        result = text[:start] + assignment + text[end:]
    else:
        result = assignment + text
    try:
        after = tomllib.loads(result)
    except tomllib.TOMLDecodeError as exc:
        raise ValidationError(f'Generated configuration is invalid: {exc}') from exc
    expected = dict(parsed)
    expected['developer_instructions'] = desired
    if after != expected:
        raise ValidationError('Unrelated Codex settings would change; refusing')
    return result
