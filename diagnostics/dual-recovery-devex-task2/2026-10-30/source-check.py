from pathlib import Path
import json,hashlib,re
D=Path(__file__).resolve().parent;W=D.parents[2];P=W/'diagnostics/dual-recovery-devex-task1/2026-10-30'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def require(v,m):
 if not v:raise RuntimeError(m)
b=json.loads((D/'build.json').read_text());checks={}
checks['numerics_exact_Task1_inverse']=(D/'simplex_numerics.jl').read_text().replace(b['metadata'],'',1)==(P/'simplex_numerics.jl').read_text()
s=(D/'simplex_recovery.jl').read_text();checks['recovery_exact_Task1_inverse']=s.replace(b['new_weight_loop'],b['original_weight_loop'],1)==(P/'simplex_recovery.jl').read_text()
ref=(D/'legacy_rebuild_reference.jl').read_text().split('const J=JSimplex\n',1)[1].rsplit('\nend\n',1)[0]
checks['reference_exact_original']=ref.replace('J.','')==b['original_weight_loop']
checks['initial_tests_first_preserved']=sha(D/'recovery_weight_tests.before-static-refinement.jl')==b['tests_first_sha256']
pins=json.loads((D/'source-pins.json').read_text());checks['all81_readtime_pins']=len(pins['bindings'])==81 and all(sha(Path(n))==h for n,h in pins['bindings'].items())
checks['Task1_parent_exact']=all(sha(Path(n))==h for n,h in b['parent_sources'].items())
# Inverse proves all normal kernel/constructor/publication/precision text remains.
checks['original_kernel_unchanged']=s[s.index('# Preserve the previous private entry'):]==(P/'simplex_recovery.jl').read_text().split('# Preserve the previous private entry',1)[1].join(['# Preserve the previous private entry',''])
checks['result_has_no_array']=all(x not in b['metadata'] for x in ('Vector','Ref{','Any','Workspace'))
checks['private_state_no_events']=all(x not in b['new_weight_loop'].split('function _prepare_recovery_devex!',1)[1] for x in ('_simplex_event!','_record_recovery!','@logmsg','_reject_auto_weight!','_switch_dual_pricing_to_devex!'))
checks['no_added_solve_entry']=b['new_weight_loop'].count('transpose_solve!')==1
checks['no_extra_finite_array_scan']='all(isfinite' not in b['new_weight_loop']
checks['source_only_report']='UNEXECUTED' in (D/'REPORT.md').read_text()
bindings=dict(pins['bindings']);bindings.update({str(p):sha(p) for p in D.iterdir() if p.is_file() and p.name!='source-check.json'})
r=dict(accepted=all(checks.values()),scope='source inverse/readtime only; no Julia',checks=checks,bindings=bindings)
with (D/'source-check.json').open('x') as f:f.write(json.dumps(r,indent=2)+'\n')
print(json.dumps(dict(accepted=r['accepted'],checks=checks,bindings=len(bindings))))
require(r['accepted'],'source proof failed')
