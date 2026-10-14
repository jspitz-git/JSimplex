from pathlib import Path
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');D=R/'diagnostics/simplex-core-architecture/results/PRESOLVE-ZERO-COEFFICIENT'
def write(n,s):
 with (D/n).open('x') as f:f.write(s)
write('red.jl','''using JSimplex, SparseArrays, Test, TOML
const D=@__DIR__
Base.include(JSimplex,joinpath(D,"probe-original.jl"))
p=LinearProblem(sparse([2.0 3.0;4.0 0.0]),[0.0,2.0];objective_constant=7.0,
    row_lower=[4.0,nothing],row_upper=[4.0,20.0],column_lower=[nothing,nothing],column_upper=[nothing,nothing])
original=deepcopy(p)
r=JSimplex.zero_conversion_probe(p)
count=JSimplex.zero_conversion_count[]
correct=size(r.problem.A)==(1,1) && r.problem.A[1,1]==-6.0 && JSimplex.bound_value(r.problem.row_upper[1])==12.0
preserved=p.A==original.A && p.row_upper==original.row_upper && p.row_lower==original.row_lower
open(joinpath(ARGS[1],"raw.toml"),"w") do io
 TOML.print(io,Dict("expected_red"=>true,"zero_conversions"=>count,"correct"=>correct,"preserved"=>preserved,"loaded_path"=>pathof(JSimplex)))
end
@testset "Missing zero matrix entries avoid exact-zero conversion" begin
 @test correct
 @test preserved
 @test count==0
end
''')
write('launch.py','''from control import *
import guard,supervisor,sys
phase=sys.argv[1];cfg=rd(D/(phase+'-config.json'));pins_path=D/(phase+'-launch-pins.json');pins=rd(pins_path)
review_path=D/(phase+'-admission.json');review=rd(review_path)
validate_review(review,sha(D/(phase+'-pins.json')),[Path(p) for p in cfg['required']])
base=rd(D/(phase+'-pins.json'))
req(set(pins['inventory'])==set(base['inventory'])|{str(D/(phase+'-pins.json')),str(review_path)},'exact launch addition')
req(all(pins['inventory'][p]==v for p,v in base['inventory'].items()),'base bindings');req(guard.pins_match(pins),'launch pins')
groups=rd(D/'host.json')['groups']
for p in D.glob('*-posthost.json'):groups+=rd(p)['groups']
h=host(groups);save(D/(phase+'-prehost.json'),h);entry=rd(D/'host.json')
req(not h['matches'] and all(h[k]==entry[k] for k in ('head','master','boot_id')),'fresh host')
out=D/(phase+'-run');req(not out.exists(),'prior output')
save(D/(phase+'-reservation.json'),dict(one_attempt=True,command=cfg['command'],pins_sha256=sha(pins_path),review_sha256=sha(review_path),max_seconds=120))
started=time.monotonic();command=[sys.executable,'-B',str(D/'guard.py'),'run',str(pins_path),str(out),'--seconds','114','--deadline',str(started+114),'--',*cfg['command']]
inv=dict(command=cfg['command'],guard_command=command,pins_sha256=sha(pins_path),review_sha256=sha(review_path),reservation_sha256=sha(D/(phase+'-reservation.json')),started=time.time())
try:
 with (D/(phase+'-launcher.log')).open('x') as log:inv['supervisor']=supervisor.run(command,log,out,started)
finally:
 inv['elapsed_seconds']=time.monotonic()-started;save(D/(phase+'-invocation.json'),inv)
 if 'supervisor' in inv:groups+=[inv['supervisor']['guard_identity'][k] for k in ('pgid','sid')]
 for n in ('current.json','process.json'):
  if (out/n).exists():
   rec=rd(out/n)
   for k in ('runner','child'):
    if k in rec:groups += [rec[k]['pgid'],rec[k]['sid']]
 post=host(groups);save(D/(phase+'-posthost.json'),post)
p=rd(out/'process.json');s=inv['supervisor'];raw=tomllib.loads((out/'raw.toml').read_text());expected=cfg['expected_returncode']
resources=[json.loads(l) for l in (out/'resources.jsonl').read_text().splitlines()]+[p['terminal_memory']]
checks={'no_processes':not post['matches'],'bounded':inv['elapsed_seconds']<=120 and not s['soft_timeout'] and not s['hard_timeout'] and 'cleanup_error' not in s,'exit':p['returncode']==expected and p['reason']=='exit'+str(expected) and s['returncode']==(0 if expected==0 else 1),'pins':p['pins_unchanged'] and guard.pins_match(pins) and rd(out/'pins.json')==pins,'command':p['command']==cfg['command'] and p['pins_sha256']==sha(pins_path),'resources':all(r['available_kib']>=6*1024**2 and r['swap_used_kib']<=1024**2 for r in resources),'loaded_path':raw['loaded_path'] in pins['inventory']}
checks['driver']=raw['correct'] and raw['preserved'] and raw['zero_conversions']>0 and raw['expected_red'] if expected==1 else raw['all_passed'] is True
save(D/(phase+'-audit.json'),dict(all_passed=all(checks.values()),checks=checks,expected_returncode=expected,scope='Expected RED is not numerical acceptance' if expected else 'Completed bounded run',sha256={str(q):sha(q) for q in out.rglob('*') if q.is_file()}));req(all(checks.values()),'audit failed; preserve/stop');print(phase,'PASS',inv['elapsed_seconds'])
''')
write('freeze-stage.py','''from control import *
import guard,sys,ast
phase=sys.argv[1];driver=sys.argv[2];expected=int(sys.argv[3]);project=sys.argv[4]
old=rd(D.with_name('PRESOLVE-LARGE-PROFILE')/'pins.json');prior=rd(D.with_name('PRESOLVE-EXACT-CACHE')/'host.json')
req(all(sha(p)==v for p,v in prior['protected'].items()),'protected files')
for p in D.glob('*.py'):ast.parse(p.read_text())
command=['/bin/bash','/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh','--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+project,str(D/driver),str(D/(phase+'-run'))]
required=sorted(str(p) for p in D.iterdir() if p.is_file() and not p.name.endswith(('-pins.json','-launch-pins.json')))
config=D/(phase+'-config.json');save(config,dict(command=command,required=required,expected_returncode=expected,project=project))
files=[p for p in old['files'] if not p.startswith(str(R))]+list(prior['protected'])+[str(R/p) for p in prior['master_identity']]+required+[str(config)]
trees=[p for p in old['trees'] if not p.startswith(str(R))]+[str(R/'src'),project]
files=sorted(set(files));save(D/(phase+'-pins.json'),dict(files=files,trees=trees,inputs=[],created=time.time(),inventory=guard.inventory(files,trees)))
print('Frozen',phase,len(rd(D/(phase+'-pins.json'))['inventory']))
''')
write('red-admission-scope.md','''# Missing-zero conversion RED admission

User approved the concrete sparse-equality optimization and short numerical attempts.
This first stage runs ONE tiny Float64 model only, before any candidate code exists.
The full original aggregate function is copied with ONLY its function name and the
single missing-entry exact conversion redirected to a forwarding counter. No method
is overwritten. The counter forwards identical conversion; it is outside performance
measurement and never production. Input: 2x+3y=4,4x<=20, free x/y, cost2y+7.
Expected exact reduced coefficient -6 and upper12, source preserved; exactly one
missing zero conversion in current code. The work test demands zero and must FAIL
(exit1, two preservation/correctness passes and one work failure). This is an actual
forwarded-work test, not a source-text RED or solver defect. Save raw before assertion.

One guard114s / inclusive supervisor120s, one Julia/BLAS1, existing compiled modules,
heap2GiB hint/VM8GiB/availableRAM6GiB/swap1GiB. No MPS input, solver, old auditor,
production/test/env changes, candidate or retry. Fresh full groups ORsessions and
pins before/after. Failure beyond the exact expected RED stops. Admission review
must bind every required config path and the pins SHA before launcher execution.
''')
