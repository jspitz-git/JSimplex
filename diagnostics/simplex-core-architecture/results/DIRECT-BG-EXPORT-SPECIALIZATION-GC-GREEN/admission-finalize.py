"""Final fresh inventory/host read and exclusive exact-stage admission write; no launch."""
import sys,json,time,hashlib
from pathlib import Path
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
P=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-SPECIALIZATION-GC-DRIVER'
Q=P.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-GC-GREEN');RUN=P/'runs/greengc300';O=P/'outers/greengc300'
sys.path.insert(0,str(P));import control as c
j=c.rd(Q/'admission-check.json');s=c.rd(RUN/'sealed.json');cfg=c.config('greengc300')
assert j['all_passed'] is True and j['findings']==[] and j['checks_passed']==7513
assert c.sha(RUN/'sealed.json')==j['sealed_sha256']
prepared=c.preparation();extra,groups=c.predecessor('greengc300')
assert len(extra)==86 and len(groups)==262
assert c.seal_files(cfg,prepared,extra)==s['files']
assert c.guard.inventory(s['files'],s['trees'])==s['inventory']
c.validate_sources();c.validate_environment()
outer=c.verify_outer('greengc300',s,live=True)
h=c.full_host(groups);h['memory']=c.guard.memory();h['remote']=c.git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture')
assert c.host_safe(h) and h['groups']==s['groups'] and len(h['groups'])==262 and not c.guard.pressure(h['memory'])
assert all(h[k]==s[k] for k in ['head','master','boot_id'])
assert dict(line.split('\t')[::-1] for line in h['remote'].splitlines())=={'refs/heads/codex/simplex-core-architecture':s['head'],'refs/heads/master':s['master']}
assert not c.git('diff','--name-only') and not c.git('diff','--cached','--name-only')
assert {p.name for p in RUN.iterdir()}=={'host.json','config.json','sealed.json'}
assert {p.name for p in O.iterdir()}=={'outer-ready.json'}
assert time.time()-c.rd(O/'outer-ready.json')['ready_time']<1200
c.save(Q/'admission-final-check.json',dict(all_passed=True,time=time.time(),inventory_paths=len(s['inventory']),sealed_sha256=c.sha(RUN/'sealed.json'),host=h,outer_identity=outer,scope='Fresh full inventory read plus exact source/preparation/predecessor/host before admission'))
primary={n:c.sha(n) for n in s['files']};primary[str(RUN/'sealed.json')]=c.sha(RUN/'sealed.json')
assert all(primary[n]==s['inventory'][n]['sha256'] for n in s['files']) and len(primary)==2420
names=['admission-check.py','admission-check.json','admission-check-first.py','admission-check-first.json','admission-review.md','admission-finalize.py','admission-final-check.json','host-entry.json','entry.json','request.txt']
evidence={str(Q/n):c.sha(Q/n) for n in names}
assert c.guard.process_identity(outer['pid'])==outer and not (O/'release.json').exists()
v=dict(scope='BG specialization GC exact-stage admission',phase='greengc300',accepted=True,findings=[],pins_sha256=primary[str(RUN/'sealed.json')],sha256=primary,evidence_sha256=evidence,checks_passed=j['checks_passed'],sealed_files=len(s['files']),prior_groups_and_sessions=262,predecessor_paths=86,predecessor_result_bindings=81,predecessor_external_closure_bindings=8,production_work_memory_findings=[],limitations=['Admission only; no result, performance or Task3 qualification.','Process-wide GC does not prove finalizer drain, native freeing or compilation cure.','Inaccessible executable links are a host-visibility limit.'])
c.save(RUN/'admission.json',v)
c.verify_review(c.rd(RUN/'admission.json'),RUN/'sealed.json',s['files']+[str(RUN/'sealed.json')],'BG specialization GC exact-stage admission','greengc300')
print(json.dumps(dict(accepted=True,checks_passed=j['checks_passed'],primary_bindings=len(primary),evidence_bindings=len(evidence),prior_groups=262,predecessor_paths=86,admission_sha256=c.sha(RUN/'admission.json'))))
