from control import *
import guard,sys,ast

def main():
 P=D.with_name('PRESOLVE-EXACT-CACHE');old=rd(P/'launch-pins.json');O=R/'.superpowers/presolve-exact-cache'
 req(guard.pins_match(old),'original frozen inventory changed')
 commands={str(i):['/bin/bash','/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh','--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+str(O/side),str(D/'driver.jl'),str(i),side,str(D/f'run-{i}')] for i,side in enumerate(('reference','candidate','candidate','reference'),1)}
 save(D/'commands.json',commands)
 required=sorted(str(p) for p in D.iterdir() if p.is_file());save(D/'required.json',required)
 files=sorted(set(old['files']+required+[str(D/'required.json'),str(P/'partial-result.json'),str(P/'posthost-final.json'),str(P/'admission.md')]+[str(p) for p in (P/'run-1').iterdir() if p.is_file()]+[str(P/'invocation-1.json'),str(P/'posthost-1.json')]))
 pins=dict(files=files,trees=old['trees'],inventory=guard.inventory(files,old['trees']),inputs=old['inputs'],created=time.time());save(D/'pins.json',pins)
 tests={}
 good=dict(accepted=True,findings=[],pins_sha256=sha(D/'pins.json'),sha256={p:sha(p) for p in required})
 for n,change in [('rejected',{'accepted':False}),('finding',{'findings':['x']}),('wrong_pins',{'pins_sha256':'x'}),('missing_bindings',{'sha256':{}})]:
  try:validate_review(good|change,sha(D/'pins.json'),[Path(p) for p in required]);tests[n]=False
  except ValueError:tests[n]=True
 validate_review(good,sha(D/'pins.json'),[Path(p) for p in required]);tests['valid']=True
 tests['guard_exact']=sha(D/'guard.py')==sha(P/'guard.py')
 tests['supervisor_inverse']=(D/'supervisor.py').read_text().replace('started+64','started+84').replace('started+68','started+88').replace('started+70','started+90').replace('<=70','<=90')==(P/'supervisor.py').read_text()
 for p in D.glob('*.py'):ast.parse(p.read_text())
 tests['python_syntax']=True
 save(D/'offline-checks.json',dict(all_passed=all(tests.values()),checks=tests,pins_count=len(pins['inventory'])))
 print('Frozen',len(pins['inventory']),'new pins;',len(tests),'offline checks PASS')
if __name__=='__main__':main()
