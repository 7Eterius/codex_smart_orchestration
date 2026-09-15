"""Restore a specific Smart backup only if all recorded post-state still matches.

No force flag, directory wipe or inferred latest backup. Old files require an
exact before-hash match; new files are deleted only with matching after-hashes.
Apply through the normal backed-up installer transaction, making undo reversible.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from .errors import ValidationError
from .plan import OperationPlan
from .transaction import Mutation


def prepare_restore(home: Path, backup: Path):
    from .smart_install import safe_path, _read
    home = home.expanduser().absolute()
    backup = backup.expanduser().absolute()
    allowed = home / '.smart-orchestration-backups'
    safe_path(backup, home)
    if backup.parent != allowed:
        raise ValidationError('Select one direct backup directory under .smart-orchestration-backups')
    manifest = backup / 'manifest.json'
    safe_path(manifest, home)
    data = json.loads(manifest.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('schema') != 1 or data.get('workflow') != 'Smart Orchestration' or not isinstance(data.get('files'), list):
        raise ValidationError('Unrecognized backup manifest')
    changes, previous, seen = [], {}, set()
    cleanup_dirs: list[Path] = []
    raw_created_dirs = data.get('created_dirs', [])
    if not isinstance(raw_created_dirs, list) or not all(isinstance(item, str) and item for item in raw_created_dirs):
        raise ValidationError('Invalid created_dirs manifest')
    for raw in raw_created_dirs:
        relative_dir = Path(raw)
        if relative_dir.is_absolute() or '..' in relative_dir.parts or not relative_dir.parts:
            raise ValidationError('Unsafe created directory in backup manifest')
        directory = home / relative_dir
        safe_path(directory, home)
        cleanup_dirs.append(directory)
    sha = lambda value: hashlib.sha256(value).hexdigest() if value is not None else None
    for record in data['files']:
        if not isinstance(record, dict) or not isinstance(record.get('path'), str):
            raise ValidationError('Invalid backup record')
        relative = Path(record['path'])
        if relative.is_absolute() or '..' in relative.parts or not relative.parts:
            raise ValidationError('Unsafe backup target')
        if not (str(relative) in ('config.toml', 'AGENTS.md') or relative.parts[0] in ('codex_workflow', 'agents', 'skills')):
            raise ValidationError('Backup target is not a workflow surface')
        path = home / relative
        if path in seen:
            raise ValidationError('Duplicate backup target')
        seen.add(path)
        safe_path(path, home)
        current = _read(path)
        if sha(current) != record.get('after'):
            raise ValidationError(f'Newer edits conflict with restore: {relative}')
        if record.get('existed') is True:
            source = backup / 'files' / relative
            safe_path(source, home)
            content = _read(source)
            if content is None or sha(content) != record.get('before'):
                raise ValidationError(f'Backup bytes missing or altered: {relative}')
        elif record.get('existed') is False and record.get('before') is None:
            content = None
        else:
            raise ValidationError('Invalid prior-state marker')
        mode = record.get('before_mode')
        if mode is None:
            mode = record.get('mode', 0o600)
        if isinstance(mode, bool) or not isinstance(mode, int) or mode < 0 or mode > 0o777:
            raise ValidationError('Invalid backup file mode')
        changes.append(Mutation(path, content, mode))
        previous[str(path)] = current
    return OperationPlan('restore-smart-backup', changes, ['Exact changed-file restoration only; restart Codex after applying.'], [],
                         {'workflow': 'Smart Orchestration', 'version': 'restore', 'project_mutations': 0},
                         cleanup_dirs=cleanup_dirs), previous
