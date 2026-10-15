"""One-shot literal/inverse checks only. This is not a Julia test or parser."""
from pathlib import Path
import hashlib,json,re,subprocess
R=Path(__file__).resolve().parents[4];D=Path(__file__).resolve().parent
C=R/'diagnostics/direct-lu-markowitz/reproduce';A=D.parent/'DIRECT-LU-ADMISSION'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(p):return json.loads(p.read_text())
r=rd(D/'replacements.json');test=(D/'correctness.jl').read_text();driver=(D/'driver.jl').read_text();original=(C/'correctness.jl').read_text();checks={}
a,b=r['test']['old'],r['test']['new']
checks['test_exact_whole_file_inverse']=test.count(b)==1 and test.replace(b,a)==original
inverse=driver
for x in reversed(r['driver']):
    if inverse.count(x['new'])!=1:raise ValueError('Driver inverse not unique')
    inverse=inverse.replace(x['new'],x['old'])
checks['driver_exact_three_replacement_inverse']=len(r['driver'])==3 and inverse==(A/'driver.jl').read_text()
checks['five_added_assertions']=b.count('@test ')==5 and test.count('@test ')==original.count('@test ')+5
checks['same_single_existing_refactor_entry']=test.count('lu!(backend.factorization,')==original.count('lu!(backend.factorization,')==1
checks['copy_then_nzval_then_refactor_order']=b.index('refactor_input = copy(B)')<b.index('refactor_input.nzval .*= 2.0')<b.index('lu!(backend.factorization,refactor_input)')<b.index('@test issuccess')
checks['pattern_owner_value_oracles']=all(x in b for x in ('refactor_input.colptr == B.colptr','refactor_input.rowval == B.rowval','a !== b','isequal(refactor_input.nzval[k],2.0*B.nzval[k])'))
fixtures=(C/'fixtures.jl').read_text()
checks['stored_zero_fixture_retained']='SparseMatrixCSC(4,4,collect(1:4:17),repeat(collect(1:4),4)' in fixtures
checks['future_export_count']=driver.count('("exports",:test_exports,130)')==1 and 100+6*5==130
counts=[130,66,12,200,18272,288,62,8,144,195,96,84]
checks['future_total_count']=sum(counts)==19557
checks['latest_world_binding_lookup']=all(x in driver for x in ('Base.invokelatest(() -> getfield(Main,fn)())','Base.invokelatest(() -> getfield(Main,:run_direct_lu_red)())'))
frozen=rd(D/'frozen-inputs.json')['sha256']
checks['all136_frozen_files_unchanged']=len(frozen)==136 and all(sha(R/n)==h for n,h in frozen.items())
baseline=rd(D.parent/'DIRECT-LU-PREPARATION/baseline.json')['sha256']
checks['all514_baseline_files_unchanged']=len(baseline)==514 and all(sha(R/n)==h for n,h in baseline.items())
cont=rd(D/'continuation.json')['mappings']
checks['six_exact_prior_continuation_bindings']=len(cont)==6 and all(sha(R/x['preserved_path'])==x['sha256']==rd(R/x['record'])['sha256'][x['key']] for x in cont)
host=rd(D/'host.json')
checks['fresh_host_full200_groups_sessions_noJulia']=len(host['groups'])==200 and host['matches']==[]
checks['no_reservation_output_launcher']=not any(p.exists() for p in (D/'reservation.json',D/'run',D/'launch.py'))
checks['original_false_audit_preserved']=rd(A/'green-audit.json')['all_passed'] is False and rd(A/'red-audit.json')['all_passed'] is True
checks['no_tracked_production_diff']=subprocess.check_output(['git','diff','--name-only','--','src','test','Project.toml','.github'],cwd=R,text=True)==''
paths=[*D.glob('*.py'),D/'correctness.jl',D/'driver.jl',D/'host.json',D/'replacements.json',D/'frozen-inputs.json',D/'continuation.json',R/'diagnostics/simplex-core-architecture/DIRECT-LU-TEST-REPAIR.md',C/'fixtures.jl',C/'correctness.jl',A/'driver.jl']
result=dict(all_passed=all(checks.values()),checks=checks,scope='OFFLINE text/inverse only; no Julia execution',expected_counts=counts,sha256={str(p.relative_to(R)):sha(p) for p in sorted(set(paths))})
with (D/'source-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result['checks'],indent=2))
if not result['all_passed']:raise SystemExit('Offline check refused')
