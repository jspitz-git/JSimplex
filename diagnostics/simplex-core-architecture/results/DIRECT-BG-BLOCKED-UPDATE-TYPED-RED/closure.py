"""One diagnostic timeout closure; never converts the failed RED to acceptance."""
from pathlib import Path
import sys,json
E=Path(__file__).resolve().parent;D=E.with_name('DIRECT-BG-BLOCKED-UPDATE-TYPED-HARNESS');R=D.parents[3];sys.path.insert(0,str(D));import control as c
run=D/'runs/red300';o=D/'outers/red300';checks={}
def ck(k,v):
 checks[k]=bool(v)
 if not v:raise RuntimeError(k)
v=c.rd(E/'result-review.json');expected={str(p) for root in [run,o] for p in root.rglob('*') if p.is_file()}
ck('independent_timeout_diagnostic_only',v.get('accepted') is True and v.get('qualification_accepted') is False and v.get('findings')==[] and v.get('scope')=='BG blocked typed RED timeout diagnostic' and v.get('phase')=='red300')
ck('exact_result_review_bindings',set(v['sha256'])==expected and c.bindings(v) and c.bindings(v,'evidence_sha256'))
p=c.rd(E/'postcheck.json');ck('supplemental_prefix_checks',p['all_passed'] is True and p['qualification_accepted'] is False and all(p['checks'].values()) and c.bindings(p))
a=c.rd(run/'audit.json');ck('original_false_audit_preserved',a['all_passed'] is False and a['pure_timeout'] is False and c.bindings(a))
ck('no_RED_acceptance_or_GREEN',not (run/'result-review.json').exists() and not (D/'runs/green300').exists() and not (D/'outers/green300').exists())
ck('external_closure',c.validate_result_closure('red300',c.rd(run/'outer-closure.json')))
ck('preparation_frozen',bool(c.preparation()))
ck('expected_refs',c.git('rev-parse','HEAD')=='9a537a3ec590351f2a7b516a4efc53f7c790efaa' and c.git('rev-parse','master')==c.MASTER)
ck('tracked_clean',c.git('diff','--name-only')==c.git('diff','--cached','--name-only')=='')
h=c.full_host(c.rd(run/'outer-closure.json')['host']['groups']);h['memory']=c.guard.memory();ck('fresh289_closed_noJulia',len(h['groups'])==289 and c.host_safe(h));c.save(E/'host-final.json',h)
ledger=R/'.superpowers/sdd/2026-10-19-direct-bg-blocked-update/progress.md';before=(E/'progress.md.before-red').read_bytes();ck('exact_continuation_before',ledger.read_bytes()==before)
text='\n\n## Blocked BG typed RED300 incomplete timeout\n\nOne independently admitted red300 attempt consumed. Admission7140PASS/2220sealed+5launch bindings; first reviewer fixture-metadata comparison failure preserved and separatev2PASS, no target edits. Timeout guardwall_time child-9/292.735178973s; supervisor296.420549699s below300/soft_timeouttrue; outer2/305.6775706s includes outside checks. Original admitted auditfalse/pure_timeoutfalse/Exact payload membership remains frozen. Saved23files: units1..10/costs1..10/load3; no raw or unit11 completion. Completedprefix32793pass/2expectedN026(dense96native+Markowitz)/0error/broken. Panel11768pass includesP011/P095-P102zero-allocation/decision/value-owner predicates; no standalone rawprobe. Interrupted sparse256/native unqualified, sixN026notverified, fullREDNOTaccepted, GREENblocked; no acceptedREDresultreceiptinrun. All289PGIDsANDsessionsabsent/noJulia, old286plus209350/210015/210016; nextfreshpreflightusesfull289.293resource samples minRAM19704276KiB/swap0/maxRSS2655488KiB. Lifecycle146.953642577s/compile5.45724323s/GC70.329119083s/101559811032cumulativeB/666986881events; diagnosticcostnotproductionkernel orliveallocation, no speedup. New offline prefix check and independent diagnostic review8228PASS accepted fidelityonly, no rerun. Ruling: current explicit300s limit and concrete no-auto-retry gate control this attempt; earlier general longer-test preference doesnotadmit retryhere. Later longer admission separately reviewed; do not infer pure-timeoutmathematicalproof from unsavedunit. Review declines fullnumerical/Task3/unrecordedunit judgments becausemissingresults; broaderTask2/Task3open. No production/test/env/CI/master/globalSTATUSroadmapchange. Preserveallraw/scripts/reviews/failedaudit/selectorcorrection; no cleanup or automaticGREEN.\n'
after=before+text.encode();(E/'progress.md.after-red').write_bytes(after);ledger.write_bytes(after);ck('continuation_exact_append',ledger.read_bytes()==after)
files=sorted([p for root in [E,run,o] for p in root.rglob('*') if p.is_file()]);c.save(E/'closure.json',dict(all_passed=True,qualification_accepted=False,checks=checks,sha256={str(p):c.sha(p) for p in files},scope='Diagnostic fidelity/publication closure, not RED qualification'))
print(json.dumps(dict(all_passed=True,qualification_accepted=False,checks=len(checks),bindings=len(files))))
