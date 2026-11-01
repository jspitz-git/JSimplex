from pathlib import Path
import sys,json,time,os,importlib.util,subprocess
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;W=D.parents[2];sys.path.insert(0,str(D/'guard'))
import guard_reviewed as G
import supervisor_reviewed as S
O=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl/diagnostics/direct-ss-local-updates/task4')
s=importlib.util.spec_from_file_location('oldhost',O/'launch-final.py');H=importlib.util.module_from_spec(s);s.loader.exec_module(H)
def read(p):return json.loads(p.read_text())
def require(v,m):
 if not v:raise ValueError(m)
def host():
 require((D/'project/src').is_symlink() and (D/'project/src').resolve(strict=True)==W/'src','exact staged source alias')
 h=H.host(O/'run-1');base=read(D/'host.json');require(h['boot_id']==base['boot_id'],'boot changed');groups=set(base['checked_groups'])|set(h['checked_groups'])
 for p in D.glob('*-run/guard/process.json'):
  d=read(p)
  for k in ('runner','child'):
   a=d.get(k,{})
   if a.get('boot_id')==h['boot_id']:groups.update((a['pgid'],a['sid']))
 for p in Path('/proc').glob('[0-9]*'):
  try:
   a=H.H.identity(p.name);require(a['pgid'] not in groups and a['sid'] not in groups,'old group/session active')
  except (FileNotFoundError,ProcessLookupError):pass
 require(H.H.git(W,'rev-parse','HEAD')==read(D/'runtime.json')['experiment'],'experiment ref changed')
 require(H.H.git(W,'branch','--show-current')=='codex/dual-step-experiment','experiment branch changed')
 h.update(checked_groups=sorted(groups),experiment=H.H.git(W,'rev-parse','HEAD'),no_julia=True);return h

def main():
 mode=sys.argv[1];require(mode in ('qualify','compare'),'mode');cfg=read(D/(mode+'-contract.json'));pins=D/(mode+'-pins.json');review=D/(mode+'-admission.json')
 a=read(review);require(a.get('accepted') is True and a.get('pins_sha256')==G.digest(pins),'exact independently accepted admission');p=read(pins);require(G.pins_match(p),'pins unchanged')
 if mode=='compare':require(read(D/'qualify-run/result.json')['accepted'] is True and read(D/'qualify-run/audit.json')['accepted'] is True,'separately admitted actual qualification first')
 out=D/(mode+'-run');out.mkdir(exist_ok=False);start=time.monotonic();limit=1800;deadline=start+limit
 G.atomic_json(out/'reservation.json',dict(runner=G.process_identity(os.getpid()),started=start,deadline=deadline,pins_sha256=G.digest(pins),admission_sha256=G.digest(review)))
 G.atomic_json(out/'preflight.json',host());os.environ.update(read(D/'runtime.json')['environment'])
 cmd=[sys.executable,'-B',str(D/'guard/guard_reviewed.py'),'run',str(pins),str(out/'guard'),'--expected-exit','0','--seconds',str(deadline-time.monotonic()-8),'--deadline',str(deadline-8),'--',*cfg['command']]
 with (out/'supervisor.log').open('x') as f:sup=S.run(cmd,f,out/'guard',start,limit)
 G.atomic_json(out/'supervision.json',sup);proc=read(out/'guard/process.json')
 with (out/'audit.log').open('x') as f:code=subprocess.run([sys.executable,'-B',str(D/'audit.py'),mode,str(out)],stdout=f,stderr=subprocess.STDOUT).returncode
 G.atomic_json(out/'terminal-host.json',host());matched=G.pins_match(p);elapsed=time.monotonic()-start
 r=dict(accepted=sup.get('accepted') is True and proc['returncode']==0 and proc['reason']=='exit0' and proc['pins_unchanged'] and matched and code==0 and elapsed<=limit,mode=mode,exit=proc['returncode'],reason=proc['reason'],audit_exit=code,pins_unchanged=matched,elapsed_seconds=elapsed,limit_seconds=limit)
 G.atomic_json(out/'result.json',r);print(json.dumps(r),flush=True);return 0 if r['accepted'] else 1
if __name__=='__main__':sys.exit(main())
