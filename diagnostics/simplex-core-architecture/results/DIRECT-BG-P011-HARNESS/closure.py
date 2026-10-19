"""One-shot offline publication closure. Never launches diagnostic entrypoints."""
from pathlib import Path
import json
import control as c
D=c.D
checks={}
def check(n,v): checks[n]=bool(v)
def bindings(name,old=False):
 j=c.rd(D/name)
 mapping={'audit.py':'audit.py.before-review','ADMISSION.md':'ADMISSION.md.before-review','required-paths.json':'required-paths.initial.json','preparation-pins.json':'preparation-pins.initial.json'}
 for n,h in j.get('sha256',{}).items():
  p=Path(n);p=p if p.is_absolute() else D/p
  if old and p.parent==D and p.name in mapping:p=D/mapping[p.name]
  if c.sha(p)!=h:return False
 return True
prepared=c.preparation()
r=c.rd(D/'review.json')
check('accepted_exact_preparation',r['accepted'] is True and r['findings']==[] and len(r['sha256'])==88)
check('launch_unadmitted',r['launch_admitted'] is False and r['julia_invoked'] is False and r['execution_entrypoints_invoked'] is False)
for n,count in [('tests-reviewed.json',392),('review-final-evidence.json',22)]:
 j=c.rd(D/n);check(n,j['all_passed'] is True and j['count']==count and len(j['checks'])==count and bindings(n))
for n,count in [('fix-check.json',6),('source-supplement.json',5)]:
 j=c.rd(D/n);check(n,j['all_passed'] is True and len(j['checks'])==count and all(v is True for v in j['checks'].values()) and bindings(n))
s=c.rd(D/'source-check.json')
check('original_false_preserved',s['all_passed'] is False and len(s['checks'])==26 and [k for k,v in s['checks'].items() if not v]==['two_args'] and bindings('source-check.json',True))
check('original_synthetics_preserved',c.rd(D/'tests.json')['count']==382 and c.rd(D/'tests.json')['all_passed'] is True and bindings('tests.json',True))
j=c.rd(D/'review-initial.json')
check('rejection_preserved',j['accepted'] is False and len(j['findings'])==1 and bindings('review-initial.json',True))
check('original_manifest_preserved',len(c.rd(D/'preparation-pins.initial.json')['sha256'])==74 and bindings('preparation-pins.initial.json',True) and j['pins_sha256']==c.sha(D/'preparation-pins.initial.json'))
check('no_run_outputs',not (D/'runs').exists() and not (D/'outers').exists())
check('driver_frozen',c.sha(c.PROBE/'driver.jl')=='29c8d67755e4f86a7375f89536d24a0cb119a06a583650bc3f31bc9eccc956bf')
check('entry_ref',c.git('rev-parse','HEAD')==c.ENTRY)
check('master_ref',c.git('rev-parse','master')==c.MASTER)
check('no_tracked_edits',c.git('diff','--name-only')=='' and c.git('diff','--cached','--name-only')=='')
h=c.rd(D/'host-final.json');check('fresh_host',c.host_safe(h) and len(h['groups'])==274)
w=c.R/'.superpowers/sdd/2026-10-19-direct-bg-blocked-update/progress.md'
check('ledger_snapshot',w.read_bytes()==(D/'progress.md.final-P011-harness').read_bytes())
paths=sorted(p for p in D.iterdir() if p.is_file())
result=dict(all_passed=all(checks.values()),checks=checks,sha256={str(p):c.sha(p) for p in paths},scope='Offline closure only; saved synthetic evidence checked, no reruns or Julia')
c.save(D/'closure.json',result)
print(json.dumps({'all_passed':result['all_passed'],'checks':checks,'bindings':len(paths)}))
if not result['all_passed']:raise SystemExit(1)
