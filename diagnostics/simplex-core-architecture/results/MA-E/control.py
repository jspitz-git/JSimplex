"""Offline-testable serial admission helpers; import has no process side effects."""
from pathlib import Path
import hashlib,json,os,sys,subprocess,time,math
D=Path(__file__).resolve().parent;R=D.parents[3]
OUT=R/'.superpowers/simplex-core-architecture/MA-F/attempt-1'
WRAPPER=Path('/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh')
def require(x,m):
 if not x:raise ValueError(m)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def save(p,x):
 p=Path(p);t=p.with_name(p.name+'.pending')
 with t.open('x') as f:json.dump(x,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 os.link(t,p);t.unlink()
def stages():
 result=[dict(id='red',stage='red',side='reference',seconds=30),dict(id='qualification',stage='qualification',side='candidate',seconds=120)]
 for pair in range(1,11):
  for side in (('reference','candidate') if pair%2 else ('candidate','reference')):
   result.append(dict(id=f'pair{pair:02d}-{side}',stage='cost',side=side,seconds=60,pair=pair,phase='warm' if pair<=3 else 'measured'))
 return result
STAGES=stages()
def command(s):return ['/bin/bash',str(WRAPPER),'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+str(D/'overlays'/s['side']),str(D/'driver.jl'),str(D/'configs'/(s['id']+'.toml'))]
def host(groups):
 matches=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   t=(p/'stat').read_text();f=t[t.rfind(')')+2:].split();comm=(p/'comm').read_text().strip()
   if int(f[2]) in groups or int(f[3]) in groups or comm.lower().startswith('julia'):matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
  except (FileNotFoundError,ProcessLookupError):pass
 return dict(boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),groups=sorted(groups),matches=matches)
def refs():return {str(p):subprocess.check_output(['git','-C',str(p),'rev-parse','HEAD'],text=True).strip() for p in (R,Path('/home/jspitz/JSimplex.jl'))}
def remaining(start,cost_start,now,s):
 require(all(type(x) in (int,float) and math.isfinite(x) for x in (start,now)) and now>=start,'clock')
 vals=[s['seconds'],750-(now-start)]
 if s['stage']=='cost':
  require(cost_start is not None and start<=cost_start<=now,'cost clock');vals.append(600-(now-cost_start))
 limit=min(vals);require(limit>0,'deadline exhausted');return limit

def memory_ok(m):return type(m['available_kib']) is int and m['available_kib']>=6*1024**2 and type(m['swap_used_kib']) is int and 0<=m['swap_used_kib']<=1024**2

def terminal(p,limit,cmd,pinhash):
 try:return p['reason']=='exit0' and type(p['returncode']) is int and p['returncode']==0 and p['command']==cmd and p['pins_sha256']==pinhash and p['pins_unchanged'] is True and type(p['elapsed_including_launch']) in (int,float) and math.isfinite(p['elapsed_including_launch']) and 0<=p['elapsed_including_launch']<=limit and memory_ok(p['terminal_memory'])
 except (KeyError,TypeError,ValueError):return False

def inventory_ok(pins,required,hashfn=sha):
 try:return pins['trees']==pins['inputs']==[] and set(pins['files'])==set(pins['inventory']) and set(required)<=set(pins['inventory']) and all(v['sha256']==hashfn(p) and v['resolved']==str(Path(p).resolve()) for p,v in pins['inventory'].items()) and all(pins['inventory'][p]['sha256']==h for p,h in required.items())
 except (KeyError,TypeError,OSError):return False

def seal_ok(a,current_refs,pinhash,hashfn=sha):
 try:
  mandatory={str(D/n) for n in ('admission-pins.json','required-paths.json','review.json','review.md','driver.jl','kernels.jl','auditor.py','control.py','guard.py','launcher.py','seal.py','admission.md')}
  return (a['accepted'] is True and a['stage']=='MA-F-attempt-1' and a['attempts']==1 and a['refs']==current_refs and a['pin_sha256']==pinhash and a['commands']==[command(s) for s in STAGES] and a['output']==str(OUT) and mandatory<=set(a['sha256']) and all(hashfn(p)==h for p,h in a['sha256'].items()))
 except (KeyError,TypeError,OSError):return False
