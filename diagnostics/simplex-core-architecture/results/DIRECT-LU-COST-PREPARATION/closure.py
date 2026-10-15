"""One-shot publication closure for OFFLINE preparation; no numerical execution."""
from control import *
from evidence import validate_predecessor
import guard,ast
review=rd(D/'preparation-review.json');pins=rd(D/'preparation-pins.json')
checks={}
validate_review(review,D/'preparation-pins.json',rd(D/'required.json'));checks['independent_review_exact']=True
checks['all_preparation_pins']=guard.pins_match(pins)
checks['all48_input_checks']=rd(D/'offline-tests.json')['all_passed'] and len(rd(D/'offline-tests.json')['checks'])==48
checks['all61_control_checks']=rd(D/'control-tests.json')['all_passed'] and len(rd(D/'control-tests.json')['checks'])==61
checks['author_seven']=rd(D/'author-check.json')['all_passed'] and all(sha(n)==h for n,h in rd(D/'author-check.json')['sha256'].items())
checks['correctness_predecessor']=bool(validate_predecessor('cost1'))
checks['no_numerical_artifacts']=not any(D.glob('*-run')) and not any(D.glob('*reservation*')) and not any(D.glob('*sealed-pins*'))
base=rd(D.parent/'DIRECT-LU-PREPARATION/baseline.json')['sha256'];checks['all514_production_baseline']=len(base)==514 and all(sha(R/n)==h for n,h in base.items())
for p in D.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
checks['python_sources_parse']=True
mappings=rd(D/'continuation.json')['mappings'];checks['four_continuation_maps']=len(mappings)==4 and all(sha(R/m['preserved_path'])==m['sha256'] for m in mappings)
for phase in ('cost1','cost2'):phase_config(phase)
checks['exact_two_configurations']=True
fresh=host(rd(D/'host.json')['groups']);save(D/'closure-host.json',fresh)
checks['fresh202_groups_sessions']=len(fresh['groups'])==202 and not fresh['matches']
checks['refs_unchanged']=all(fresh[k]==rd(D/'host.json')[k] for k in ('head','master','boot_id'))
checks['authored_diff_clean']=subprocess.run(['git','diff','--check'],cwd=R,capture_output=True).returncode==0
report=R/'diagnostics/simplex-core-architecture/DIRECT-LU-COST-PREPARATION.md'
status=R/'diagnostics/simplex-core-architecture/STATUS.md';road=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
checks['continuation_points_to_pending_cost1']='Task3 OFFLINE cost preparation is independently accepted' in status.read_text() and 'No performance acceptance yet' in status.read_text()
paths=[p for p in D.iterdir() if p.is_file() and p.name not in ('closure.json','publication.json')]+[report,status,road]
result=dict(all_passed=all(checks.values()),checks=checks,sha256={str(p.relative_to(R)):sha(p) for p in sorted(paths)})
save(D/'closure.json',result);req(result['all_passed'],'Offline closure rejected')
print(json.dumps(dict(all_passed=True,checks=len(checks),bindings=len(result['sha256']))))
