from pathlib import Path
import sys,json,time,os,importlib.util,subprocess,re
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
 h=H.host(O/'run-1');base=read(D/'host.json');require(h['boot_id']==base['boot_id'],'boot changed');groups=set(base['checked_groups'])|set(h['checked_groups'])
 for p in D.glob('*-run/guard/process.json'):
  d=read(p)
  for k in ('runner','child'):
   a=d.get(k,{})
   if a.get('boot_id')==h['boot_id']:groups.update((a['pgid'],a['sid']))
 for p in Path('/proc').glob('[0-9]*'):
  try:
   a=H.H.identity(p.name)
   require(a['pgid'] not in groups and a['sid'] not in groups,'old group/session active')
  except (FileNotFoundError,ProcessLookupError):pass
 require(H.H.git(W,'rev-parse','HEAD')==read(D/'runtime.json')['experiment'],'experiment ref changed')
 require(H.H.git(W,'branch','--show-current')=='codex/dual-step-experiment','experiment branch changed')
 h['checked_groups']=sorted(groups);h['experiment']=H.H.git(W,'rev-parse','HEAD');h['no_julia']=True;return h

def main():
 stage=sys.argv[1];require(stage in ('red','green'),'stage');cfg=read(D/(stage+'-contract.json'));pins=D/(stage+'-pins.json');review=D/(stage+'-admission.json')
 a=read(review);require(a.get('accepted') is True and a.get('pins_sha256')==G.digest(pins),'bound independent admission missing');p=read(pins);require(G.pins_match(p),'pins changed')
 out=D/(stage+'-run');out.mkdir(exist_ok=False);start=time.monotonic();limit=1800;deadline=start+limit
 G.atomic_json(out/'reservation.json',dict(runner=G.process_identity(os.getpid()),started=start,deadline=deadline,pins_sha256=G.digest(pins),admission_sha256=G.digest(review)))
 G.atomic_json(out/'preflight.json',host());os.environ.update(read(D/'runtime.json')['environment'])
 cmd=[sys.executable,'-B',str(D/'guard/guard_reviewed.py'),'run',str(pins),str(out/'guard'),'--expected-exit',str(cfg['exit']),'--seconds',str(deadline-time.monotonic()-6),'--deadline',str(deadline-6),'--',*cfg['command']]
 with (out/'supervisor.log').open('x') as f:sup=S.run(cmd,f,out/'guard',start,limit)
 G.atomic_json(out/'supervision.json',sup);proc=read(out/'guard/process.json');log=(out/'guard/run.log').read_text(errors='replace')
 if stage=='red':valid=bool(re.search(r'4 passed, 5 failed, 0 errored, 0 broken',log)) and 'Test Failed' in log
 else:valid='DUAL_ENGINE_TASK5_COMPLETED' in log and 'Test Failed' not in log and 'Error During Test' not in log
 G.atomic_json(out/'terminal-host.json',host());matched=G.pins_match(p);elapsed=time.monotonic()-start
 r=dict(accepted=sup.get('accepted') is True and proc['returncode']==cfg['exit'] and proc['reason']=='exit'+str(cfg['exit']) and proc['pins_unchanged'] and matched and valid and elapsed<=limit,stage=stage,exit=proc['returncode'],reason=proc['reason'],expected_test_outcome=valid,pins_unchanged=matched,elapsed_seconds=elapsed,limit_seconds=limit)
 G.atomic_json(out/'result.json',r);print(json.dumps(r),flush=True);return 0 if r['accepted'] else 1
if __name__=='__main__':sys.exit(main())
