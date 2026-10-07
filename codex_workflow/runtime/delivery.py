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
from pathlib import Path

MAX_INPUT_BYTES = 65536
MAX_COUNT = 1000000
LIMITATION = ('Supplied-fact advice only; not native enforcement, authenticated '
              'quota/evidence, permission to write, or acceptance.')
OWNERS = frozenset({'main', 'simple_executor', 'routine_executor', 'default_executor',
                    'deep_executor', 'senior_executor', 'tester', 'reviewer',
                    'senior_reviewer', 'companion', 'investigator', 'archivist'})


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
    if domain == 'code':
        guides.append('testing.md')
        workspace = 'reuse' if facts['isolated'] else ('consider_isolation' if size == 'large' else 'in_place')
        if workspace in {'reuse', 'consider_isolation'}:
            guides.append('branches.md')
        tdd = ('red_green' if facts['testable'] and (facts['behavior_change'] or kind == 'bug') else
               'characterize' if facts['testable'] and kind == 'refactor' else 'alternative')
    if facts.get('tdd_required', False):
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
                  'mandatory_gates_pending'}, {'limit'})
    quota = _choice(facts['quota'], {'available', 'low', 'exhausted', 'unknown'})
    requested = _count(facts['requested_workers'], 5)
    slots = facts['available_slots']
    if slots is not None:
        _count(slots, 128)
    ready = _count(facts['independent_ready'], 128)
    gates = _boolean(facts['mandatory_gates_pending'])
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
        remaining = limit['maximum'] - limit['spent'] - limit['committed']
        if not current:
            envelope_action = 'inspect_budget'
        elif remaining <= 0:
            envelope_action = 'checkpoint'
        elif limit['next_estimate'] is None:
            envelope_action = 'inspect_budget'
        elif limit['next_estimate'] > remaining:
            envelope_action = 'replan_budget'
    workers = 0
    if quota == 'exhausted':
        action = 'checkpoint'
    elif envelope_action:
        action = envelope_action
    elif slots is None:
        action = 'inspect_capacity'
    else:
        # Unknown usage is not a command to run an expensive quota audit.
        ceiling = 1 if quota == 'low' else 2 if quota == 'unknown' else 5
        workers = min(requested, slots, ready, ceiling)
        action = 'proceed_bounded' if workers else 'direct_or_wait'
    return _result(action=action, max_new_workers=workers, cost_verified=False,
                   mandatory_gates_pending=gates,
                   gate_policy='Preserve required gates; checkpoint instead of waiving them.')


def recovery(facts: dict) -> dict:
    """Stop nonconverging repair work; reaching a cap never resolves a blocker.

    failed_fixes counts failed causal fixes for the same defect; repair_rounds
    counts complete fix/re-review waves for the task, across all owner changes.
    Counters are supplied, not persistent or authenticated by this helper.
    """
    _keys(facts, {'task', 'defect', 'previous_owner', 'failed_fixes', 'repair_rounds',
                  'same_defect_no_progress', 'new_evidence', 'blocking',
                  'authority_needed', 'budget_exhausted'})
    for key in ('task', 'defect'):
        _text(facts[key])
    owner = _choice(facts['previous_owner'], OWNERS)
    for key in ('failed_fixes', 'repair_rounds'):
        _count(facts[key])
    for key in ('same_defect_no_progress', 'new_evidence', 'blocking',
                'authority_needed', 'budget_exhausted'):
        _boolean(facts[key])
    if facts['budget_exhausted']:
        action = 'checkpoint'
    elif facts['authority_needed']:
        action = 'decision_needed'
    elif not facts['blocking']:
        action = 'record_nonblocking'
    elif facts['failed_fixes'] >= 3 or facts['repair_rounds'] >= 3:
        action = 'replan'
    elif facts['same_defect_no_progress']:
        action = 'replan' if owner in {'main', 'senior_executor', 'senior_reviewer'} else 'escalate'
    elif not facts['new_evidence']:
        action = 'investigate'
    else:
        action = 'bounded_fix'
    return _result(action=action, task=facts['task'], defect=facts['defect'],
                   failed_fixes=facts['failed_fixes'], repair_rounds=facts['repair_rounds'],
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


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.input.is_symlink() or not args.input.is_file():
            raise DeliveryError('Input must be a regular file, not a symlink')
        with args.input.open('rb') as stream:
            raw = stream.read(MAX_INPUT_BYTES + 1)
        if len(raw) > MAX_INPUT_BYTES:
            raise DeliveryError('Input exceeds size limit')
        value = json.loads(raw, object_pairs_hook=_pairs, parse_constant=_nonfinite)
        _keys(value, {'operation', 'facts'})
        operation = _choice(value['operation'], {'prepare', 'budget', 'recover'})
        result = {'prepare': practices, 'budget': budget, 'recover': recovery}[operation](value['facts'])
        print(json.dumps(result, sort_keys=True))
        return 0 if result['action'] in {'proceed', 'proceed_bounded', 'direct_or_wait',
                                         'bounded_fix', 'record_nonblocking'} else 1
    except (OSError, ValueError, TypeError, RecursionError, OverflowError) as exc:
        import sys
        print(json.dumps({'error': str(exc), 'limitation': LIMITATION}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
