"""Exclusive S5-O publication closure, run only after both independent result reviews."""
from common_reviewed import *
import subprocess,time
info=read(H/'integration.json');checks={}
for label,review in [('green-1','green-review.md'),('master-1','master-review.md')]:
 a=read(H/(label+'-audit.json'));post=read(H/(label+'-postcheck.json'));p=read(B/label/'process.json');pins=read(B/label/'pins.json')
 checks[label+'_audit']=a['all_passed'] is True and all(v is True for v in a['checks'].values())
 checks[label+'_postcheck']=post['all_passed'] is True and all(v is True for v in post['checks'].values())
 checks[label+'_full_pins']=all(sha(f)==v['sha256'] for f,v in pins['inventory'].items())
 checks[label+'_raw_portable']=all(sha(B/label/f)==sha(H/label/f)==v for f,v in a['raw_sha256'].items())
 checks[label+'_review']='Verdict: ACCEPTED' in (H/review).read_text()
 checks[label+'_groups']=not absent([p['runner']['pgid'],p['child']['pgid']])['matches']
s=read(H/'schema.json');checks['actual_candidate_both']=sha(R/REL)==sha(MAIN/REL)==s['candidate_sha256']
checks['all_source_test_CI_equal']=subprocess.check_output(['git','diff','master','--','src','test','.github'],cwd=R)==b''
checks['master_ref']=subprocess.check_output(['git','rev-parse','master'],cwd=R,text=True).strip()==info['master_commit']
checks['only_test_commit']=subprocess.check_output(['git','diff-tree','--no-commit-id','--name-only','-r',info['test_commit']],cwd=R,text=True).splitlines()==[REL]
checks['user6']=all(sha(f)==v for f,v in read(H/'host-before.json')['user_hashes'].items())
checks['historical_N789']=all(sha(H/'original-test.jl' if f==str(R/REL) else f)==v for f,v in read(H.parent/'S5-N/evidence.json')['sha256'].items())
checks['preserved_N_closure']=all(sha(H/'STATUS.md.before-O' if f=='diagnostics/simplex-core-architecture/STATUS.md' else H/'2026-10-11-simplex-core-architecture.md.before-O' if f=='docs/superpowers/plans/2026-10-11-simplex-core-architecture.md' else R/f)==v for f,v in read(H.parent/'S5-N/closure.json')['sha256'].items())
checks['binding_correction']=read(H/'review-fix.json')['all_passed'] is True and 'Verdict: NOT ACCEPTED' in (H/'prelaunch-review.md').read_text() and 'Verdict: ACCEPTED' in (H/'prelaunch-final-review.md').read_text()
paths={p for p in H.iterdir() if p.is_file()}|{R/'diagnostics/simplex-core-architecture/STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',R/'docs/superpowers/plans/2026-10-13-basis-initialization-handoff-contract.md',R/'diagnostics/simplex-core-architecture/S5-DUAL-AUXILIARY-PENDING-OBSERVER-TEST-INTEGRATION.md',R/'diagnostics/simplex-core-architecture/S5-DUAL-AUXILIARY-PENDING-OBSERVER-TEST-INTEGRATION-REVIEW.md'}
x={'all_passed':all(checks.values()),'checks':checks,'sha256':{str(p):sha(p) for p in sorted(paths)},'time_ns':time.time_ns()};dump(H/'closure.json',x)
print(json.dumps({'all_passed':x['all_passed'],'checks':checks}));raise SystemExit(0 if x['all_passed'] else 1)
