from pathlib import Path
import json
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');E=R/'diagnostics/simplex-core-architecture/results';D=E/'DIRECT-BG-EXPORT-SPECIALIZATION-DRIVER';Q=E/'DIRECT-BG-EXPORT-SPECIALIZATION-RED'
def put(n,s):
 with (Q/n).open('x') as f:f.write(s)
put('prepare-execution.py',Path(__file__).read_text())
put('request.txt','Prosím ověř podmínky spuštění, nech konkrétní RED běh nezávisle schválit a ověř očekávaná tři selhání podle přijatého plánu specializace exportu/importu BG s limitem 300 sekund.\n')
put('outer.py','''"""One explicit RED300 invocation after exact admission and release. No auto retry."""
from pathlib import Path
import sys,os,time,runpy,traceback
Q=Path(__file__).resolve().parent
D=Q.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-DRIVER');sys.path.insert(0,str(D))
import control as c
PHASE='red300';RUN=D/'runs'/PHASE

def valid_release(v,seal_sha,review_sha,identity_sha):
 return type(v) is dict and v==dict(phase=PHASE,sealed_sha256=seal_sha,admission_sha256=review_sha,outer_ready_sha256=identity_sha,one_attempt=True)

def main():
 os.chdir(c.R)
 identity=c.guard.process_identity(os.getpid())
 c.require(identity['pid']==identity['pgid']==identity['sid'],'Outer must own isolated group/session')
 c.require(not (Q/'release.json').exists() and not (Q/'outer-ready.json').exists(),'Existing outer run/release')
 c.save(Q/'outer-ready.json',dict(identity=identity,script_sha256=c.sha(__file__),waiting_only=True,phase=PHASE,expected_launcher=str(D/'launch.py'),ready_time=time.time()))
 print('OUTER READY: waiting for independently accepted exact admission and explicit release',flush=True)
 deadline=time.monotonic()+1200
 while not (Q/'release.json').exists():
  if time.monotonic()>=deadline:
   c.save(Q/'outer-outcome.json',dict(launched=False,reason='admission wait expired',identity=identity));return 2
  time.sleep(.2)
 sp=RUN/'sealed.json';rp=RUN/'admission.json';s=c.rd(sp);v=c.rd(rp)
 c.require(valid_release(c.rd(Q/'release.json'),c.sha(sp),c.sha(rp),c.sha(Q/'outer-ready.json')),'Release binding')
 c.verify_review(v,sp,s['files']+[str(sp)],'BG specialization exact-stage admission',PHASE)
 c.require(c.guard.process_identity(os.getpid())==identity and s['outer_identity']==identity,'Outer identity drift')
 c.require(c.guard.pins_match(s),'Sealed inputs changed')
 c.save(Q/'outer-invocation.json',dict(identity=identity,phase=PHASE,seal_sha256=c.sha(sp),review_sha256=c.sha(rp),release_sha256=c.sha(Q/'release.json'),launcher_sha256=c.sha(D/'launch.py'),method='runpy.run_path unchanged launch.py as __main__ in this outer process'))
 started=time.monotonic();code=0;error=''
 try:
  sys.argv=[str(D/'launch.py'),PHASE]
  runpy.run_path(str(D/'launch.py'),run_name='__main__')
 except BaseException as e:
  code=e.code if isinstance(e,SystemExit) and isinstance(e.code,int) else 2
  error=''.join(traceback.format_exception(e));print(error,flush=True)
 finally:
  c.save(Q/'outer-outcome.json',dict(identity=identity,launched=True,returncode=code,error=error,elapsed_with_checks_seconds=time.monotonic()-started,scope='Outer time includes immutable pre/post checks and auditor; not benchmark or numerical guard duration'))
 return code
if __name__=='__main__':sys.exit(main())
''')
s=(D/'seal.py').read_text().replace('from control import *', "from pathlib import Path\nimport sys\nQ=Path(__file__).resolve().parent\nD=Q.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-DRIVER')\nsys.path.insert(0,str(D))\nfrom control import *")
s=s.replace("cfg=config(phase);validate_environment();", "require(phase=='red300','Only authorized RED300');ready=rd(Q/'outer-ready.json');outer=ready['identity']\n require(guard.process_identity(outer['pid'])==outer and outer['pid']==outer['pgid']==outer['sid'],'Outer not alive/isolated')\n require(ready['script_sha256']==sha(Q/'outer.py') and ready['phase']==phase and ready['waiting_only'] is True,'Outer ready linkage')\n cfg=config(phase);validate_environment();")
s=s.replace("# All production tracked bytes individually pinned; no .git tree/cache snapshot.", "extra_paths=rd(Q/'outer-required.json')['paths']\n require(all(Path(p).is_file() for p in extra_paths),'Outer inputs missing')\n files=sorted(set(files+extra_paths))\n # All production tracked bytes and immutable outer wrapper inputs pinned.")
s=s.replace("dict(phase=phase,head=h['head']", "dict(phase=phase,outer_identity=outer,head=h['head']")
put('seal-outer.py',s)
put('EXECUTION.md','''# Exact RED300 admission supplement

This human request authorizes exactly the prepared RED300 experiment (Julia300s,
inner292s), not GREEN or a new design. Source/candidate/kernel/guard/supervisor/
launcher/auditor remain byte-identical to the accepted preparation. Runtime expected
exit1, exactly3allocation failures,3native cells,60windows/1440explicit factor
solves, no structural suite. All input/output/residual/compile/byte/event predicates
remain as prepared. No profiler or IR query, no production/test/env/CI/master change.

The prepared review additionally requires the outer launcher identity before
admission and its group/session closure after return. outer.py is an isolated
Python group/session launched through setsid. It records actual boot/start_ticks/
command/PGID/SID and waits WITHOUT Julia for a hash-bound release. Waiting is bounded
at1200seconds and is not a numerical allowance. It cannot invoke launch.py before
exact independent admission verifies the sealed files, outer identity and release
hashes. It then executes the unchanged launch.py once through runpy in the SAME
outer process, preserving its OS identity. The existing inner supervisor/guard
owns the Julia300/292bound and resource constraints. No wrapper retry is provided.
Outer elapsed includes immutable hash checks/auditor and is not a benchmark.

seal-outer.py is a new copy of prepared seal.py with only explicitREDrestriction,
outer identity checks and additional immutable Q files/outer_identity metadata.
Actual Julia config/command/paths and old sealed inputs/trees are unchanged.
The old seal is not executed/rewritten. Its old preparation hashes remain intact.
All extra input paths are listed literally in outer-required.json, including the
outer source, actual readyidentity, this supplement, new seal source, offline tests,
request and fresh entry host. Release/invocation/outcome are new postseal records
and must not exist when sealing. The outer is expected LIVE during exact review;
it is separately identified, not misreported as an absent historical process.

After the outer returns, a separate host call must append its PGID AND SID to
all in-process guard/child groups, verify fullgroup/session absence and no Julia,
and bind its original command/startticks/boot. Outer identity is carried into every
later phase through required predecessor evidence; future GREEN must explicitly
merge this supplementary closure's groups. In-process posthost cannot prove its
own caller exited. Any error or unexpected RED outcome is preserved without
candidate/count/gate retuning or rerun. This task's300second request does not
silently start600seconds; a timeout is independently classified first.
''')
put('outer-offline-check.py','''"""New pure outer release/source inverse checks only; never invoke main."""
from pathlib import Path
import importlib.util,json,ast,sys
Q=Path(__file__).resolve().parent;D=Q.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-DRIVER');sys.path.insert(0,str(D));import control as c
sp=importlib.util.spec_from_file_location('waiting_outer_definitions',Q/'outer.py');o=importlib.util.module_from_spec(sp);sp.loader.exec_module(o)
checks={}
def ck(n,v):checks[n]=bool(v);c.require(v,n)
v=dict(phase='red300',sealed_sha256='s',admission_sha256='a',outer_ready_sha256='i',one_attempt=True)
ck('exact_release',o.valid_release(v,'s','a','i'))
for k in v:
 z=dict(v);z[k]='wrong';ck('wrong_'+k,not o.valid_release(z,'s','a','i'))
z=dict(v,extra=True);ck('extra_release',not o.valid_release(z,'s','a','i'))
ck('bad_type',not o.valid_release([], 's','a','i'))
for p in Q.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
ck('new_python_syntax',True)
s=(Q/'outer.py').read_text();ck('review_before_invocation',s.index('c.verify_review(')<s.index('runpy.run_path(str('))
ck('identity_before_invocation',s.index("s['outer_identity']==identity")<s.index('runpy.run_path(str('))
ck('pins_before_invocation',s.index('c.guard.pins_match(s)')<s.index('runpy.run_path(str('))
ck('one_invocation',s.count('runpy.run_path(str(')==1)
ck('no_release_or_reservation',not (Q/'release.json').exists() and not (D/'runs/red300').exists())
c.save(Q/'outer-offline-check.json',dict(all_passed=True,checks=checks,sha256={str(p):c.sha(p) for p in Q.glob('*.py')},scope='Pure Python release and source ordering; no outer/Julia launch'))
print('Outer offline checks',len(checks),'PASS')
''')
paths=[str(Q/n) for n in ['host-entry.json','prepare-execution.py','request.txt','outer.py','seal-outer.py','EXECUTION.md','outer-offline-check.py','outer-offline-check.json','outer-required.json','outer-ready.json']]
put('outer-required.json',json.dumps(dict(paths=sorted(paths)),indent=2)+'\n')
print('Prepared outer identity linkage; no Julia or outer process started.')
