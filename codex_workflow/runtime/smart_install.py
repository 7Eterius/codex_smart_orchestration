#!/usr/bin/env python3
"""Install Smart Orchestration globally. Preview by default; --apply writes.

No project paths, repository scanning, source/store edits, model calls or Git.
Python 3.11+. Apply may complete in an active Codex session; restart afterward.
Backups live outside the managed runtime.
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
from runtime.plan import OperationPlan, read_json, read_string_list, resolve_owned_runtime_path, json_mutation
from runtime.release import parse_semver, acquire, select_latest
from runtime.runtime_ops import plan_runtime_files
from runtime.smart_config import patch_config, SMART
from runtime.transaction import Mutation
from runtime.agent_defaults import configure, parse as parse_config
from runtime.config_assessment import assess_configuration


def safe_path(path: Path, home: Path) -> None:
    if ".." in path.parts or ".." in home.parts:
        raise ValidationError("Parent traversal is not allowed in installation paths")
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
        # An installed runtime has generated templates/state. Reapply its pristine
        # distribution, not a synthetic package assembled from runtime files.
        source = runtime.runtime / '.source_backup' / package.version
        safe_path(source, home)
        package = PackageLayout.resolve(source)
    installed_version = runtime.runtime / 'operate/VERSION'
    safe_path(installed_version, home)
    if installed_version.is_file() and parse_semver(installed_version.read_text().strip()) > parse_semver(package.version):
        raise ValidationError('Refusing to downgrade a newer installation')
    # Inspect only managed targets, not unrelated plugin/skill trees.
    for directory in (runtime.runtime, runtime.agents, runtime.skills):
        safe_path(directory, home)
        if directory.exists() and not directory.is_dir():
            raise ValidationError(f'Expected a directory: {directory}')
    for name in package.worker_names:
        safe_path(runtime.agents / f'{name}.toml', home)
        safe_path(runtime.runtime / 'templates/agents' / f'{name}.toml', home)
    for skill in package.skill_names:
        skill_root = runtime.skills / skill
        safe_path(skill_root, home)
        if skill_root.is_dir():
            for target in skill_root.rglob('*'):
                safe_path(target, home)
        source_root = package.skill_templates / skill
        for source in source_root.rglob('*'):
            if source.is_file():
                relative = source.relative_to(source_root)
                target = skill_root / relative
                template = runtime.runtime / 'templates/skills' / skill / relative
                safe_path(target, home)
                safe_path(template, home)
                before_skill = _read(target)
                known_skill = _read(template)
                if before_skill is not None and before_skill != source.read_bytes() and before_skill != known_skill:
                    raise ValidationError(f'Custom/unowned skill file requires review: {target}')
    for path in (runtime.config_toml, runtime.user_agents):
        safe_path(path, home)
        _read(path)
    current_config = runtime.config_toml.read_text() if runtime.config_toml.is_file() else ''
    from runtime._toml import tomllib
    parsed = parse_config(current_config)
    assessment = assess_configuration(parsed)
    if assessment['errors']:
        raise ValidationError('; '.join(assessment['errors']))
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
    mutations, owned, cleanup_dirs = plan_runtime_files(package, runtime)

    # Retired workflow-owned skills are the one deletion class the global installer
    # may apply automatically. Unknown user files remain preserved. This lets a
    # reviewed release retire a managed skill instead of silently reinstalling or
    # leaving it behind.
    current_state = read_json(runtime.runtime / USER_STATE, default={})
    previous_owned_skills = set(read_string_list(current_state, 'owned_skills'))
    retired_skills = previous_owned_skills - package.skill_names
    retired_skill_roots = tuple(runtime.skills / skill for skill in sorted(retired_skills))
    retired_template_paths: set[Path] = set()
    if retired_skills:
        template_root = runtime.runtime / 'templates' / 'skills'
        for relative in read_string_list(current_state, 'owned_runtime_files'):
            parts = Path(relative).parts
            if len(parts) < 3 or parts[:2] != ('templates', 'skills') or parts[2] not in retired_skills:
                continue
            target = resolve_owned_runtime_path(runtime.runtime, relative)
            mutations.append(Mutation(target, None))
            retired_template_paths.add(target)
            cursor = target.parent
            while cursor.is_relative_to(template_root):
                cleanup_dirs.append(cursor)
                if cursor == template_root:
                    break
                cursor = cursor.parent

    # Preserve every unrelated TOML value, including parent model/effort/speed,
    # tool permissions, agent limits and existing developer instructions.
    rendered_config = patch_config(current_config, home)
    rendered_config, default_warnings, defaults_added = configure(rendered_config)
    chosen = {}
    preserved_deletions = []
    for mutation in mutations:
        safe_path(mutation.path, home)
        if mutation.content is None:
            retired_owned_skill = (
                any(mutation.path.is_relative_to(root) for root in retired_skill_roots)
                or mutation.path in retired_template_paths
            )
            if not retired_owned_skill:
                # Unknown extra files are not garbage merely because a new package
                # does not ship them. Never remove owner additions during adoption.
                preserved_deletions.append(str(mutation.path))
                continue
        if mutation.path == runtime.config_toml:
            mutation = Mutation(mutation.path, rendered_config.encode(), 0o600)
        elif mutation.path == runtime.user_agents:
            # Rewrite only the owned block, never surrounding owner instructions.
            from runtime.markers import replace
            entry = mutation.content.decode('utf-8')
            body = extract(entry, USER_MANAGED).replace('~/.codex', str(home))
            mutation = Mutation(mutation.path, replace(entry, USER_MANAGED, body).encode('utf-8'), 0o600)
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
        if path.is_relative_to(runtime.runtime / '.source_backup') and before is not None:
            raise ValidationError(f'Historical source collision; do not overwrite an existing version: {path}')
        mode = path.stat().st_mode & 0o777 if path.exists() else 0o600
        changed.append(Mutation(path, mutation.content, mode))
        before_by_path[str(path)] = before
    assessment = assess_configuration(parse_config(rendered_config))
    warnings = list(dict.fromkeys(default_warnings + assessment['warnings']))
    if preserved_deletions:
        warnings.append(f"Preserved {len(preserved_deletions)} extra installed file(s); no automatic cleanup.")
    if (home / 'AGENTS.override.md').is_file():
        warnings.append('AGENTS.override.md is preserved; activation also uses developer_instructions.')
    for name, profile in parsed.get('profiles', {}).items():
        if isinstance(profile, dict) and 'developer_instructions' in profile:
            warnings.append(f'Profile {name!r} overrides developer_instructions; verify effective activation when using it.')
    warnings.append('Project config can override global config. Do not claim model/effort or activation without observable evidence.')
    plan = OperationPlan('install-smart-global', changed, warnings, [], {
        'workflow':'Smart Orchestration', 'version':package.version, 'scope':str(home),
        'project_mutations':0, 'parent_settings':'preserved', 'child_defaults_added': defaults_added,
        'configuration_assessment': assessment,
        'retired_owned_skills': sorted(retired_skills),
    }, cleanup_dirs=cleanup_dirs)
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
        created_dirs: set[Path] = set()
        for mutation in plan.mutations:
            path = mutation.path
            safe_path(path, home)
            if _read(path) != before[str(path)]:
                raise ValidationError(f'File changed during preparation; stop and report the conflict: {path}')
            cursor = path.parent
            while cursor != home and not cursor.exists():
                created_dirs.add(cursor)
                cursor = cursor.parent
            relative = path.relative_to(home)
            previous = before[str(path)]
            if previous is not None:
                backup_mutations.append(Mutation(backup / 'files' / relative, previous, 0o600))
            records.append({'path':str(relative), 'existed':previous is not None,
                            'before':digest(previous) if previous is not None else None,
                            'after':digest(mutation.content) if mutation.content is not None else None,
                            'mode':mutation.mode, 'before_mode': path.stat().st_mode & 0o777 if path.exists() else None})
        manifest = json.dumps({'schema':1,'workflow':'Smart Orchestration','files':records,
                               'created_dirs':[str(path.relative_to(home)) for path in sorted(created_dirs, key=lambda item: (len(item.parts), str(item)))]},
                              indent=2).encode()
        backup_mutations.append(Mutation(backup / 'manifest.json', manifest, 0o600))
        backup.mkdir(parents=True, exist_ok=False, mode=0o700)
        OperationPlan('backup-and-install-smart', backup_mutations + plan.mutations, [], [], cleanup_dirs=plan.cleanup_dirs).apply()
        return backup
    finally:
        lock.rmdir()


def status(home: Path) -> dict:
    home = home.expanduser().absolute()
    config_path = home / 'config.toml'
    safe_path(config_path, home)
    from runtime._toml import tomllib
    cfg = parse_config(config_path.read_text()) if config_path.is_file() else {}
    instructions = cfg.get('developer_instructions', '')
    policy = home / 'codex_workflow/smart_orchestration.md'
    version = home / 'codex_workflow/operate/VERSION'
    for path in (policy, version):
        safe_path(path, home)
    block_ok = False
    if isinstance(instructions,str) and SMART.start in instructions and SMART.end in instructions:
        block_ok = bool(extract(instructions, SMART))
    return {'workflow':'Smart Orchestration', 'configuration_assessment':assess_configuration(cfg),
            'global_bootstrap_present':block_ok,
            'policy_present':policy.is_file(), 'version':version.read_text().strip() if version.is_file() else None,
            'agents': {key: cfg.get('agents', {}).get(key) for key in ('max_concurrent_threads_per_session', 'max_threads', 'default_subagent_model', 'default_subagent_reasoning_effort')},
            'note':'Disk configuration verified only; restart Codex and verify effective role/model settings in a live task.'}


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--codex-home',type=Path,default=Path(os.environ.get('CODEX_HOME','~/.codex')))
    parser.add_argument('--package-root',type=Path,default=PACKAGE)
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--check',action='store_true')
    parser.add_argument('--update',action='store_true',help='Acquire a checksummed fork release, not upstream')
    parser.add_argument('--restore-backup', type=Path, help='Exact, conflict-checked restoration of a named backup; preview unless --apply')
    args=parser.parse_args(argv)
    if args.restore_backup and args.update:
        parser.error('--restore-backup and --update are mutually exclusive')
    temporary=None
    try:
        if args.check:
            if args.apply or args.update or args.restore_backup:
                raise ValidationError('--check cannot be combined with --apply or --update')
            print(json.dumps(status(args.codex_home),indent=2))
            return 0
        package_root=args.package_root
        if args.update:
            temporary,package_root=acquire(select_latest())
            # The verified incoming release owns its schema and installer version.
            # Never validate a newer role/resource set against the old launcher.
            import subprocess
            incoming = package_root / 'runtime/smart_install.py'
            if incoming.is_symlink() or not incoming.is_file():
                raise ValidationError('Verified release lacks a regular Smart installer')
            command = [sys.executable, '-B', str(incoming), '--package-root', str(package_root),
                       '--codex-home', str(args.codex_home.expanduser())]
            if args.apply:
                command.append('--apply')
            return subprocess.run(command, check=False).returncode
        if args.restore_backup:
            if args.update:
                raise ValidationError('--restore-backup and --update are mutually exclusive')
            from runtime.smart_restore import prepare_restore
            plan,before=prepare_restore(args.codex_home,args.restore_backup)
        else:
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
                      'status':('Backup restored. Restart Codex manually after this command finishes.' if args.restore_backup else 'Installed globally. Restart Codex manually after this command finishes.') if backup else 'Already installed; no writes.'}
        else:
            result['status']='Preview only. Re-run with --apply in this session; restart Codex manually after a successful apply.'
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
