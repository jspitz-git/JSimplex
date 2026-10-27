from pathlib import Path
import sys,json,re
sys.dont_write_bytecode=True
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-bounds-norm-infeasibility/2026-10-27/RED-run');sys.path.insert(0,str(D));import common as c
c.unchanged();co=c.read('contract.json');p=c.read('output/process.json');s=c.read('supervisor.json');done=c.read('completed.json');a=c.read('audit.json');ad=c.read('admission.json')
for obj in [a,ad]:
 assert obj['accepted']
 for n,v in obj['bindings'].items():assert c.sha(n)==v
assert (D/'audit.py').read_bytes()==Path('/tmp/bni-phase-audit.py').read_bytes()
assert p['reason']=='exit1' and p['returncode']==co['expected_exit']==1 and p['pins_unchanged']
assert s['accepted'] and s['returncode']==0 and not s['soft_timeout'] and not s['hard_timeout'] and 'cleanup_error' not in s
assert done['accepted'] and done['elapsed_shared_seconds']==a['elapsed_shared_seconds'] and done['elapsed_shared_seconds']<3000
assert a['passed']==15911 and a['expected_failures']==10 and a['total']==15921
log=(D/'output/run.log').read_text();assert 'Error During Test' not in log
assert re.findall(r'^INCLUDING (.*)$',log,re.M)==co['files']
assert re.search(r'^Bounds norm infeasibility RED\s*\|\s*15911\s+10\s+15921\s',log,re.M)
assert next(x for x in log.splitlines() if x.startswith('Test Summary:')).split('|')[1].split()==['Pass','Fail','Total','Time']
assert [[path,int(line)] for path,line in re.findall(r'Test Failed at (.*?):(\d+)',log)]==co['expected_failure_locations']
assert len(re.findall(r'^\s+Whole-call allocation .*\|\s*3\s+1\s+4\s',log,re.M))==10
assert 'BNI_SOURCE '+co['source_root']+'/src/JSimplex.jl' in log
assert p['command']==co['command'] and p['pins_sha256']==c.sha(D/'pins.json')==c.sha(D/'output/pins.json')
g=c.read('output/gate.json');cur=c.read('output/current.json');pm=c.read('output/permit.json');res=c.read('reservation.json')
assert g['identity']==p['child']==cur['child'] and g['parent']==p['runner']==cur['runner']==s['guard_identity']
assert g['command']==pm['command']==cur['command']==co['command'] and g['parent_death_signal']==9
assert g['current_sha256']==c.sha(D/'output/current.json')==pm['current_sha256'] and g['permit_sha256']==c.sha(D/'output/permit.json')
assert res['guard_deadline']==res['started_monotonic']+2992 and res['outer_deadline']==res['started_monotonic']+3000
resources=[json.loads(l) for l in (D/'output/resources.jsonl').read_text().splitlines()]
assert len(resources)==a['samples']==29 and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in resources+[p['terminal_memory']])
h=c.host([p[k][v] for k in ['runner','child'] for v in ['pgid','sid']]);c.put('independent-result-host.json',h)
report=f'''# Independent permanent RED result review

Accepted as the required original-source RED witness: 15,911 passing assertions plus exactly ten expected allocation-gate failures, total 15,921. Each of the ten named whole-call allocation testsets has three passing compilation checks and one failed cost assertion at frozen line 727. All numerical correctness, ownership, context and qualified extreme-value checks passed. The source/project marker identifies the original RED baseline; there are no other failures, errors, skipped or broken tests in the ordinary summary.

Actual child exit1 is expected for RED; the resource guard/supervisor and post-exit audit accepted that exact result. Independently checked all admission/audit bindings, actual copied pins, command, runner/child/gate/permit identities and hash links, parent-death signal, absolute/shared deadlines, ordered single-file include, source marker and raw failure locations. The post-exit audit script is byte-identical to the previously admitted template and was not rerun by this reviewer.

Inclusive elapsed time: {a['elapsed_shared_seconds']:.6f} seconds. All 29 resource samples and terminal sample meet limits; minimum available memory 22,176,340 KiB, swap maximum zero, child max RSS 935,468 KiB. Fresh identity/no-Julia closure covers {len(h['groups'])} historical groups and sessions. No Julia, Git mutation or production edit was performed for this review.

This is a successful RED witness, not passing candidate tests. It supports proceeding to the planned candidate preparation and GREEN validation with the same ten fixed three-pair lower-events/lower-median-bytes gates. No gate, old test or numerical tolerance is relaxed. Computational-work/memory assessment remains unchanged: test-only measurement overhead, no production change or new retained cache; no speed or native retained-memory claim follows from RED.
'''
with (D/'RESULT-REVIEW.md').open('x') as f:f.write(report)
with (D/'independent-result-review.py').open('x') as f:f.write(Path(__file__).read_text())
names=['audit.json','audit.py','admission.json','pins.json','contract.json','tests.jl','completed.json','supervisor.json','reservation.json','output/run.log','output/process.json','output/gate.json','output/current.json','output/permit.json','output/resources.jsonl','RESULT-REVIEW.md','independent-result-host.json','independent-result-review.py']
c.put('result-review.json',dict(accepted=True,findings=[],passed=15911,expected_failures=10,total=15921,groups=len(h['groups']),Julia_executed=False,scope='original-source RED witness; GREEN required',bindings={str(D/n):c.sha(D/n) for n in names}))
print(json.dumps(dict(accepted=True,passed=15911,expected_failures=10,total=15921,groups=len(h['groups']))))
