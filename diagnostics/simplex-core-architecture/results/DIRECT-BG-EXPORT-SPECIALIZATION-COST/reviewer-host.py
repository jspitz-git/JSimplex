"""Independent read-only host/ref snapshot. No Julia or runtime admission."""
from pathlib import Path
import json,subprocess,time,os
D=Path(__file__).resolve().parent;R=D.parents[3]
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True).strip()
groups=set(json.loads((D/'host-entry.json').read_text())['groups']);matches=[];unreadable=[];unreadable_exe=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  fields=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip();cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace');exe=''
  try:exe=str((p/'exe').resolve(strict=True))
  except PermissionError:unreadable_exe.append(int(p.name))
  except FileNotFoundError:pass
  if int(fields[2]) in groups or int(fields[3]) in groups or any(Path(x).name.lower().startswith('julia') for x in [comm,cmd.split(' ',1)[0],exe]):matches.append(dict(pid=int(p.name),pgid=int(fields[2]),sid=int(fields[3]),start_ticks=int(fields[19]),command=cmd,comm=comm,exe=exe))
 except (FileNotFoundError,ProcessLookupError):pass
 except PermissionError:unreadable.append(int(p.name))
record=dict(time=time.time(),head=git('rev-parse','HEAD'),master=git('rev-parse','master'),branch=git('branch','--show-current'),remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'),tracked_worktree=git('diff','--name-only'),tracked_index=git('diff','--cached','--name-only'),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),groups=sorted(groups),matches=matches,unreadable_identity_pids=unreadable,unreadable_exe_pids=unreadable_exe,scope='All265PGIDs AND sessions/stat/comm/argv0/readable exe; inaccessible exe links explicitly retained')
record['all_passed']=record['head']=='7fd611127d3e3366c25ddb531768c3610548f303' and record['master']=='26e2291745999f485a74f643298ca997d65c7205' and not record['tracked_worktree'] and not record['tracked_index'] and not matches and not unreadable and record['head']+'\trefs/heads/codex/simplex-core-architecture' in record['remote'] and record['master']+'\trefs/heads/master' in record['remote']
with (D/'reviewer-host.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in record.items() if k!='groups'}))
