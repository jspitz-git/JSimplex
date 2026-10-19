"""One new offline preparation closure after independent review."""
from pathlib import Path
import sys,json,subprocess
D=Path(__file__).resolve().parent;R=D.parents[3];sys.path.insert(0,str(D));import control as c
checks={}
def check(k,v):
 checks[k]=bool(v)
 if not v:raise RuntimeError(k)
review=c.rd(D/'review.json');m=D/'preparation-pins.json';pins=c.rd(m)
c.verify_review(review,m,list(pins['sha256'])+[str(m)],'BG blocked typed harness preparation')
check('independent_preparation_accepted_not_launch',review['accepted'] is True and review['findings']==[] and review.get('launch_admitted') is False)
check('prepared_bindings',bool(c.preparation()))
check('all_copied_sources_unchanged',all(c.sha(D/n)==v['sha256']==c.sha(v['source']) for n,v in c.rd(D/'copied-files.json').items()))
c.validate_qualification();check('prior_qualifications_fault_inverse_unchanged',True)
t=c.rd(D/'tests.json');check('synthetic_tests_pass',t['all_passed'] is True and t['count']==4736 and c.bindings(t))
s=c.rd(D/'source-check.json');check('source_checks_pass',s['all_passed'] is True and len(s['checks'])==27 and all(s['checks'].values()) and c.bindings(s))
check('no_numerical_artifacts',not any((D/n).exists() for n in ['runs','outers']))
check('master_and_entry',c.git('rev-parse','HEAD')=='2821702085f6bdaceb48c71a8774c99200e242eb' and c.git('rev-parse','master')==c.MASTER)
check('tracked_clean',c.git('diff','--name-only')==c.git('diff','--cached','--name-only')=='')
h=c.full_host(c.rd(D/'historical-groups.json')['groups']);h['memory']=c.guard.memory();check('fresh_full286_groups_sessions_no_julia',len(h['groups'])==286 and c.host_safe(h));c.save(D/'host-closure.json',h)
ledger=R/'.superpowers/sdd/2026-10-19-direct-bg-blocked-update/progress.md';before=(D/'progress.md.pre-review').read_bytes();check('continuation_preserved',ledger.read_bytes()==before)
text='\n\nBlocked BG typed RED/GREEN harness preparation independently accepted, no open findings; launch_admitted=false. Exact preparation manifest and reviewer receipt bound. Python synthetic 4736/source27 passed; no Julia, seal, outer, reservation, release, or numerical output. New 28-unit/168-site/60-payload harness keeps original numerical/lifecycle tests and fixtures; accepted typed P011 and immutable zero counters used in both future phases. RED expects only six N026 coverage failures; GREEN requires newly accepted full RED and external closure first. Historical P011 GREEN and immutable-zero qualification preserved. Fresh full286 historical PGIDs AND SIDs clean. No unnecessary production work/memory introduced; cold snapshots/timers/serialization recorded and overlapping, no speedup claim. Next possible step: fresh exact red300 admission and independent approval, only on explicit execution request. Master26e2291/CI/global STATUS/roadmap unchanged; broader Task2/Task3 open. All preparation artifacts frozen after publication; no old rerun or workspace cleanup.\n'
after=before+text.encode()
with (D/'progress.md.after-preparation').open('xb') as f:f.write(after)
ledger.write_bytes(after);check('continuation_exact_append',ledger.read_bytes()==after)
files=sorted(p for p in D.rglob('*') if p.is_file());c.save(D/'closure.json',{'all_passed':True,'checks':checks,'sha256':{str(p):c.sha(p) for p in files},'scope':'Offline preparation only; no numerical admission'})
print(json.dumps({'all_passed':True,'checks':len(checks),'bindings':len(files)}))
