"""New result closure after independent review; reads saved evidence only."""
from pathlib import Path
import sys,json,hashlib,subprocess
E=Path(__file__).resolve().parent;R=E.parents[3];D=E.with_name('DIRECT-BG-P011-TYPED-HARNESS');sys.path.insert(0,str(D));import control as c
run=D/'runs/p011-red300';outer=D/'outers/p011-red300'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
checks={}
def check(k,v):
 checks[k]=bool(v)
 if not v:raise RuntimeError(k)
v=rd(run/'result-review.json')
check('independent_result_accepted',v['accepted'] is True and v['findings']==[] and v['scope']=='P011 typed RED result' and v['phase']=='p011-red300')
files,groups=c.predecessor('p011-green300');check('real_green_predecessor_gate_read_only',bool(files) and len(groups)==282)
check('review_supplementary_bindings',all(sha(n)==h for n,h in v.get('evidence_sha256',{}).items()))
rv=rd(E/'result-review-check.json')
check('independent_359_checks',rv['all_passed'] is True and rv['findings']==[] and len(rv['checks'])==359 and all(x['passed'] is True for x in rv['checks']))
mapping=rd(E/'result-review-preservation.json')
check('reviewer_initial_bytes_preserved',all(sha(x['preserved'])==x['sha256'] for x in mapping['original_paths_to_preserved'].values()) and sha(E/'result-review-initial.json')==mapping['initial_receipt_sha256'])
check('corrected_reviewer_bound',sha(E/'result-review-check.py')==mapping['corrected_script_sha256'] and sha(E/'result-review-check.json')==sha(E/'result-review-check.corrected.json')==mapping['corrected_result_sha256'])
check('admitted_audit_pass',rd(run/'audit.json')['all_passed'] is True)
check('audit_unchanged_bindings',all(sha(n)==h for n,h in rd(run/'audit.json')['sha256'].items()))
post=rd(E/'postcheck.json');check('twelve_postchecks',post['all_passed'] is True and len(post['checks'])==12 and all(post['checks'].values()))
check('postcheck_bindings',all(sha(n)==h for n,h in post['sha256'].items()))
check('exact_red_result',post['totals']==[11759,1,0,0] and [x['site'] for x in post['failures']]==['P011'])
check('four_zero_allocation_counters',all(type(post['probe'][k]) is int and post['probe'][k]==0 for k in ['bytes','events','consumed_bytes','consumed_events']))
check('unchanged_inputs',post['probe']['values_unchanged'] is True and post['probe']['owners_unchanged'] is True)
check('original_harness_preparation_unchanged',bool(c.preparation()))
check('entry_refs',git('rev-parse','HEAD')=='e2b2ad2ce70301693fe142f04e58b2252271393e' and git('rev-parse','master')==c.MASTER)
check('tracked_index_unchanged',git('diff','--name-only')==git('diff','--cached','--name-only')=='')
check('no_green_action',not (D/'runs/p011-green300').exists() and not (D/'outers/p011-green300').exists())
ledger=R/'.superpowers/sdd/2026-10-19-direct-bg-blocked-update/progress.md';old=(E/'progress.md.before-red').read_bytes()
check('continuation_before_preserved',ledger.read_bytes()==old)
append=b'\n\nP011 typed harness RED completed once and independently accepted. Exact new phase p011-red300 on prepared shared-zero kernel/original P011:11759pass/1expectedP011fail/0error/0broken; nine payloads, admitted auditorPASS, twelve supplemental saved-result checksPASS. Separate typed n32probe direct and consumed arms0B/0events, three full dimension-rejection decisions and input values/selectedowners preserved; original macro byte amount/object identity NOTmeasured. Fresh admission170checks/1901sealedfiles+seal, launch1906inventory, 300s supervisor/292schild. Childexit1/guard-supervisor-outer0, childinclusive9.536379164s/supervisor10.086823962s, no timeout/termination/retry. Nine resource samples,minRAM21899296KiBswap0,maxchildRSS720912KiB. External closurefull283groupsANDsessions/no visibleJulia; boot1ecae454-f1f5-4e2e-a95c-7b5474243126 outer200591 start14111913,guard201265 start14132642,child201266 start14132697 (PID=PGID=SID each), all absent. Include all three new IDs with historical280 in next fresh host scan. Saved result review exact run membership accepted; GREEN predecessor gate checked read-only. Cold load/probe/test compilation+snapshots+serialization retained; overlapping recordsNOTspeedup, no production work/memory/safeguard change. No GREEN/lifecycle/streams/sixN026/Task3 measurement. All raw/scripts/audits/admissions frozen, never rerun/rewrite. Next freshGREEN preflight/exact independent admission and one prepared p011-green300 if requested; no automatic launch. Master26e2291/CI/globalSTATUSroadmap unchanged; broaderplanopen.\n'
after=old+append
with (E/'progress.md.after-red').open('xb') as f:f.write(after)
ledger.write_bytes(after);check('continuation_exact_append',ledger.read_bytes()==after and after.startswith(old))
files=sorted(p for root in [E,run,outer] for p in root.rglob('*') if p.is_file())
with (E/'closure.json').open('x') as f:json.dump(dict(all_passed=True,checks=checks,scope='RED qualified only; no GREEN or broader performance acceptance',sha256={str(p):sha(p) for p in files}),f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=True,checks=len(checks),bindings=len(files))))
