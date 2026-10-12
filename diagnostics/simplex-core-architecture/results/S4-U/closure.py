from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';E=D/'results/S4-U';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();a=json.loads((E/'source-contract.json').read_text());i=json.loads((E/'independent.json').read_text());h=json.loads((E/'host-final.json').read_text());checks={}
checks['20_source_six_independent_checks']=len(a['checks'])==20 and all(a['checks'].values()) and len(i['checks'])==6 and all(i['checks'].values())
checks['all627_readtime_hashes_unchanged']=len(a['sha256'])==627 and all(sha(p)==v for p,v in a['sha256'].items())
checks['six_user_files_unchanged']=len(h['user_hashes'])==6 and all(sha(p)==v for p,v in h['user_hashes'].items())
checks['production_test_CI_equal_master']=not subprocess.check_output(['git','diff','master','--','src','test','.github'])
checks['old_E_to_T_evidence_unchanged']=not subprocess.check_output(['git','diff','HEAD','--',*[str(D/'results'/('S4-'+x)) for x in 'EFGHIJKLMNOPQRST'],str(D/'reproduce')])
checks['refs_unchanged_precommit']=subprocess.check_output(['git','rev-parse','HEAD','master'],text=True)==h['refs']
checks['host_absent_old_groups_noJulia']=not h['matches'] and not h['pids_present'] and h['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
checks['review_accepted']='no unresolved Critical, Important or Minor' in (D/'S4-ISOLATED-BOOTSTRAP-CONTRACT-REVIEW.md').read_text()
checks['no_numeric_plan_next_bounded_readonly']='No numerical plan is created' in (D/'S4-ISOLATED-BOOTSTRAP-CONTRACT.md').read_text() and 'Do not execute the proposed sandbox' in (R/'docs/superpowers/plans/2026-10-12-hh-readonly-bootstrap-feasibility.md').read_text()
files=[D/'STATUS.md',D/'S4-ISOLATED-BOOTSTRAP-CONTRACT.md',D/'S4-ISOLATED-BOOTSTRAP-CONTRACT-REVIEW.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',R/'docs/superpowers/plans/2026-10-12-hh-readonly-bootstrap-feasibility.md',*sorted(E.iterdir())]
obj=dict(checks=checks,all_passed=all(checks.values()),final_sha256={str(p):sha(p) for p in files if p.is_file()})
with (E/'closure.json').open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
print(json.dumps(checks));assert obj['all_passed']
