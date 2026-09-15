#!/usr/bin/env python3
"""Install Smart Orchestration globally. Preview by default; --apply writes.

No project paths, repository scanning, source/store edits, model calls or Git.
Python 3.11+. Quit Codex before applying. Backups live outside the managed runtime.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import uuid

if sys.version_info < (3, 11):
    raise SystemExit('Use Python 3.11+ (on this Mac: /opt/homebrew/bin/python3.11).')
PACKAGE = Path(__file__).resolve().parent.parent
if str(PACKAGE) not in sys.path:
    sys.path.insert(0, str(PACKAGE))
from runtime.errors import ValidationError, WorkflowError
from runtime.layout import PackageLayout, RuntimePaths, USER_STATE
from runtime.markers import USER_MANAGED, extract
from runtime.plan import OperationPlan, read_json, json_mutation
from runtime.release import parse_semver, acquire, select_latest
from runtime.runtime_ops import plan_runtime_files
from runtime.smart_config import patch_config, SMART
from runtime.transaction import Mutation


def safe_path(path: Path, home: Path) -> None:
    try:
        path.relative_to(home)
    except ValueError as exc:
        raise ValidationError(f'Target outside Codex home: {path}') from exc
    cursor = path
    while cursor != home.parent:
        if cursor.is_symlink():
            raise ValidationError(f'Refusing symlink in target ancestry: {cursor}')
        if cursor == home:
            break
        cursor = cursor.parent


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read(path: Path) -> bytes | None:
    if path.exists() and not path.is_file():
        raise ValidationError(f'Target is not a regular file: {path}')
    return path.read_bytes() if path.is_file() else None


def prepare(package_root: Path, home: Path) -> tuple[OperationPlan, dict[str, bytes | None]]:
    home = home.expanduser().absolute()
    safe_path(home, home)
    package = PackageLayout.resolve(package_root)
    if not (package.root / 'smart_orchestration.md').is_file():
        raise ValidationError('Not a Smart Orchestration package')
    runtime = RuntimePaths(home)
    if package.root == runtime.runtime.resolve():
        # Safe: all planned bytes are read before the transaction starts.
        pass
    installed_version = runtime.runtime / 'operate/VERSION'
    safe_path(installed_version, home)
    if installed_version.is_file() and parse_semver(installed_version.read_text().strip()) > parse_semver(package.version):
        raise ValidationError('Refusing to downgrade a newer installation')
    # Reject active symlinks before inherited planning can follow/read them.
    for directory in (runtime.runtime, runtime.agents, runtime.skills):
        safe_path(directory, home)
        if directory.exists() and not directory.is_dir():
            raise ValidationError(f'Expected a directory: {directory}')
        if directory.is_dir():
            for path in directory.rglob('*'):
                if path.is_symlink():
                    # Backups are never installed or read as live source.
                    if '.backups' not in path.parts and '.source_backup' not in path.parts:
                        raise ValidationError(f'Symlink in managed surface: {path}')
    for path in (runtime.config_toml, runtime.user_agents):
        safe_path(path, home)
        _read(path)
    current_config = runtime.config_toml.read_text() if runtime.config_toml.is_file() else ''
    from runtime._toml import tomllib
    parsed = tomllib.loads(current_config)
    if parsed.get('agents', {}).get('enabled') is False or parsed.get('features', {}).get('multi_agent') is False:
        raise ValidationError('Subagents are explicitly disabled in config.toml; enable them deliberately before installing')
    # Never replace an unowned worker or silently erase an owner's worker tuning.
    for name in package.worker_names:
        target = runtime.agents / f'{name}.toml'
        if not target.exists():
            continue
        before = target.read_bytes()
        incoming = (package.agent_templates / f'{name}.toml').read_bytes()
        template = runtime.runtime / 'templates/agents' / f'{name}.toml'
        known = template.read_bytes() if template.is_file() else None
        if before != incoming and (known is None or before != known):
            raise ValidationError(f'Custom/unowned worker requires review before replacement: {target}')
    mutations, owned, _cleanup = plan_runtime_files(package, runtime)
    # Preserve every unrelated TOML value, including parent model/effort/speed,
    # tool permissions, agent limits and existing developer instructions.
    rendered_config = patch_config(current_config, home)
    chosen = {}
    for mutation in mutations:
        safe_path(mutation.path, home)
        if mutation.path == runtime.config_toml:
            mutation = Mutation(mutation.path, rendered_config.encode(), 0o600)
        elif mutation.path == runtime.user_agents:
            mutation = Mutation(mutation.path, mutation.content.replace(b'~/.codex', str(home).encode()), 0o600)
        chosen[mutation.path] = mutation
    state = {
        'schema_version': 1, 'version': package.version, 'workflow': 'Smart Orchestration',
        'mode': 'global', 'owned_runtime_files': sorted(owned),
        'owned_workers': sorted(package.worker_names), 'owned_skills': sorted(package.skill_names),
    }
    state_mutation = json_mutation(runtime.runtime / USER_STATE, state)
    chosen[state_mutation.path] = state_mutation
    changed = []
    before_by_path = {}
    for path, mutation in chosen.items():
        safe_path(path, home)
        before = _read(path)
        if before == mutation.content:
            continue
        mode = path.stat().st_mode & 0o777 if path.exists() else 0o600
        changed.append(Mutation(path, mutation.content, mode))
        before_by_path[str(path)] = before
    warnings = []
    if (home / 'AGENTS.override.md').is_file():
        warnings.append('AGENTS.override.md is preserved; activation also uses developer_instructions.')
    for name, profile in parsed.get('profiles', {}).items():
        if isinstance(profile, dict) and 'developer_instructions' in profile:
            warnings.append(f'Profile {name!r} overrides developer_instructions; verify effective activation when using it.')
    warnings.append('Project config can override global config. Do not claim model/effort or activation without observable evidence.')
    plan = OperationPlan('install-smart-global', changed, warnings, [], {
        'workflow':'Smart Orchestration', 'version':package.version, 'scope':str(home),
        'project_mutations':0, 'parent_settings':'preserved',
    })
    return plan, before_by_path


def apply_plan(plan: OperationPlan, before: dict[str, bytes | None], home: Path) -> Path | None:
    home = home.expanduser().absolute()
    if not plan.mutations:
        return None
    # A lock prevents concurrent installers, not concurrent Codex agents.
    home.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock = home / '.smart-orchestration-install.lock'
    safe_path(lock, home)
    try:
        lock.mkdir(mode=0o700)
    except FileExistsError as exc:
        raise ValidationError('Another installer or stale install lock exists; inspect it before retrying') from exc
    try:
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
        backup = home / '.smart-orchestration-backups' / stamp
        safe_path(backup, home)
        records, backup_mutations = [], []
        for mutation in plan.mutations:
            path = mutation.path
            safe_path(path, home)
            if _read(path) != before[str(path)]:
                raise ValidationError(f'File changed during preparation; quit Codex and retry: {path}')
            relative = path.relative_to(home)
            previous = before[str(path)]
            if previous is not None:
                backup_mutations.append(Mutation(backup / 'files' / relative, previous, 0o600))
            records.append({'path':str(relative), 'existed':previous is not None,
                            'before':digest(previous) if previous is not None else None,
                            'after':digest(mutation.content) if mutation.content is not None else None,
                            'mode':mutation.mode})
        manifest = json.dumps({'schema':1,'workflow':'Smart Orchestration','files':records}, indent=2).encode()
        backup_mutations.append(Mutation(backup / 'manifest.json', manifest, 0o600))
        backup.mkdir(parents=True, exist_ok=False, mode=0o700)
        OperationPlan('backup-and-install-smart', backup_mutations + plan.mutations, [], []).apply()
        return backup
    finally:
        lock.rmdir()


def status(home: Path) -> dict:
    home = home.expanduser().absolute()
    config_path = home / 'config.toml'
    safe_path(config_path, home)
    from runtime._toml import tomllib
    cfg = tomllib.loads(config_path.read_text()) if config_path.is_file() else {}
    instructions = cfg.get('developer_instructions', '')
    policy = home / 'codex_workflow/smart_orchestration.md'
    version = home / 'codex_workflow/operate/VERSION'
    for path in (policy, version):
        safe_path(path, home)
    block_ok = False
    if isinstance(instructions,str) and SMART.start in instructions and SMART.end in instructions:
        block_ok = bool(extract(instructions, SMART))
    return {'workflow':'Smart Orchestration', 'global_bootstrap_present':block_ok,
            'policy_present':policy.is_file(), 'version':version.read_text().strip() if version.is_file() else None,
            'note':'Disk configuration verified only; restart Codex and verify effective role/model settings in a live task.'}


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--codex-home',type=Path,default=Path(os.environ.get('CODEX_HOME','~/.codex')))
    parser.add_argument('--package-root',type=Path,default=PACKAGE)
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--check',action='store_true')
    parser.add_argument('--update',action='store_true',help='Acquire a checksummed fork release, not upstream')
    args=parser.parse_args(argv)
    temporary=None
    try:
        if args.check:
            if args.apply or args.update:
                raise ValidationError('--check cannot be combined with --apply or --update')
            print(json.dumps(status(args.codex_home),indent=2))
            return 0
        package_root=args.package_root
        if args.update:
            temporary,package_root=acquire(select_latest())
        plan,before=prepare(package_root,args.codex_home)
        result=plan.summary()
        result['applied']=False
        if not args.apply:
            result['planned_files']=[str(m.path) for m in plan.mutations]
        if args.apply:
            backup=apply_plan(plan,before,args.codex_home)
            result['applied']=True
            result['backup']=str(backup) if backup else None
            result = {'workflow':'Smart Orchestration', 'version':plan.details['version'],
                      'applied':True, 'changed_files':len(plan.mutations),
                      'backup':str(backup) if backup else None, 'warnings':plan.warnings,
                      'status':'Installed globally. Restart Codex.' if backup else 'Already installed; no writes.'}
        else:
            result['status']='Preview only. Quit Codex, then use --apply.'
        print(json.dumps(result,indent=2,sort_keys=True))
        return 0
    except (OSError,ValueError,WorkflowError) as exc:
        print(json.dumps({'applied':False,'error':str(exc)}),file=sys.stderr)
        return 1
    finally:
        if temporary is not None:
            temporary.cleanup()


if __name__=='__main__':
    raise SystemExit(main())
