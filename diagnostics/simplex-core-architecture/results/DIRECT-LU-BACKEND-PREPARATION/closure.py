from control import *
from evidence import validate_predecessor
import guard,ast
checks={};v=rd(D/'preparation-review.json')
validate_review(v,D/'preparation-pins.json',rd(D/'required.json'));checks['independent_preparation_review']=True
reviewcheck=rd(D/'reviewer-check.json');checks['independent20checks']=reviewcheck['all_passed'] is True and len(reviewcheck['checks'])==20 and all(sha(n)==h for n,h in reviewcheck['sha256'].items())
checks['full_preparation_pins']=guard.pins_match(rd(D/'preparation-pins.json'))
validate_predecessor('probe');checks['frozen_predecessor']=True
for label,n in (('synthetic','offline-tests.json'),('source','source-check.json')):
 z=rd(D/n);checks[label+'_pass']=z['all_passed'] is True
 checks[label+'_bindings']=all(sha(p)==h for p,h in z['sha256'].items())
checks['original_failed_selector_preserved']=(D/'source-check-error.txt').is_file() and 'prepared_spikes.jl' in (D/'source-check.py').read_text()
checks['filename_only_correction']=(D/'source-check.py').read_text().replace('prepared_spikes.jl','triangular_spikes.jl')==(D/'source-check-2.py').read_text()
m=rd(D/'continuation.json')['mappings'];checks['four_before_mappings']=len(m)==4 and all(sha(R/z['preserved_path'])==z['sha256']==rd(R/z['record'])['sha256'][z['key']] for z in m)
base=rd(D.parent/'DIRECT-LU-PREPARATION/baseline.json')['sha256'];checks['baseline514']=len(base)==514 and all(sha(R/n)==h for n,h in base.items())
checks['no_numerical_stage']=not any(D.glob('probe-*'))
checks['old_cost2_absent']=not any((D.parent/'DIRECT-LU-COST-PREPARATION').glob('cost2-*'))
h=host(rd(D/'host.json')['groups']);save(D/'closure-host.json',h)
checks['fresh204groups_sessions_noJulia']=len(h['groups'])==204 and not h['matches']
checks['refs_boot']=all(h[k]==rd(D/'host.json')[k] for k in ('head','master','boot_id'))
for n in ('continue.py','closure.py','publication.py'):ast.parse((D/n).read_text())
checks['new_closure_syntax']=True
checks['diff_clean']=subprocess.run(['git','diff','--check'],cwd=R,capture_output=True).returncode==0
s=R/'diagnostics/simplex-core-architecture/STATUS.md';road=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md';report=R/'diagnostics/simplex-core-architecture/DIRECT-LU-BACKEND-PREPARATION.md'
checks['continuation_pending_exact_stage']='Preparation\nacceptance alone does not admit execution' in s.read_text() and 'not cost2 or a benchmark retry' in road.read_text()
paths=[p for p in D.iterdir() if p.is_file() and p.name not in ('closure.json','publication.json')]+[s,road,report]
out=dict(all_passed=all(checks.values()),checks=checks,sha256={str(p.relative_to(R)):sha(p) for p in sorted(paths)})
save(D/'closure.json',out);req(out['all_passed'],'Closure failed; preserve and stop');print(dict(checks=len(checks),bindings=len(out['sha256']),all_passed=True))
