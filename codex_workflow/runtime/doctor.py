#!/usr/bin/env python3
"""Read-only installed-contract audit. Does not claim live model/tool behavior.
Only known files under CODEX_HOME are read. No project scan, transcript or network.
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
from runtime.agent_defaults import DEFAULTS, parse
from runtime.layout import BUILTIN_WORKERS
from runtime.smart_config import SMART
from runtime.markers import extract, USER_MANAGED
from runtime.smart_install import safe_path
from runtime.errors import WorkflowError


def inspect(home: Path) -> dict:
    home = home.expanduser().absolute()
    result = {'workflow': 'Smart Orchestration', 'issues': [], 'workers': [],
              'verification': 'On-disk contracts only; live routing, history isolation, model availability and quota are unverified.'}
    def read(relative):
        path = home / relative
        safe_path(path, home)
        return path.read_text(encoding='utf-8') if path.is_file() else None
    text = read('config.toml')
    cfg = parse(text or '')
    dev = cfg.get('developer_instructions', '')
    if not isinstance(dev, str) or SMART.start not in dev:
        result['issues'].append('Global Smart bootstrap missing.')
    elif not extract(dev, SMART).strip():
        result['issues'].append('Global Smart bootstrap is empty.')
    global_text = read('AGENTS.md')
    if not global_text or USER_MANAGED.start not in global_text:
        result['issues'].append('Managed global entry missing.')
    else:
        extract(global_text, USER_MANAGED)
    result['version'] = (read('codex_workflow/operate/VERSION') or '').strip() or None
    if not read('codex_workflow/smart_orchestration.md'):
        result['issues'].append('Canonical policy missing.')
    agents = cfg.get('agents', {})
    cap = agents.get('max_concurrent_threads_per_session', agents.get('max_threads'))
    result['configured_child_defaults'] = {key: agents.get(key) for key in DEFAULTS}
    result['effective_configured_cap'] = cap
    if not isinstance(cap, int) or isinstance(cap, bool) or cap < 1 or cap > 3:
        result['issues'].append('A 1-3 child concurrency cap is not established in this config.')
    if agents.get('enabled') is False:
        result['issues'].append('Root subagents are disabled.')
    for key in ('default_subagent_model', 'default_subagent_reasoning_effort'):
        if agents.get(key) != DEFAULTS[key]:
            result['issues'].append(f'agents.{key} is missing or differs from the economical fallback.')
    if cfg.get('service_tier') in ('fast', 'priority'):
        result['issues'].append('Parent Fast/priority speed is configured; review its allowance cost.')
    for name in sorted(BUILTIN_WORKERS):
        worker = read('agents/' + name + '.toml')
        template = read('codex_workflow/templates/agents/' + name + '.toml')
        data = tomllib.loads(worker) if worker else {}
        child_agents = data.get('agents', {})
        no_recursion = isinstance(child_agents, dict) and child_agents.get('enabled') is False
        row = {'role': name, 'present': worker is not None, 'matches_installed_template': worker is not None and worker == template,
               'model': data.get('model'), 'effort': data.get('model_reasoning_effort'), 'child_delegation_disabled': no_recursion}
        result['workers'].append(row)
        if not row['present'] or not row['matches_installed_template'] or not no_recursion:
            result['issues'].append(f'Worker {name}: missing, locally changed, or recursive delegation not disabled.')
    result['override_warning'] = 'Profile, project, command-line and per-spawn overrides can change observed behavior; no override files were modified.'
    result['ok'] = not result['issues']
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
        print(json.dumps({'ok': False, 'error': str(error), 'writes_performed': 0}))
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
