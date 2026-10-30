from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/dual-recovery-devex-cost-admission/2026-10-30';P=W/'diagnostics/dual-recovery-devex-task4/2026-10-30'
sys.path.insert(0,str(D));import common as C
checks={}
def ck(k,v):
 checks[k]=bool(v)
 if not v:raise AssertionError(k)
a=(P/'tests/reference.jl').read_text().replace('JS.','');b=(P/'overlays/reference/src/simplex_recovery.jl').read_text()
ck('qualified legacy public body exact',a[a.index('function refine_basis_solve!'):a.index('\nfunction _refine_basis_solve!')].strip()==b[b.index('function refine_basis_solve!'):b.index('\n_checkpoint_model')].strip())
ck('qualified legacy private body exact',a[a.index('function _refine_basis_solve!'):a.index('\nend # module')].strip()==b[b.index('function _refine_basis_solve!'):b.index('\n# A clock-only guard')].strip())
used,facts=C.prior('reference-cost');ck('pure prior exact',used==1033.6005972509156 and [v['accepted'] for v in facts]==[True,False,True])
try:C.prior('candidate-cost')
except FileNotFoundError:refused=True
else:refused=False
ck('candidate cannot proceed without closed reference',refused)
old=C.owners;h=C.read(D/'host.json')['host'];boot=h['boot_id'];base=set(h['checked_groups'])
def record(n,boot):return dict(pid=n,pgid=n,sid=n+100,boot_id=boot,start_ticks=200,command='synthetic')
records={'reference-cost':[('launcher',record(9000001,boot)),('runner',record(9000002,boot)),('child',record(9000003,boot))],'candidate-cost':[('launcher',record(9000011,boot)),('runner',record(9000012,boot)),('child',record(9000013,boot))]}
def g(vals):return set(v for _,a in vals for v in (a['pgid'],a['sid']))
try:
 C.owners=lambda p:records[p]
 ck('reference postflight includes group AND distinct session',C.expected_groups('reference-cost',boot,False)==base|g(records['reference-cost'][1:]))
 ck('reference close includes launcher group AND session',C.expected_groups('reference-cost',boot,True)==base|g(records['reference-cost']))
 ck('candidate postflight retains all reference owners',C.expected_groups('candidate-cost',boot,False)==base|g(records['reference-cost'])|g(records['candidate-cost'][1:]))
 ck('candidate close retains all six owners',C.expected_groups('candidate-cost',boot,True)==base|g(records['reference-cost'])|g(records['candidate-cost']))
 ck('boot scopes old identities',C.expected_groups('candidate-cost','another-boot',True)==set())
finally:C.owners=old
ck('no runtime outputs',not C.RUN.exists());ck('no submitted mains or guards imported',not any(n in sys.modules for n in ('seal','launch','close','guard_reviewed','supervisor_reviewed','entry_gate','offline_tests','offline_tests_final')))
r=dict(accepted=True,scope='offline_preparation',runtime_qualified=False,numerical_admission=False,checks=checks,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),D/'common.py',D/'host.json',P/'tests/reference.jl',P/'overlays/reference/src/simplex_recovery.jl']})
with Path('/tmp/devex-cost-preparation-review-flow-result.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(dict(accepted=True,checks=len(checks))))
