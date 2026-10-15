#!/usr/bin/env python3
"""Optional assignment/capacity advice. No native calls, writes, or permission grants.

Use at substantive transfers, not every tool call. Supplied evidence is not
independently authenticated. Existing allocator scope/hold/review checks still bind.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import stat

LIMITATION = 'Supplied-fact advice, not authenticated authority, native admission, locks or acceptance.'
WRITERS = frozenset({'main', 'simple_executor', 'routine_executor', 'default_executor',
                     'deep_executor', 'senior_executor'})
REVIEWERS = frozenset({'reviewer', 'senior_reviewer'})
ROLES = WRITERS | REVIEWERS | {'investigator', 'tester', 'companion', 'archivist'}
PURPOSES = {'implementation', 'diagnosis', 'check_design', 'test_execution', 'semantic_review',
            'lookup', 'checkpoint', 'known_operation'}


class ContractError(ValueError):
    pass


def keys(obj, required, optional=()):
    if not isinstance(obj, dict) or set(obj)-set(required)-set(optional) or set(required)-set(obj):
        raise ContractError('Unexpected or missing fields')


def text(value):
    if (not isinstance(value, str) or not value.strip() or len(value)>512
            or any(ord(c)<32 or 127<=ord(c)<=159 or 0xD800<=ord(c)<=0xDFFF for c in value)):
        raise ContractError('Expected bounded nonempty text')
    return value


def count(value, maximum=1000000):
    if type(value) is not int or not 0<=value<=maximum:
        raise ContractError('Expected bounded nonnegative integer')
    return value


def boolean(value):
    if type(value) is not bool:
        raise ContractError('Expected boolean')
    return value


def choice(value, options):
    if not isinstance(value, str) or value not in options:
        raise ContractError('Unrecognized choice')
    return value


def strings(value, allow_empty=True):
    if not isinstance(value, list) or len(value)>64 or (not allow_empty and not value):
        raise ContractError('Expected bounded list')
    result = [text(v) for v in value]
    if len(set(result))!=len(result):
        raise ContractError('Duplicate identifiers')
    return result


def result(action, **kw):
    return dict(action=action, **kw, authorizes_writes=False, accepted=False, limitation=LIMITATION)


def role_fits(role, purpose, risk):
    if purpose=='semantic_review':
        return role in REVIEWERS and (risk!='critical' or role=='senior_reviewer')
    if purpose=='test_execution':
        return role=='tester' or role in WRITERS
    if purpose in {'implementation', 'check_design'}:
        return role in WRITERS and (risk!='critical' or role in {'main','senior_executor'})
    if purpose=='diagnosis':
        return (role=='investigator' or role in WRITERS) and (risk!='critical' or role in {'main','senior_executor'})
    if purpose=='lookup':
        return role=='companion' or role in WRITERS or role=='investigator'
    if purpose=='checkpoint':
        return role=='archivist' or role=='main'
    return role in WRITERS and (risk!='critical' or role in {'main','senior_executor'})


def transition(facts):
    """Check a proposed material assignment change without retagging a live agent."""
    keys(facts, {'task','assignment','from_owner','to_owner','from_role','to_role','purpose',
                 'risk','previous_work_stopped','candidate_held','authority_ref','scope_ref',
                 'requirement_ref','evidence_refs','pending_gates','failed_fixes','repair_rounds'},
         {'review_baseline_ref'})
    for k in ('task','assignment','from_owner','to_owner','scope_ref','requirement_ref'):
        text(facts[k])
    for k in ('from_role','to_role'): choice(facts[k], ROLES)
    choice(facts['purpose'], PURPOSES); choice(facts['risk'], {'low','material','critical'})
    for k in ('previous_work_stopped','candidate_held'): boolean(facts[k])
    if facts['authority_ref'] is not None: text(facts['authority_ref'])
    for k in ('evidence_refs','pending_gates'): strings(facts[k])
    for k in ('failed_fixes','repair_rounds'): count(facts[k])
    if 'review_baseline_ref' in facts:
        text(facts['review_baseline_ref'])
        if (facts['purpose']!='semantic_review' or facts['from_role'] not in REVIEWERS
                or facts['from_role']!=facts['to_role'] or facts['from_owner']!=facts['to_owner']):
            raise ContractError('Review baseline is only for the same retained reviewer')
    payload = {k:facts[k] for k in ('task','assignment','purpose','to_role','scope_ref',
                                    'requirement_ref','failed_fixes','repair_rounds')}
    payload.update({k:facts[k] for k in ('from_owner','to_owner','from_role','risk','authority_ref')})
    payload.update(pending_gates=list(facts['pending_gates']),evidence_refs=list(facts['evidence_refs']))
    if not facts['previous_work_stopped']:
        return result('wait_for_handover', **payload)
    if facts['authority_ref'] is None:
        return result('decision_needed', **payload)
    if not role_fits(facts['to_role'], facts['purpose'], facts['risk']):
        return result('select_suitable_role', **payload)
    if facts['candidate_held'] and facts['purpose'] in {'implementation','check_design','known_operation'}:
        return result('release_hold_before_writes', **payload)
    same = facts['from_owner']==facts['to_owner']
    if same and facts['from_role']!=facts['to_role']:
        return result('dispatch_named_role', **payload)
    if same and facts['purpose']=='semantic_review':
        if 'review_baseline_ref' not in facts:
            return result('independent_reviewer_required', **payload)
        payload['review_baseline_ref']=facts['review_baseline_ref']
        if not facts['candidate_held']:
            return result('hold_candidate_before_review', **payload)
    if facts['purpose']=='semantic_review' and not facts['candidate_held']:
        return result('hold_candidate_before_review', **payload)
    return result('reuse_bounded_context' if same else 'transfer_ready_for_allocator', **payload)


def capacity(facts):
    """Normalize one explicitly observed native domain. Never guess V1/V2 precedence."""
    keys(facts, {'domain','evidence_ref','observation_current','effective_limit_verified',
                 'native_limit','primary_included','owned_open_workers','other_occupants'})
    text(facts['domain'])
    if facts['evidence_ref'] is not None: text(facts['evidence_ref'])
    for k in ('observation_current','effective_limit_verified'): boolean(facts[k])
    if facts['primary_included'] is not None: boolean(facts['primary_included'])
    for k in ('native_limit','owned_open_workers','other_occupants'):
        if facts[k] is not None: count(facts[k], 1024)
    unknown = (not facts['observation_current'] or not facts['effective_limit_verified']
               or any(facts[k] is None for k in ('evidence_ref','native_limit','primary_included',
                                                 'owned_open_workers','other_occupants')))
    if unknown:
        return result('inspect_native_capacity', max_new_workers=0, domain=facts['domain'],
                      native_capacity_verified=False)
    free_native = facts['native_limit']-int(facts['primary_included'])-facts['owned_open_workers']-facts['other_occupants']
    free_smart = 5-facts['owned_open_workers']
    slots = max(0, min(free_smart, free_native))
    return result('capacity_available' if slots else 'reuse_or_wait', max_new_workers=slots,
                  domain=facts['domain'], evidence_ref=facts['evidence_ref'],
                  native_capacity_verified=False,
                  observation_basis='Caller asserts current effective native-domain observation; not independently checked.')


def read_json(path, max_bytes=65536):
    if type(max_bytes) is not int or not 1<=max_bytes<=4*1024*1024:
        raise ContractError('Invalid JSON byte limit')
    if path.is_symlink(): raise ContractError('Symlink input')
    fd=os.open(path, os.O_RDONLY|getattr(os,'O_NOFOLLOW',0)|getattr(os,'O_NONBLOCK',0))
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode): raise ContractError('Input must be regular')
        with os.fdopen(fd,'rb',closefd=False) as stream: raw=stream.read(max_bytes+1)
    finally: os.close(fd)
    if len(raw)>max_bytes: raise ContractError('Input too large')
    def pairs(values):
        out={}
        for k,v in values:
            if k in out: raise ContractError('Duplicate JSON key')
            out[k]=v
        return out
    def invalid(_): raise ContractError('Nonfinite JSON value')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        obj=read_json(args.input); keys(obj,{'operation','facts'})
        op=choice(obj['operation'], {'transition','capacity'})
        out={'transition':transition,'capacity':capacity}[op](obj['facts'])
        print(json.dumps(out,sort_keys=True))
        return 0 if out['action'] in {'reuse_bounded_context','transfer_ready_for_allocator','capacity_available'} else 1
    except (OSError, ValueError, RecursionError) as exc:
        print(json.dumps(dict(error=str(exc),limitation=LIMITATION)))
        return 2

if __name__=='__main__': raise SystemExit(main())
