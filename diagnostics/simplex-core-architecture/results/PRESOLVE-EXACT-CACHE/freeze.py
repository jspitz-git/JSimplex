from control import *
import guard,sys

def main():
 old=rd(R/'diagnostics/simplex-core-architecture/results/MASTER-PROFILE/pins.json');hostdata=rd(D/'host.json');O=R/'.superpowers/presolve-exact-cache'
 commands={}
 for i,side in enumerate(('reference','candidate','candidate','reference'),1):
  commands[str(i)]=['/bin/bash','/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh','--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+str(O/side),str(D/'driver.jl'),str(i),side,str(D/f'run-{i}')]
 save(D/'commands.json',commands)
 required=sorted(str(p) for p in D.iterdir() if p.is_file())+[str(D/'commands.json')]
 required=sorted(set(required));save(D/'required.json',required)
 files=sorted(set([p for p in old['files'] if not p.startswith(str(R)+'/')]+[str(R/p) for p in hostdata['master_identity']]+list(hostdata['protected'])+required+[str(D/'required.json'),str(Path(sys.executable).resolve())]))
 trees=[p for p in old['trees'] if not p.startswith(str(R)+'/')]+[str(R/'src'),str(O/'reference'),str(O/'candidate')]
 inputs=[str(R/f['path']) for f in tomllib.loads((D/'cases.toml').read_text())['cases']]
 req(all(Path(p).stat().st_size<2000000 for p in inputs),'small whitelist')
 files=sorted(set(files+inputs));pins=dict(files=files,trees=trees,inventory=guard.inventory(files,trees),inputs=inputs,created=time.time())
 save(D/'pins.json',pins)
 # This is a source/failure-gate selfcheck, not a launcher or Julia execution.
 good=dict(accepted=True,findings=[],pins_sha256=sha(D/'pins.json'),sha256={p:sha(p) for p in required})
 tests={}
 for name,change in [('rejected',{'accepted':False}),('finding',{'findings':['test']}),('bad_pins',{'pins_sha256':'wrong'}),('missing_bindings',{'sha256':{}}),('missing_acceptance',{'accepted':None})]:
  try:validate_review(good|change,sha(D/'pins.json'),[Path(p) for p in required]);tests[name]=False
  except ValueError:tests[name]=True
 validate_review(good,sha(D/'pins.json'),[Path(p) for p in required]);tests['valid_review']=True
 tests['guard_byteexact']=sha(D/'guard.py')==sha(R/'diagnostics/simplex-core-architecture/results/MA-X/guard.py');tests['supervisor_byteexact']=sha(D/'supervisor.py')==sha(R/'diagnostics/simplex-core-architecture/results/MA-X/supervisor.py')
 save(D/'offline-checks.json',dict(all_passed=all(tests.values()),checks=tests,pins_count=len(pins['inventory'])))
 print('Frozen',len(pins['inventory']),'inputs;',len(tests),'offline checks PASS')
if __name__=='__main__':main()
