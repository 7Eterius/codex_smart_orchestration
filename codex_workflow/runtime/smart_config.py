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
    return f'''Smart Orchestration: Main reads {json.dumps(policy, ensure_ascii=False)} once for substantive work. Named workers follow role/capsule.
Delegation is the execution default, including small edits and review fixes. Main owns product/architecture/design judgment, assessment/acceptance; Luna implements/operates. Main inspects actual running visuals, sends grouped findings as correction tasks to the same suitable worker, then rechecks results. Do not self-patch to save time or pre-write implementation for a worker to paste.
Main baseline is GPT-6.1 Sol Medium; preserve explicit owner selections. Give bounded outcome, scope, deliverables, gates and wake conditions. Recover context progressively: project index/status -> relevant identity -> specific rule/file; do not dump the parent transcript or all docs.
Workers own waits/ordinary repair. timeout alone triggers no progress SEND, duplicate inspection or test. Wake Main for review-ready/completed, decision-needed / DECISION_NEEDED, blocked, required checkpoint or user interruption. DECISION_NEEDED names the question, evidence and why it exceeds the settled brief.
Evidence beats narrative: actual state/tool output/checks outrank worker summaries. Where structured facts already exist, use runtime/challenge.py once before expensive review; CLEAR is not correctness or acceptance. Mechanical challenge returns to worker; protected judgment returns to Main.
Routine/Default may dispatch one Tester only under execution.md with explicit authority and supported mechanics; otherwise Main dispatches that Tester. Tester falsifies the stable patch from original task + full diff, not writer confidence.
At most two Smart-owned open threads across the run. Observe native release before reuse. No manager, invented tools, expanded permissions, project rewrite or claimed activation from disk. Main-only execution needs explicit user override or observed narrow tool/permission boundary. Independent gates, owner approval and No-agent/read-only requests remain binding.'''


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
