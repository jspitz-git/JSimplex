"""One-shot diagnostic-failure closure; never converts failed correctness to PASS."""
from pathlib import Path
import json,hashlib,subprocess,sys,tomllib
R=Path(__file__).resolve().parents[4];D=Path(__file__).resolve().parent;A=D.parent/'DIRECT-LU-ADMISSION'
sys.path.insert(0,str(A));import guard
from control_reviewed import sha,rd,req,save,git
checks={};post=rd(D/'postcheck.json');analysis=rd(D/'source-analysis.json');review=rd(D/'review.json')
checks['result_review_accepts_diagnosis']=review['decision']=='accepted_diagnostic_failure' and review['findings']==[]
checks['result_review_bindings']=all(sha(Path(n) if Path(n).is_absolute() else R/n)==h for n,h in review['sha256'].items())
checks['postcheck_false_preserved']=post['all_passed'] is False and len(post['checks'])==20 and sum(post['checks'].values())==17
checks['postcheck_bindings']=all(sha(R/n)==h for n,h in post['sha256'].items())
checks['source_explanation_bound']=analysis['all_passed'] and len(analysis['checks'])==10 and all(sha(n)==h for n,h in analysis['sha256'].items())
for phase in ('red','green'):
    checks[phase+'_all_launch_pins_unchanged']=guard.pins_match(rd(A/(phase+'-launch-pins.json')))
    checks[phase+'_all_sealed_pins_unchanged']=guard.pins_match(rd(A/(phase+'-sealed-pins.json')))
    audit=rd(A/(phase+'-audit.json'))
    checks[phase+'_audit_bindings']=all(sha(n)==h for n,h in audit['sha256'].items())
r=post['results']['red'];g=post['results']['green']
checks['red_expected_failure_accepted']=r['raw']['total_fail']==3 and r['raw']['total_pass']==0 and r['raw']['total_error']==0 and r['exit']==1 and rd(A/'red-audit.json')['all_passed'] is True
checks['green_failed_prefix_preserved']=g['raw']['total_pass']==89 and g['raw']['total_error']==1 and g['raw']['total_fail']==0 and not g['raw']['completed'] and len(g['raw']['groups'])==1 and g['exit']==2 and rd(A/'green-audit.json')['all_passed'] is False
checks['eleven_groups_not_started']=all(not (A/'green-run'/f'started-{n}.toml').exists() for n in range(2,13))
checks['consumed_reservations_unchanged']=all(rd(A/(p+'-reservation.json'))['one_attempt'] is True for p in ('red','green'))
host=rd(D/'final-host.json')
checks['separate_full_host_closure']=len(host['groups'])==200 and host['matches']==[] and all(host[k]==rd(A/'green-posthost.json')[k] for k in ('boot_id','head','master'))
checks['refs_unchanged']=git('rev-parse','HEAD')==host['head'] and git('rev-parse','master')==host['master']=='6f68e24e8ddac42b948da8fcc2d636c010751194'
baseline=rd(D.parent/'DIRECT-LU-PREPARATION/baseline.json')
checks['source_test_CI514_unchanged']=len(baseline['sha256'])==514 and all(sha(R/n)==h for n,h in baseline['sha256'].items())
cont=rd(D/'continuation.json')
checks['four_prior_continuation_mappings']=len(cont['mappings'])==4 and all(sha(R/v['preserved_path'])==v['sha256']==rd(R/v['record'])['sha256'][v['key']] for v in cont['mappings'])
checks['tracked_authored_whitespace']=subprocess.run(['git','diff','--check'],cwd=R).returncode==0
paths=[p for p in D.rglob('*') if p.is_file() and p.name not in ('closure.json','publication.json')]
paths += [A/('stage-'+phase+'-review.md') for phase in ('red','green')]
for phase in ('red','green'):
    paths += [p for p in A.glob(phase+'-*') if p.is_file()]+[p for p in (A/(phase+'-run')).rglob('*') if p.is_file()]
paths += [R/'diagnostics/simplex-core-architecture/DIRECT-LU-CORRECTNESS.md',R/'diagnostics/simplex-core-architecture/STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md']
result=dict(all_passed=all(checks.values()),checks=checks,scope='Accepted preservation and diagnosis of failed correctness, NOT numerical acceptance',sha256={str(p.relative_to(R)):sha(p) for p in sorted(set(paths))})
save(D/'closure.json',result);print(json.dumps(dict(all_passed=result['all_passed'],checks=checks,bindings=len(result['sha256'])),indent=2));req(result['all_passed'],'Diagnostic closure refused')
