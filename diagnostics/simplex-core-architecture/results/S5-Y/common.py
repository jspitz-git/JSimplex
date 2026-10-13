from pathlib import Path
import hashlib,json,time,sys,subprocess,math,os
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');M=Path('/home/jspitz/JSimplex.jl');H=Path(__file__).resolve().parent;X=H.parent/'S5-X'
B=R/'.superpowers/simplex-core-architecture/S5-Y/qualification-1';G=H/'guard.py';C=X/'candidate.jl'
EXPECTED='5c941e86131ed503149de5a47ac46fc7665507861a25ec16654b6711968fdf18'
REFS={str(R):'f45899f3b06c819943498f9906c8ffefca31c15a',str(M):'2b546e946ddb7fdb6c0092df9cc19f566e301aa2'}
W=Path('/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh')
PLAN=R/'docs/superpowers/plans/2026-10-13-crash-fallback-observer-qualification.md'
GROUPS={23249,23257,49081,49084,52772,52774,53479,53481,60706,60708,63808,63815,64420,64422,71824,71826,75902,75907,76742,76746}
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
def absent(extra=()):
 matches=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   s=(p/'stat').read_text();v=s[s.rindex(')')+2:].split()
   if int(v[2]) in GROUPS|set(extra) or (p/'comm').read_text().strip()=='julia':matches.append(dict(pid=int(p.name),pgid=int(v[2]),start_ticks=int(v[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
  except FileNotFoundError:pass
 return dict(groups=sorted(GROUPS|set(extra)),matches=matches,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),time_ns=time.time_ns())
def refs():return {str(p):subprocess.check_output(['git','-C',str(p),'rev-parse','HEAD'],text=True).strip() for p in (R,M)}
def command():return ['/bin/bash',str(W),'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+str(R),str(C),str(B/'raw.toml')]
def guard_command():return [sys.executable,str(G),'run',str(H/'pins.json'),str(B),'--seconds','120','--',*command()]
def essentials():return [C,G,W,W.parents[3]/'.superpowers/basis-chain-cost/julia.sh',PLAN,H/'common.py',H/'launcher.py',H/'audit.py',H/'schema.json',H/'admission.md',H/'entry.json',H/'host.json',H/'prepare.py',H/'prepare_guard.py',H/'guard-source.json',H/'failure_tests.py',H/'failure-tests.json']
def required():
 req=read(H/'required-paths.json')['sha256'];assert set(map(str,essentials())).issubset(req) and req[str(C)]==EXPECTED;return req
TREES={str(p/d) for p in (R,M) for d in ('src','test')}
def inventory_ok(pins):
 req=required();inv=pins['inventory']
 return set(req)|{str(H/'required-paths.json')}<=set(inv) and all(inv[k]['sha256']==v for k,v in req.items()) and all(sha(k)==v['sha256'] and str(Path(k).resolve(strict=True))==v['resolved'] for k,v in inv.items()) and set(pins['trees'])==TREES and all({str(p) for p in Path(t).rglob('*') if p.is_file()}=={k for k in inv if Path(k).is_relative_to(t)} for t in TREES)
def accepted(record=None,hashfn=sha,current=None):
 a=read(H/'acceptance.json') if record is None else record
 required_paths=set(map(str,essentials()))|{str(H/n) for n in ('required-paths.json','admission-pins.json','admission-review.md')}
 review=(H/'admission-review.md').read_text()
 return a.get('accepted') is True and a.get('unresolved_findings')==[] and a.get('root')==str(R) and a.get('refs')==(refs() if current is None else current)==REFS and a.get('command')==command() and a.get('candidate_sha256')==EXPECTED and required_paths<=set(a.get('sha256',{})) and all(hashfn(k)==v for k,v in a['sha256'].items()) and 'Verdict: ACCEPTED' in review and 'Unresolved findings: []' in review
def launch_ok():
 b=read(H/'launch-binding.json');inv=read(H/'pins.json')['inventory'];extra={str(H/n) for n in ('acceptance.json','admission-review.md','admission-pins.json')}
 return accepted() and extra<=set(inv) and all(sha(k)==inv[k]['sha256'] for k in extra) and b.get('command')==command() and b.get('refs')==refs()==REFS and b.get('accepted') is True and {str(H/n) for n in ('pins.json','acceptance.json','launcher.py','audit.py')}<=set(b.get('sha256',{})) and all(sha(k)==v for k,v in b['sha256'].items())
def terminal_ok(p):
 t=p.get('elapsed_including_launch');return type(t) in (int,float) and math.isfinite(t) and 0<=t<=120 and p.get('reason')=='exit0' and type(p.get('returncode')) is int and p['returncode']==0 and p.get('pins_unchanged') is True

def invocation_ok(inv,res,log,p,pin):
 return type(inv.get('returncode')) is int and inv['returncode']==0 and 'error' not in inv and inv.get('command')==guard_command() and res.get('command')==command() and res.get('pins_sha256')==pin and res.get('output')==str(B) and res.get('launch_binding_sha256')==sha(H/'launch-binding.json') and log==p and all(type(x) is int for x in (res.get('time_ns'),inv.get('started_ns'),inv.get('ended_ns'))) and res['time_ns']<=inv['started_ns']<=inv['ended_ns'] and inv['host']['boot_id']==p['runner']['boot_id'] and inv['host']['matches']==[]

def invoke(cmd,log_path,record_path,cwd,host):
 inv=dict(command=cmd,started_ns=time.time_ns(),host=host,returncode=None)
 try:
  assert not host['matches']
  with Path(log_path).open('x') as log:
   run=subprocess.run(cmd,cwd=cwd,stdout=log,stderr=subprocess.STDOUT);inv['returncode']=run.returncode
 except BaseException as error:inv['error']=repr(error)
 finally:inv['ended_ns']=time.time_ns();dump(record_path,inv)
 return inv
