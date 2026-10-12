from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';E=D/'results/S4-T';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();a=json.loads((E/'source-contract.json').read_text());i=json.loads((E/'independent.json').read_text());fix=json.loads((E/'review-fix.json').read_text());h=json.loads((E/'host-final.json').read_text());checks={}
checks['17_source_8_author_checks']=len(a['checks'])==17 and all(a['checks'].values()) and len(i['checks'])==8 and all(i['checks'].values())
checks['603_current_one_preserved']=len(a['sha256'])==604 and len(fix['before'])==1 and all(sha(fix['before'][p]['preserved'] if p in fix['before'] else p)==v for p,v in a['sha256'].items())
checks['corrected_report_and_four_gates']=all(sha(p)==v for p,v in fix['after'].items()) and len(fix['checks'])==4 and all(fix['checks'].values())
checks['user6_preserved']=all(sha(p)==v for p,v in h['user_hashes'].items())
checks['source_test_CI_same_master']=not subprocess.check_output(['git','diff','master','--','src','test','.github'])
checks['old_E_to_S_evidence_unchanged']=not subprocess.check_output(['git','diff','HEAD','--',*[str(D/'results'/('S4-'+x)) for x in 'EFGHIJKLMNOPQRS'],str(D/'reproduce')])
checks['refs_unchanged_before_commit']=subprocess.check_output(['git','rev-parse','HEAD','master'],text=True)==h['refs']
checks['fresh_host_fullgroups_absent']=not h['matches'] and not h['pids_present'] and h['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
checks['final_review_accepted']='no unresolved Critical, Important or Minor' in (D/'S4-ISOLATED-PUBLIC-LP-WORK-CONTRACT-REVIEW.md').read_text()
checks['no_launch_next_source_only']='launch_supported\nis false' in (D/'S4-ISOLATED-PUBLIC-LP-WORK-CONTRACT.md').read_text() and 'NO numerical launch/plan in U' in (R/'docs/superpowers/plans/2026-10-12-hh-isolated-bootstrap-contract.md').read_text()
files=[D/'STATUS.md',D/'S4-ISOLATED-PUBLIC-LP-WORK-CONTRACT.md',D/'S4-ISOLATED-PUBLIC-LP-WORK-CONTRACT-REVIEW.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',R/'docs/superpowers/plans/2026-10-12-hh-isolated-bootstrap-contract.md',*sorted(E.iterdir())]
obj=dict(checks=checks,all_passed=all(checks.values()),final_sha256={str(p):sha(p) for p in files if p.is_file()})
with (E/'closure.json').open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
print(json.dumps(checks));assert obj['all_passed']
