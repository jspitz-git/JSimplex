"""Owned startup handshake; never executes Julia before identity publication."""
from pathlib import Path
import os,sys,json,time,signal
import guard_reviewed as guard

def require(v,m):
 if not v:raise ValueError(m)
def check_parent(pid,start,boot):
 p=guard.process_identity(pid)
 require(os.getppid()==pid and p['start_ticks']==start and p['boot_id']==boot,'guard parent changed')
 return p

def main(args):
 require(len(args)>=8 and args[5]=='--','gate arguments')
 out=Path(args[0]);pid=int(args[1]);ticks=int(args[2]);boot=args[3];deadline=float(args[4]);command=args[6:]
 require(command and time.monotonic()<deadline,'gate deadline/command')
 # Check the signal inherited from guard.child_setup, not merely a promised setting.
 import ctypes
 sig=ctypes.c_int(0)
 result=guard._LIBC.prctl(2,ctypes.cast(ctypes.pointer(sig),ctypes.c_void_p).value,0,0,0)
 require(result==0 and sig.value==signal.SIGKILL,'parent-death signal missing')
 while True:
  parent=check_parent(pid,ticks,boot)
  require(time.monotonic()<deadline,'gate deadline')
  if (out/'permit.json').is_file():break
  time.sleep(min(.01,max(0.,deadline-time.monotonic())))
 current=json.loads((out/'current.json').read_text());permit=json.loads((out/'permit.json').read_text())
 own=guard.process_identity(os.getpid())
 require(current['runner']==parent and current['child']==own,'published identities')
 require(permit=={'current_sha256':guard.digest(out/'current.json'),'command':command} and current['command']==command,'permit binding')
 guard.atomic_json(out/'gate.json',{'identity':own,'parent':parent,'current_sha256':guard.digest(out/'current.json'),'permit_sha256':guard.digest(out/'permit.json'),'command':command,'parent_death_signal':int(sig.value),'monotonic_ready':time.monotonic()})
 check_parent(pid,ticks,boot);require(time.monotonic()<deadline,'final gate deadline')
 os.execvpe(command[0],command,os.environ)
if __name__=='__main__':main(sys.argv[1:])
