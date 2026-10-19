"""One GREEN result closure after independent review, no numerical/auditor rerun."""
from pathlib import Path
import sys,json,hashlib,subprocess
E=Path(__file__).resolve().parent;R=E.parents[3];D=E.with_name('DIRECT-BG-P011-TYPED-HARNESS');sys.path.insert(0,str(D));import control as c
phase='p011-green300';run=D/'runs'/phase;outer=D/'outers'/phase
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
checks={}
def check(k,v):
 checks[k]=bool(v)
 if not v:raise RuntimeError(k)
v=rd(run/'result-review.json')
check('independent_result_accepted',v['accepted'] is True and v['findings']==[] and v['scope']=='P011 typed GREEN result' and v['phase']==phase)
files,groups=c.result_review(phase,'P011 typed GREEN result','result-review.json');check('exact_result_membership',len(files)==27)
check('review_supplementary_bindings',all(sha(n)==h for n,h in v.get('evidence_sha256',{}).items()))
check('admitted_external_closure',c.validate_result_closure(phase,rd(run/'outer-closure.json')) is True)
rv=rd(E/'result-review-check.json');check('independent_result_checks',rv['all_passed'] is True and rv['findings']==[] and len(rv['checks'])>0 and all(x['passed'] is True for x in rv['checks']))
check('admitted_audit_pass',rd(run/'audit.json')['all_passed'] is True)
check('audit_unchanged_bindings',all(sha(n)==h for n,h in rd(run/'audit.json')['sha256'].items()))
post=rd(E/'postcheck.json');check('thirteen_postchecks',post['all_passed'] is True and len(post['checks'])==13 and all(post['checks'].values()))
check('postcheck_bindings',all(sha(n)==h for n,h in post['sha256'].items()))
check('exact_green_result',post['totals']==[11768,0,0,0] and post['failures']==[])
check('four_zero_allocation_counters',all(type(post['probe'][k]) is int and post['probe'][k]==0 for k in ['bytes','events','consumed_bytes','consumed_events']))
check('unchanged_inputs',post['probe']['values_unchanged'] is True and post['probe']['owners_unchanged'] is True)
check('original_harness_and_red_unchanged',bool(c.preparation()) and bool(c.predecessor(phase)[0]))
check('entry_refs',git('rev-parse','HEAD')=='a01d1cde19feb72ee0b6396981281cabf5bd9672' and git('rev-parse','master')==c.MASTER)
check('tracked_index_unchanged',git('diff','--name-only')==git('diff','--cached','--name-only')=='')
h=rd(E/'full-group-closure.json');check('full_history_closure',c.host_safe(h) and set(rd(E/'host-entry.json')['groups'])<=set(h['groups']))
ledger=R/'.superpowers/sdd/2026-10-19-direct-bg-blocked-update/progress.md';old=(E/'progress.md.before-green').read_bytes()
check('continuation_before_preserved',ledger.read_bytes()==old)
p=rd(run/'output/process.json');oi=rd(outer/'outer-ready.json')['identity'];sealed=rd(run/'sealed.json');launch=rd(run/'launch-pins.json')
append=('\n\n## P011 typed measurement repair GREEN completed\n\nOne independently admitted p011-green300 passed 11768 assertions with no failures/errors/broken tests; exact P001-P102 occurrences and four groups passed. Four typed-probe allocation counters are zero; complete decisions, input values and selected owners are preserved. Accepted RED remains frozen, no rerun.\n\n'
 + "Independent result checks: " + str(len(rv["checks"])) + "; admitted auditor and 13 supplemental checks PASS. Seal/launch inventory: " + str(len(sealed["files"])) + "/" + str(len(launch["inventory"])) + ". Limits: 300 seconds supervisor, 292 seconds child. All exits zero, no timeout/retry. Inclusive child seconds (not benchmark): " + str(post["process_seconds"]) + ". Resources: " + json.dumps(post["resource_summary"],sort_keys=True) + "\n\n"
 + "Full historical closure: " + str(len(h["groups"])) + " groups AND sessions, all absent/no visible Julia, including old RED outer. Next preflight must use this full list. New identities: " + json.dumps({"outer":oi,"runner":p["runner"],"child":p["child"]},sort_keys=True) + "\n\n"
 + 'Cold compilation, snapshots and serialization costs are saved; overlapping records do not establish a speedup. No production work/memory or safeguard change, lifecycle/stream/six-N026 qualification, Task3 measurement or production integration. Exact P011 measurement repair qualified; broader blocked BG Task2/Task3 open.\n\nCompleted evidence/scripts/admissions/audits/reviews frozen. Next separate preparation may apply accepted typed P011 repair and shared-zero candidate to remaining blocked-update RED/GREEN harness, with source/input/review gates. Do not reuse this consumed attempt or automatically launch further numerics. Master 26e2291, CI and global STATUS/roadmap unchanged.\n').encode()
after=old+append
with (E/'progress.md.after-green').open('xb') as f:f.write(after)
ledger.write_bytes(after);check('continuation_exact_append',ledger.read_bytes()==after and after.startswith(old))
files=sorted(p for root in [E,run,outer] for p in root.rglob('*') if p.is_file())
with (E/'closure.json').open('x') as f:json.dump(dict(all_passed=True,checks=checks,scope='P011 GREEN measurement repair qualified; wider blocked-update qualification open',sha256={str(p):sha(p) for p in files}),f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=True,checks=len(checks),bindings=len(files))))
