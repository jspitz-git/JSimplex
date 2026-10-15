"""New finalization helpers; no numerical execution or historical auditor calls."""
from pathlib import Path
import json,hashlib,subprocess,time
Q=Path(__file__).resolve().parent;R=Q.parents[3];PREV=Q.parent/'NATIVE-PIVOT-PREPARATION'
STATUS=R/'diagnostics/simplex-core-architecture/STATUS.md';ROAD=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
HEAD='294d4435e888577d90533b50c3c44da6702976e6';MASTER='6f68e24e8ddac42b948da8fcc2d636c010751194'
def require(v,m):
 if not v:raise RuntimeError(m)
def rd(p):return json.loads(Path(p).read_text())
def save(p,v):
 with Path(p).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def path(n):return Path(n) if Path(n).is_absolute() else R/n
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True).strip()
def bindings(z):return all(sha(path(n))==h for n,h in z['sha256'].items())
def host():
 old=rd(Q/'host.json');groups=old['groups'];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[];unreadable=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   z=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip();exe=''
   try:exe=str((p/'exe').resolve(strict=True))
   except PermissionError:unreadable.append(int(p.name))
   except FileNotFoundError:pass
   if int(z[2]) in groups or int(z[3]) in groups or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):
    matches.append(dict(pid=int(p.name),pgid=int(z[2]),sid=int(z[3]),start_ticks=int(z[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'),comm=comm,exe=exe,boot_id=boot))
  except (FileNotFoundError,ProcessLookupError):pass
 return dict(time=time.time(),boot_id=boot,groups=groups,matches=matches,unreadable_exe_pids=unreadable,scope='All process stat/comm and readable exe; inaccessible system exe symlinks are a visibility limit',head=git('rev-parse','HEAD'),master=git('rev-parse','master'))
def verify_host(h):
 require(not h['matches'],'Prior groups/sessions or Julia present')
 require(h['head']==HEAD and h['master']==MASTER,'Unexpected refs')
 require(h['boot_id']==rd(Q/'host.json')['boot_id'],'Boot changed')
