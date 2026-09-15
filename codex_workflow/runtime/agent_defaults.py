"""Conservative child defaults, preserving explicit owner configuration.

Only absent scalar keys are inserted. Existing settings (including lower caps,
legacy aliases, model choices and disabled agents) are never silently replaced.
The complete parsed result must equal the intended one-key-at-a-time change.
"""
from __future__ import annotations
import copy
import json
import re
from ._toml import tomllib
from .errors import ValidationError
from .smart_config import _statements

DEFAULTS = {
    'max_concurrent_threads_per_session': 3,
    'default_subagent_model': 'gpt-5.6-luna',
    'default_subagent_reasoning_effort': 'medium',
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
            warnings.append(f'Explicit agents.{key} preserved; it differs from the economical default.')
    cap = agents.get('max_concurrent_threads_per_session', agents.get('max_threads'))
    if cap is not None and cap > 3:
        warnings.append('Explicit concurrency above 3 preserved. Normal Smart fan-out remains 1-3; review the cap deliberately.')
    if not added:
        return text, warnings, {}
    # Safest common representation: add absent assignments to the explicit table.
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
        # Inline/dotted definitions have subtle table-closure rules. Preserve them
        # rather than attempt a lossy serializer; expose the missing defaults.
        warnings.append('Inline/dotted [agents] syntax preserved. Missing child defaults were not inserted; use named roles and inspect configuration.')
        return text, warnings, {}
    else:
        result = text + ('\n' if text and not text.endswith('\n') else '') + '\n[agents]\n' + lines
    desired = copy.deepcopy(cfg)
    desired.setdefault('agents', {}).update(added)
    if parse(result) != desired:
        raise ValidationError('Child-default edit would change unrelated settings')
    return result, warnings, added
