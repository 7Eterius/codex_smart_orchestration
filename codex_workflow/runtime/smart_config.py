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
    return f'''Smart Orchestration 3.1: Main reads {json.dumps(policy, ensure_ascii=False)} once for substantive work. Named workers follow role/task.
Optimize accepted quality, elapsed time and total model work, not cheap tokens alone. Main owns product/architecture/design judgment and acceptance. Main may implement small understood fixes or context-heavy critical-path work directly; do not delegate every typo or pre-solve whole worker patches.
Routine/Luna Max handles ordinary implementation and bounded unknown bugs; Investigator/Luna Max handles causal discovery; Simple/Luna Max handles known recipes. Default/Sol Low handles moderate work and adaptive tools, Deep/Sol Medium deep work, Senior/Sol High serious/critical work. Start at appropriate depth, not a mandatory ladder. One same-defect evidence-based correction without progress triggers Sol/Main diagnosis with original evidence.
Tester/Luna Medium runs approved tests and reports receipts; it is not semantic sign-off or coverage authority. Reviewer/Luna Max independently reviews ordinary changes; Senior Reviewer/Sol High handles deep/critical risk. Focused checks during edits, required complete suites on stable integrated candidates. Reuse applicable verified runs instead of duplicating suites across agents; mandatory fresh/full gates win. Zero tests, missing shards, incomplete runs and unresolved flaky failures are not valid passes.
Dispatch useful independent work in parallel before waiting. Start with two branches; at most five Smart-owned open threads within actual owner/client capacity, excluding Main. Main may work on a disjoint critical path. Declare read/write scopes, prerequisites and mutable resources; whole-tree tests cannot race writers. Reserve semantic-review capacity; Tester cannot replace it. Budget test processes/CPU/RAM separately. Completion is not native closure.
Read only relevant sources and guides. No manager or mandatory ledger. Preserve candidate holds, original logs, independent gates and actual visuals. Main-authored fixes need required independent review. Release holds before repair and refresh affected proof. Missing evidence is UNVERIFIED; affected drift STALE. Workers own command waits; timeout alone causes no progress SEND, duplicate suite or unfinished-diff scan. Honor real user interruptions.
No invented tools, silent model/effort downgrade, automatic Fast/Astra, permission expansion, cap increase, ungranted Git/production writes or restart. Preserve explicit owner/profile/speed settings. Owner/project, approval, no-agent and read-only rules bind. Disk consistency is not live activation or measured savings.'''


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
