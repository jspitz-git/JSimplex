from pathlib import Path
import json,hashlib,os,time,subprocess
E=Path(__file__).resolve().parent;D=E.with_name(E.name+'-HARNESS');R=D.parents[3];RUN=D/'runs/red1800';O=D/'outers/red1800'
def rd(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for x in iter(lambda:f.read(1048576),b''):h.update(x)
 return h.hexdigest()
def save(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')
s=rd(RUN/'sealed.json');v=rd(E/'independent-admission-check-v2.json');assert v['all_passed'] is True and v['count']==3467
assert sha(RUN/'sealed.json')==v['sealed_sha256']
assert set(p.name for p in RUN.iterdir())=={'config.json','host.json','sealed.json'}
assert set(p.name for p in O.iterdir())=={'outer-ready.json'}
for n,rec in s['inventory'].items():assert rec=={'resolved':str(Path(n).resolve(strict=True)),'sha256':sha(n)},n
paths=set(s['files'])
for t in s['trees']:
 root=Path(t);assert root.is_dir() and not root.is_symlink()
 for p in root.rglob('*'):
  assert not (p.is_symlink() and (p.is_dir() or not p.exists()))
  if p.is_file():paths.add(str(p))
assert paths==set(s['inventory'])
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();ident=s['outer_identity'];groups=set(s['groups']);members=[];bad=[];unreadexe=[];unreadid=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  f=(p/'stat').read_text().rsplit(')',1)[1].split();cmd=(p/'cmdline').read_bytes();comm=(p/'comm').read_text().strip();exe=''
  try:exe=str((p/'exe').resolve(strict=True))
  except PermissionError:unreadexe.append(int(p.name))
  except FileNotFoundError:pass
  row=dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),boot_id=boot,command=cmd.replace(b'\0',b' ').decode(errors='replace'))
  if row['pgid'] in groups or row['sid'] in groups or any(Path(z).name.lower().startswith('julia') for z in [comm,cmd.split(b'\0')[0].decode(errors='replace'),exe]):bad.append(row)
  if row['pgid']==ident['pgid'] or row['sid']==ident['sid']:members.append(row)
 except (FileNotFoundError,ProcessLookupError):pass
 except PermissionError:unreadid.append(int(p.name))
assert bad==[] and unreadid==[] and members==[ident] and boot==s['boot_id']
env=rd(D/'environment.json');oe=dict(x.split(b'=',1) for x in Path('/proc/214974/environ').read_bytes().split(b'\0') if b'=' in x)
assert {k:oe.get(k.encode(),b'').decode() if k.encode() in oe else None for k in env}==env
assert str(Path('/proc/214974/cwd').resolve())==str(R)
mem={ln.split(':')[0]:int(ln.split()[1]) for ln in Path('/proc/meminfo').read_text().splitlines()};memory=dict(available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree'])
assert memory['available_kib']>=6*1024**2 and memory['swap_used_kib']<=1024**2
q=lambda *a:subprocess.check_output(['git',*a],cwd=R,text=True).strip()
assert q('rev-parse','HEAD')==s['head'] and q('rev-parse','master')==s['master'] and not q('diff','--name-only') and not q('diff','--cached','--name-only')
remote=q('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture');assert set(remote.splitlines())=={s['head']+'\trefs/heads/codex/simplex-core-architecture',s['master']+'\trefs/heads/master'}
final=dict(all_passed=True,time=time.time(),sealed_sha256=sha(RUN/'sealed.json'),inventory_entries_rehashed=len(paths),outer_identity=ident,groups_checked=len(groups),matches=bad,unreadable_identity_pids=unreadid,unreadable_exe_pids=unreadexe,memory=memory,remote=remote,scope='Final independent exact admission publication checks; no launch or release')
save(E/'admission-publication-check.json',final)
names=['independent-admission-check.py','independent-admission-check-failure.json','independent-admission-check-v2.py','independent-admission-check-v2.json','admission-review.md','admission-publication.py','admission-publication-check.json']
evidence={str(E/n):sha(E/n) for n in names}
bound={n:s['inventory'][n]['sha256'] for n in s['files']};bound[str(RUN/'sealed.json')]=sha(RUN/'sealed.json')
receipt=dict(accepted=True,findings=[],scope='BG blocked typed RED repeat exact-run admission',phase='red1800',pins_sha256=sha(RUN/'sealed.json'),sha256=bound,evidence_sha256=evidence)
save(RUN/'admission.json',receipt)
print(json.dumps(dict(accepted=True,scope=receipt['scope'],phase='red1800',seal_sha256=receipt['pins_sha256'],admission_sha256=sha(RUN/'admission.json'),bindings=len(bound),supplementary=len(evidence),memory=memory,admission=str(RUN/'admission.json'))))
