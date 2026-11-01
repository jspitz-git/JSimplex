"""Bound guard housekeeping as well as Julia. Definitions only on import."""
from pathlib import Path
from types import SimpleNamespace
import json,os,signal,subprocess,time
import guard_reviewed as guard

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
    if not p.exists():raise ValueError('startup identity unavailable; parent-death gate prevents Julia; cleanup not certified')
    v=json.loads(p.read_text())['child']
    try:a=guard.process_identity(v['pid'])
    except (FileNotFoundError,ProcessLookupError):
        if guard.active_group_members(v['pid']):raise ValueError('leader absent with surviving group/session; cleanup incomplete')
        return None
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

STABLE_KEYS=('pid','pgid','sid','start_ticks','boot_id')

def same_process(a,b):
    return all(a[k]==b[k] for k in STABLE_KEYS)

def capture_started_identity(p,command,started,limit,record):
    # Popen owns an unreaped child. Never poll/reap while acquiring identity.
    expected=' '.join(command)+' '
    deadline=min(time.monotonic()+2.0,started+limit-6.0)
    initial=None
    while time.monotonic()<deadline:
        try:
            current=guard.process_identity(p.pid)
            if initial is None:
                initial=current;record['guard_initial_identity']=current
            if not same_process(initial,current):raise ValueError('startup process identity changed')
            if current['pid']!=p.pid or current['pgid']!=p.pid or current['sid']!=p.pid:
                raise ValueError('startup process not owned session leader')
            if current['command']==expected and current['command']:
                confirm=guard.process_identity(p.pid)
                if same_process(initial,confirm) and confirm['command']==expected and time.monotonic()<deadline:
                    return confirm
        except (FileNotFoundError,ProcessLookupError):
            pass
        time.sleep(0.001)
    raise TimeoutError('actual nonempty exec command not captured within startup/shared deadline')

def signal_owned_startup(p,fd,initial,sig,record):
    # This narrow failure cleanup uses held pidfd + unreaped direct Popen owner.
    # It does not replace the strict command-bearing identity after startup.
    if p.returncode is not None:return False
    try:
        a=guard.process_identity(p.pid)
        b=guard.process_identity(p.pid)
        if not same_process(a,b):return False
        if initial is not None and not same_process(initial,b):return False
        if b['pid']!=p.pid or b['pgid']!=p.pid or b['sid']!=p.pid:return False
        record['guard_cleanup_identity']=b
        if fd is not None:signal.pidfd_send_signal(fd,sig,None,0)
        else:os.kill(p.pid,sig) # still unreaped Popen-owned PID; no PID reuse
        return True
    except (FileNotFoundError,ProcessLookupError):return False

def run(command,log,out,started,limit):
    record=dict(soft_timeout=False,hard_timeout=False,child_kill=False,guard_term=False,guard_kill=False,abnormal_cleanup_attempted=False,child_cleanup_attempted=False)
    p=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    fd=None;identity=None
    try:
        try:
            fd=os.pidfd_open(p.pid,0)
            identity=capture_started_identity(p,command,started,limit,record)
            record['guard_identity']=identity
        except Exception as e:
            record['startup_error']=repr(e);record['abnormal_cleanup_attempted']=True
            try:record['guard_term']=signal_owned_startup(p,fd,record.get('guard_initial_identity'),signal.SIGTERM,record)
            except Exception as cleanup:record['cleanup_error']=repr(cleanup)
            try:
                p.wait(timeout=max(0.,min(time.monotonic()+0.5,started+limit-2)-time.monotonic()))
            except subprocess.TimeoutExpired:
                try:record['guard_kill']=signal_owned_startup(p,fd,record.get('guard_initial_identity'),signal.SIGKILL,record)
                except Exception as cleanup:record['cleanup_error']=repr(cleanup)
                try:p.wait(timeout=max(0.,started+limit-time.monotonic()))
                except subprocess.TimeoutExpired:record['cleanup_error']='startup guard not reaped by shared deadline'
            record['returncode']=p.returncode
            record['child_cleanup_attempted']=True
            if (Path(out)/'current.json').exists():
                try:record['child_kill']=kill_child(out)
                except Exception as cleanup:record['cleanup_error']=repr(cleanup)
            else:
                # Guard died before publication; entry's parent-death gate forbids Julia.
                record['startup_child_not_published']=True
            record['elapsed_seconds']=time.monotonic()-started
            record['accepted']=False
            return record
        try:
            record['returncode']=p.wait(timeout=max(0.,started+limit-6-time.monotonic()))
        except subprocess.TimeoutExpired:
            record['soft_timeout']=True;record['guard_term']=send_one(identity,signal.SIGTERM)
            try:record['returncode']=p.wait(timeout=max(0.,started+limit-2-time.monotonic()))
            except subprocess.TimeoutExpired:
                record['hard_timeout']=True;record['child_cleanup_attempted']=True
                try:record['child_kill']=kill_child(out)
                except Exception as e:record['cleanup_error']=repr(e)
                record['guard_kill']=send_one(identity,signal.SIGKILL)
                try:record['returncode']=p.wait(timeout=max(0.,started+limit-time.monotonic()))
                except subprocess.TimeoutExpired:record['returncode']=None;record['cleanup_error']='guard not reaped by inclusive deadline'
        if record.get('returncode')!=0 or record['soft_timeout'] or 'cleanup_error' in record:
            record['abnormal_cleanup_attempted']=True
            if not record['child_cleanup_attempted']:
                if time.monotonic()>=started+limit:record['cleanup_error']='no global time remains for abnormal-exit cleanup'
                else:
                    record['child_cleanup_attempted']=True
                    try:record['child_kill']=kill_child(out) or record['child_kill']
                    except Exception as e:record['cleanup_error']=repr(e)
        record['elapsed_seconds']=time.monotonic()-started
        record['accepted']=record['returncode']==0 and not record['soft_timeout'] and not record['hard_timeout'] and 'cleanup_error' not in record and record['elapsed_seconds']<=limit
        return record
    finally:
        if fd is not None:os.close(fd)
