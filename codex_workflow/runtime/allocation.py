#!/usr/bin/env python3
"""Bounded Smart 3 routing and prospective ownership checks; no native scheduling.

Facts, scopes and authority are supplied observations. No files, logs, processes,
models, permissions or native agent state are changed. Approval is not execution.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROLES = frozenset({'simple_executor', 'routine_executor', 'default_executor',
                   'senior_executor', 'tester', 'companion', 'investigator', 'archivist'})
REVIEW_OWNERS = frozenset({'routine_executor', 'default_executor'})
WRITERS = frozenset({'simple_executor', 'routine_executor', 'default_executor', 'senior_executor'})
SMART_OPEN_LIMIT = 4
MAX_INPUT_BYTES = 65536
MAX_THREADS = 128
LIMITATION = 'Advisory policy from supplied observations, not native enforcement or a correctness/cost guarantee.'


class AllocationError(ValueError):
    pass


def _keys(value, required, optional=()):
    if not isinstance(value, dict) or set(value) - set(required) - set(optional) or set(required) - set(value):
        raise AllocationError('Unexpected or missing fields')


def _bool(value):
    if type(value) is not bool:
        raise AllocationError('Expected a boolean, not a truthy value')
    return value


def _text(value):
    if (not isinstance(value, str) or not value.strip() or len(value) > 512
            or any(ord(c) < 32 or 127 <= ord(c) <= 159 or 0xD800 <= ord(c) <= 0xDFFF for c in value)):
        raise AllocationError('Expected a bounded nonempty identifier')
    return value


def classify(task: dict) -> dict:
    """Route uncertainty to intelligence, not every small job to another agent.

    Existing six fields remain accepted. Optional mechanical/in_context/on_critical_path
    and stalled describe why a handoff is useful. Absent mechanical is NOT evidence
    that ordinary implementation or browser investigation is cheap-model work.
    """
    _keys(task, {'kind', 'risk', 'settled', 'tiny', 'deep', 'independent_required'},
          {'mechanical', 'in_context', 'on_critical_path', 'stalled'})
    kind = _text(task['kind'])
    if kind not in {'answer', 'judgment', 'operation', 'implementation', 'verification', 'discovery', 'memory'}:
        raise AllocationError('Unrecognized assignment kind')
    if _text(task['risk']) not in {'low', 'material', 'critical'}:
        raise AllocationError('Unrecognized risk')
    for key in ('settled', 'tiny', 'deep', 'independent_required', 'mechanical',
                'in_context', 'on_critical_path', 'stalled'):
        if key in task:
            _bool(task[key])
    if task['tiny'] and task['deep']:
        raise AllocationError('Tiny and deep are contradictory')
    review = task['independent_required'] or task['risk'] != 'low' or task['deep']
    mechanical = task.get('mechanical', False)
    if kind == 'answer':
        role, reason = 'main', 'answer_without_team'
    elif kind == 'judgment' or not task['settled']:
        role, reason = 'main', 'resolve_judgment_or_contract'
    elif kind == 'verification':
        role, reason = 'tester', 'independent_verification_without_writer'
    elif kind == 'memory':
        role, reason = 'archivist', 'authorized_checkpoint_only'
    elif task.get('stalled', False):
        role, reason = 'default_executor', 'intelligent_diagnosis_not_another_cheap_retry'
    elif kind == 'discovery':
        role, reason = ('companion', 'exact_lookup') if mechanical and not task['deep'] else ('investigator', 'causal_investigation')
    elif ((task['tiny'] and task.get('in_context', True))
          or (task.get('in_context', False) and task.get('on_critical_path', False))):
        role, reason = 'main', 'direct_bounded_finish_avoids_handoff'
    elif task['deep'] or not mechanical or task['risk'] != 'low':
        role, reason = 'default_executor', 'sol_problem_solving_default'
    elif kind == 'operation' or task['tiny']:
        role, reason = 'simple_executor', 'known_mechanical_work'
    else:
        role, reason = 'routine_executor', 'prescribed_bulk_implementation'
    reviewer = 'tester' if review and kind in {'implementation', 'operation'} else None
    return {'owner': role, 'reviewer': reviewer, 'reason': reason, 'limitation': LIMITATION}


def _paths(value, *, absolute=False):
    if not isinstance(value, list) or len(value) > MAX_THREADS:
        raise AllocationError('Expected a bounded path list')
    for item in value:
        _text(item)
        parts = item[1:].split('/') if absolute else item.split('/')
        if (item != item.strip() or '\\' in item or ':' in item
                or (absolute and not item.startswith('/'))
                or (not absolute and item.startswith('/'))
                or (item != '.' and any(p in {'', '.', '..', '.git'} for p in parts))):
            raise AllocationError('Use canonical paths; relative . means the entire workspace')
    if len(set(value)) != len(value):
        raise AllocationError('Duplicate scope entry')
    return value


def _scope(value):
    _keys(value, {'workspace', 'reads', 'writes', 'resource_reads', 'resource_writes'})
    _paths([value['workspace']], absolute=True)
    for key in ('reads', 'writes', 'resource_reads', 'resource_writes'):
        _paths(value[key])
    if '.' in value['resource_reads'] or '.' in value['resource_writes']:
        raise AllocationError('Shared resources need explicit canonical names, not .')
    return value


def _overlap(a, b):
    return a == b or a.startswith(b + '/') or b.startswith(a + '/')


def _conflict(a, b):
    """Read/write conflicts, including nested roots and shared mutable resources."""
    def local(scope, key):
        return [scope['workspace'] if p == '.' else scope['workspace'] + '/' + p for p in scope[key]]
    def collides(aw, ar, bw, br):
        return any(_overlap(x, y) for x in aw for y in bw + br) or any(_overlap(x, y) for x in bw for y in ar)
    return (collides(local(a, 'writes'), local(a, 'reads'), local(b, 'writes'), local(b, 'reads'))
            or collides(a['resource_writes'], a['resource_reads'], b['resource_writes'], b['resource_reads']))


def _inventory(obs: dict):
    _keys(obs, {'caller', 'cap', 'complete', 'close_supported', 'threads'},
          {'primary', 'main_scope', 'accepted_units'})
    primary = _text(obs.get('primary', 'main'))
    caller = _text(obs['caller'])
    cap = obs['cap']
    if cap is not None and (type(cap) is not int or not 1 <= cap <= MAX_THREADS):
        raise AllocationError('Cap must be a positive bounded integer or null')
    _bool(obs['complete']); _bool(obs['close_supported'])
    if obs.get('main_scope') is not None:
        _scope(obs['main_scope'])
    accepted = obs.get('accepted_units', {})
    if not isinstance(accepted, dict) or len(accepted) > MAX_THREADS:
        raise AllocationError('Accepted units need a bounded evidence-reference map')
    for unit, proof in accepted.items():
        _text(unit); _text(proof)
    if not isinstance(obs['threads'], list) or len(obs['threads']) > MAX_THREADS:
        raise AllocationError('Thread inventory too large or malformed')
    entries = {}
    for t in obs['threads']:
        _keys(t, {'id', 'parent', 'unit', 'role', 'state', 'owned', 'retain', 'durable', 'released_resources'},
              {'closure_evidence', 'review_authorized', 'scope', 'review_reserved'})
        for key in ('id', 'parent', 'unit', 'role'):
            _text(t[key])
        if t['id'] in entries or t['id'] == t['parent'] or t['id'] == primary:
            raise AllocationError('Duplicate/self-parented thread or primary included as a spawned thread')
        if _text(t['state']) not in {'running', 'waiting', 'completed', 'closing', 'closed', 'unknown'}:
            raise AllocationError('Invalid lifecycle state')
        for key in ('owned', 'retain', 'durable', 'released_resources', 'review_authorized', 'review_reserved'):
            if key in t:
                _bool(t[key])
        if 'closure_evidence' in t:
            _text(t['closure_evidence'])
        if t['state'] == 'closed' and not t.get('closure_evidence'):
            raise AllocationError('Closed needs an observed native result reference, not a final message')
        if 'scope' in t:
            _scope(t['scope'])
        entries[t['id']] = t
    for ident in entries:
        seen, current = set(), ident
        while current in entries:
            if current in seen:
                raise AllocationError('Cyclic thread parents')
            seen.add(current); current = entries[current]['parent']
    opened = {key: t for key, t in entries.items() if t['state'] != 'closed'}
    closable = sorted(t['id'] for t in opened.values()
                      if t['parent'] == caller and t['owned'] and t['state'] == 'completed'
                      and not t['retain'] and t['durable'] and t['released_resources']
                      and not any(c['parent'] == t['id'] for c in opened.values()))
    return cap, entries, opened, closable


def next_action(obs: dict, request: dict) -> dict:
    """Check one prospective action. Call again only after material state changes.

    Parallelism requires explicit scopes, settled dependencies and Main activity.
    Legacy unscoped calls support one unit and its reviewer, not unproven fan-out.
    Reservations survive in observations as review_reserved; they are not slot creation.
    """
    _keys(request, {'unit', 'role', 'reserve', 'reuse_id', 'spawn_failed', 'state_changed'},
          {'intent', 'scope', 'depends_on', 'candidate_held'})
    unit, role = _text(request['unit']), _text(request['role'])
    if role not in ROLES:
        raise AllocationError('Requested role is not a Smart role')
    intent = _text(request.get('intent', 'work'))
    if intent not in {'work', 'readback', 'cleanup'}:
        raise AllocationError('Intent must be work, readback or cleanup')
    if type(request['reserve']) is not int or request['reserve'] not in (0, 1):
        raise AllocationError('Reserve must be zero or one review slot')
    for key in ('spawn_failed', 'state_changed', 'candidate_held'):
        if key in request:
            _bool(request[key])
    if request['reuse_id'] is not None:
        _text(request['reuse_id'])
    if intent == 'readback' and (request['reuse_id'] is None or request['reserve'] != 0):
        raise AllocationError('Readback requires an existing handle and no reserved slot')
    if intent == 'cleanup' and (request['reuse_id'] is not None or request['reserve'] != 0):
        raise AllocationError('Cleanup cannot reuse work or reserve capacity')
    scope = _scope(request['scope']) if 'scope' in request else None
    deps = request.get('depends_on', [])
    if not isinstance(deps, list) or len(deps) > MAX_THREADS:
        raise AllocationError('Dependencies must be a bounded list')
    for dep in deps:
        _text(dep)
    if len(set(deps)) != len(deps) or unit in deps:
        raise AllocationError('Duplicate/self dependency')
    cap, entries, opened, closable = _inventory(obs)
    result = {'action': 'inspect', 'reason': 'incomplete_inventory', 'open_count': len(opened),
              'cap': cap, 'limitation': LIMITATION}
    if not obs['complete']:
        return result
    primary = obs.get('primary', 'main')
    caller = entries.get(obs['caller'])
    if obs['caller'] != primary:
        if caller is None or not caller['owned']:
            raise AllocationError('Caller must be the declared primary or a known owned thread')
        if caller['state'] not in {'running', 'waiting', 'completed'}:
            raise AllocationError('Caller lifecycle does not permit work or cleanup')

    def cleanup():
        if closable and obs['close_supported']:
            return {**result, 'action': 'close', 'reason': 'release_completed_children', 'ids': closable,
                    'then': 'reobserve; closure requested is not closure observed'}
        return None

    if intent == 'cleanup':
        return cleanup() or {**result, 'action': 'wait', 'reason': 'no_supported_cleanup'}
    reuse = entries.get(request['reuse_id'])
    if request['reuse_id'] is None:
        same = [t for t in opened.values() if t['owned'] and t['unit'] == unit and t['role'] == role]
        if not same and (released := cleanup()) is not None:
            return released
    if caller is not None:
        if (caller['state'] not in {'running', 'waiting'} or caller['role'] not in REVIEW_OWNERS
                or role != 'tester' or caller['unit'] != unit or not caller.get('review_authorized', False)):
            raise AllocationError('New review work requires an active same-unit owner with explicit review authority')
    if request['reuse_id'] is not None:
        if (reuse is None or not reuse['owned'] or reuse['parent'] != obs['caller']
                or reuse['role'] != role or reuse['unit'] != unit or reuse['state'] not in {'completed', 'waiting'}):
            raise AllocationError('Reuse requires a stopped same-unit owned direct child with matching role')
    if intent == 'work' and role in WRITERS and any(
            t['owned'] and t['unit'] == unit and t['role'] in WRITERS
            and t['id'] != request['reuse_id'] for t in opened.values()):
        same_role = request['reuse_id'] is None and any(t['owned'] and t['unit'] == unit and t['role'] == role for t in opened.values())
        return {**result, 'action': 'wait', 'reason': 'assignment_already_open' if same_role else 'existing_writer_requires_explicit_transfer'}
    if intent == 'readback':
        return {**result, 'action': 'reuse', 'reason': 'readback_only', 'id': reuse['id'], 'intent': intent}
    missing = [d for d in deps if d not in obs.get('accepted_units', {})]
    if missing:
        return {**result, 'action': 'wait', 'reason': 'dependencies_not_accepted', 'dependencies': missing}
    if reuse and 'scope' in reuse:
        if scope is not None and scope != reuse['scope']:
            return {**result, 'action': 'blocked', 'reason': 'scope_change_requires_transfer'}
        scope = reuse['scope']
    peers = [t for t in opened.values() if t['id'] != request['reuse_id']]
    if scope is not None:
        if 'main_scope' not in obs:
            return {**result, 'action': 'inspect', 'reason': 'main_activity_unknown'}
        if obs['main_scope'] is not None and _conflict(scope, obs['main_scope']):
            return {**result, 'action': 'wait', 'reason': 'main_scope_conflict'}
        for t in peers:
            stopped = t['state'] in {'waiting', 'completed'}
            same_unit = t['owned'] and t['unit'] == unit
            resource_conflict = ('scope' not in t or _conflict(
                {**scope, 'reads': [], 'writes': []},
                {**t.get('scope', scope), 'reads': [], 'writes': []}))
            resources_safe = t['released_resources'] or not resource_conflict
            review_writes_safe = ('scope' in t and not _conflict(
                {**scope, 'reads': [], 'resource_reads': [], 'resource_writes': []},
                {**t['scope'], 'reads': t['scope']['reads'] + t['scope']['writes'],
                 'writes': [], 'resource_reads': [], 'resource_writes': []}))
            if (role == 'tester' and same_unit and t['role'] in WRITERS and stopped
                    and request.get('candidate_held', False) and resources_safe and review_writes_safe):
                continue
            if (role in WRITERS and same_unit and t['role'] == 'tester' and stopped
                    and request.get('candidate_held') is False and resources_safe):
                continue
            if 'scope' not in t:
                return {**result, 'action': 'inspect', 'reason': 'peer_scope_unknown', 'peer': t['id']}
            if _conflict(scope, t['scope']):
                return {**result, 'action': 'wait', 'reason': 'scope_or_resource_conflict', 'peer': t['id']}
    elif any(t['unit'] != unit for t in peers):
        return {**result, 'action': 'inspect', 'reason': 'parallel_scopes_required'}
    if reuse:
        return {**result, 'action': 'reuse', 'reason': 'same_unit_delta', 'id': reuse['id'], 'intent': intent}
    if any(t['owned'] and t['unit'] == unit and t['role'] == role for t in opened.values()):
        return {**result, 'action': 'wait', 'reason': 'assignment_already_open'}
    if request['spawn_failed'] and not request['state_changed']:
        return {**result, 'action': 'blocked', 'reason': 'no_blind_spawn_retry'}
    if cap is None:
        return {**result, 'reason': 'capacity_unknown'}
    reserved = {t['unit'] for t in opened.values() if t['owned'] and t.get('review_reserved', False)
                and not any(r['owned'] and r['unit'] == t['unit'] and r['role'] == 'tester' for r in opened.values())}
    if role == 'tester':
        reserved.discard(unit)
    if request['reserve']:
        reserved.add(unit)
    # One reusable review slot is shared by queued reviews, not one per writer.
    review_slot = bool(reserved) and role != 'tester' and not any(
        t['owned'] and t['role'] == 'tester' for t in opened.values())
    required = 1 + int(review_slot)
    limit = SMART_OPEN_LIMIT if scope is not None else 2
    if sum(t['owned'] for t in opened.values()) + required > limit:
        return {**result, 'action': 'blocked', 'reason': 'smart_open_thread_budget', 'required_free': required}
    if cap - len(opened) < required:
        return {**result, 'action': 'blocked', 'reason': 'insufficient_open_thread_budget', 'required_free': required}
    return {**result, 'action': 'spawn', 'reason': 'budget_available', 'role': role,
            'reserve': request['reserve'], 'record_review_reserved': bool(request['reserve'])}


def review_host(*, nested_observed: bool, owner_role: str, free_slots: int, close_supported: bool) -> str:
    _bool(nested_observed); _bool(close_supported)
    if _text(owner_role) not in ROLES or type(free_slots) is not int or free_slots < 0:
        raise AllocationError('Invalid review-host inputs')
    if free_slots == 0:
        return 'release_completed_owner_then_main' if close_supported else 'blocked'
    return 'owner' if nested_observed and owner_role in REVIEW_OWNERS and close_supported else 'main'


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise AllocationError('Duplicate JSON key')
        result[key] = value
    return result


def _nonfinite(value):
    raise AllocationError('Non-finite JSON numbers are not accepted')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True, help='Small private observation JSON, not a log archive')
    args = parser.parse_args(argv)
    try:
        if args.input.is_symlink() or not args.input.is_file():
            raise AllocationError('Input must be a regular file')
        with args.input.open('rb') as stream:
            data = stream.read(MAX_INPUT_BYTES + 1)
        if len(data) > MAX_INPUT_BYTES:
            raise AllocationError('Input exceeds size limit')
        try:
            value = json.loads(data, object_pairs_hook=_pairs, parse_constant=_nonfinite)
        except RecursionError as exc:
            raise AllocationError('JSON nesting exceeds parser limit') from exc
        _keys(value, {'observation', 'request'})
        result = next_action(value['observation'], value['request'])
        print(json.dumps(result, sort_keys=True))
        return 0 if result['action'] in {'spawn', 'reuse', 'close'} else 1
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({'action': 'blocked', 'error': str(exc), 'limitation': LIMITATION}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
