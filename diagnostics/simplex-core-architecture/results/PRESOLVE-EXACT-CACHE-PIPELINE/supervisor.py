"""Bound guard housekeeping as well as Julia. Definitions only on import."""
from pathlib import Path
from types import SimpleNamespace
import json,os,signal,subprocess,time
import guard

def send_one(identity,sig,owner=None):
    """An unreaped Popen leader plus pidfd and two identity reads prevent PID reuse."""
    fd=None
    try:
        before=guard.process_identity(identity['pid'])
        if not guard.same_identity(before,identity):return False
        fd=os.pidfd_open(identity['pid'],0)
        after=guard.process_identity(identity['pid'])
        if not guard.same_identity(before,after):return False
        if owner is not None and (not guard.identity_owned(after,owner["pid"]) or not guard.same_identity(owner,guard.process_identity(owner["pid"]))):return False
        signal.pidfd_send_signal(fd,sig,None,0)
        return True
    except (FileNotFoundError,ProcessLookupError):return False
    finally:
        if fd is not None:os.close(fd)

def child_snapshot(out):
    p=Path(out)/'current.json'
    if not p.exists():return None
    v=json.loads(p.read_text())['child']
    try:a=guard.process_identity(v['pid'])
    except (FileNotFoundError,ProcessLookupError):return None
    # exec replaces the wrapper command; bind its current command freshly.
    if any(a[k]!=v[k] for k in ('pid','pgid','sid','start_ticks','boot_id')):raise ValueError('child identity changed')
    if a['pid']!=a['pgid'] or a['pid']!=a['sid']:raise ValueError('child session')
    return a

def kill_child(out):
    a=child_snapshot(out)
    if a is None:return False
    b=guard.process_identity(a['pid'])
    if not guard.same_identity(a,b):raise ValueError('child changed during capture')
    members=[guard.process_identity(pid) for pid in guard.active_group_members(a['pid'])]
    members.sort(key=lambda m:m['pid']==a['pid']) # leader last
    sent=True
    for member in members:
        if not guard.identity_owned(member,a['pid']):raise ValueError('foreign member')
        sent=send_one(member,signal.SIGKILL,owner=a) and sent
    return sent

def run(command,log,out,started):
    record=dict(soft_timeout=False,hard_timeout=False,child_kill=False,guard_term=False,guard_kill=False)
    p=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    identity=guard.process_identity(p.pid);record['guard_identity']=identity
    try:
        record['returncode']=p.wait(timeout=max(0.,started+64-time.monotonic()))
    except subprocess.TimeoutExpired:
        record['soft_timeout']=True;record['guard_term']=send_one(identity,signal.SIGTERM)
        try:record['returncode']=p.wait(timeout=max(0.,started+68-time.monotonic()))
        except subprocess.TimeoutExpired:
            record['hard_timeout']=True
            try:record['child_kill']=kill_child(out)
            except Exception as e:record['cleanup_error']=repr(e)
            record['guard_kill']=send_one(identity,signal.SIGKILL)
            try:record['returncode']=p.wait(timeout=max(0.,started+70-time.monotonic()))
            except subprocess.TimeoutExpired:record['returncode']=None;record['cleanup_error']='guard not reaped by inclusive deadline'
    record['elapsed_seconds']=time.monotonic()-started
    # A timeout is a failed attempt even if signal handling returned status zero.
    record['accepted']=record['returncode']==0 and not record['soft_timeout'] and not record['hard_timeout'] and 'cleanup_error' not in record and record['elapsed_seconds']<=70
    return record
