from pathlib import Path
import sys,json,subprocess,hashlib,ast
sys.dont_write_bytecode=True
O=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-bounds-norm-infeasibility/2026-10-27');D=O/'MASTER-run';sys.path.insert(0,str(D));import common as c
c.unchanged();h=c.host();assert len(h['groups'])==647 and len(c.read('pins.json')['inventory'])==793
rd=lambda n:json.loads((O/n).read_text())
cr=rd('commit-review.json');pc=rd('production-commit.json');gr=rd('GREEN-run/result-review.json');gc=rd('GREEN-run/contract.json');ia=rd('integration-after.json');ib=rd('integration-before.json');mp=rd('integration-historical-path-map.json')
for obj in [cr,gr]:
 assert obj['accepted'] and obj['findings']==[]
 for n,v in obj['bindings'].items():assert c.sha(n)==v
assert c.git(['rev-parse','HEAD'])==pc['commit']==cr['commit']==c.TARGET
assert c.git(['show','-s','--format=%P',c.TARGET])==pc['parent']==cr['parent']==mp['master_before']=='9d29b1f0aa21932217b03ca7b35dd91281baaae6'
assert c.git(['rev-parse',c.TARGET+'^{tree}'])==pc['tree']==cr['tree']
assert c.git(['diff-tree','--no-commit-id','--name-only','-r',c.TARGET]).splitlines()==pc['names']==cr['names']
assert ia==dict(fast_forward=True,protected_unchanged=True,pushed=False,target=c.TARGET,unrelated_indexes_unchanged=True)
assert ib['target']==c.TARGET and ib['staged']=='' and not c.git(['diff','--cached','--name-only'])
for obj in [mp['master_index_before'],mp['source_before']]:
 for n,v in obj.items():assert c.sha(v['before'])==v['sha256']
for n,v in mp['source_before'].items():assert Path(v['before']).read_bytes()==subprocess.check_output(['git','-C',str(c.M),'show',pc['parent']+':'+str(Path(n).relative_to(c.M))])
# Index is the exact integrated commit tree, and all tracked production/test bytes match its blobs.
tree={}
for line in c.git(['ls-tree','-r',c.TARGET]).splitlines():
 meta,name=line.split('\t');mode,kind,oid=meta.split();tree[name]=(mode,oid)
index={}
for line in c.git(['ls-files','--stage']).splitlines():
 meta,name=line.split('\t');mode,oid,stage=meta.split();assert stage=='0';index[name]=(mode,oid)
assert index==tree and len(tree)==3558
for name,(mode,oid) in tree.items():
 if name.startswith(('src/','test/')) or name=='Project.toml':
  data=(c.M/name).read_bytes();assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==oid
for n,oid in pc['blobs'].items():assert tree[n][1]==oid and (c.M/n).read_bytes()==(O/'GREEN'/n).read_bytes()
co=c.read('contract.json');assert co['arm']=='MASTER' and co['files']==gc['files'] and len(co['files'])==51
assert co['expected_total']==gr['passed']==gr['total']==314009 and co['expected_exit']==co['expected_failures']==0 and co['expected_failure_locations']==[]
assert co['source_root']==str(c.M) and co['command'][-2]=='--project='+str(c.M) and co['command'][-1]==str(D/'tests.jl')
assert co['guard_limit_seconds']==2992 and co['shared_limit_seconds']==3000
for name in co['files']:assert (c.M/'test'/name).read_bytes()==(O/'GREEN/test'/name).read_bytes()
assert (D/'tests.jl').read_text()==(O/'GREEN-run/tests.jl').read_text().replace(str(O/'GREEN'),str(c.M)).replace('GREEN','MASTER')
assert (D/'launch.py').read_bytes()==(O/'GREEN-run/launch.py').read_bytes()
for n in ['entry_gate.py','guard_reviewed.py','supervisor_reviewed.py']:assert (D/'guard'/n).read_bytes()==(O/'GREEN-run/guard'/n).read_bytes()
for n in ['common.py','launch.py']:ast.parse((D/n).read_text())
assert Path('/tmp/bni-phase-audit.py').read_bytes()==(O/'RED-run/audit.py').read_bytes()
assert not (D/'reservation.json').exists() and not (D/'output').exists()
c.put('independent-host.json',h)
report='''# Independent concrete MASTER admission

Accepted for one fresh actual-MASTER run only, before push. No Julia, Git mutation or old audit was executed by this reviewer. The concrete command selects /home/jspitz/JSimplex.jl as project/source, existing compiled modules, Julia/BLAS one thread and GC 1,0. It includes exactly the same 51 whole test files as accepted GREEN and freezes the exact 314,009 passing-assertion total, zero failures and expected exit0. Driver bytes equal GREEN apart from source root/phase name.

Authoritative HEAD/master are ce5d4a74019e0dc2e656d08161641c498b159e7b; origin/master remains parent 9d29b1f0aa21932217b03ca7b35dd91281baaae6. Actual commit parent/tree/four changed names/blob IDs match the independent accepted commit review. All 3,558 current index entries equal the integrated commit tree; tracked source/test/Project bytes match their Git blobs, all changed bytes equal accepted GREEN, and every selected test file is byte-identical to GREEN. Index is clean. Integration-before/after evidence and exact historical source/index before-images were checked; old source before-images equal parent commit blobs. Unrelated/protected files/indexes remain pinned.

All 793 concrete pins and their whole-tree memberships, source/project/ref/environment checks and prior commit/GREEN review bindings pass. Fresh 647-group AND session closure verifies boot/start-ticks/command identity, fixed unrelated WSL allowance, no active Julia and resource headroom. Guard code and launch are unchanged from GREEN: one exclusive attempt, 2,992-second guard inside 3,000-second shared deadline, 2 GiB heap hint/8 GiB address-space ceiling and established RAM/swap limits. The ordinary post-exit phase auditor remains byte-identical to the admitted RED template. Actual MASTER result is required before push; GREEN is not substituted for it.

Computational work/memory: this admission introduces no production change. The accepted A/B/C implementation preserves scans, solves, arithmetic/tolerances and retained-state boundaries; readonly-zero readiness branches and cold specialized-method metadata remain counted. Independent raw-cost evidence and limitations remain in the earlier result review, including uncertain direct-norm/FTRAN timing and no native-retention or end-to-end speedup claim. The fresh test execution is validation overhead, not a benchmark rerun.
'''
with (D/'ADMISSION-REVIEW.md').open('x') as f:f.write(report)
with (D/'independent-admission.py').open('x') as f:f.write(Path(__file__).read_text())
paths=[D/n for n in ['pins.json','contract.json','tests.jl','common.py','launch.py','ADMISSION-REVIEW.md','independent-host.json','independent-admission.py']]+[O/n for n in ['commit-review.json','production-commit.json','integration-before.json','integration-after.json','integration-historical-path-map.json','GREEN-run/result-review.json']]+[Path('/tmp/bni-phase-audit.py')]
c.put('admission.json',dict(accepted=True,findings=[],bindings={str(p):c.sha(p) for p in paths},commit=c.TARGET,pins=793,groups=647,files=51,expected_total=314009,Julia_executed=False,Git_mutated=False,scope='one fresh actual MASTER validation before push'))
print('accepted actual MASTER; 793 pins, 647 groups, 51 whole files, frozen 314009 total')
