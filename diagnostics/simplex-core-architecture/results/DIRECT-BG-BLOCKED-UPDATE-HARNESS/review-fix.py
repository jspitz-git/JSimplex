from pathlib import Path
import json,hashlib,sys,importlib.util,copy
H=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-HARNESS')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def change(n,a,b):
 p=H/n;s=p.read_text()
 if s.count(a)!=1:raise RuntimeError((n,a,s.count(a)))
 p.write_text(s.replace(a,b))
for n in ['driver.jl','oracle.py','control.py','audit.py','ADMISSION.md','REPORT.md','MEMORY-WORK.md','preparation-pins.json','required-paths.json']:
 with (H/(n+'.before-review')).open('xb') as f:f.write((H/n).read_bytes())
(H/'review-fix.py').write_bytes(Path(__file__).read_bytes())
change('driver.jl','    totals(root)\nend\nfunction main()', '''    a=totals(root)
    expected=RED && name in ("dense96/native","dense96/markowitz","dense256/native","dense256/markowitz","dense96-long32/native","dense96-long32/markowitz") ? 1 : 0
    require(a[2]==expected && a[3]==a[4]==0 && HarnessRecords.failure_count[]==expected &&
        all(r["site"]=="N026" && r["kind"]=="fail" for r in HarnessRecords.failures),"Unexpected unit failure; saved prefix retained")
    a
end
function main()''')
change('oracle.py',"def trace_counts(e,finished):\n",'''TRACE_EVENTS={'pivot','pure_row','finish','declined_before_gather'}|{'event_'+s for s in ['begin','finish','panel_begin','panel_pivot','scalar_pivot','pure','panel_reject','panel_commit','eligibility','scalar_suffix']}
def trace_counts(e,finished):
 need(set(e)<=TRACE_EVENTS|{'catch_overflow','catch_nonfinite'},'Unknown trace event')
 need(e.get('event_pure',0)<=e.get('pure_row',0) and (e.get('event_pure',0)==0)==(e.get('pure_row',0)==0),'Pure event/row consistency')
 need(e.get('event_scalar_suffix',0)<=finished,'At most one scalar suffix/trace')
 begun=e.get('event_panel_begin',0);committed=e.get('event_panel_commit',0);rejected=e.get('event_panel_reject',0);declined=e.get('declined_before_gather',0)
 need(0<=declined<=rejected<=finished and begun==committed+rejected-declined and e.get('event_eligibility',0)==begun+declined,'Panel/eligibility attempt accounting')
 need(8*committed<=e.get('event_panel_pivot',0)<=8*begun,'Panel raw pivot budget')
''')
change('oracle.py',"  f=schedule['fixtures'][(index-3)//2];u=f['updates'];n=f['n']\n", "  f=schedule['fixtures'][(index-3)//2];u=f['updates'];n=f['n']\n  need(set(e)<=TRACE_EVENTS,'Unexpected stream catch/event')\n")
# Recorded remote refs belong to each fresh host, not an unrecorded post-run condition.
change('control.py'," return dict(time=time.time(),groups=groups,matches=matches,boot_id=", " return dict(remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'),time=time.time(),groups=groups,matches=matches,boot_id=")
change('control.py',"def host_safe(h):return h.get('matches')==[] and h.get('unreadable_identity_pids')==[]", "def host_safe(h):return h.get('matches')==[] and h.get('unreadable_identity_pids')==[] and h['head']+'\\trefs/heads/codex/simplex-core-architecture' in h.get('remote','') and h['master']==MASTER and MASTER+'\\trefs/heads/master' in h.get('remote','')")
change('audit.py',' prefix(saved_units,schedule,phase)\n','')
change('audit.py',"and sup.get('accepted') is False and not any(s in log for s in ['TEST FAILURE:','FATAL DRIVER:','GROUP/COUNT MISMATCH'])", "and sup.get('accepted') is False and 'error' not in p and not any(s in log for s in ['TEST FAILURE:','BROKEN TEST:','ERROR:','FATAL DRIVER:','GROUP/COUNT MISMATCH','LoadError','Test Failed','Test Error','OutOfMemoryError'])")
change('audit.py'," if pure:return dict(all_passed=False,pure_timeout=True,result={},error='Incomplete pure timeout; separate reviewed longer admission required')", " if pure:\n  prefix(saved_units,schedule,phase)\n  return dict(all_passed=False,pure_timeout=True,result={},error='Incomplete pure timeout; separate reviewed longer admission required')")
with (H/'ADMISSION.md').open('a') as f:f.write('''
## Independent-review corrections

After every unit is saved, the driver stops before the next unit on any unexpected Fail/Error/Broken or wrong named failure identity. Only the exact expected RED coverage failures continue. Closed event names and pure-row/panel/eligibility consistency supplement fixed trace completion counts. Fresh host evidence now records and validates both remote diagnostic and master refs at sealing and launch, not merely at publication. Timeout classification also rejects explicit process errors and failure/error/OOM log markers. Complete output passes the result oracle once; timeout prefixes use the prefix oracle separately. Original drafts and first review are preserved under `.before-review`/`review-first` files.
''')
with (H/'MEMORY-WORK.md').open('a') as f:f.write('\nReview amendment: full successful result validation executes once (removed a duplicate prefix validation); unexpected unit failures stop subsequent costly units. Event counters have a closed bounded vocabulary. No additional numerical work or candidate memory.\n')
with (H/'REPORT.md').open('a') as f:f.write('\nIndependent-review findings are addressed by saved-prefix stop at unit boundaries, closed event bookkeeping, fresh recorded remote refs at admission/launch, and stricter timeout classification. Drafts and original preparation manifest are preserved. Final reviewer acceptance and supplementary checks will bind corrected bytes separately; original hashes are not retroactively changed.\n')
# New synthetic helpers and exclusive result paths; initial scripts/results frozen.
s=(H/'synthetic.py').read_text().replace("'event_panel_pivot':12}","'event_scalar_pivot':12}")
s=s.replace("e.update(event_panel_begin=panels,event_panel_commit=panels,event_eligibility=panels)","e.update(event_panel_begin=panels,event_panel_commit=panels,event_eligibility=panels,event_panel_pivot=8*panels,pivot=2*u+8*panels)")
s=s.replace("   'missing_unit':", "   'unknown_event':lambda r,w:w['unit-3.toml']['records']['events'].update(unknown_event=1),\n   'pure_without_rows':lambda r,w:w['unit-3.toml']['records']['events'].update(event_pure=1),\n   'unknown_stream_catch':lambda r,w:w['unit-3.toml']['records']['events'].update(catch_overflow=1),\n   'missing_unit':")
s=s.replace("D/'synthetic.json'","D/'synthetic-reviewed.json'")
with (H/'synthetic-reviewed.py').open('x') as f:f.write(s)
s=(H/'full-audit-tests.py').read_text().replace('from synthetic import mock,S',"import importlib.util\nspec=importlib.util.spec_from_file_location('synthetic_reviewed',D/'synthetic-reviewed.py');sm=importlib.util.module_from_spec(spec);spec.loader.exec_module(sm);mock,S=sm.mock,sm.S")
s=s.replace("host=dict(head='h',master='m',boot_id='b',groups=[1],matches=[],unreadable_identity_pids=[])","host=dict(head='h',master=a.MASTER,boot_id='b',groups=[1],matches=[],unreadable_identity_pids=[],remote='h\\trefs/heads/codex/simplex-core-architecture\\n'+a.MASTER+'\\trefs/heads/master')")
s=s.replace("config=cfg,head='h',master='m',boot_id", "config=cfg,head='h',master=a.MASTER,boot_id")
s=s.replace("   'missing_unit':", "   'remote_diagnostic_drift':lambda:mutate('prehost.json',lambda v:v.update(remote=a.MASTER+'\\trefs/heads/master'),run),\n   'unknown_event':lambda:mutate('unit-3.toml',lambda v:v['records']['events'].update(unknown_event=1)),\n   'missing_unit':")
s=s.replace("  (out/'unit-1.toml').write_text('{');", "  (out/'run.log').write_text('BEGIN BG blocked U driver red300\\nERROR: saved failure');rejected('error_log_not_pure_timeout',lambda:a.checks_for('red300'))\n  (out/'run.log').write_text('BEGIN BG blocked U driver red300\\n')\n  mutate('process.json',lambda v:v.update(error='original exception'));rejected('process_error_not_pure_timeout',lambda:a.checks_for('red300'))\n  mutate('process.json',lambda v:v.pop('error'))\n  (out/'unit-1.toml').write_text('{');")
s=s.replace("D/'full-audit-tests.json'","D/'full-audit-tests-reviewed.json'")
with (H/'full-audit-tests-reviewed.py').open('x') as f:f.write(s)
print('Separate review fixes and revised controls prepared')
