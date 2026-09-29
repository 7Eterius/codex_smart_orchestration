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
    return f'''Smart Orchestration: Main reads {json.dumps(policy, ensure_ascii=False)} once for substantive
work. Named workers follow their role/capsule, not global main orchestration.
Delegation is the execution default, including small edits and review fixes. Main owns
product/architecture/design decisions, detailed assessment and acceptance. Named Luna
workers implement/operate. Main inspects actual running visuals, sends grouped findings as correction tasks
to the same suitable worker, then rechecks results. Do not self-patch to save time or
pre-write implementation for a worker to paste. Direct answers/briefs/decisive inspection stay main.
Main baseline is GPT-6.1 Sol Medium; preserve explicit owner selections.
Assign outcome, stop and wake conditions: review-ready, complete, decision-needed or blocked.
Workers own command/test waits and ordinary repairs. Use supported long interruptible waits;
timeout alone triggers no progress SEND, repeated inspection or test. No acknowledgements.
Main returns for real decisions, required design review and acceptance; honor user interruptions.
Routine/Default may dispatch one independent Tester only under execution.md with explicit
authority and supported mechanics; otherwise main dispatches that named Tester.
At most two Smart-owned open threads across the run, including descendants/old units.
Preserve results/resources and observe native closure before reuse. No extra manager.
Main-only execution requires explicit user override or an observed narrowly authorized
tool/permission boundary, stated once; delegate the rest. Missing nesting is not an excuse.
Keep independent gates, owner approval, selected models/effort, permissions and project constraints.
No-agent/read-only requests remain binding. No invented tools, expanded permissions, project
rewrite or claimed live activation from disk alone.'''


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
