"""Insert only absent defaults. Explicit owner settings are never replaced."""
from __future__ import annotations
import copy
import json
import re
from ._toml import tomllib
from .errors import ValidationError
from .smart_config import _statements

DEFAULTS = {
    'max_concurrent_threads_per_session': 5,
    'default_subagent_model': 'gpt-6-luna',
    'default_subagent_reasoning_effort': 'max',
}


def parse(text: str) -> dict:
    try:
        cfg = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise ValidationError(f'Invalid Codex TOML: {exc}') from exc
    for section in ('agents', 'features', 'profiles'):
        if section in cfg and not isinstance(cfg[section], dict):
            raise ValidationError(f'[{section}] must be a table')
    return cfg


def configure(text: str) -> tuple[str, list[str], dict]:
    cfg = parse(text)
    agents = cfg.get('agents', {})
    added = {key: value for key, value in DEFAULTS.items() if key not in agents}
    if 'max_threads' in agents:
        added.pop('max_concurrent_threads_per_session', None)
    warnings = []
    for key in ('max_threads', 'max_concurrent_threads_per_session'):
        if key in agents and (isinstance(agents[key], bool) or not isinstance(agents[key], int) or agents[key] < 1):
            raise ValidationError(f'agents.{key} must be a positive integer')
    if 'max_threads' in agents and 'max_concurrent_threads_per_session' in agents:
        raise ValidationError('Both concurrency aliases are set; reconcile the duplicate before installing')
    for key in ('default_subagent_model', 'default_subagent_reasoning_effort'):
        if key in agents and (not isinstance(agents[key], str) or not agents[key].strip()):
            raise ValidationError(f'agents.{key} must be a nonempty string')
        if key in agents and agents[key] != DEFAULTS[key]:
            warnings.append(f'Explicit agents.{key} preserved; it differs from the Smart 3.1 balanced default. Named role settings still apply.')
    cap = agents.get('max_concurrent_threads_per_session', agents.get('max_threads'))
    if cap is not None and cap < 5:
        warnings.append('Existing lower concurrency cap preserved. Smart 3 uses fewer parallel branches or serial review; no cap increase was made.')
    elif cap is not None and cap > 5:
        warnings.append('Higher owner cap preserved. Smart 3 uses at most five owned open threads, not a fan-out target.')
    if not added:
        return text, warnings, {}
    spans = list(_statements(text))
    insertion = None
    root_agents = False
    for start, end in spans:
        statement = text[start:end]
        stripped = statement.strip()
        if re.fullmatch(r'\[\s*(?:agents|"agents"|\'agents\')\s*\]\s*(?:#.*)?', stripped):
            insertion = end
            break
        if re.match(r'\s*(?:agents|"agents"|\'agents\')\s*(?:=|\.)', statement):
            root_agents = True
    lines = ''.join(f'{key} = {json.dumps(value)}\n' for key, value in added.items())
    if insertion is not None:
        prefix = text[:insertion]
        result = prefix + ('' if prefix.endswith('\n') else '\n') + lines + text[insertion:]
    elif root_agents:
        warnings.append('Inline/dotted [agents] syntax preserved. Missing child defaults were not inserted; use named roles and inspect configuration.')
        return text, warnings, {}
    else:
        result = text + ('\n' if text and not text.endswith('\n') else '') + '\n[agents]\n' + lines
    desired = copy.deepcopy(cfg)
    desired.setdefault('agents', {}).update(added)
    if parse(result) != desired:
        raise ValidationError('Child-default edit would change unrelated settings')
    return result, warnings, added
