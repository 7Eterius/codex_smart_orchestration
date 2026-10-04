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
    return f'''Smart Orchestration 3.0: Main reads {json.dumps(policy, ensure_ascii=False)} once for substantive work. Named workers follow role/task.
Optimize accepted results for time and total cost, not maximum cheap-model delegation. Main owns product/architecture/design judgment and acceptance. Main may implement small understood changes or critical-path work directly. No mandatory handoff for a tiny fix.
Use default_executor (GPT-6.1 Sol Medium) for problem-solving, normal implementation and adaptive tools; tester (Sol Medium) for required independent review; Senior (Sol xhigh) for evidenced depth. Luna is for explicit mechanical recipes/prescribed repetition, not unknown bugs. One same-defect correction without progress triggers Sol/Main diagnosis rather than another cheap retry. Preserve explicit models and speed settings.
Dispatch useful independent work in parallel before waiting; Main may work on a disjoint path. Start with two branches, at most four owned open threads within observed owner/client limits. Declare read/write scopes, prerequisites and mutable resources; never race a writer or held candidate, share a desktop/session, or infer independence from different filenames. Preserve review capacity and observe native release.
Read known sources directly and retrieve only needed context. No manager, mandatory ledger or per-action preflight. Main inspects actual visuals, groups findings and rechecks. Direct corrections need ownership transfer and affected-evidence refresh. Required independent gates still apply to Main-authored work; correction review may reuse a recorded baseline, never mandatory fresh checks.
Use original evidence; missing proof is UNVERIFIED, affected drift STALE. Wait only after assigning useful ready work; timeout alone creates no status SEND or duplicate test. Honor real user interruptions. No invented tools, hidden model downgrade, permission expansion, ungranted Git/production writes or automatic restart. Owner/project, approval, no-agent and read-only constraints bind. Disk integrity is not live activation or measured savings.'''


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
