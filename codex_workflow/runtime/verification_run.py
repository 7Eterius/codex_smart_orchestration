#!/usr/bin/env python3
"""Run an explicitly approved verification batch with immutable, private receipts.

Preview is the default. --apply executes argv with the caller's existing rights;
it is NOT a sandbox or an approval bypass. No network/model API, auto-retry, cache,
source repair, snapshot acceptance or automatic hooks. Prefer existing CI receipts.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import signal
import subprocess
import time
import uuid

if __package__:
    from . import candidate
    from .work_contracts import read_json, keys, text, count
else:
    import candidate
    from work_contracts import read_json, keys, text, count

LIMITATION = ('Process and listed-input evidence only. No semantic acceptance, complete dependency '
              'discovery, external-state attestation or global execution lock.')
MAX_OUTPUT = 16 * 1024 * 1024


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def validate(plan):
    keys(plan, {'schema','task','requirement_ref','root','inputs','environment_ref','commands'})
    if type(plan['schema']) is not int or plan['schema']!=1: raise ValueError('Unsupported plan schema')
    for k in ('task','requirement_ref','environment_ref','root'): text(plan[k])
    root=Path(plan['root'])
    if not root.is_absolute() or root.is_symlink() or not root.is_dir(): raise ValueError('Existing absolute root required')
    if not isinstance(plan['inputs'], list) or not plan['inputs']: raise ValueError('Explicit input scopes required')
    for name in plan['inputs']: candidate._relative(name)
    commands=plan['commands']
    if not isinstance(commands, list) or not 1<=len(commands)<=16: raise ValueError('Supply 1-16 approved commands')
    seen=set()
    for c in commands:
        keys(c, {'id','argv','timeout_seconds'}, {'expected_exit'})
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,63}',text(c['id'])) or c['id'] in seen:
            raise ValueError('Command IDs must be unique safe names')
        seen.add(c['id'])
        if not isinstance(c['argv'],list) or not 1<=len(c['argv'])<=128: raise ValueError('Bounded argv required')
        for arg in c['argv']:
            if not isinstance(arg,str) or '\0' in arg or len(arg)>8192: raise ValueError('Invalid argv')
        if not c['argv'][0]: raise ValueError('Missing executable')
        if not 1<=count(c['timeout_seconds'], 14400)<=14400: raise ValueError('Bounded command timeout required')
        code=c.get('expected_exit',0)
        if type(code) is not int or not 0<=code<=255: raise ValueError('Invalid expected exit code')
    return root.resolve(strict=True)


def write_new(path, data):
    fd=os.open(path, os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,'O_NOFOLLOW',0),0o600)
    with os.fdopen(fd,'w',encoding='utf-8') as stream:
        json.dump(data,stream,sort_keys=True,indent=2); stream.write('\n')


def _stop(process):
    # Only the new process group created below, never another worker or caller.
    try: os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError: pass
    try: process.wait(timeout=2)
    except subprocess.TimeoutExpired: pass
    # The direct child may exit while descendants still hold the output pipe.
    # Finish only this created process group, even after the direct child exits.
    try: os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError: pass
    process.wait(timeout=3)


def execute(command, root, log_path):
    started=time.monotonic(); status='completed'; size=0; marker_tail=b''; nested=set()
    fd=os.open(log_path, os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,'O_NOFOLLOW',0),0o600)
    output_hash=hashlib.sha256()
    with os.fdopen(fd,'wb') as log:
        try:
            process=subprocess.Popen(command['argv'],cwd=root,stdin=subprocess.DEVNULL,
                                     stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                                     shell=False,start_new_session=True)
        except OSError as exc:
            return dict(status='launch_error',exit_code=None,error_type=type(exc).__name__,
                        output_complete=False,output_bytes=0,output_sha256=output_hash.hexdigest())
        selector=selectors.DefaultSelector()
        selector.register(process.stdout,selectors.EVENT_READ)
        try:
            while True:
                remaining=command['timeout_seconds']-(time.monotonic()-started)
                if remaining<=0:
                    status='timeout'; _stop(process); break
                events=selector.select(min(remaining,0.2))
                if events:
                    data=os.read(process.stdout.fileno(),65536)
                    if not data:
                        if process.poll() is not None: break
                        time.sleep(min(remaining,0.02)); continue
                    available=MAX_OUTPUT-size
                    kept=data[:available]; log.write(kept); output_hash.update(kept); size+=len(kept)
                    lines=(marker_tail+kept).split(b'\n'); marker_tail=lines.pop()[-4096:]
                    for line in lines:
                        match=re.fullmatch(rb'exit_status=(-?\d{1,6})\s*',line)
                        if match: nested.add(int(match[1]))
                    if len(data)>available:
                        status='output_limit'; _stop(process); break
                elif process.poll() is not None:
                    # Keep draining until EOF. Descendants holding the pipe are bounded by timeout.
                    continue
            if status=='completed': process.wait(timeout=max(.1,command['timeout_seconds']-(time.monotonic()-started)))
        except KeyboardInterrupt:
            status='interrupted'; _stop(process)
        except subprocess.TimeoutExpired:
            status='timeout'; _stop(process)
        except BaseException:
            _stop(process); raise
        finally:
            selector.close(); process.stdout.close()
        match=re.fullmatch(rb'exit_status=(-?\d{1,6})\s*',marker_tail)
        if match: nested.add(int(match[1]))
        code=process.returncode
        conflict=code==0 and any(n!=0 for n in nested)
        return dict(status=status,exit_code=code,expected_exit=command.get('expected_exit',0),
                    elapsed_seconds=round(time.monotonic()-started,3),output_bytes=size,
                    output_sha256=output_hash.hexdigest(),output_complete=status=='completed',
                    embedded_exit_markers=sorted(nested),conflicting_exit_evidence=conflict,
                    expected_process_outcome_observed=status=='completed' and not conflict and code==command.get('expected_exit',0),
                    test_verdict='not_inferred_from_process_exit')


def run(plan, evidence_parent, apply=False):
    root=validate(plan)
    before=candidate.snapshot(root,plan['inputs'])
    parent=evidence_parent.expanduser()
    if not parent.is_dir() or parent.is_symlink(): raise ValueError('Evidence parent must already exist')
    parent=parent.resolve(strict=True)
    for scope in before['scopes']:
        watched=root/scope['path']
        if parent==watched or parent.is_relative_to(watched): raise ValueError('Evidence must be outside watched inputs')
    if not apply:
        return dict(action='preview',commands=len(plan['commands']),candidate=before['fingerprint'],
                    plan_digest=digest(plan),writes=False,limitation=LIMITATION)
    # Cooperative lock for the same plan in the same chosen evidence parent only.
    lock_path=parent/('.smart-check-'+digest(plan)+'.lock')
    fd=os.open(lock_path,os.O_CREAT|os.O_RDWR|getattr(os,'O_NOFOLLOW',0),0o600)
    try:
        import stat
        if not stat.S_ISREG(os.fstat(fd).st_mode) or os.fstat(fd).st_nlink!=1:
            raise ValueError('Unsafe verification lock')
        try: fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            return dict(action='already_running',commands_executed=0,limitation=LIMITATION)
        # Recheck after admission; identity is not a native source lock.
        if not candidate.verify(before)['matched']: raise ValueError('Inputs drifted before execution')
        folder=parent/('smart-check-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:12])
        folder.mkdir(mode=0o700)
        write_new(folder/'candidate.before.json',before)
        write_new(folder/'plan.PRIVATE.json',plan)
        rows=[]; halted=False
        for command in plan['commands']:
            if halted:
                rows.append(dict(id=command['id'],status='not_run')); continue
            log=folder/(command['id']+'.log')
            row=execute(command,root,log); row.update(id=command['id'],log=log.name)
            rows.append(row)
            halted=not row.get('expected_process_outcome_observed',False)
        try:
            after=candidate.snapshot(root,plan['inputs']); write_new(folder/'candidate.after.json',after)
            unchanged=after['fingerprint']==before['fingerprint']
        except (OSError,ValueError): unchanged=False
        outcome='stale_inputs' if not unchanged else 'needs_inspection' if halted else 'expected_process_outcomes_observed'
        receipt=dict(schema=1,task=plan['task'],requirement_ref=plan['requirement_ref'],
                     environment_ref=plan['environment_ref'],plan_digest=digest(plan),
                     candidate=before['fingerprint'],listed_inputs_unchanged=unchanged,
                     outcome=outcome,commands=rows,semantic_acceptance=False,
                     environment_attested=False,limitation=LIMITATION,
                     note='Embedded exit markers are untrusted output hints. Conflicts prevent a clean receipt; no exit code proves test discovery, coverage, freshness of external targets or acceptance.')
        write_new(folder/'receipt.json',receipt)
        return dict(action=outcome,receipt=str(folder/'receipt.json'),commands_executed=sum(r['status']!='not_run' for r in rows),
                    semantic_acceptance=False,limitation=LIMITATION)
    finally:
        os.close(fd)  # Preserve the stable lock inode. Unlinking creates a race between contenders.


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',type=Path,required=True)
    parser.add_argument('--evidence-parent',type=Path,required=True)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args(argv)
    try:
        out=run(read_json(args.plan),args.evidence_parent,args.apply)
        print(json.dumps(out,sort_keys=True))
        return 0 if out['action'] in {'preview','expected_process_outcomes_observed'} else 1
    except (OSError,ValueError,RecursionError) as exc:
        print(json.dumps(dict(action='error',error=str(exc),limitation=LIMITATION)))
        return 2

if __name__=='__main__': raise SystemExit(main())
