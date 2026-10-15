#!/usr/bin/env python3
"""Read-only, offline audit of local Codex rollout JSONL. Python 3.11+.

Outputs are newly created private files outside CODEX_HOME. No network, model calls,
subprocesses, log deletion, configuration edits, or raw transcript exports.
Run: python3 smart_weekly_stats.py --days 7
See README.md for accounting rules and material limits.
"""
from __future__ import annotations

import sys
if sys.version_info < (3, 11):
    sys.exit("Python 3.11 or newer is required. No packages need to be installed.")

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import hashlib
from functools import lru_cache
import hmac
import json
import math
import os
from pathlib import Path
import re
import secrets
import shlex
import stat
import statistics
import sys
import time
import tomllib
import zipfile
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

VERSION = '1.2.1'
UTC = timezone.utc
SCHEMA_REFERENCE = 'openai/codex@f0c5077c34ec7a76b4ad9134835925e6ae3d72ec'
SMART_REFERENCE = 'Smart 4.2.1 presets (unchanged model/effort map from 4.0.1)'
EXPECTED = {
    'simple_executor': ('gpt-6-luna', 'max'),
    'routine_executor': ('gpt-6-luna', 'max'),
    'default_executor': ('gpt-6.1-sol', 'low'),
    'deep_executor': ('gpt-6.1-sol', 'medium'),
    'senior_executor': ('gpt-6.1-sol', 'high'),
    'tester': ('gpt-6-luna', 'medium'),
    'reviewer': ('gpt-6-luna', 'max'),
    'senior_reviewer': ('gpt-6.1-sol', 'high'),
    'investigator': ('gpt-6-luna', 'max'),
    'companion': ('gpt-6-luna', 'max'),
    'archivist': ('gpt-6-luna', 'max'),
}
FIELDS = ('input_tokens', 'cached_input_tokens', 'output_tokens', 'reasoning_output_tokens')
RECOGNIZED_TOOLS = {'exec_command', 'shell_command', 'shell', 'write_stdin',
    'apply_patch', 'spawn_agent', 'wait', 'wait_agent', 'send_input', 'resume_agent',
    'close_agent', 'update_plan', 'view_image', 'list_agents',
    'exec', 'js_repl', 'send_message', 'followup_task', 'interrupt_agent', 'wait_for_agent', 'tool_search'}
ZERO = (0, 0, 0, 0)
SMART_RE = re.compile(r'(?:Smart Orchestration\s+v?|codex-workflow-version:\s*)(\d+\.\d+(?:\.\d+)?)', re.I)
EDIT_RE = re.compile(r'(?:^|[;&|\n])\s*(?:git\s+(?:checkout|switch|merge|cherry-pick|reset|rebase)|'
                     r'sed\s+-i|perl\s+-[^\s]*i|(?:rm|mv|cp|touch)\s)|(?:^|[^>])>(?!>)')
LIMITATIONS = [
    'This is a local-record audit, not an account bill, enforced quota meter, or experiment proving Smart caused improvements.',
    'Only existing sessions/archived_sessions JSONL are read. Ephemeral, deleted, unlogged, remote-only and unsupported traces are unavailable.',
    'Current installation settings are not historical model or version evidence. A Smart 4.0 instruction marker cannot establish patch version 4.0.1.',
    'Workflow cohorts are session-level associations, not per-call version proof. Sessions may span upgrades, and copied instruction markers are not compliance evidence.',
    'Named role + recorded model/effort can establish routing conformance, not task difficulty, sound judgment, reviewer independence, or code correctness.',
    'Turn completion, exit zero and a final assistant message are not independently accepted deliverables. Failed commands can be intentional TDD RED checks.',
    'Repeated test commands are investigation candidates, not proven redundant tests. Source, configuration, environment and external state may have changed invisibly.',
    'Elapsed turn intervals can include human approval and waits; overlapping worker durations are not additive wall-clock time or CPU time.',
    'Raw turn overlap can count one worker several times. The separate distinct-worker overlap merges its intervals; neither proves open-thread cap compliance or independence.',
    'Typed CommandExecution lifecycle items are parsed; arbitrary code-mode JavaScript is never executed or treated as proof a nested command ran. Unsupported schemas remain a coverage gap.',
    'Tool totals include outer code-mode wrappers and observed nested calls; they are not a count of model requests. Missing test evidence is not proof that no tests ran.',
    'Legacy counter accounting is conservative. Replayed history, ambiguous first snapshots, gaps and counter resets are disclosed rather than treated as exact billing.',
    'Token input includes cached input; output includes reasoning output. Do not add either subset a second time. Optional API-equivalent estimates are not subscription usage.',
    'A previous-week comparison is descriptive, not causal; workload, project, model choice, logging and task difficulty may differ.',
    'The targeted local audit disproved the apparent 14-worker peak: copied parent turns were present. This version filters that mechanism but is not a re-audit of your raw logs.',
    'Test command recognition uses a conservative executable-position shell subset; substitutions, heredocs, JS and unknown wrappers remain unsupported. Native wrapper exit zero is not a test pass.',
    'Historical native role tags do not describe later duty transfers. Mixed-duty sessions must not be used as pure-role cost or difficulty benchmarks.',
]


def stamp(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool) and -1e14 < value < 1e14 and math.isfinite(value):
        try:
            return datetime.fromtimestamp(value / 1000 if value > 1e11 else value, UTC)
        except (ValueError, OverflowError, OSError):
            return None
    if not isinstance(value, str):
        return None
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return result.astimezone(UTC) if result.tzinfo else None
    except ValueError:
        return None


def iso(value):
    return value.isoformat().replace('+00:00', 'Z') if value else None


def finite(value, upper=1e15):
    return type(value) in (int, float) and 0 <= value <= upper and math.isfinite(value)


def label(value, default='unknown'):
    return value if isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/+\-]{0,99}', value) else default


def mapping(value):
    return value if isinstance(value, dict) else {}


def stringify(value):
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return stringify(value.get('text', value.get('content', '')))
    if isinstance(value, list):
        return '\n'.join(stringify(x) for x in value)
    return ''


def unpack_args(value):
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            return mapping(json.loads(value))
        except (ValueError, RecursionError):
            pass
    return {}


def command_text(value):
    if isinstance(value, str):
        return value
    if isinstance(value, list) and all(isinstance(x, str) for x in value):
        if len(value) >= 3 and Path(value[0]).name in {'bash', 'zsh', 'sh', 'fish'} and 'c' in value[1]:
            return value[2]
        return shlex.join(value)
    return ''


