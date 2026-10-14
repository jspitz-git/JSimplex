"""One-shot OFFLINE admission closure. No Julia or launch; old scripts never run."""
from control_reviewed import *
import guard
old=R/'diagnostics/simplex-core-architecture/results/DIRECT-LU-PREPARATION'
baseline=rd(old/'baseline.json');checks={}
checks['baseline_514_unchanged']=len(baseline['sha256'])==514 and all(sha(R/n)==h for n,h in baseline['sha256'].items())
h=rd(D/'host.json')
checks['refs_unchanged']=git('rev-parse','HEAD')==h['head'] and git('rev-parse','master')==h['master']
checks['initial_preflight']=len(h['groups'])==196 and h['matches']==[] and bool(h['boot_id'])
checks['initial_inventory_unchanged']=guard.pins_match(rd(D/'preparation-pins.json'))
checks['revised_inventory_unchanged']=guard.pins_match(rd(D/'preparation-pins-reviewed.json'))
initial=rd(D/'preparation-review.json')
checks['initial_review_preserved']=initial['accepted'] is False and len(initial['findings'])==2 and initial['pins_sha256']==sha(D/'preparation-pins.json') and set(initial['sha256'])==set(rd(D/'required.json')) and all(sha(n)==v for n,v in initial['sha256'].items())
review=rd(D/'preparation-review-final.json')
validate_review(review,D/'preparation-pins-reviewed.json',rd(D/'required-reviewed.json'))
checks['independent_final_acceptance']=review['accepted'] is True and review['findings']==[]
checks['initial_synthetic_35']=rd(D/'offline-tests.json')['all_passed'] and len(rd(D/'offline-tests.json')['checks'])==35
checks['amendment_synthetic_56']=rd(D/'review-fix-tests.json')['all_passed'] and len(rd(D/'review-fix-tests.json')['checks'])==56
checks['preserved_syntax_failure']=(D/'initial/control.py').is_file() and (D/'preparation-failure.json').is_file()
cont=rd(D/'continuation.json')
checks['four_exact_continuation_mappings']=len(cont['mappings'])==4 and all(sha(R/v['preserved_path'])==v['sha256']==rd(R/v['record'])['sha256'][v['key']] for v in cont['mappings'])
checks['plan_spec_frozen']=sha(R/'docs/superpowers/plans/2026-10-14-direct-lu-markowitz.md')=='fb0b3609260394b0719423301284a0713475af793db53e1a828c0dce12efb5d7' and sha(R/'docs/superpowers/specs/2026-10-14-direct-lu-markowitz.md')=='1f53fca7568e94a0302eb646b405715ac81e00121172f4e29e17b2f085f381fc'
staging=rd(D/'staging.json');W=Path(staging['root']);C=R/'diagnostics/direct-lu-markowitz/reproduce'
anchor=b'include("huangfu_hall_factorization.jl")\n';extra=b'include("factor-export.jl")\ninclude("direct-factor.jl")\n'
checks['overlay_inverse']=(W/'candidate/src/JSimplex.jl').read_bytes().replace(anchor+extra,anchor)==(W/'reference/src/JSimplex.jl').read_bytes()
checks['exact_candidate_copies']=all((W/'candidate/src'/n).read_bytes()==(C/n).read_bytes() for n in ('factor-export.jl','direct-factor.jl')) and all((W/side/n).read_bytes()==(C/n).read_bytes() for side in ('reference','candidate') for n in ('correctness.jl','red.jl','fixtures.jl'))
checks['focused_exact_slices']=all((D/'focused'/v['output']).read_bytes()==(R/v['source']).read_bytes()[v['start_byte']:v['end_byte']] for v in staging['focused'])
checks['counts_19527']=sum(g['counts'][0] for g in rd(D/'config.json')['phases']['green']['groups'])==19527
checks['no_stage_execution_artifacts']=all(not list(D.glob(phase+'-*')) for phase in ('red','green'))
checks['tracked_diff_clean']=subprocess.run(['git','diff','--check'],cwd=R).returncode==0
paths=sorted(p for p in D.rglob('*') if p.is_file() and p.name not in ('closure.json','publication.json'))+[R/'diagnostics/simplex-core-architecture/DIRECT-LU-ADMISSION.md',R/'diagnostics/simplex-core-architecture/STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md']
result=dict(all_passed=all(checks.values()),checks=checks,scope='Offline admission preparation only; no Julia/test/numerical/process-launch evidence',sha256={str(p.relative_to(R)):sha(p) for p in paths})
save(D/'closure.json',result)
print(json.dumps(dict(all_passed=result['all_passed'],checks=checks,bindings=len(result['sha256'])),indent=2))
req(result['all_passed'],'Closure refused')
