from pathlib import Path
import hashlib
p=Path('codex_workflow/runtime/delivery.py')
b=p.read_bytes()
assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()=='49c37d593815972640951c115c807137c39d50df','Unexpected source'
s=p.read_text()
def sub(old,new):
    global s
    assert s.count(old)==1,(old[:100],s.count(old))
    s=s.replace(old,new)
sub('import math\nfrom pathlib import Path', 'import math\nimport os\nimport stat\nfrom fractions import Fraction\nfrom pathlib import Path')
sub("                    'senior_reviewer', 'companion', 'investigator', 'archivist'})", "                    'senior_reviewer', 'companion', 'investigator', 'archivist'})\nPATCH_OWNERS = frozenset({'main', 'simple_executor', 'routine_executor',\n                          'default_executor', 'deep_executor', 'senior_executor'})")
sub("    if domain == 'code':\n        guides.append('testing.md')", "    code_change = domain == 'code' and (\n        kind not in {'research', 'writing'} or facts['behavior_change'])\n    if code_change:\n        guides.append('testing.md')")
sub("    if facts.get('tdd_required', False):\n        if domain != 'code'", "    if facts.get('tdd_required', False):\n        if domain == 'code' and 'testing.md' not in guides:\n            guides.append('testing.md')\n        if domain != 'code'")
sub("                  'mandatory_gates_pending'}, {'limit'})", "                  'mandatory_gates_pending'}, {'limit', 'open_workers'})")
sub("    gates = _boolean(facts['mandatory_gates_pending'])\n    envelope_action = None", "    gates = _boolean(facts['mandatory_gates_pending'])\n    opened = facts.get('open_workers')\n    if opened is not None:\n        _count(opened, 128)\n    envelope_action = None")
sub("        remaining = limit['maximum'] - limit['spent'] - limit['committed']", "        # Compare the supplied decimal values exactly. Binary subtraction can\n        # reject a fitting 0.1 + 0.2 budget or erase a small real overrun.\n        remaining = (Fraction(str(limit['maximum'])) - Fraction(str(limit['spent']))\n                     - Fraction(str(limit['committed'])))")
sub("        elif limit['next_estimate'] > remaining:", "        elif Fraction(str(limit['next_estimate'])) > remaining:")
sub("    elif slots is None:\n        action = 'inspect_capacity'", "    elif slots is None or ('open_workers' in facts and opened is None):\n        action = 'inspect_capacity'")
sub("        workers = min(requested, slots, ready, ceiling)", "        workers = min(requested, slots, ready, max(0, ceiling - (opened or 0)))")
sub("    return _result(action=action, max_new_workers=workers, cost_verified=False,", "    return _result(action=action, max_new_workers=workers, cost_verified=False,\n                   open_workers=opened,\n                   limit_scope='total_open_workers' if opened is not None else 'new_batch_only',")
sub('def recovery(facts: dict) -> dict:', '''def _repair_window(facts: dict) -> tuple[int, str | None, bool]:
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


def recovery(facts: dict) -> dict:''')
sub("                  'authority_needed', 'budget_exhausted'})", "                  'authority_needed', 'budget_exhausted'}, {'replan'})")
sub("    if facts['budget_exhausted']:\n        action = 'checkpoint'", "    remaining, replan_ref, fresh_replan = _repair_window(facts)\n    if facts['budget_exhausted']:\n        action = 'checkpoint'")
sub("    elif facts['failed_fixes'] >= 3 or facts['repair_rounds'] >= 3:\n        action = 'replan'\n    elif facts['same_defect_no_progress']:", "    elif remaining == 0:\n        action = 'replan'\n    elif facts['same_defect_no_progress'] and not fresh_replan:")
sub("    elif not facts['new_evidence']:\n        action = 'investigate'\n    else:\n        action = 'bounded_fix'", "    elif not facts['new_evidence']:\n        action = 'investigate'\n    elif owner not in PATCH_OWNERS:\n        action = 'assign_implementation'\n    else:\n        action = 'bounded_fix'")
sub("                   failed_fixes=facts['failed_fixes'], repair_rounds=facts['repair_rounds'],", "                   failed_fixes=facts['failed_fixes'], repair_rounds=facts['repair_rounds'],\n                   remaining_attempts=remaining, replan_ref=replan_ref,")
sub('def main(argv=None) -> int:', '''def _read_input(path: Path) -> bytes:
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


def main(argv=None) -> int:''')
sub("        if args.input.is_symlink() or not args.input.is_file():\n            raise DeliveryError('Input must be a regular file, not a symlink')\n        with args.input.open('rb') as stream:\n            raw = stream.read(MAX_INPUT_BYTES + 1)\n        if len(raw) > MAX_INPUT_BYTES:\n            raise DeliveryError('Input exceeds size limit')", "        raw = _read_input(args.input)")
sub("    except (OSError, ValueError, TypeError, RecursionError, OverflowError) as exc:", "    except (OSError, ValueError, RecursionError) as exc:")
compile(s,str(p),'exec')
b=s.encode()
assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()=='b79ce1249f5eed6eb5410e381a31f81fee3cb093','Does not match locally tested source'
p.write_text(s)
