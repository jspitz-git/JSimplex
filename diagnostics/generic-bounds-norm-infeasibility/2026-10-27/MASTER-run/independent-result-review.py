from pathlib import Path
import sys,json,re,subprocess,hashlib
sys.dont_write_bytecode=True
O=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-bounds-norm-infeasibility/2026-10-27');D=O/'MASTER-run';sys.path.insert(0,str(D));import common as c
c.unchanged();co=c.read('contract.json');p=c.read('output/process.json');s=c.read('supervisor.json');done=c.read('completed.json');a=c.read('audit.json');ad=c.read('admission.json')
for obj in [a,ad]:
 assert obj['accepted']
 for n,v in obj['bindings'].items():assert c.sha(n)==v
assert (D/'audit.py').read_bytes()==Path('/tmp/bni-phase-audit.py').read_bytes()==(O/'RED-run/audit.py').read_bytes()
assert p['reason']=='exit0' and p['returncode']==co['expected_exit']==0 and p['pins_unchanged']
assert s['accepted'] and s['returncode']==0 and not s['soft_timeout'] and not s['hard_timeout'] and 'cleanup_error' not in s
assert done['accepted'] and done['elapsed_shared_seconds']==a['elapsed_shared_seconds'] and done['elapsed_shared_seconds']<3000
assert a['passed']==a['total']==co['expected_total']==314009 and a['expected_failures']==0
log=(D/'output/run.log').read_text();assert 'Error During Test' not in log and 'Test Failed at ' not in log and not re.search(r'^ERROR:',log,re.M)
assert re.findall(r'^INCLUDING (.*)$',log,re.M)==co['files'] and len(co['files'])==51
assert re.search(r'^Bounds norm infeasibility MASTER\s*\|\s*314009\s+314009\s',log,re.M)
assert next(x for x in log.splitlines() if x.startswith('Test Summary:')).split('|')[1].split()==['Pass','Total','Time']
assert log.count('BNI_COMPLETED MASTER')==1 and 'BNI_SOURCE '+str(c.M/'src/JSimplex.jl') in log
assert p['command']==co['command'] and p['pins_sha256']==c.sha(D/'pins.json')==c.sha(D/'output/pins.json')
g=c.read('output/gate.json');cur=c.read('output/current.json');pm=c.read('output/permit.json');res=c.read('reservation.json')
assert g['identity']==p['child']==cur['child'] and g['parent']==p['runner']==cur['runner']==s['guard_identity']
assert g['command']==pm['command']==cur['command']==co['command'] and g['parent_death_signal']==9
assert g['current_sha256']==c.sha(D/'output/current.json')==pm['current_sha256'] and g['permit_sha256']==c.sha(D/'output/permit.json')
assert res['guard_deadline']==res['started_monotonic']+2992 and res['outer_deadline']==res['started_monotonic']+3000
resources=[json.loads(l) for l in (D/'output/resources.jsonl').read_text().splitlines()]
assert len(resources)==a['samples']==1926 and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in resources+[p['terminal_memory']])
assert min(x['available_kib'] for x in resources)==a['minimum_available_kib']==19014044 and max(x['swap_used_kib'] for x in resources)==a['maximum_swap_kib']==0 and p['child_maxrss_kib']==a['child_maxrss_kib']==3797272
pc=json.loads((O/'production-commit.json').read_text());cr=json.loads((O/'commit-review.json').read_text());gr=json.loads((O/'GREEN-run/result-review.json').read_text());gc=json.loads((O/'GREEN-run/contract.json').read_text())
assert c.git(['rev-parse','HEAD'])==c.git(['rev-parse','master'])==pc['commit']==cr['commit']==c.TARGET and c.git(['rev-parse','origin/master'])==pc['parent']=='9d29b1f0aa21932217b03ca7b35dd91281baaae6'
assert c.git(['show','-s','--format=%P',c.TARGET])==pc['parent'] and c.git(['rev-parse',c.TARGET+'^{tree}'])==pc['tree']
assert not c.git(['diff','--cached','--name-only']) and co['files']==gc['files'] and gr['passed']==314009
for obj in [cr,gr]:
 assert obj['accepted']
 for n,v in obj['bindings'].items():assert c.sha(n)==v
