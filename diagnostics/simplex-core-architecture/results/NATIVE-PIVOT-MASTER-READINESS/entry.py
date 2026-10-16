from pathlib import Path
import json,hashlib,subprocess,time
Q=Path(__file__).resolve().parent;R=Q.parents[3];B=Q.parent
HEAD='4c2198feb82d273fa71056f9c3cedc678549a7e0';MASTER='6f68e24e8ddac42b948da8fcc2d636c010751194'
def require(v,m):
 if not v: raise RuntimeError(m)
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,o):
 with p.open('x') as f:json.dump(o,f,indent=2);f.write('\n')
groups=json.loads((B/'NATIVE-PIVOT-INTEGRATION-180-QUALIFICATION/closure-host.json').read_text())['groups'];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[];unreadable=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip();exe=''
  try:exe=str((p/'exe').resolve(strict=True))
  except PermissionError:unreadable.append(int(p.name))
  except FileNotFoundError:pass
  if int(s[2]) in groups or int(s[3]) in groups or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):
   matches.append(dict(pid=int(p.name),pgid=int(s[2]),sid=int(s[3]),start_ticks=int(s[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'),comm=comm,exe=exe,boot_id=boot))
 except (FileNotFoundError,ProcessLookupError):pass
host=dict(time=time.time(),boot_id=boot,groups=groups,matches=matches,unreadable_exe_pids=unreadable,scope='All process stat/comm and readable exe; inaccessible system exe symlinks are a visibility limit',head=git('rev-parse','HEAD'),master=git('rev-parse','master'),remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'),status=git('status','--porcelain'),entry_sha256=sha(Path(__file__)))
save(Q/'host.json',host)
require(not matches,'Processes present');require(host['head']==HEAD and host['master']==MASTER,'Refs changed');require(HEAD+'\trefs/heads/codex/simplex-core-architecture' in host['remote'] and MASTER+'\trefs/heads/master' in host['remote'],'Remote mismatch');require(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'Tracked changes')
for name,src in [('STATUS.md.before-readiness',R/'diagnostics/simplex-core-architecture/STATUS.md'),('roadmap.md.before-readiness',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md')]:
 with (Q/name).open('xb') as f:f.write(src.read_bytes())
print('Fresh refs / 220 groups AND sessions / no Julia PASS; continuation bytes preserved')
