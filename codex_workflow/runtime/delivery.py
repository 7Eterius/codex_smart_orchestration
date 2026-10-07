#!/usr/bin/env python3
"""Optional, stateless delivery advice from bounded supplied facts.

No model calls, native quota reads, scheduling, Git operations, source edits, or
acceptance decisions. Use existing task notes, not a mandatory ledger. Advice
cannot authenticate observations or enforce spending against concurrent work.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import stat
from fractions import Fraction
from pathlib import Path

MAX_INPUT_BYTES = 65536
MAX_COUNT = 1000000
LIMITATION = ('Supplied-fact advice only; not native enforcement, authenticated '
              'quota/evidence, permission to write, or acceptance.')
OWNERS = frozenset({'main', 'simple_executor', 'routine_executor', 'default_executor',
                    'deep_executor', 'senior_executor', 'tester', 'reviewer',
                    'senior_reviewer', 'companion', 'investigator', 'archivist'})
PATCH_OWNERS = frozenset({'main', 'simple_executor', 'routine_executor',
                          'default_executor', 'deep_executor', 'senior_executor'})


class DeliveryError(ValueError):
    pass


def _keys(value: dict, required: set[str], optional: set[str] = frozenset()) -> None:
    if (not isinstance(value, dict) or required - value.keys()
            or value.keys() - required - optional):
        raise DeliveryError('Unexpected or missing fields')


def _choice(value: str, choices: set[str] | frozenset[str]) -> str:
    if not isinstance(value, str) or value not in choices:
        raise DeliveryError('Unrecognized choice')
    return value


def _boolean(value: bool) -> bool:
    if type(value) is not bool:
        raise DeliveryError('Expected boolean')
    return value


def _count(value: int, maximum: int = MAX_COUNT) -> int:
    if type(value) is not int or not 0 <= value <= maximum:
        raise DeliveryError('Expected bounded nonnegative integer')
    return value


def _number(value: float) -> float:
    if type(value) not in (int, float) or not 0 <= value <= 1e15 or not math.isfinite(value):
        raise DeliveryError('Expected bounded finite nonnegative number')
    return value


def _text(value: str) -> str:
    if (not isinstance(value, str) or not value.strip() or len(value) > 256
            or any(ord(c) < 32 or 127 <= ord(c) <= 159 or 0xD800 <= ord(c) <= 0xDFFF for c in value)):
        raise DeliveryError('Expected bounded nonempty identifier')
    return value


def _result(**values) -> dict:
    return {**values, 'authorizes_writes': False, 'limitation': LIMITATION}


def practices(facts: dict) -> dict:
    """Select only useful engineering practices; role routing stays in allocation.py."""
    _keys(facts, {'domain', 'kind', 'size', 'clarity', 'risk', 'behavior_change',
                  'testable', 'isolated', 'long_running'}, {'tdd_required'})
    domain = _choice(facts['domain'], {'code', 'noncode'})
    kind = _choice(facts['kind'], {'feature', 'bug', 'refactor', 'mechanical',
                                  'research', 'writing', 'operations'})
    size = _choice(facts['size'], {'small', 'medium', 'large'})
    clarity = _choice(facts['clarity'], {'clear', 'ambiguous'})
    risk = _choice(facts['risk'], {'low', 'material', 'critical'})
    for key in ('behavior_change', 'testable', 'isolated', 'long_running', 'tdd_required'):
        if key in facts:
            _boolean(facts[key])
    plan = ('durable' if size == 'large' or facts['long_running'] else
            'direct' if size == 'small' and clarity == 'clear' and risk == 'low' else 'lean')
    action = 'resolve_requirements' if clarity == 'ambiguous' else 'proceed'
    guides = ['planning.md'] if plan != 'direct' or clarity == 'ambiguous' else []
    if kind == 'bug':
        guides.append('debugging.md')
    tdd = 'not_applicable'
    workspace = 'none'
    code_change = domain == 'code' and (
        kind not in {'research', 'writing'} or facts['behavior_change'])
    if code_change:
        guides.append('testing.md')
        workspace = 'reuse' if facts['isolated'] else ('consider_isolation' if size == 'large' else 'in_place')
        if workspace in {'reuse', 'consider_isolation'}:
            guides.append('branches.md')
        tdd = ('red_green' if facts['testable'] and (facts['behavior_change'] or kind == 'bug') else
               'characterize' if facts['testable'] and kind == 'refactor' else 'alternative')
    if facts.get('tdd_required', False):
        if domain == 'code' and 'testing.md' not in guides:
            guides.append('testing.md')
        if domain != 'code' or not facts['testable']:
            action, tdd = 'resolve_test_strategy', 'blocked'
        else:
            tdd = 'red_green'
    return _result(action=action, brainstorm='targeted' if clarity == 'ambiguous' else 'none',
                   plan=plan, tdd=tdd, workspace=workspace, guides=guides)


def budget(facts: dict) -> dict:
    """Bound the next batch; money, tokens and account allowance are never converted.

    An optional explicit envelope uses one unit. next_estimate covers the ENTIRE
    proposed batch, including its verification, not just one worker's next call.
    """
    _keys(facts, {'quota', 'requested_workers', 'available_slots', 'independent_ready',
                  'mandatory_gates_pending'}, {'limit', 'open_workers'})
    quota = _choice(facts['quota'], {'available', 'low', 'exhausted', 'unknown'})
    requested = _count(facts['requested_workers'], 5)
    slots = facts['available_slots']
    if slots is not None:
        _count(slots, 128)
    ready = _count(facts['independent_ready'], 128)
    gates = _boolean(facts['mandatory_gates_pending'])
    opened = facts.get('open_workers')
    if opened is not None:
        _count(opened, 128)
    envelope_action = None
    if 'limit' in facts:
        limit = facts['limit']
        _keys(limit, {'unit', 'maximum', 'spent', 'committed', 'next_estimate', 'observation_current'})
        _choice(limit['unit'], {'tokens', 'credits', 'seconds', 'requests'})
        for key in ('maximum', 'spent', 'committed'):
            _number(limit[key])
        if limit['maximum'] == 0:
            raise DeliveryError('Explicit maximum must be positive')
        if limit['next_estimate'] is not None:
            _number(limit['next_estimate'])
        current = _boolean(limit['observation_current'])
        # Compare the supplied decimal values exactly. Binary subtraction can
        # reject a fitting 0.1 + 0.2 budget or erase a small real overrun.
        remaining = (Fraction(str(limit['maximum'])) - Fraction(str(limit['spent']))
                     - Fraction(str(limit['committed'])))
        if not current:
            envelope_action = 'inspect_budget'
        elif remaining <= 0:
            envelope_action = 'checkpoint'
        elif limit['next_estimate'] is None:
            envelope_action = 'inspect_budget'
        elif Fraction(str(limit['next_estimate'])) > remaining:
            envelope_action = 'replan_budget'
    workers = 0
    if quota == 'exhausted':
        action = 'checkpoint'
    elif envelope_action:
        action = envelope_action
    elif slots is None or ('open_workers' in facts and opened is None):
        action = 'inspect_capacity'
    else:
        # Unknown usage is not a command to run an expensive quota audit.
        ceiling = 1 if quota == 'low' else 2 if quota == 'unknown' else 5
        workers = min(requested, slots, ready, max(0, ceiling - (opened or 0)))
        action = 'proceed_bounded' if workers else 'direct_or_wait'
    return _result(action=action, max_new_workers=workers, cost_verified=False,
                   open_workers=opened,
                   limit_scope='total_open_workers' if opened is not None else 'new_batch_only',
                   mandatory_gates_pending=gates,
                   gate_policy='Preserve required gates; checkpoint instead of waiving them.')


def _repair_window(facts: dict) -> tuple[int, str | None, bool]:
    """Keep lifetime counters while bounding a recorded Main replan window.

    The decision reference is supplied evidence, not authenticated approval.
    Failure and review counters can describe the same attempt, so use the larger
    delta rather than counting one failed repair twice.
    """
    baseline_fixes = baseline_rounds = 0
    allowance = 3
    reference = None
    if 'replan' in facts:
        record = facts['replan']
        _keys(record, {'task', 'defect', 'decision_ref', 'failed_fixes',
                       'repair_rounds', 'attempt_limit'})
        for key in ('task', 'defect', 'decision_ref'):
            _text(record[key])
        if any(record[key] != facts[key] for key in ('task', 'defect')):
            raise DeliveryError('Replan belongs to another task or defect')
        baseline_fixes = _count(record['failed_fixes'])
        baseline_rounds = _count(record['repair_rounds'])
        allowance = _count(record['attempt_limit'], 3)
        if allowance == 0:
            raise DeliveryError('Replan attempt limit must be between one and three')
        if baseline_fixes > facts['failed_fixes'] or baseline_rounds > facts['repair_rounds']:
            raise DeliveryError('Cumulative repair counts cannot precede the replan baseline')
        reference = record['decision_ref']
    used = max(facts['failed_fixes'] - baseline_fixes,
               facts['repair_rounds'] - baseline_rounds)
    return max(0, allowance - used), reference, reference is not None and used == 0


def recovery(facts: dict) -> dict:
    """Stop nonconverging repair work; reaching a cap never resolves a blocker.

    failed_fixes counts failed causal fixes for the same defect; repair_rounds
    counts complete fix/re-review waves for the task, across all owner changes.
    Counters are supplied, not persistent or authenticated by this helper.
    """
    _keys(facts, {'task', 'defect', 'previous_owner', 'failed_fixes', 'repair_rounds',
                  'same_defect_no_progress', 'new_evidence', 'blocking',
                  'authority_needed', 'budget_exhausted'}, {'replan'})
    for key in ('task', 'defect'):
        _text(facts[key])
    owner = _choice(facts['previous_owner'], OWNERS)
    for key in ('failed_fixes', 'repair_rounds'):
        _count(facts[key])
    for key in ('same_defect_no_progress', 'new_evidence', 'blocking',
                'authority_needed', 'budget_exhausted'):
        _boolean(facts[key])
    remaining, replan_ref, fresh_replan = _repair_window(facts)
    if facts['budget_exhausted']:
        action = 'checkpoint'
    elif facts['authority_needed']:
        action = 'decision_needed'
    elif not facts['blocking']:
        action = 'record_nonblocking'
    elif remaining == 0:
        action = 'replan'
    elif facts['same_defect_no_progress'] and not fresh_replan:
        action = 'replan' if owner in {'main', 'senior_executor', 'senior_reviewer'} else 'escalate'
    elif not facts['new_evidence']:
        action = 'investigate'
    elif owner not in PATCH_OWNERS:
        action = 'assign_implementation'
    else:
        action = 'bounded_fix'
    return _result(action=action, task=facts['task'], defect=facts['defect'],
                   failed_fixes=facts['failed_fixes'], repair_rounds=facts['repair_rounds'],
                   remaining_attempts=remaining, replan_ref=replan_ref,
                   may_patch=action == 'bounded_fix', blocking_unresolved=facts['blocking'],
                   accepted=False)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise DeliveryError('Duplicate JSON key')
        result[key] = value
    return result


def _nonfinite(value):
    raise DeliveryError('Non-finite JSON number')


def _read_input(path: Path) -> bytes:
    """Bound reads and validate the opened object, not just a prior path check.

    NOFOLLOW/NONBLOCK harden the final component on supported POSIX hosts. This
    is not protection against all ancestor/path races or a filesystem sandbox.
    """
    if path.is_symlink() or not path.is_file():
        raise DeliveryError('Input must be a regular file, not a symlink')
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
    descriptor = os.open(path, flags)
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise DeliveryError('Opened input is not a regular file')
        with os.fdopen(descriptor, 'rb', closefd=False) as stream:
            raw = stream.read(MAX_INPUT_BYTES + 1)
    finally:
        os.close(descriptor)
    if len(raw) > MAX_INPUT_BYTES:
        raise DeliveryError('Input exceeds size limit')
    return raw


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        raw = _read_input(args.input)
        value = json.loads(raw, object_pairs_hook=_pairs, parse_constant=_nonfinite)
        _keys(value, {'operation', 'facts'})
        operation = _choice(value['operation'], {'prepare', 'budget', 'recover'})
        result = {'prepare': practices, 'budget': budget, 'recover': recovery}[operation](value['facts'])
        print(json.dumps(result, sort_keys=True))
        return 0 if result['action'] in {'proceed', 'proceed_bounded', 'direct_or_wait',
                                         'bounded_fix', 'record_nonblocking'} else 1
    except (OSError, ValueError, RecursionError) as exc:
        import sys
        print(json.dumps({'error': str(exc), 'limitation': LIMITATION}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