for n in co['files']:assert (c.M/'test'/n).read_bytes()==(O/'GREEN/test'/n).read_bytes()
mp=json.loads((O/'integration-historical-path-map.json').read_text())
for obj in [mp['master_index_before'],mp['source_before']]:
 for n,v in obj.items():assert c.sha(v['before'])==v['sha256']
# Confirm every tracked current source/test blob still equals the actual commit.
for line in c.git(['ls-tree','-r',c.TARGET]).splitlines():
 meta,name=line.split('\t');mode,kind,oid=meta.split()
 if name.startswith(('src/','test/')) or name=='Project.toml':
  b=(c.M/name).read_bytes();assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid
h=c.host([p[k][v] for k in ['runner','child'] for v in ['pgid','sid']]);assert len(h['groups'])==649;c.put('independent-result-host.json',h)
report=f'''# Independent actual MASTER result review

Accepted actual MASTER validation: 314,009/314,009 ordinary assertions passed across the exact ordered 51 whole files used by GREEN, with zero failures/errors/skips/broken tests and one MASTER completion marker. This is a fresh run from /home/jspitz/JSimplex.jl at ce5d4a74019e0dc2e656d08161641c498b159e7b, not substituted GREEN evidence. Local HEAD/master match that independently reviewed commit; origin/master is still parent 9d29b1f0aa21932217b03ca7b35dd91281baaae6 pending publication.

Independently verified all actual admission/audit bindings, 793 pins and whole-tree membership/protected state, command/project/source marker, exact ordered includes, frozen GREEN total, runner/child/gate/permit identity/hash links, copied pins, parent-death signal, expected exit0, accepted supervisor/completion and shared deadlines. Actual tracked source/test/Project bytes still equal commit blobs; selected tests equal GREEN. Commit parent/tree and historical source/index before-image hashes remain correct; index is clean. Post-exit audit source equals the admitted template and was not rerun by this reviewer. Anchored top-level ERROR checks distinguish ordinary recovery Info messages containing NUMERICAL_ERROR from genuine runtime errors.

Inclusive time {a['elapsed_shared_seconds']:.9f} seconds, within 3,000 seconds. All 1,926 resource samples and terminal checks pass; minimum available RAM 19,014,044 KiB, maximum swap use zero, child max RSS 3,797,272 KiB. Fresh host inspection closes 649 historical process groups AND sessions with boot/start-ticks/command identity, fixed WSL allowance and no Julia. No Julia execution, Git mutation or production edit was performed by this reviewer.

This result satisfies the actual-MASTER prerequisite for the separately reviewed normal, non-force push and subsequent remote verification. It does not itself push, assert remote equality, close final publication or broaden test coverage. Original comparison-2 remains failed for its 18 oracle assertions; only its unchanged cost data was separately qualified. No cost remeasurement occurred.

Computational work/memory assessment remains as previously accepted: no unnecessary production scan, solve, copy, conversion or retained data cache; readonly-zero readiness and cold method metadata costs remain accounted for. Allocation benefits are supported by retained paired measurements; direct-norm/FTRAN timing and native retained-memory benefits are not claimed. MASTER is correctness/regression validation, not an end-to-end performance benchmark.
'''
with (D/'RESULT-REVIEW.md').open('x') as f:f.write(report)
with (D/'independent-result-review.py').open('x') as f:f.write(Path(__file__).read_text())
paths=[D/n for n in ['audit.json','audit.py','admission.json','pins.json','contract.json','tests.jl','completed.json','supervisor.json','reservation.json','output/run.log','output/process.json','output/gate.json','output/current.json','output/permit.json','output/resources.jsonl','RESULT-REVIEW.md','independent-result-host.json','independent-result-review.py']]+[O/n for n in ['production-commit.json','commit-review.json','integration-before.json','integration-after.json','integration-historical-path-map.json','GREEN-run/result-review.json']]
c.put('result-review.json',dict(accepted=True,findings=[],passed=314009,total=314009,expected_failures=0,files=51,pins=793,groups=649,elapsed_shared_seconds=a['elapsed_shared_seconds'],commit=c.TARGET,Julia_executed=False,Git_mutated=False,scope='actual MASTER accepted; reviewed normal push and remote verification remain',bindings={str(p):c.sha(p) for p in paths}))
print(json.dumps(dict(accepted=True,passed=314009,files=51,groups=649,elapsed=a['elapsed_shared_seconds'])))
