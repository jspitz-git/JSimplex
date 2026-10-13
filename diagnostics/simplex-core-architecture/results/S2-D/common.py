"""S2-D offline-prepared admission; importing this module launches nothing."""
from pathlib import Path
import hashlib,json,os,sys,subprocess,time,math
D=Path(__file__).resolve().parent;R=D.parents[3];C=D.parent/'S2-C';OVERLAY=D/'overlay'
OUT=R/'.superpowers/simplex-core-architecture/S2-D/qualification-1'
W=Path('/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh')
RUNTIME=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/bin/julia')
GROUPS={23249,23257,49081,49084,52772,52774,53479,53481,60706,60708,63808,63815,64420,64422,71824,71826,75902,75907,76742,76746,84681,84689,89395,89399,90313,90323}
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
def command():return ['/bin/bash',str(W),'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+str(OVERLAY),str(D/'driver.jl'),str(OUT/'raw')]
def guard_command():return [sys.executable,str(D/'guard.py'),'run',str(D/'launch-pins.json'),str(OUT),'--seconds','180','--',*command()]
def absent(extra=()):
 matches=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   s=(p/'stat').read_text();f=s[s.rindex(')')+2:].split();comm=(p/'comm').read_text().strip()
   if int(f[2]) in GROUPS|set(extra) or int(f[3]) in GROUPS|set(extra) or comm.lower().startswith('julia'):
    matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
  except FileNotFoundError:pass
 return dict(boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),matches=matches,groups=sorted(GROUPS|set(extra)))
def current_refs():return {str(p):subprocess.check_output(['git','-C',str(p),'rev-parse','HEAD'],text=True).strip() for p in (R,Path('/home/jspitz/JSimplex.jl'))}
def manifest_ok(pins,requirements,hashfn=sha):
 try:
  inv=pins['inventory'];required=set(requirements)|{str(D/'required-paths.json')}
  return (required.issubset(inv) and set(pins['files'])==set(inv) and pins['trees']==[] and pins['inputs']==[] and
    all(inv[p]['sha256']==h for p,h in requirements.items()) and
    all(hashfn(p)==v['sha256'] and str(Path(p).resolve(strict=True))==v['resolved'] for p,v in inv.items()))
 except (KeyError,TypeError,OSError):return False

def allowance_valid(a,pin_hash,refs,hashfn=sha):
 try:
  mandatory={str(D/n) for n in ('admission.md','driver.jl','common.py','launcher.py','audit.py','guard.py','fixtures.toml','budget.json','required-paths.json','admission-pins.json','review.md','reviewer-check.json','launch-pins.json')}
  return (a.get('accepted') is True and a.get('numerical_allowance') is True and a.get('unresolved_findings')==[] and
   type(a.get('attempts')) is int and a['attempts']==1 and a.get('stage')=='S2-D-qualification-1' and
   a.get('command')==command() and a.get('output')==str(OUT) and a.get('refs')==refs and
   a.get('pins_sha256')==pin_hash and mandatory.issubset(a['sha256']) and
   a['sha256'][str(D/'launch-pins.json')]==pin_hash and all(hashfn(p)==h for p,h in a['sha256'].items()))
 except (KeyError,TypeError,OSError):return False

def terminal_ok(p):
 try:
  t=p['elapsed_including_launch'];m=p['terminal_memory']
  return (p['reason']=='exit0' and type(p['returncode']) is int and p['returncode']==0 and p['pins_unchanged'] is True and
   type(t) in (int,float) and math.isfinite(t) and 0<=t<=180 and
   type(m['available_kib']) is int and m['available_kib']>=6*1024**2 and
   type(m['swap_used_kib']) is int and 0<=m['swap_used_kib']<=1024**2)
 except (KeyError,TypeError):return False
