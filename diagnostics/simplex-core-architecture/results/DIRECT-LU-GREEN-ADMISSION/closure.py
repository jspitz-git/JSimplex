"""One-shot offline closure; no stage sealing or numerical work."""
from control import *
import guard
checks={};pins_path=D/'preparation-pins.json';pins=rd(pins_path);review=rd(D/'preparation-review.json')
validate_review(review,pins_path,rd(D/'required.json'));checks['independent_review_exact_membership']=True
checks['all4611_preparation_pins']=len(pins['inventory'])==4611 and guard.pins_match(pins)
tests=rd(D/'offline-tests.json');checks['all72_helper_checks']=tests['all_passed'] is True and len(tests['checks'])==72 and all(tests['checks'].values())
checks['green_only_fixed_schedule']=sum(g['counts'][0] for g in phase_config('green')['groups'])==19557
base=rd(D.parent/'DIRECT-LU-PREPARATION/baseline.json')['sha256'];checks['baseline514_unchanged']=len(base)==514 and all(sha(R/n)==h for n,h in base.items())
line=rd(D/'source-lineage.json');checks['guard_supervisor_byteidentical']=all(sha(D/n)==h for n,h in line['unchanged'].items())
s=rd(D/'staging.json');w=Path(s['root']);checks['exact_new_overlay']=set(s['original_sha256'])=={str(p.relative_to(w)) for p in w.rglob('*') if p.is_file()} and all(sha(w/n)==(s['correctness_sha256'] if n=='correctness.jl' else h) for n,h in s['original_sha256'].items())
checks['unchanged_focused_slices']=all((D/'focused'/v['output']).read_bytes()==(R/v['source']).read_bytes()[v['start_byte']:v['end_byte']] for v in s['focused'])
m=rd(D/'continuation.json')['mappings'];checks['four_prior_continuation_maps']=len(m)==4 and all(sha(R/x['preserved_path'])==x['sha256']==rd(R/x['record'])['sha256'][x['key']] for x in m)
h=rd(D/'host.json');checks['fresh200_group_session_preflight']=len(h['groups'])==200 and h['matches']==[]
checks['refs_unchanged']=git('rev-parse','HEAD')==h['head'] and git('rev-parse','master')==h['master']=='6f68e24e8ddac42b948da8fcc2d636c010751194'
checks['no_stage_output_reservation']=not any((D/n).exists() for n in ('green-seal-host.json','green-sealed-pins.json','green-admission.json','green-reservation.json','green-run','red-run'))
checks['old_GREEN_false_preserved']=rd(D.parent/'DIRECT-LU-ADMISSION/green-audit.json')['all_passed'] is False
checks['no_production_diff']=not git('diff','--name-only','--','src','test','Project.toml','.github')
checks['authored_diff_clean']=subprocess.run(['git','diff','--check'],cwd=R).returncode==0
paths=[p for p in D.rglob('*') if p.is_file() and p.name not in ('closure.json','publication.json')]
paths += [R/'diagnostics/simplex-core-architecture/DIRECT-LU-GREEN-ADMISSION.md',R/'diagnostics/simplex-core-architecture/STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md']
result=dict(all_passed=all(checks.values()),checks=checks,scope='Offline corrected GREEN admission preparation; no launch/runtime acceptance',sha256={str(p.relative_to(R)):sha(p) for p in sorted(set(paths))})
save(D/'closure.json',result);print(json.dumps(dict(all_passed=result['all_passed'],checks=checks,bindings=len(result['sha256'])),indent=2));req(result['all_passed'],'Closure refused')
