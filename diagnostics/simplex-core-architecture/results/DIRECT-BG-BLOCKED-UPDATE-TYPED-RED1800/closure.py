"""One OOM/SIGSEGV diagnostic closure; never accepts incomplete RED."""
from pathlib import Path
import sys,json
E=Path(__file__).resolve().parent;D=E.with_name('DIRECT-BG-BLOCKED-UPDATE-TYPED-RED1800-HARNESS');R=D.parents[3];sys.path.insert(0,str(D));import control as c
run=D/'runs/red1800';o=D/'outers/red1800';checks={}
def ck(k,v):
 checks[k]=bool(v)
 if not v:raise RuntimeError(k)
v=c.rd(E/'result-review.json');expected={str(p) for root in [run,o] for p in root.rglob('*') if p.is_file()}
ck('independent_diagnostic_only',v.get('accepted') is True and v.get('qualification_accepted') is False and v.get('findings')==[] and v.get('scope')=='BG blocked typed RED1800 OOM diagnostic' and v.get('phase')=='red1800')
ck('exact_result_review_bindings',set(v['sha256'])==expected and c.bindings(v) and c.bindings(v,'evidence_sha256'))
p=c.rd(E/'postcheck.json');ck('supplemental_prefix_checks',p['all_passed'] is True and p['qualification_accepted'] is False and all(p['checks'].values()) and c.bindings(p))
a=c.rd(run/'audit.json');ck('original_false_audit_preserved',a['all_passed'] is False and a['pure_timeout'] is False and c.bindings(a))
ck('no_RED_acceptance_or_GREEN',not (run/'result-review.json').exists() and not (D/'runs/green1800').exists() and not (D/'outers/green1800').exists())
ck('external_closure',c.validate_result_closure('red1800',c.rd(run/'outer-closure.json')))
ck('preparation_frozen',bool(c.preparation()))
ck('expected_refs',c.git('rev-parse','HEAD')=='cc9d35dc3e2c526bcae8b752ca2ea43dad9a5212' and c.git('rev-parse','master')==c.MASTER)
ck('tracked_clean',c.git('diff','--name-only')==c.git('diff','--cached','--name-only')=='')
h=c.full_host(c.rd(run/'outer-closure.json')['host']['groups']);h['memory']=c.guard.memory();ck('fresh292groups_sessions_closed',len(h['groups'])==292 and c.host_safe(h));c.save(E/'host-final.json',h)
ledger=R/'.superpowers/sdd/2026-10-19-direct-bg-blocked-update/progress.md';before=(E/'progress.md.before-red1800').read_bytes();ck('continuation_before_exact',ledger.read_bytes()==before)
text='''\n\n## Blocked BG RED1800 incomplete OOM/SIGSEGV\n\nOne separately and independently admitted 1800-second repeat is consumed. The child ended with exit-11 after776.087964727s, following fatal OutOfMemoryError then SIGSEGV during finalizers. Supervisor776.724177337s/return1/accepted=false; outer786.032045617s/return2 includes integrity checks outside the supervisor. No timeout or termination flag was set. The admitted audit remains all_passed=false, pure_timeout=false, Exact payload membership. No automatic retry or higher memory limit.\n\nExactly27 payload files survive: units1..12/costs1..12/three loads. The saved prefix has55695 passes, two expected N026 failures (dense96/native and Markowitz), zero errors/broken. Panel11768 including P011 and P095-P102 passes; both sparse256 cases completed. Unit13 dense256/native began without saved completion/cost; units14..28 did not start, final raw absent. Six expected failures and full RED remain unverified, GREEN/Task3 blocked.\n\nThe775 samples have minimum availableRAM14527116KiB and swap0; sampled VmPeak reaches8388608KiB, matching unchanged RLIMIT_AS8GiB. OS wait maxRSS7709432KiB and sampled HWM7710180KiB are separate records. Free system RAM does not remove the per-process virtual-address-space cap. Logs support memory exhaustion under that cap, but do not locate the initial application allocation or prove a leak/BG defect. Saved sparse256 cold costs are172.390993109s/173.484848308s and roughly182GB cumulative allocation traffic each, not retained memory or production performance. No unit13 cost attribution.\n\nAdmission3467 checks passed, exact2352 seal subjects/2353 review bindings/2357 launch subjects. Initial reviewer-shell PATH assertion failure and corrected v2 actual-outer environment check remain preserved. New supplemental prefix check21PASS and fresh independent diagnostic review accepted fidelity only. All292 historical/new groups AND sessions are absent, with executable-link visibility limits explicit. Prior RED300 timeout and its81 lineage bindings remain unchanged and unaccepted.\n\nRuling: complete RED, unit13 mathematics, exact initial allocating operation, native retention and Task3 performance are outside the evidence; no numerical acceptance follows. The next useful work is source/log analysis of diagnostic allocation and retention before any separate proposal. Production/test/environment/CI/master/global STATUS/roadmap remain unchanged. Preserve all raw files, old failures and worktrees.\n'''
after=before+text.encode()
with (E/'progress.md.after-red1800').open('xb') as f:f.write(after)
ledger.write_bytes(after);ck('continuation_append_exact',ledger.read_bytes()==after)
files=sorted(p for root in [E,run,o] for p in root.rglob('*') if p.is_file())
c.save(E/'closure.json',dict(all_passed=True,qualification_accepted=False,checks=checks,sha256={str(p):c.sha(p) for p in files},scope='Diagnostic fidelity/publication closure; RED remains unaccepted'))
print(json.dumps(dict(all_passed=True,qualification_accepted=False,checks=len(checks),bindings=len(files))))