def is_test_command(command, depth=0):
    """Recognize executable positions, not test words in quoted inspection arguments.

    Conservative shell subset only. No execution, variable expansion, JS parsing,
    command substitution, heredoc interpretation or package-script speculation.
    """
    if not isinstance(command,str) or len(command)>100000 or depth>3:
        return False
    if any(x in command for x in ('<<','`','$(')):
        return False
    try:
        lexer=shlex.shlex(command,posix=False,punctuation_chars=';&|()\n')
        lexer.whitespace=' \t\r'; lexer.commenters='#'
        tokens=list(lexer)
        segments=[]; segment=[]
        for raw in tokens:
            if raw and all(c in ';&|()\n' for c in raw):
                if segment: segments.append(segment); segment=[]
                continue
            decoded=shlex.split(raw,posix=True)
            if len(decoded)!=1: return False
            segment.append(decoded[0])
        if segment: segments.append(segment)
    except ValueError:
        return False
    for args in segments:
        while args and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*=.*',args[0],re.S): args=args[1:]
        if not args: continue
        name=Path(args[0]).name
        if name=='env':
            args=args[1:]
            while args and (args[0]=='--' or re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*=.*',args[0],re.S)): args=args[1:]
            if not args or args[0].startswith('-'): continue
            name=Path(args[0]).name
        rest=args[1:]
        if name in {'sh','bash','zsh'} and len(rest)>=2 and rest[0] in {'-c','-lc','-ec'}:
            if is_test_command(rest[1],depth+1): return True
            continue
        if name in {'npm','pnpm','yarn','bun'}:
            if rest and rest[0] in {'run','run-script'}: rest=rest[1:]
            if rest and (re.fullmatch(r'test(?::[\w:-]+)?',rest[0]) or rest[0] in {'vitest','jest'}): return True
            if rest[:2]==['playwright','test']: return True
            if rest and rest[0]=='exec':
                rest=rest[1:]
                if rest and rest[0]=='--': rest=rest[1:]
                if rest and (rest[0] in {'vitest','jest'} or rest[:2]==['playwright','test']): return True
        elif name in {'npx','bunx'}:
            if rest and (rest[0] in {'vitest','jest'} or rest[:2]==['playwright','test']): return True
        elif name in {'pytest','vitest','jest'}: return True
        elif name=='uv' and rest and rest[0]=='run':
            if is_test_command(shlex.join(rest[1:]),depth+1): return True
        elif re.fullmatch(r'python[\d.]*',name):
            while rest and rest[0] in {'-B','-u','-q','-I','-E','-s'}: rest=rest[1:]
            if len(rest)>=2 and rest[0]=='-m' and rest[1] in {'pytest','unittest'}: return True
            if rest and re.fullmatch(r'test_[\w.-]+\.py',Path(rest[0]).name): return True
        elif name in {'cargo','go','swift','make'} and rest and rest[0]=='test': return True
        elif name=='xcodebuild' and 'test' in rest: return True
    return False


def vector(value):
    """Require input/output; optional cache/reasoning remain flagged when absent."""
    if not isinstance(value, dict) or not all(k in value for k in ('input_tokens', 'output_tokens')):
        return None
    values = []
    for k in FIELDS:
        v = value.get(k, 0)
        if type(v) is not int or not 0 <= v <= 10**16:
            return None
        values.append(v)
    if values[1] > values[0] or values[3] > values[2]:
        return None
    if 'total_tokens' in value and (type(value['total_tokens']) is not int or value['total_tokens'] != values[0]+values[2]):
        return None
    return tuple(values)


def total(v):
    return v[0] + v[2]


def add(a, b):
    return tuple(x+y for x, y in zip(a, b))


def payload_tokens(v):
    return dict(zip(FIELDS, v), total_tokens=total(v))


def percentile(values, p):
    if not values:
        return None
    ordered = sorted(values)
    return round(ordered[max(0, math.ceil(p*len(ordered))-1)], 3)


def parse_duration(value):
    if finite(value, 1e9):
        return float(value)
    if isinstance(value, dict) and finite(value.get('secs'), 1e9) and finite(value.get('nanos', 0), 1e9):
        return value['secs'] + value.get('nanos', 0)/1e9
    if isinstance(value, str) and len(value)<=64:
        m = re.fullmatch(r'(\d+(?:\.\d+)?|\.\d+)\s*(ms|s|seconds)', value)
        if m:
            n = float(m[1])
            seconds=n/1000 if m[2]=='ms' else n
            return seconds if finite(seconds,1e9) else None
    return None


class Ids:
    def __init__(self):
        self.key = secrets.token_bytes(32)

    def get(self, kind, value):
        return kind + '-' + hmac.new(self.key, str(value).encode(), hashlib.sha256).hexdigest()[:14]


@dataclass
class Session:
    sid: str
    parent: str | None = None
    family: str | None = None
    fork: str | None = None
    kind: str = 'unknown'
    role: str = 'unknown'
    role_evidence: str = 'unavailable'
    created: datetime | None = None
    project: str = ''
    version_markers: set = field(default_factory=set)
    cli_versions: set = field(default_factory=set)
    files: set = field(default_factory=set)
    boundary_present: bool = False


class LegacyCounter:
    """Conservative fallback. Never sum repeated last_token_usage blindly."""
    def __init__(self, diagnostics):
        self.prev = None
        self.seen = set()
        self.diag = diagnostics

    def consume(self, info, in_period):
        cur = vector(mapping(info).get('total_token_usage'))
        last = vector(mapping(info).get('last_token_usage'))
        def note(name, amount=1):
            if in_period:
                self.diag[name] += amount
        if cur is None:
            note('legacy_without_usable_cumulative_snapshot_excluded')
            return None  # Last alone cannot distinguish a stale rate-limit broadcast.
        if total(cur) == 0:
            note('legacy_zero_or_synthetic_checkpoint_ignored')
            return None
        if last is not None and total(last) == 0:
            note('legacy_zero_last_checkpoint_ignored')
            return None  # Do not let a replay checkpoint change the active stream baseline.
        if cur in self.seen:
            note('legacy_repeated_snapshot_ignored')
            return None
        self.seen.add(cur)
        previous = self.prev
        self.prev = cur
        if previous is None:
            if last is None:
                note('legacy_opening_snapshot_baselined_without_counting')
                return None
            if cur != last:
                note('legacy_opening_unattributed_history_tokens', max(0, total(cur)-total(last)))
                return last, 'legacy_opening_last', cur
            return last, 'legacy_matching_delta', cur
        delta = tuple(a-b for a, b in zip(cur, previous))
        if any(x < 0 for x in delta) or delta[1] > delta[0] or delta[3] > delta[2]:
            note('legacy_counter_resets_or_inconsistent_deltas')
            return (last, 'legacy_reset_last', cur) if last and total(last) else None
        if last is not None and delta != last:
            note('legacy_delta_last_disagreement')
            note('legacy_unattributed_gap_tokens', max(0, total(delta)-total(last)))
            return last, 'legacy_disagreement_last', cur
        if last is None:
            note('legacy_delta_without_last_corroboration_excluded')
            return None
        return (delta, 'legacy_matching_delta', cur) if total(delta) else None


class Collector:
    def __init__(self, home, start, end, tz, max_bytes=16*1024**3, max_line=8*1024**2,
                 all_files=False, progress=True, max_events=500000):
        self.home, self.start, self.end, self.tz = home, start, end, tz
        self.max_bytes, self.max_line, self.all_files, self.progress = max_bytes, max_line, all_files, progress
        self.max_events = max_events
        self.ids = Ids()
        self.diag = Counter()
        self.sessions = {}
        self.usages = []
        self.calls = {}
        self.turns = {}
        self.events = []
        self.activity = {}
        self.rates = []
        self.private_sources = {}
        self.input_files = []
        self.event_seen = set()
        self.schema = Counter()
        self.bytes_read = 0
        self.partial = False
        self.last_progress = 0.0
        self.process_calls = {}
        self.item_observations = []

    def session(self, sid):
        if sid not in self.sessions:
            self.sessions[sid] = Session(sid)
        return self.sessions[sid]

    def in_window(self, ts):
        return ts is not None and self.start <= ts < self.end

    def discover(self, roots):
        files, inodes = [], set()
        for root in roots:
            if root.is_symlink() or not root.is_dir():
                self.diag['missing_or_symlink_source_roots'] += 1
                continue
            for directory, dirs, names in os.walk(root, followlinks=False):
                dirs[:] = sorted(d for d in dirs if not (Path(directory)/d).is_symlink())
                for name in sorted(names):
                    if not name.endswith('.jsonl'):
                        continue
                    p = Path(directory)/name
                    try:
                        st = p.lstat()
                        if not stat.S_ISREG(st.st_mode):
                            self.diag['special_or_symlink_files_skipped'] += 1
                            continue
                        inode = (st.st_dev, st.st_ino)
                        if inode in inodes:
                            self.diag['same_physical_file_skipped'] += 1
                            continue
                        inodes.add(inode)
                        if not self.all_files and st.st_mtime < self.start.timestamp():
                            self.diag['older_mtime_files_skipped'] += 1
                            continue
                        files.append((p, st))
                    except OSError:
                        self.diag['unreadable_paths'] += 1
        # Prefer newest files if the user-selected scan bound is reached.
        files.sort(key=lambda x: (-x[1].st_mtime, str(x[0])))
        self.diag['candidate_files'] = len(files)
        self.diag['candidate_log_bytes'] = sum(s.st_size for _, s in files)
        return files

    def read_lines(self, path, initial):
        flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
        fd = os.open(path, flags)
        try:
            opened = os.fstat(fd)
            if not stat.S_ISREG(opened.st_mode) or (opened.st_ino, opened.st_dev) != (initial.st_ino, initial.st_dev):
                self.diag['changed_file_identity_skipped'] += 1
                self.partial = True
                return
            remaining, lineno = opened.st_size, 0
            with os.fdopen(fd, 'rb', closefd=False) as f:
                while remaining > 0:
                    available = self.max_bytes-self.bytes_read
                    if available <= 0:
                        self.partial = True
                        self.diag['scan_byte_limit_reached'] = 1
                        return
                    raw = f.readline(min(self.max_line+1, remaining, available))
                    if not raw:
                        break
                    remaining -= len(raw)
                    self.bytes_read += len(raw)
                    lineno += 1
                    if len(raw) > self.max_line or (not raw.endswith(b'\n') and remaining > 0):
                        # Drain an oversized record in bounded chunks, never parse its fragments.
                        self.diag['oversized_or_scan_cut_records_skipped'] += 1
                        self.partial = True
                        while raw and not raw.endswith(b'\n') and remaining > 0:
                            size = min(self.max_line, remaining, self.max_bytes-self.bytes_read)
                            if size <= 0:
                                break
                            raw = f.readline(size)
                            remaining -= len(raw)
                            self.bytes_read += len(raw)
                        continue
                    try:
                        obj = json.loads(raw)
                        if isinstance(obj, dict):
                            yield lineno, obj
                        else:
                            self.diag['non_object_json_records'] += 1
                    except (ValueError, UnicodeError, RecursionError):
                        self.diag['invalid_or_partial_json_records'] += 1
                        self.partial = True
            after = os.fstat(fd)
            if after.st_size != opened.st_size or after.st_mtime_ns != opened.st_mtime_ns:
                self.diag['files_changed_during_read'] += 1
                self.partial = True
        finally:
            os.close(fd)

    def collect(self, roots):
        files = self.discover(roots)
        for index, (path, st) in enumerate(files, 1):
            if self.bytes_read >= self.max_bytes or self.diag['retained_event_limit_reached']:
                self.partial = True
                self.diag['files_not_scanned_due_to_resource_limit'] += len(files)-index+1
                break
            fid = self.ids.get('file', str(path))
            self.private_sources[fid] = str(path)
            self.input_files.append(fid)
            try:
                self.parse_file(path, st, fid)
                self.diag['files_scanned'] += 1
            except OSError:
                self.diag['file_read_errors'] += 1
                self.partial = True
            if self.progress and time.monotonic()-self.last_progress > 2:
                print(f'Analyzed {index}/{len(files)} files; read {self.bytes_read/1024**2:.0f} MiB.', file=sys.stderr)
                self.last_progress = time.monotonic()
        self.link()
        return self

    def metadata(self, p, fallback, fid):
        sid = str(p.get('id') or p.get('thread_id') or fallback)
        s = self.session(sid)
        source = p.get('source')
        sub = mapping(mapping(source).get('subagent'))
        spawned = mapping(sub.get('thread_spawn'))
        parent = p.get('parent_thread_id') or spawned.get('parent_thread_id')
        s.parent = str(parent) if parent else s.parent
        s.fork = str(p['forked_from_id']) if p.get('forked_from_id') else s.fork
        s.family = str(p['session_id']) if p.get('session_id') else s.family
        s.created = stamp(p.get('timestamp')) or s.created
        s.project = p.get('cwd') if isinstance(p.get('cwd'), str) else s.project
        s.kind = ('worker' if s.parent or 'subagent' in mapping(source) or p.get('thread_source')=='subagent' or (isinstance(source, str) and source.startswith('subagent'))
                  else 'internal' if 'internal' in mapping(source)
                  else 'main' if source in ('cli','vscode','exec','mcp') or 'custom' in mapping(source)
                  else s.kind)
        role = p.get('agent_role') or p.get('agent_type') or spawned.get('agent_role') or spawned.get('agent_type')
        if role:
            s.role, s.role_evidence = role if role in EXPECTED else 'other', 'session_metadata'
        if s.kind == 'main':
            s.role = 'main'
        v = label(p.get('cli_version'))
        if v != 'unknown':
            s.cli_versions.add(v)
        s.files.add(fid)
        # Only inspect instruction fields, never user messages or arbitrary transcript mentions.
        for k in ('base_instructions', 'developer_instructions', 'instructions'):
            s.version_markers.update(SMART_RE.findall(stringify(p.get(k))))
        s.boundary_present |= p.get('subagent_history_start_ordinal') is not None or bool(p.get('history_base'))
        return s

    def parse_file(self, path, st, fid):
        s = None
        model, effort, turn_id, project = 'unknown', 'unknown', '', ''
        meter = LegacyCounter(self.diag)
        for line, obj in self.read_lines(path, st):
            if len(self.event_seen) + len(self.usages) >= self.max_events:
                self.diag['retained_event_limit_reached'] = 1
                self.partial = True
                break
            typ = obj.get('type', '')
            p = mapping(obj.get('payload'))
            if not isinstance(typ, str) or ('type' in p and not isinstance(p['type'], str)):
                self.diag['invalid_event_type_records'] += 1
                self.partial = True
                continue
            ts = stamp(obj.get('timestamp'))
            if typ == 'session_meta':
                if s is None:
                    s = self.metadata(p, fid, fid)
                    project = s.project
                elif str(p.get('id') or '') != s.sid:
                    self.diag['nested_or_replayed_session_meta_ignored'] += 1
                continue
            if s is None:
                self.diag['records_before_session_metadata_excluded'] += 1
                continue
            is_child = s.parent is not None or s.fork is not None or s.kind == 'worker'
            owner = p.get('thread_id')
            # Explicit logical ownership takes precedence over the physical file location.
            if owner and str(owner) != s.sid:
                if self.in_window(ts):
                    self.diag['foreign_owner_records_excluded'] += 1
                continue
            if is_child and s.created and ts and ts < s.created:
                if self.in_window(ts):
                    self.diag['precreation_inherited_records_excluded'] += 1
                continue
            if ts and ts >= self.end:
                continue
            if typ == 'response_item' and p.get('type') == 'message' and p.get('role') in ('system', 'developer'):
                s.version_markers.update(SMART_RE.findall(stringify(p.get('content'))))
            if typ == 'turn_context' or (typ == 'event_msg' and p.get('type') == 'thread_settings_applied'):
                ctx = mapping(p.get('thread_settings')) or p
                model = label(ctx.get('model'), model)
                effort = label(ctx.get('effort') or ctx.get('reasoning_effort') or
                               mapping(mapping(ctx.get('collaboration_mode')).get('settings')).get('reasoning_effort'), 'unknown')
                if isinstance(ctx.get('cwd'), str):
                    project = ctx['cwd']
                if ctx.get('turn_id'):
                    turn_id = str(ctx['turn_id'])
                for key in ('developer_instructions', 'user_instructions'):
                    # These are instruction snapshots, not proof of execution or patch-level activation.
                    s.version_markers.update(SMART_RE.findall(stringify(ctx.get(key))))
                if not self.in_window(ts):
                    continue
            event = p.get('type', '') if typ == 'event_msg' else typ
            if self.in_window(ts):
                previous_activity = self.activity.get(s.sid, (ts, ts))
                self.activity[s.sid] = (min(previous_activity[0], ts), max(previous_activity[1], ts))
                self.schema[label(typ)+'/'+label(event)] += 1
            if event == 'token_count':
                info = mapping(p.get('info'))
                result = meter.consume(info, self.in_window(ts))
                if result and self.in_window(ts):
                    v, method, sig = result
                    self.usages.append(dict(sid=s.sid, ts=ts, turn=turn_id, model=model, effort=effort,
                        v=v, method=method, signature=sig, source=fid, line=line, response=None,
                        subset_fields_missing=any(k not in mapping(info.get('last_token_usage')) for k in FIELDS)))
                if self.in_window(ts):
                    self.rate(p.get('rate_limits'), ts)
                continue
            if typ in ('token_usage_record', 'token_usage'):
                if not self.in_window(ts):
                    continue
                v = vector(p.get('usage'))
                response = p.get('response_id')
                if v is None or not response:
                    self.diag['invalid_response_usage_records_excluded'] += 1
                    continue
                self.usages.append(dict(sid=s.sid, ts=ts, turn=str(p.get('turn_id') or turn_id),
                    model=model, effort=effort, v=v, method='response_id', signature=None,
                    source=fid, line=line, response=str(response),
                    subset_fields_missing=any(k not in mapping(p.get('usage')) for k in FIELDS)))
                continue
            # Before-window start events help clip intervals and correlate command completions.
            if ts is None:
                self.diag['untimed_nonusage_records_excluded'] += 1
                continue
            if typ not in ('event_msg','response_item','compacted','turn_context'):
                continue
            if not self.in_window(ts) and event not in ('task_started','turn_started','exec_command_begin'):
                continue
            selected = {k:p.get(k) for k in ('type','call_id','id','turn_id','name','timestamp','response_id')}
            if event in ('item_started', 'item_completed'):
                item = mapping(p.get('item'))
                selected['item_id'] = item.get('id')
                selected['item_type'] = item.get('type')
                # Lifecycle records can share timestamps, including successive
                # output updates. Do not suppress distinct nested items.
                selected['item_hash'] = hashlib.sha256(json.dumps(item, sort_keys=True).encode()).hexdigest()
            if typ == 'response_item':
                selected['content_hash'] = hashlib.sha256(json.dumps(p,sort_keys=True).encode()).hexdigest()
            key = (s.sid, iso(ts), typ, json.dumps(selected,sort_keys=True))
            if key in self.event_seen:
                self.diag['duplicate_nonusage_records_ignored'] += 1
                continue
            self.event_seen.add(key)
            if event in ('item_started', 'item_completed'):
                self.item_record(s.sid, p, ts, event, project, fid, line, turn_id)
                continue
            if event in ('task_started','turn_started'):
                turn_id = str(p.get('turn_id') or self.ids.get('untagged-turn', (fid,line)))
                keyt = (s.sid, turn_id)
                self.turns.setdefault(keyt, dict(sid=s.sid, turn=turn_id, start=stamp(p.get('started_at')) or ts,
                    end=None, status='unfinished', source=fid, line=line))
            elif event in ('task_complete','turn_complete','turn_aborted'):
                tid = str(p.get('turn_id') or turn_id or self.ids.get('untagged-turn', (fid,line)))
                keyt = (s.sid, tid)
                row = self.turns.setdefault(keyt, dict(sid=s.sid, turn=tid, start=stamp(p.get('started_at')),
                    source=fid,line=line))
                row.update(end=stamp(p.get('completed_at')) or ts,
                           status='aborted' if event=='turn_aborted' else 'error' if p.get('error') else 'completed')
                if row.get('start') is None and finite(p.get('duration_ms'), 10**10):
                    row['start'] = row['end']-timedelta(milliseconds=p['duration_ms'])
            elif event in ('error','stream_error','context_compacted','plan_update','shutdown_complete') or typ == 'compacted':
                self.events.append(dict(sid=s.sid,ts=ts,kind=event))
            elif event in ('exec_command_begin','exec_command_end'):
                cid = str(p.get('call_id') or self.ids.get('call',(fid,line)))
                cmd = command_text(p.get('command'))
                row = self.call(s.sid,cid,ts,event,cmd,project,fid,line,turn_id)
                if event=='exec_command_begin':
                    row['started'] = ts
                    row['start_evidence'] = 'start_event'
                else:
                    self.finish(row,ts,p,structured=True)
            elif event in ('patch_apply_begin','patch_apply_end'):
                self.events.append(dict(sid=s.sid,ts=ts,kind='edit_observed'))
            elif event.startswith('collab_'):
                self.events.append(dict(sid=s.sid,ts=ts,kind=event))
                if event == 'collab_agent_spawn_end':
                    child = p.get('new_thread_id') or p.get('receiver_thread_id')
                    if child:
                        cs = self.session(str(child)); cs.parent = s.sid; cs.kind='worker'
                        role = p.get('agent_role') or p.get('agent_type')
                        if role in EXPECTED and cs.role=='unknown':
                            cs.role,cs.role_evidence=role,'spawn_event'
            elif typ=='response_item':
                ptyp = p.get('type')
                if ptyp in ('function_call','custom_tool_call','local_shell_call'):
                    name = str(p.get('name') or ('shell' if ptyp=='local_shell_call' else 'unknown')).split('.')[-1]
                    args = unpack_args(p.get('arguments')) or mapping(p.get('action'))
                    cid = str(p.get('call_id') or p.get('id') or self.ids.get('call',(fid,line)))
                    cmd = command_text(args.get('cmd') or args.get('command'))
                    row = self.call(s.sid,cid,ts,name,cmd,args.get('workdir') or args.get('cwd') or project,fid,line,turn_id)
                    row['tool'] = name if name in RECOGNIZED_TOOLS else 'other'
                    row['start_evidence'] = 'call_record'
                    if name not in RECOGNIZED_TOOLS:
                        row['unknown_tool_id'] = self.ids.get('tool', name)
                    row['requested_role'] = args.get('agent_type') if args.get('agent_type') in EXPECTED else args.get('agent_role') if args.get('agent_role') in EXPECTED else None
                    if name=='write_stdin' and args.get('session_id') is not None:
                        row['process_ref'] = str(args['session_id'])
                    wait = args.get('timeout_ms',args.get('yield_time_ms'))
                    if name in ('wait','wait_agent','write_stdin') and finite(wait):
                        row['requested_wait_ms'] = wait
                    if name=='apply_patch' or (cmd and EDIT_RE.search(cmd)):
                        self.events.append(dict(sid=s.sid,ts=ts,kind='edit_observed'))
                elif ptyp in ('function_call_output','custom_tool_call_output','local_shell_call_output'):
                    cid = str(p.get('call_id') or p.get('id') or '')
                    row = self.calls.get((s.sid,cid))
                    if row:
                        self.finish(row,ts,p.get('output'),structured=False)
                        if row['tool']=='spawn_agent':
                            out=unpack_args(p.get('output'))
                            child=out.get('agent_id') or out.get('thread_id')
                            if child:
                                cs=self.session(str(child));cs.parent=s.sid;cs.kind='worker'
                                if cs.role_evidence!='session_metadata' and row.get('requested_role'):
                                    cs.role,cs.role_evidence=row['requested_role'],'spawn_request'
                                row['child_sid']=str(child)

    def item_record(self, sid, payload, ts, event, project, fid, line, turn):
        """Read persisted TurnItem metadata. Never execute or parse JS as evidence.

        Supports the protocol's PascalCase variants and serialized snake/camel
        aliases. Only typed CommandExecution records prove a nested command ran.
        Code-mode source text is deliberately not treated as execution evidence.
        """
        item = mapping(payload.get('item'))
        kind = re.sub(r'[_-]', '', str(item.get('type', ''))).lower()
        known = {'commandexecution', 'dynamictoolcall', 'mcptoolcall',
                 'collabagenttoolcall', 'subagentactivity', 'filechange',
                 'contextcompaction', 'functioncalloutput', 'plan',
                 'agentmessage', 'usermessage', 'reasoning', 'websearch',
                 'imageview', 'imagegeneration', 'extension', 'hookprompt',
                 'enteredreviewmode', 'exitedreviewmode'}
        self.item_observations.append((ts, kind if kind in known else 'unknown'))
        cid = str(item.get('id') or item.get('call_id') or '')
        tid = str(payload.get('turn_id') or turn)
        if kind == 'commandexecution':
            if not cid:
                self.diag['unkeyed_command_items_excluded'] += 1
                return
            cmd = command_text(item.get('command'))
            cwd = item.get('cwd') if isinstance(item.get('cwd'), str) else project
            status = re.sub(r'[_-]', '', str(item.get('status', ''))).lower()
            source = str(item.get('source', ''))
            if source == 'unified_exec_interaction':
                # An interaction is not a newly launched test process.
                self.diag['command_interaction_items_observed'] += 1
                process = str(item.get('process_id') or '')
                original = self.process_calls.get((sid, process))
                if original and event == 'item_completed':
                    self.finish(original, ts, item, structured=True)
                return
            existing = self.calls.get((sid, cid))
            row = self.call(sid, cid, ts, 'exec_command', cmd, cwd, fid, line, tid)
            row['tool'] = 'exec_command'
            row['structured_command_item'] = True
            if event == 'item_started':
                row['started'], row['start_evidence'] = ts, 'start_event'
            else:
                if existing is None:
                    duration = parse_duration(item.get('duration'))
                    row['started'] = ts - timedelta(seconds=duration) if duration is not None else ts
                    row['start_evidence'] = 'duration_inferred' if duration is not None else 'completion_only'
                self.finish(row, ts, item, structured=True)
            if status == 'inprogress':
                row['ended'] = None
            row['command_status'] = status or 'unknown'
            if item.get('process_id') is not None:
                self.process_calls[(sid, str(item['process_id']))] = row
            if cmd and EDIT_RE.search(cmd):
                self.events.append(dict(sid=sid, ts=ts, kind='edit_observed'))
        elif kind in ('dynamictoolcall', 'mcptoolcall', 'collabagenttoolcall'):
            if not cid:
                self.diag['unkeyed_tool_items_excluded'] += 1
                return
            name = str(item.get('tool') or 'unknown').split('.')[-1]
            existing = self.calls.get((sid, cid))
            row = self.call(sid, cid, ts, name, '', project, fid, line, tid)
            if row['tool'] == 'other' and name in RECOGNIZED_TOOLS:
                row['tool'] = name
            if name not in RECOGNIZED_TOOLS:
                row['unknown_tool_id'] = self.ids.get('tool', name)
            if event == 'item_completed':
                if existing is None:
                    row['start_evidence'] = 'completion_only'
                row['ended'] = ts
                duration = parse_duration(item.get('duration'))
                if duration is not None:
                    row['wall_seconds'] = duration
                    if existing is None:
                        row['started'] = ts - timedelta(seconds=duration)
                        row['start_evidence'] = 'duration_inferred'
                if item.get('success') is not None:
                    row['tool_success'] = item['success'] if type(item['success']) is bool else None
                elif 'status' in item:
                    status = str(item['status']).lower()
                    row['tool_success'] = True if status == 'completed' else False if status == 'failed' else None
            if kind == 'collabagenttoolcall' and name == 'spawn_agent':
                receivers = item.get('receiver_thread_ids')
                if isinstance(receivers, list) and len(receivers) == 1 and isinstance(receivers[0], str):
                    child = receivers[0]
                    cs = self.session(child)
                    cs.parent, cs.kind = sid, 'worker'
                    row['child_sid'] = child
        elif kind == 'functioncalloutput' and cid:
            row = self.calls.get((sid, cid))
            if row:
                self.finish(row, ts, item.get('output'), structured=False)
        elif kind in ('filechange', 'subagentactivity', 'contextcompaction', 'plan'):
            # Keep these explicitly named. Do not sum them with raw counterparts
            # as independent occurrences when duplication cannot be resolved.
            self.events.append(dict(sid=sid, ts=ts, kind='item_' + kind))

    def call(self,sid,cid,ts,name,cmd,project,fid,line,turn):
        key=(sid,cid)
        if key not in self.calls:
            self.calls[key]=dict(sid=sid,cid=cid,started=ts,ended=None,tool=name if name in RECOGNIZED_TOOLS else 'exec_command' if name.startswith('exec_command') else 'other',
                command_key=self.ids.get('cmd',str(project)+'\0'+cmd) if cmd else None,
                start_evidence='call_record',
                project_key=self.ids.get('project',project) if project else 'unknown',
                is_test=is_test_command(cmd),exit_code=None,wall_seconds=None,
                source=fid,line=line,turn=turn,output_bytes=0)
        row=self.calls[key]
        if cmd:
            row['is_test'] |= is_test_command(cmd)
            row['command_key']=self.ids.get('cmd',str(project)+'\0'+cmd)
        return row

    def finish(self,row,ts,value,structured):
        obj=mapping(value)
        text=stringify(value)
        if not text and isinstance(value,dict):
            text=stringify(value.get('aggregated_output') or value.get('stdout') or value.get('output'))
        row['output_bytes']=max(row['output_bytes'],len(text.encode('utf-8')))
        markers=[int(v) for v in re.findall(r'(?m)^\s*exit_status=(-?\d{1,6})\s*$',text)]
        row['embedded_exit_markers']=sorted(set(row.get('embedded_exit_markers',[]))|set(markers))
        code=obj.get('exit_code',mapping(obj.get('metadata')).get('exit_code'))
        if type(code) is not int:
            m=re.search(r'(?:Process exited with code|Exit code:)\s*(-?\d+)',text)
            code=int(m[1]) if m else None
        wall=parse_duration(obj.get('duration'))
        if wall is None:
            m=re.search(r'Wall time:\s*([\d.]+)\s*seconds',text)
            wall=float(m[1]) if m else None
        if wall is not None and (structured or row['wall_seconds'] is None):
            row['wall_seconds']=wall
        row['ended']=ts
        if type(code) is int:
            row['exit_code']=code
        running=re.search(r'Process running with session ID\s+(\S+)',text)
        if running:
            pid=running[1]
            self.process_calls[(row['sid'],pid)]=row
            row['process_ref']=pid
            row['ended']=None
        if row.get('process_ref') and row['tool']=='write_stdin':
            original=self.process_calls.get((row['sid'],row['process_ref']))
            if original and code is not None:
                original['ended']=ts
                original['exit_code']=code
                original['output_bytes']+=row['output_bytes']
                original['embedded_exit_markers']=sorted(set(original.get('embedded_exit_markers',[]))|set(row.get('embedded_exit_markers',[])))
        # No raw command, message, arguments, response or stdout retained.

    def rate(self,value,ts):
        snap=mapping(value)
        for name in ('primary','secondary'):
            w=mapping(snap.get(name))
            if not finite(w.get('used_percent'),100):
                continue
            self.rates.append(dict(ts=ts,limit=self.ids.get('limit',snap.get('limit_id') or 'unspecified'),
                window=name,minutes=w.get('window_minutes') if finite(w.get('window_minutes')) else None,
                reset=iso(stamp(w.get('resets_at'))),used_percent=float(w['used_percent'])))

    @lru_cache(maxsize=None)
    def root(self,sid):
        current,seen=sid,set()
        while current in self.sessions and current not in seen:
            seen.add(current);s=self.sessions[current]
            if not s.parent:
                return current
            current=s.parent
        if current in seen:
            self.diag['lineage_cycle_detected'] += 1
            return sid
        return current  # An absent parent is still a shared lineage identity.

    def link(self):
        # Physical replay timestamps can be newer than a child. Use logical
        # payload intervals and ancestor turn identity, not file location alone.
        original_turns=dict(self.turns)
        for key,t in original_turns.items():
            session=self.sessions[t['sid']]
            if not (session.parent or session.fork or session.kind=='worker'):
                continue
            reason=None
            start=t.get('start')
            if start is not None and session.created is not None and start < session.created.replace(microsecond=0):
                reason='copied_precreation_payload_turns_excluded'
            current=session.parent or session.fork
            seen={session.sid}
            while current and current not in seen:
                seen.add(current)
                if (current,t['turn']) in original_turns:
                    reason='copied_ancestor_turn_ids_excluded'; break
                parent=self.sessions.get(current)
                current=(parent.parent or parent.fork) if parent else None
            if reason:
                del self.turns[key]; self.diag[reason]+=1
            elif start is None or session.created is None:
                t['worker_interval_attribution_unknown']=True
                self.diag['worker_turns_without_birth_or_start_evidence']+=1
        # No inference about native open residency or continuous model compute.
        # Use response records per turn whenever present; never add them to legacy counters.
        authoritative={(u['sid'],u['turn']) for u in self.usages if u['method']=='response_id'}
        auth_sessions={sid for sid,_ in authoritative}
        seen=set(); chosen=[]
        for u in sorted(self.usages,key=lambda u:(u['ts'],u['sid'],u['line'])):
            if u['method']!='response_id' and ((u['sid'],u['turn']) in authoritative or (not u['turn'] and u['sid'] in auth_sessions)):
                self.diag['legacy_rows_superseded_by_response_records']+=1
                continue
            key=('response',u['response']) if u['response'] else ('legacy',u['sid'],u['ts'],u['signature'])
            if key in seen:
                self.diag['duplicate_usage_records_ignored']+=1
                continue
            seen.add(key);chosen.append(u)
        self.usages=chosen
        self.parents_with_smart_roles = {s.parent for s in self.sessions.values() if s.role in EXPECTED and s.parent}

    @lru_cache(maxsize=None)
    def association(self,sid):
        s=self.sessions[sid]
        root=self.sessions.get(self.root(sid),s)
        markers=s.version_markers|root.version_markers
        if markers:
            exact={v for v in markers if re.fullmatch(r'\d+\.\d+\.\d+',v)}
            series={'.'.join(v.split('.')[:2]) for v in markers}
            if len(exact)>1 or len(series)>1:
                return 'mixed_smart_instruction_versions'
            if exact:
                return 'instruction_marker_'+next(iter(exact))
            return 'instruction_marker_'+next(iter(series))+'_series_patch_unproven'
        if s.role in EXPECTED:
            return 'smart_named_role_only'
        if sid in self.parents_with_smart_roles:
            return 'parent_of_smart_named_role'
        return 'not_identified'

    def snapshot(self):
        result={'current_installed_version':None,'configured_worker_cap':None,
                'configured_main_model':None,'configured_main_effort':None,
                'current_role_settings':{},'note':'Read at audit time; not historical activation evidence.'}
        def read_small(p):
            if p.is_symlink() or not p.is_file() or p.stat().st_size>2*1024**2:
                return None
            with p.open('rb') as f:
                return f.read(2*1024**2+1)
        try:
            data=read_small(self.home/'codex_workflow/operate/VERSION')
            if data:
                value=data.decode().strip()
                if re.fullmatch(r'\d+\.\d+\.\d+',value):result['current_installed_version']=value
            data=read_small(self.home/'config.toml')
            if data:
                cfg=tomllib.loads(data.decode())
                result['configured_main_model']=label(cfg.get('model'))
                result['configured_main_effort']=label(cfg.get('model_reasoning_effort'))
                agents=mapping(cfg.get('agents'))
                cap=agents.get('max_concurrent_threads_per_session',agents.get('max_threads'))
                result['configured_worker_cap']=cap if type(cap) is int and 0<cap<10000 else None
            for role in EXPECTED:
                data=read_small(self.home/'agents'/f'{role}.toml')
                if data:
                    cfg=tomllib.loads(data.decode())
                    result['current_role_settings'][role]={'model':label(cfg.get('model')),
                        'effort':label(cfg.get('model_reasoning_effort'))}
        except (OSError,ValueError,UnicodeError):
            self.diag['current_config_snapshot_incomplete']+=1
        return result

    def report(self,start,end,prices=None):
        usage=[u for u in self.usages if start<=u['ts']<end]
        calls=[c for c in self.calls.values() if start<=c['started']<end]
        turns=[t for t in self.turns.values() if (t.get('end') and start<=t['end']<end)
               or (t.get('start') and start<=t['start']<end)
               or (t.get('start') and t.get('end') and t['start']<start and t['end']>=end)]
        events=[e for e in self.events if start<=e['ts']<end]
        sids={sid for sid,(a,b) in self.activity.items() if b>=start and a<end}
        sids |= {u['sid'] for u in usage}|{c['sid'] for c in calls}|{t['sid'] for t in turns}|{e['sid'] for e in events}
        sums=ZERO;by_model=defaultdict(lambda:ZERO);by_day=defaultdict(lambda:ZERO)
        by_role_model=defaultdict(lambda:ZERO)
        by_role=defaultdict(lambda:ZERO);by_association=defaultdict(lambda:ZERO);by_session=defaultdict(lambda:ZERO)
        methods=Counter();matches=Counter();cost=0.0;priced=0;cost_rows=Counter()
        for u in usage:
            sums=add(sums,u['v']);s=self.sessions[u['sid']]
            by_model[(u['model'],u['effort'])]=add(by_model[(u['model'],u['effort'])],u['v'])
            day=u['ts'].astimezone(self.tz).date().isoformat()
            by_day[day]=add(by_day[day],u['v'])
            role=s.role if s.role in EXPECTED or s.role=='main' else s.kind+':unknown_role'
            by_role[role]=add(by_role[role],u['v'])
            by_role_model[(role,u['model'],u['effort'])]=add(by_role_model[(role,u['model'],u['effort'])],u['v'])
            by_session[s.sid]=add(by_session[s.sid],u['v'])
            assoc=self.association(s.sid);by_association[assoc]=add(by_association[assoc],u['v'])
            methods[u['method']]+=1
            if s.role in EXPECTED:
                if u['model']=='unknown' or u['effort']=='unknown':
                    matches['unknown_model_or_effort_updates']+=1
                else:
                    expected=EXPECTED[s.role]
                    match=(u['model'],u['effort'])==expected
                    matches['matching_usage_updates' if match else 'mismatching_usage_updates']+=1
                    matches['matching_tokens' if match else 'mismatching_tokens']+=total(u['v'])
            if prices and u['model'] in prices['models']:
                p=prices['models'][u['model']]
                amount=((u['v'][0]-u['v'][1])*p['input']+u['v'][1]*p['cached_input']+u['v'][2]*p['output'])/1e6
                cost+=amount;priced+=total(u['v']);cost_rows[u['model']]+=amount
        tool_counts=Counter(c['tool'] for c in calls)
        tests=sorted((c for c in calls if c['is_test']),key=lambda c:c['started'])
        repeats=[];previous={};test_roles=Counter();test_exit=Counter()
        for c in tests:
            s=self.sessions[c['sid']];test_roles[s.role if s.role in EXPECTED or s.role=='main' else 'unknown']+=1
            test_exit['exit_zero' if c['exit_code']==0 else 'nonzero' if c['exit_code'] is not None else 'unknown_or_unfinished']+=1
            old=previous.get(c['command_key'])
            if old and (c['started']-old['started']).total_seconds()<=1800 and c.get('start_evidence')!='completion_only' and old.get('start_evidence')!='completion_only':
                repeats.append({'command_id':c['command_key'],'previous_session':self.ids.get('session',old['sid']),
                    'session':self.ids.get('session',c['sid']),'gap_seconds':(c['started']-old['started']).total_seconds(),
                    'previous_exit_code':old['exit_code'],'exit_code':c['exit_code'],
                    'previous_source':old['source'],'previous_line':old['line'],
                    'same_candidate_established':False,
                    'overlap_observed':bool(old['ended'] and old['ended']>c['started']),
                    'source':c['source'],'line':c['line'],'label':'Repeated command candidate; redundancy NOT established.'})
            previous[c['command_key']]=c
        durations=[];intervals=[];statuses=Counter();root_intervals=defaultdict(list)
        worker_intervals=defaultdict(list)
        for t in turns:
            statuses[t['status']]+=1
            a,b=t.get('start'),t.get('end')
            if a and b and b>=a:
                clipped_a,clipped_b=max(a,start),min(b,end)
                if clipped_b>clipped_a:
                    durations.append((b-a).total_seconds());intervals.append((clipped_a,clipped_b))
                    if self.sessions[t['sid']].kind=='worker' and not t.get('worker_interval_attribution_unknown',False):
                        root_intervals[self.root(t['sid'])].append((clipped_a,clipped_b))
                        worker_intervals[t['sid']].append((clipped_a,clipped_b))
        def peak(items):
            points=sorted([(a,1) for a,b in items]+[(b,-1) for a,b in items])
            now=best=0
            for _,delta in points:now+=delta;best=max(best,now)
            return best
        def union_seconds(items):
            duration=0.0;left=right=None
            for a,b in sorted(items):
                if right is None:left,right=a,b
                elif a>right:duration+=(right-left).total_seconds();left,right=a,b
                else:right=max(right,b)
            return duration+((right-left).total_seconds() if right else 0)
        def merge_intervals(items):
            merged=[]
            for left,right in sorted(items):
                if merged and left <= merged[-1][1]:
                    merged[-1]=(merged[-1][0], max(right, merged[-1][1]))
                else:
                    merged.append((left,right))
            return merged
        distinct_root_intervals=defaultdict(list)
        for sid, items in worker_intervals.items():
            distinct_root_intervals[self.root(sid)].extend(merge_intervals(items))
        legacy_sessions={u['sid'] for u in usage if u['method']!='response_id'}
        usage_counts=Counter(u['sid'] for u in usage)
        tool_by_sid=defaultdict(Counter)
        for call in calls:
            tool_by_sid[call['sid']][call['tool']]+=1
        sessions=[]
        for sid in sorted(sids,key=lambda sid:total(by_session[sid]),reverse=True):
            s=self.sessions[sid]
            sessions.append({'session_id':self.ids.get('session',sid),'parent_id':self.ids.get('session',s.parent) if s.parent else None,
                'root_id':self.ids.get('session',self.root(sid)),'kind':s.kind,'role':s.role,'role_evidence':s.role_evidence,
                'project_id':self.ids.get('project',s.project) if s.project else 'unknown',
                'workflow_association':self.association(sid),'tokens':payload_tokens(by_session[sid]),
                'source_ids':sorted(s.files),'cli_versions':sorted(s.cli_versions),
                'fork_history_boundary_metadata_present':s.boundary_present,
                'usage_updates':usage_counts[sid], 'tools':dict(tool_by_sid[sid]),
                'legacy_fork_attribution_caution':bool((s.parent or s.fork or s.kind=='worker') and sid in legacy_sessions)})
        root_members=defaultdict(set)
        for sid in sids:root_members[self.root(sid)].add(sid)
        roots=set(root_members)
        root_rows=[]
        for root,members in root_members.items():
            v=ZERO
            for sid in members:v=add(v,by_session[sid])
            root_rows.append({'root_id':self.ids.get('session',root),'tokens':payload_tokens(v),
                'observed_worker_sessions':sum(self.sessions[x].kind=='worker' for x in members),
                'tester_sessions':sum(self.sessions[x].role=='tester' for x in members),
                'reviewer_sessions':sum(self.sessions[x].role in ('reviewer','senior_reviewer') for x in members),
                'peak_closed_worker_turn_overlap':peak(root_intervals[root]),
                'peak_distinct_workers_with_closed_turn_overlap':peak(distinct_root_intervals[root])})
        root_rows.sort(key=lambda r:r['tokens']['total_tokens'],reverse=True)
        known_matches=matches['matching_usage_updates']+matches['mismatching_usage_updates']
        rate_groups=defaultdict(list)
        for r in self.rates:
            if start<=r['ts']<end:rate_groups[(r['limit'],r['window'],r['minutes'],r['reset'])].append(r)
        rate_rows=[]
        for key,rs in rate_groups.items():
            rs=sorted(rs,key=lambda r:r['ts']);lo,hi=rs[0],rs[-1]
            rate_rows.append(dict(limit_id=key[0],window=key[1],window_minutes=key[2],resets_at=key[3],
                first_at=iso(lo['ts']),last_at=iso(hi['ts']),first_used_percent=lo['used_percent'],
                last_used_percent=hi['used_percent'],max_used_percent=max(x['used_percent'] for x in rs),
                observed_net_change_percentage_points=round(hi['used_percent']-lo['used_percent'],4)))
        return {'window':{'start_inclusive':iso(start),'end_exclusive':iso(end),'timezone':str(self.tz)},
            'sessions_observed':len(sids),'root_groups_observed':len(roots),
            'worker_sessions':sum(self.sessions[s].kind=='worker' for s in sids),
            'session_counts_by_role':dict(Counter(self.sessions[s].role for s in sids)),
            'sessions_with_usage':len({u['sid'] for u in usage}),
            'sessions_without_usage':len(sids-{u['sid'] for u in usage}),
            'observed_token_usage':payload_tokens(sums),'usage_method_updates':dict(methods),
            'subset_fields_missing_updates':sum(u['subset_fields_missing'] for u in usage),
            'cache_read_share_of_input':round(sums[1]/sums[0],5) if sums[0] else None,
            'reasoning_share_of_output':round(sums[3]/sums[2],5) if sums[2] else None,
            'recorded_item_types':dict(Counter(k for ts,k in self.item_observations if start<=ts<end)),
            'unknown_tool_ids':dict(Counter(c.get('unknown_tool_id','unidentified') for c in calls if c['tool']=='other')),
            'models':[dict(model=k[0],effort=k[1],**payload_tokens(v)) for k,v in sorted(by_model.items(),key=lambda x:total(x[1]),reverse=True)],
            'roles':[dict(role=k,**payload_tokens(v)) for k,v in sorted(by_role.items(),key=lambda x:total(x[1]),reverse=True)],
            'daily':[dict(date=k,**payload_tokens(v)) for k,v in sorted(by_day.items())],
            'role_models':[dict(role=k[0],model=k[1],effort=k[2],**payload_tokens(v)) for k,v in sorted(by_role_model.items(),key=lambda x:total(x[1]),reverse=True)],
            'workflow_cohorts':[dict(association=k,**payload_tokens(v)) for k,v in by_association.items()],
            'routing':dict(matches,match_rate_known_updates=round(matches['matching_usage_updates']/known_matches,5) if known_matches else None,
                denominator='Usage updates with named Smart role and both historical model and effort. Does not score task suitability.'),
            'tools':dict(tool_counts),'runtime_events':dict(Counter(e['kind'] for e in events)),
            'short_wait_requests_at_most_1s':sum(c.get('requested_wait_ms',float('inf'))<=1000 for c in calls),
            'tool_output_bytes_observed':sum(c['output_bytes'] for c in calls),
            'turns':{'statuses':dict(statuses),'closed_intervals_with_duration':len(durations),
                'median_elapsed_seconds':round(statistics.median(durations),3) if durations else None,
                'p90_elapsed_seconds':percentile(durations,.9),
                'observed_closed_turn_union_seconds':union_seconds(intervals),
                'peak_closed_worker_turn_overlap_per_root':max((peak(v) for v in root_intervals.values()),default=0),
                'peak_distinct_workers_with_closed_turn_overlap_per_root':max((peak(v) for v in distinct_root_intervals.values()),default=0),
                'workers_with_overlapping_own_turn_records':sum(peak(v)>1 for v in worker_intervals.values()),
                'negative_turn_intervals_excluded':sum(bool(t.get('start') and t.get('end') and t['end']<t['start']) for t in turns),
                'concurrency_note':'Ancestor turn IDs and precreation payload intervals are excluded; birth/start-unknown worker intervals are excluded. Remaining logical turn overlap is NOT continuous model compute or native open occupancy.',
                'open_thread_policy_compliance':'UNRESOLVED_without_native_lifecycle_receipts'},
            'tests':{'recognized_test_command_starts':sum(c.get('start_evidence')!='completion_only' for c in tests),
                'recognized_test_command_runs':len(tests),
                'start_evidence':dict(Counter(c.get('start_evidence','unknown') for c in tests)),
                'structured_command_runs':sum(c.get('structured_command_item',False) for c in tests),
                'exits':dict(test_exit),'by_role':dict(test_roles),
                'recorded_tool_wall_seconds':round(sum(c['wall_seconds'] or 0 for c in tests),3),
                'runs_with_recorded_tool_walltime':sum(c['wall_seconds'] is not None for c in tests),
                'timing_note':'Per-tool wall-time may be partial for asynchronous runs. Completion-only records have unknown start times and are bucketed by observation time. Not additive task elapsed or CPU time.',
                'repeated_command_candidates':len(repeats),'examples':repeats[:100],
                'examples_exported':min(100,len(repeats)),
                'example_selection':'Earliest candidates, maximum 100; not random or a waste sample',
                'exits_are':'Native wrapper/process exits, NOT test verdicts',
                'outcome_evidence':dict(Counter(
                    'wrapper_zero_conflicts_with_embedded_nonzero' if c['exit_code']==0 and any(v!=0 for v in c.get('embedded_exit_markers',[])) else
                    'process_zero_test_verdict_unverified' if c['exit_code']==0 else
                    'nonzero_process_exit' if c['exit_code'] is not None else 'unverified' for c in tests))},
            'api_equivalent_estimate':({'currency':prices['currency'],'as_of':prices['as_of'],
                'amount_for_priced_tokens':round(cost,6),'priced_tokens':priced,'unpriced_tokens':total(sums)-priced,
                'models':{k:round(v,6) for k,v in cost_rows.items()},'not_subscription_cost':True} if prices else None),
            'rate_limit_observations':sorted(rate_rows,key=lambda r:r['last_at']),
            'quality':{'accepted_tasks':None,'first_pass_acceptance':None,'defect_escape_rate':None,
                       'causal_savings_percent':None,'reason':'Requires independent outcome labels and a comparable baseline.'},
            'sessions':sessions,'root_groups':root_rows}


def write_private(path,data):
    flags=os.O_CREAT|os.O_EXCL|os.O_WRONLY|getattr(os,'O_NOFOLLOW',0)
    fd=os.open(path,flags,0o600)
    with os.fdopen(fd,'w',encoding='utf-8') as f:f.write(data)


def pretty(n):
    return f'{n:,}' if isinstance(n,int) else 'unavailable' if n is None else str(n)


def markdown(report):
    r=report['current']; d=report['diagnostics']; tok=r['observed_token_usage']
    lines=['# Smart Orchestration: local weekly audit','',
        f"Period: **{r['window']['start_inclusive']} to {r['window']['end_exclusive']}** (end excluded). Daily buckets: {r['window']['timezone']}.",'',
        '**Coverage: PARTIAL or potentially incomplete. Inspect diagnostics before drawing conclusions.**' if report['partial_scan'] else '**Scan completed within its bounds. Missing remote/deleted/unlogged activity remains outside this audit.**','',
        '## What the records show','',
        '| Metric | Observed value |','|---|---:|',
        f"| Sessions with in-window activity | {r['sessions_observed']} |",
        f"| Main/root groups | {r['root_groups_observed']} |",
        f"| Worker sessions | {r['worker_sessions']} |",
        f"| Sessions with no usable usage evidence | {r['sessions_without_usage']} |",
        f"| Input tokens, including cache reads | {pretty(tok['input_tokens'])} |",
        f"| Cached input subset | {pretty(tok['cached_input_tokens'])} |",
        f"| Output tokens, including reasoning | {pretty(tok['output_tokens'])} |",
        f"| Reasoning output subset | {pretty(tok['reasoning_output_tokens'])} |",
        f"| Observed input + output | {pretty(tok['total_tokens'])} |",
        f"| Recognized test command runs | {r['tests'].get('recognized_test_command_runs',r['tests']['recognized_test_command_starts'])} |",
        f"| Runs with observed or duration-inferred starts | {r['tests']['recognized_test_command_starts']} |",
        f"| Repeated test-command candidates | {r['tests']['repeated_command_candidates']} |",
        f"| Median closed-turn elapsed seconds | {pretty(r['turns']['median_elapsed_seconds'])} |",
        f"| Peak overlapping closed worker turns in one root (raw intervals) | {r['turns']['peak_closed_worker_turn_overlap_per_root']} |",
        f"| Peak distinct workers with overlapping closed turns | {r['turns'].get('peak_distinct_workers_with_closed_turn_overlap_per_root', 'unavailable')} |",'',
        'Copied ancestor turns and precreation logical intervals are excluded. Distinct-worker intervals are then merged. Neither metric measures continuous compute or verifies native open-thread policy; missing or unattributed intervals remain a coverage gap.','',
        '## Is Smart actually associated with this activity?','',
        '| Evidence category | Tokens |','|---|---:|']
    for c in r['workflow_cohorts']:lines.append(f"| {c['association']} | {pretty(c['total_tokens'])} |")
    lines += ['', 'The 4.0 bootstrap does not always contain its patch number. No association row proves that every instruction was followed. Current disk configuration is reported separately.','',
        '## Historical model and effort','', '| Model | Effort | Input | Cached subset | Output | Reasoning subset |','|---|---|---:|---:|---:|---:|']
    for m in r['models']:lines.append(f"| {m['model']} | {m['effort']} | {pretty(m['input_tokens'])} | {pretty(m['cached_input_tokens'])} | {pretty(m['output_tokens'])} | {pretty(m['reasoning_output_tokens'])} |")
    lines += ['', '## Work by role','', '| Role | Sessions | Input + output tokens | Uncached input | Output |','|---|---:|---:|---:|---:|']
    for x in r['roles']:lines.append(f"| {x['role']} | {r.get('session_counts_by_role',{}).get(x['role'],'unknown')} | {pretty(x['total_tokens'])} | {pretty(x['input_tokens']-x['cached_input_tokens'])} | {pretty(x['output_tokens'])} |")
    match=r['routing'].get('match_rate_known_updates')
    lines += ['',f"Named-role routing conformance among known model/effort updates: **{match*100:.1f}%**." if match is not None else 'Named-role routing conformance: **unavailable**.',
        'This checks the 4.0.1 preset map, not whether the task deserved that model. Unknown fields and owner-selected Main are not counted as mismatches.','',
        '## Testing and orchestration overhead','',
        f"Test-command outcomes: `{json.dumps(r['tests']['exits'],sort_keys=True)}`.",
        f"Test-command runs by role: `{json.dumps(r['tests']['by_role'],sort_keys=True)}`.",
        f"Test start-time evidence: `{json.dumps(r['tests'].get('start_evidence',{}),sort_keys=True)}`.",
        f"Structured item types: `{json.dumps(r.get('recorded_item_types',{}),sort_keys=True)}`.",
        f"Tool calls: `{json.dumps(r['tools'],sort_keys=True)}`.",
        f"Runtime events: `{json.dumps(r['runtime_events'],sort_keys=True)}`.",
        f"Short requested waits (at most one second): {r['short_wait_requests_at_most_1s']}.",
        f"Recorded tool wall-time on test commands: {r['tests']['recorded_tool_wall_seconds']:.1f} seconds across {r['tests']['runs_with_recorded_tool_walltime']} runs with timing evidence.",'',
        'An expected failing regression test is not a bad result. Repeated commands can be justified by source changes, validation gates or flakiness investigation. Asynchronous command timing may cover only the initial tool call. See JSON examples for local inspection.','',
        '## Daily usage','', '| Date | Input + output tokens |','|---|---:|']
    for x in r['daily']:lines.append(f"| {x['date']} | {pretty(x['total_tokens'])} |")
    lines += ['', '## Cost and quota','']
    if r['api_equivalent_estimate']:
        c=r['api_equivalent_estimate'];lines.append(f"User-supplied {c['as_of']} rates yield **{c['amount_for_priced_tokens']:.6f} {c['currency']}** for priced tokens only; {c['unpriced_tokens']:,} tokens remain unpriced. This is an API-equivalent estimate, NOT the subscription bill or quota cost.")
    else:lines.append('No monetary estimate: no price file supplied. Token traffic is not subscription allowance, and no prices are guessed.')
    lines.append(f"Observed rate-limit windows: {len(r['rate_limit_observations'])}. Each JSON row keeps the same limit/reset identity; percentages from different windows are never added. Changes may include activity outside these local logs.")
    if report.get('previous'):
        p=report['previous'];lines += ['', '## Previous equal-length window: descriptive comparison only','',
            '| Metric | Previous | Current |','|---|---:|---:|',
            f"| Observed tokens | {p['observed_token_usage']['total_tokens']:,} | {tok['total_tokens']:,} |",
            f"| Sessions | {p['sessions_observed']} | {r['sessions_observed']} |",
            f"| Worker sessions | {p['worker_sessions']} | {r['worker_sessions']} |",
            f"| Recognized test starts | {p['tests']['recognized_test_command_starts']} | {r['tests']['recognized_test_command_starts']} |",'',
            'Different tasks and logging coverage make this unsuitable for a causal savings claim. Compare independently accepted, similar tasks before changing the routing.']
    lines += ['', '## What still needs a human check','',
        'No overall quality score is invented. Review the sample in quality-review-template.json: was the result accepted, correct on the first pass, properly verified, and free of later-discovered regressions? Use local-index.PRIVATE.json to locate source sessions. It contains local paths; do not share it.',
        '', '## Collection diagnostics','', '```json',json.dumps(d,indent=2,sort_keys=True),'```','',
        'Usage methods: `'+json.dumps(r['usage_method_updates'],sort_keys=True)+'`.','',
        '## Current configuration (not historical evidence)','', '```json',json.dumps(report['current_configuration'],indent=2,sort_keys=True),'```','',
        '## Interpretation limits','']
    lines += [f'- {s}' for s in LIMITATIONS]
    lines += ['',f"Collector {VERSION}. Source-schema reference: `{SCHEMA_REFERENCE}`.",f"Smart preset/evaluation reference: `{SMART_REFERENCE}`.",'']
    return '\n'.join(lines)


def prices_file(path):
    if not path:return None
    if path.stat().st_size>1000000:raise ValueError('Price file too large.')
    p=json.loads(path.read_text())
    if not isinstance(p,dict) or not isinstance(p.get('models'),dict):raise ValueError('Price file requires a models object.')
    for model,rates in p['models'].items():
        if label(model)=='unknown' or not isinstance(rates,dict):raise ValueError('Invalid price model key.')
        if not all(finite(rates.get(k)) for k in ('input','cached_input','output')):raise ValueError('Prices must be finite nonnegative numbers per million tokens.')
    if not isinstance(p.get('as_of'),str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',p['as_of']):raise ValueError('Price as_of must be YYYY-MM-DD.')
    if not isinstance(p.get('currency'),str) or not re.fullmatch(r'[A-Z]{3}',p['currency']):raise ValueError('Use a three-letter currency code.')
    return p


def cli_time(value,tz):
    try:
        d=datetime.fromisoformat(value.replace('Z','+00:00'))
        return (d.replace(tzinfo=tz) if d.tzinfo is None else d).astimezone(UTC)
    except ValueError as e:raise argparse.ArgumentTypeError('Use YYYY-MM-DD or ISO date/time.') from e


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--days',type=int,default=7,help='Rolling lookback from --until / current time (default 7).')
    parser.add_argument('--since',help='Explicit inclusive local date or ISO timestamp, overrides --days.')
    parser.add_argument('--until',help='Explicit exclusive local date or ISO timestamp (default now).')
    parser.add_argument('--timezone',default='Asia/Tbilisi',help='Daily buckets and dates without offsets.')
    parser.add_argument('--codex-home',type=Path,default=Path(os.environ.get('CODEX_HOME','~/.codex')).expanduser())
    parser.add_argument('--sessions-dir',type=Path,action='append',help='Additional explicit rollout directories; repeatable.')
    parser.add_argument('--out',type=Path,help='NEW output directory; defaults to Desktop/Smart-stats-<timestamp>.')
    parser.add_argument('--compare-previous',action='store_true',help='Also summarize the preceding equal-length window; not a causal comparison.')
    parser.add_argument('--all-files',action='store_true',help='Do not prune by file modification time, useful for restored logs.')
    parser.add_argument('--max-scan-gib',type=float,default=16,help='Read bound across logs; partial results are flagged (default 16 GiB).')
    parser.add_argument('--max-events',type=int,default=500000,help='Retained-event bound for memory usage; partial results flagged (default 500000).')
    parser.add_argument('--max-line-mib',type=int,default=8,help='Largest individual JSONL record parsed (default 8 MiB); increase if oversized records were skipped.')
    parser.add_argument('--prices',type=Path,help='Optional user-supplied per-million token prices; never fetched online.')
    parser.add_argument('--quiet',action='store_true')
    args=parser.parse_args(argv)
    try:
        if not 1<=args.days<=366:raise ValueError('--days must be 1 to 366.')
        if not 1<=args.max_line_mib<=256:raise ValueError('--max-line-mib must be between 1 and 256.')
        if not 1<=args.max_events<=10000000:raise ValueError('--max-events must be 1 to 10000000.')
        if not finite(args.max_scan_gib,1024) or args.max_scan_gib<=0:raise ValueError('--max-scan-gib must be positive and at most 1024.')
        tz=ZoneInfo(args.timezone)
        end=cli_time(args.until,tz) if args.until else datetime.now(UTC)
        start=cli_time(args.since,tz) if args.since else end-timedelta(days=args.days)
        if start>=end or end-start>timedelta(days=366):raise ValueError('Window must be positive and at most 366 days.')
        scan_start=start-(end-start) if args.compare_previous else start
        home=args.codex_home.expanduser().resolve()
        desktop=Path.home()/'Desktop'
        base=desktop if desktop.is_dir() else Path.cwd()
        out=(args.out.expanduser() if args.out else base/f'Smart-stats-{datetime.now(tz):%Y%m%d-%H%M%S}').resolve()
        roots=[home/'sessions',home/'archived_sessions']+[x.expanduser().resolve() for x in (args.sessions_dir or [])]
        if out==home or home in out.parents or any(out==r or r in out.parents for r in roots):
            raise ValueError('Output must be outside Codex and source log directories.')
        if out.exists():raise ValueError('Output directory already exists. Choose a new --out directory; nothing was overwritten.')
        prices=prices_file(args.prices)
        c=Collector(home,scan_start,end,tz,max_bytes=int(args.max_scan_gib*1024**3),max_line=args.max_line_mib*1024**2,all_files=args.all_files,progress=not args.quiet,max_events=args.max_events)
        c.collect(roots)
        current=c.report(start,end,prices)
        snapshot=c.snapshot()
        report={'collector_version':VERSION,'generated_at':iso(datetime.now(UTC)),
            'schema_reference':SCHEMA_REFERENCE,'smart_reference':SMART_REFERENCE,
            'partial_scan':c.partial,'current':current,
            'previous':c.report(scan_start,start,prices) if args.compare_previous else None,
            'diagnostics':dict(c.diag,bytes_read=c.bytes_read,max_scan_bytes=c.max_bytes,
                mtime_prefilter_enabled=not args.all_files,max_retained_events=args.max_events,max_line_bytes=c.max_line),
            'current_configuration':snapshot,'limitations':LIMITATIONS,
            'schema_counts':dict(c.schema)}
        out.mkdir(mode=0o700,parents=False)
        write_private(out/'report.json',json.dumps(report,indent=2,sort_keys=True)+'\n')
        write_private(out/'report.md',markdown(report))
        index={'warning':'PRIVATE: local paths and native session identifiers. Do not include in a shared report.',
            'files':c.private_sources,'sessions':{c.ids.get('session',sid):{'native_thread_id':sid,
            'source_files':[c.private_sources[fid] for fid in sorted(s.files)],'working_directory':s.project}
            for sid,s in c.sessions.items()}}
        write_private(out/'local-index.PRIVATE.json',json.dumps(index,indent=2)+'\n')
        quality={'instructions':'Largest token-consuming root groups, a targeted diagnostic sample, NOT a random quality estimate. Edit only locally. Do not add sensitive text to any shared copy.',
            'sample':[{**r,'accepted':None,'first_pass_accepted':None,'required_verification_satisfied':None,
                       'avoidable_rework':None,'later_defect_discovered':None}
                      for r in current['root_groups'][:10]]}
        write_private(out/'quality-review-template.json',json.dumps(quality,indent=2)+'\n')
        # The share bundle deliberately excludes the private lookup index and raw logs.
        zpath=out/'SHARE-summary.zip'
        fd=os.open(zpath,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.close(fd)
        with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED) as z:
            for name in ('report.md','report.json','quality-review-template.json'):
                z.write(out/name,name)
        print(f'\nReport: {out / "report.md"}\nShareable summary: {zpath}\nKeep local: {out / "local-index.PRIVATE.json"}')
        print(f"Observed: {current['sessions_observed']} sessions, {current['worker_sessions']} workers, {current['observed_token_usage']['total_tokens']:,} input+output tokens.")
        if current['sessions_observed']==0:
            print('No supported in-window session activity was found. Check CODEX_HOME, dates, archived logs and --all-files. Zero observations do not mean zero usage.',file=sys.stderr)
            return 2
        if c.partial:
            print('PARTIAL scan: inspect report diagnostics before using totals.',file=sys.stderr)
            return 1
        return 0
    except (OSError,ValueError,ZoneInfoNotFoundError,argparse.ArgumentTypeError) as e:
        print(f'Error: {e}',file=sys.stderr)
        return 2


if __name__=='__main__':
    if sys.version_info<(3,11):
        sys.exit('Python 3.11 or newer is required. No packages need to be installed.')
    raise SystemExit(main())
