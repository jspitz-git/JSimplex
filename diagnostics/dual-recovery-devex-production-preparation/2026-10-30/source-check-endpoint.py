from pathlib import Path
import json,re,hashlib
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/dual-recovery-devex-production-preparation/2026-10-30';old=W/'diagnostics/dual-recovery-devex-task4/2026-10-30/endpoint.jl';new=D/'prepared/test/recovery_devex_pivot_tests.jl';record=json.loads((D/'source-check.json').read_text());pattern=r'@test(?:_throws|_broken|_skip)?\b'
def selected(p):return [s.strip().replace('revalidation.value','revalidation').replace('reset.value','reset') for s in p.read_text().splitlines() if re.match(pattern,s.lstrip())]
a,b=selected(old),selected(new)
checks=dict(initial22_other_checks_true=len(record['checks'])==23 and [k for k,v in record['checks'].items() if not v]==['endpoint23_assertions_retained_ordered_plus_work'],original23_prepared24_assertion_sites=len(a)==23 and len(b)==24,all23_original_checks_ordered_unchanged=b[:-1]==a,exact_added_work_oracle=b[-1]=='@test calls==(1,3) && (f.builder.last.forwards,f.builder.last.backwards)==(2,4)',testset_is_not_an_assertion=re.match(pattern,'@testset "a" begin') is None,all_initial_bindings_unchanged=all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in record['bindings'].items()))
paths=[old,new,D/'source-check.py',D/'source-check.json',Path(__file__)];result=dict(accepted=all(checks.values()),scope='separate bounded correction of endpoint assertion selector only; no Julia or candidate/test change',checks=checks,original_assertions=a,prepared_assertions=b,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},explanation='Initial startswith(@test) also counted @testset; explicit @test/@test_throws token regex excludes the testset header. Initial failed record/source preserved; original production/test payload unchanged.')
with (D/'source-check-endpoint.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
with (D/'source-check-endpoint.py').open('xb') as f:f.write(Path(__file__).read_bytes())
print(json.dumps(dict(accepted=result['accepted'],checks=len(checks),old_sites=len(a),new_sites=len(b))))
if not result['accepted']:raise SystemExit(1)
