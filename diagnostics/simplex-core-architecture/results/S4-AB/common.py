"""S4-AB offline admission helpers. Importing launches no process."""
from pathlib import Path
import hashlib,json,os,sys,subprocess,time,math
D=Path(__file__).resolve().parent;R=D.parents[3]
OUT=R/'.superpowers/simplex-core-architecture/S4-AB/qualification-1'
WRAPPER=Path('/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh')
GROUPS={75907, 71824, 71826, 156956, 156957, 60706, 52772, 60708, 52774, 64420, 64422, 89395, 89399, 49081, 49084, 63808, 160834, 160835, 76742, 63815, 84681, 76746, 90313, 23249, 84689, 90323, 23257, 128482, 128483, 53479, 53481, 75902}
FINAL_NAMES=('required-paths.json',)
def require(ok,message):
 if not ok:raise ValueError(message)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):
 p=Path(p);tmp=p.with_name(p.name+'.pending')
 with tmp.open('x') as f:json.dump(x,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 os.link(tmp,p);tmp.unlink()
def command():
 return ['/bin/bash',str(WRAPPER),'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+str(R),str(D/'driver.jl'),str(OUT)]

def guard_command():return [sys.executable,str(D/'guard.py'),'run',str(D/'launch-pins.json'),str(OUT),'--seconds','120','--',*command()]
def refs():
 return {str(p):subprocess.check_output(['git','-C',str(p),'rev-parse','HEAD'],text=True).strip() for p in (R,Path('/home/jspitz/JSimplex.jl'))}
def absent(extra=()):
 groups=GROUPS|set(extra);matches=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   s=(p/'stat').read_text();f=s[s.rindex(')')+2:].split();comm=(p/'comm').read_text().strip()
   if int(f[2]) in groups or int(f[3]) in groups or comm.lower().startswith('julia'):
    matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
  except FileNotFoundError:pass
 return dict(boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),groups=sorted(groups),matches=matches)
def manifest_ok(pins,required,hashfn=sha):
 try:
  inv=pins['inventory']
  return (pins['trees']==[] and pins['inputs']==[] and set(pins['files'])==set(inv) and set(required).issubset(inv) and
    all(inv[p]['sha256']==h for p,h in required.items()) and
    all(hashfn(p)==v['sha256'] and str(Path(p).resolve(strict=True))==v['resolved'] for p,v in inv.items()))
 except (KeyError,TypeError,OSError):return False
def allowance_ok(a,pin_hash,current_refs,hashfn=sha):
 try:
  mandatory={str(D/n) for n in (*FINAL_NAMES,'common.py','guard.py','launcher.py','audit.py','plan.md','authorization.json','oracle.py','launch-pins.json','numerical-review.md')}|{str(D/'driver.jl'),str(D/'candidate-methods.jl')}
  return (a['accepted'] is True and a['numerical_allowance'] is True and a['unresolved_findings']==[] and
   type(a['attempts']) is int and a['attempts']==1 and a['stage']=='S4-AB-qualification-1' and
   type(a['human_authorization']) is str and bool(a['human_authorization'].strip()) and
   a['refs']==current_refs and a['command']==command() and a['output']==str(OUT) and a['pins_sha256']==pin_hash and
   mandatory.issubset(a['sha256']) and a['sha256'][str(D/'launch-pins.json')]==pin_hash and
   all(hashfn(p)==h for p,h in a['sha256'].items()))
 except (KeyError,TypeError,OSError):return False
def terminal_ok(p):
 try:
  t=p['elapsed_including_launch'];m=p['terminal_memory']
  return (p['reason']=='exit0' and type(p['returncode']) is int and p['returncode']==0 and p['pins_unchanged'] is True and
   type(t) in (int,float) and math.isfinite(t) and 0<=t<=120 and
   type(m['available_kib']) is int and m['available_kib']>=6*1024**2 and type(m['swap_used_kib']) is int and 0<=m['swap_used_kib']<=1024**2)
 except (KeyError,TypeError):return False

from oracle import raw_ok
