#!/usr/bin/env python3
"""Read-only installed-contract audit with separate errors/warnings/unverified.

Reads only known CODEX_HOME files. No profile/project scan, chat read or model call.
An ok result means no detected configuration error, not proven live activation.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys

if sys.version_info < (3, 11):
    raise SystemExit('Python 3.11 or newer is required.')
PACKAGE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PACKAGE))
from runtime._toml import tomllib
from runtime.agent_defaults import parse
from runtime.config_assessment import assess_configuration
from runtime.layout import BUILTIN_WORKERS
from runtime.smart_config import SMART
from runtime.markers import extract, USER_MANAGED
from runtime.smart_install import safe_path
from runtime.errors import WorkflowError


def inspect(home: Path) -> dict:
    home = home.expanduser().absolute()
    def read(relative):
        path = home / relative
        safe_path(path, home)
        if path.exists() and not path.is_file():
            raise ValueError(f'Expected a regular file: {relative}')
        return path.read_text(encoding='utf-8') if path.is_file() else None
    text = read('config.toml')
    cfg = parse(text or '')
    result = assess_configuration(cfg)
    result.update({'workflow': 'Smart Orchestration', 'workers': [],
                   'verification': result['assessment_scope']})
    errors, warnings = result['errors'], result['warnings']
    dev = cfg.get('developer_instructions', '')
    if not isinstance(dev, str) or SMART.start not in dev:
        errors.append('Global Smart bootstrap missing.')
    elif not extract(dev, SMART).strip():
        errors.append('Global Smart bootstrap is empty.')
    global_text = read('AGENTS.md')
    if not global_text or USER_MANAGED.start not in global_text:
        errors.append('Managed global entry missing.')
    elif not extract(global_text, USER_MANAGED).strip():
        errors.append('Managed global entry is empty.')
    result['version'] = (read('codex_workflow/operate/VERSION') or '').strip() or None
    if result['version'] is None:
        errors.append('Installed version is missing.')
    if not read('codex_workflow/smart_orchestration.md'):
        errors.append('Canonical policy missing.')
    if (home / 'AGENTS.override.md').exists():
        warnings.append('AGENTS.override.md exists and was not read or changed; effective startup remains unverified.')
    for name in sorted(BUILTIN_WORKERS):
        worker = read('agents/' + name + '.toml')
        template = read('codex_workflow/templates/agents/' + name + '.toml')
        data = tomllib.loads(worker) if worker else {}
        child_agents = data.get('agents', {})
        no_recursion = isinstance(child_agents, dict) and child_agents.get('enabled') is False
        row = {'role': name, 'present': worker is not None,
               'matches_installed_template': worker is not None and worker == template,
               'model': data.get('model'), 'effort': data.get('model_reasoning_effort'),
               'child_delegation_disabled': no_recursion}
        result['workers'].append(row)
        if worker is None:
            errors.append(f'Worker {name} is missing.')
            continue
        if data.get('name') != name:
            errors.append(f'Worker {name} has a mismatched role name.')
        for key in ('model', 'model_reasoning_effort', 'developer_instructions'):
            if not isinstance(data.get(key), str) or not data[key].strip():
                errors.append(f'Worker {name}: {key} must be a nonempty string.')
        if not no_recursion:
            errors.append(f'Worker {name}: recursive delegation is not disabled in its configuration.')
        if template is None:
            errors.append(f'Installed template for {name} is missing.')
        elif worker != template:
            warnings.append(f'Worker {name} differs from its installed template; owner edits are preserved and require review before replacement.')
    result['override_warning'] = 'Profile, project, command-line and per-spawn overrides may change behavior; none were resolved or modified.'
    result['issues'] = list(errors)  # Compatibility: issues now means errors, not preferences.
    result['ok'] = not errors
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--codex-home', type=Path, default=Path(os.environ.get('CODEX_HOME', '~/.codex')))
    args = parser.parse_args(argv)
    try:
        result = inspect(args.codex_home)
        print(json.dumps(result, indent=2))
        return 0 if result['ok'] else 1
    except (OSError, ValueError, WorkflowError) as error:
        print(json.dumps({'ok': False, 'errors': [str(error)], 'warnings': [],
                          'unverified': ['Assessment could not be completed.'], 'writes_performed': 0}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
