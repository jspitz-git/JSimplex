"""New pure outer release/source inverse checks only; never invoke main."""
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
