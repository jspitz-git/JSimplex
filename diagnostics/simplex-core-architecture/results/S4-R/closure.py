from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';E=D/'results/S4-R';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();a=json.loads((E/'source-contract.json').read_text());i=json.loads((E/'independent.json').read_text());h=json.loads((E/'host-final.json').read_text());checks={}
checks['source24_and_independent8_pass']=len(a['checks'])==24 and all(a['checks'].values()) and len(i['checks'])==8 and all(i['checks'].values())
checks['readtime570_still_exact']=len(a['sha256'])==570 and all(sha(p)==v for p,v in a['sha256'].items())
checks['fresh_full_groups_empty']=h['matches']==[] and h['pids_present']==[] and h['boot_id']=='dade7243-9103-4398-bb45-fa28fbc0be72'
checks['user6_unchanged']=len(h['user_hashes'])==6 and all(sha(p)==v for p,v in h['user_hashes'].items())
checks['source_test_CI_master_unchanged']=not subprocess.check_output(['git','diff','master','--','src','test','.github'])
checks['refs_unchanged_precommit']=subprocess.check_output(['git','rev-parse','HEAD','master'],text=True)==h['refs']
old=['diagnostics/simplex-core-architecture/results/S4-'+x for x in 'EFGHIJKLMNOPQ'];checks['old_evidence_reproduce_unchanged']=not subprocess.check_output(['git','diff','HEAD','--',*old,'diagnostics/simplex-core-architecture/reproduce'])
review=(D/'S4-PUBLIC-CONTROLLER-REUSE-CONTRACT-REVIEW.md').read_text();checks['review_no_findings_and_scoped_rehash']='No Critical, Important or Minor findings' in review and 'NOT a full570 rehash' in review
checks['continuation_source_only']='next S4-S source-only' in (D/'STATUS.md').read_text().lower().replace('next s4-s','next S4-S') and 'No Julia, module loading' in (R/'docs/superpowers/plans/2026-10-12-hh-isolated-module-loading-contract.md').read_text()
files=[D/'STATUS.md',D/'S4-PUBLIC-CONTROLLER-REUSE-CONTRACT.md',D/'S4-PUBLIC-CONTROLLER-REUSE-CONTRACT-REVIEW.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',R/'docs/superpowers/plans/2026-10-12-hh-isolated-module-loading-contract.md',*sorted(E.iterdir())]
result=dict(checks=checks,all_passed=all(checks.values()),final_sha256={str(p):sha(p) for p in files if p.is_file()})
with (E/'closure.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(checks));assert result['all_passed']
