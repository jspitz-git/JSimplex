"""Independent bounded text/hash/environment correction review; no closure import."""
from pathlib import Path
import json,hashlib,os
D=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
rd=lambda p:json.loads(Path(p).read_text())
checks={}
def check(n,v):
 checks[n]=bool(v)
 if not v:raise AssertionError(n)
old='publication-names.json';new='publication-names-final.json'
for a,b in [('closure-final.py','closure-final-2.py'),('publication.py','publication-final.py')]:
 s=(D/a).read_text();t=(D/b).read_text()
 check('single_names_rebind_'+b,s.count(old)==1 and s.replace(old,new)==t)
failure=rd(D/'closure-attempt-1.json')
check('failure_script_identity',failure['script']=='closure-final.py' and failure['script_sha256']==sha(D/'closure-final.py'))
check('failure_remains_rejection',failure['exit_code']==1 and failure['login'] is True and 'Loading environment drift' in failure['output'])
s=(D/'closure-final-2.py').read_text()
check('environment_before_outputs',s.index('c.validate_environment()')<s.index('host=c.full_host()')<s.index("c.save(D/'host-closure.json'")<s.index("c.save(D/'closure.json'"))
check('exact_nonlogin_environment',{k:os.environ.get(k) for k in rd(D/'environment.json')}==rd(D/'environment.json'))
check('no_closure_or_numerical_outputs',all(not (D/n).exists() for n in ['host-closure.json','closure.json','publication.json','runs']))
review=rd(D/'review.json')
for n in ['control.py','environment.json','preparation-pins.json','driver.jl','guard.py','supervisor.py','seal.py','launch.py','audit.py','oracle.py']:
 check('unchanged_preparation_'+n,sha(D/n)==review['sha256'][str(D/n)])
check('review_preparation_identity',review['accepted'] is True and review['findings']==[] and review['pins_sha256']==sha(D/'preparation-pins.json'))
check('final_names_not_yet_frozen',not (D/new).exists())
text='''# Independent bounded closure/publication correction review

Accepted for the bounded offline correction only; findings:0. `closure-final-2.py` is exactly `closure-final.py` with its single publication-names.json reference rebound to publication-names-final.json. `publication-final.py` has exactly the same single reference change from `publication.py`. No validation, failure handling, preparation review, source/runtime/environment, host/group/session, remote-ref, membership, exclusive-output, stage-name or blob gate was weakened.

The preserved failed attempt records exit1 at validate_environment, with the original script hash verified. Source order places that check before host inspection/output and closure output. Independent inspection confirms host-closure.json, closure.json, publication.json and runs are absent. The current non-login environment matches every pinned environment key exactly. The reported login-shell PATH difference is preserved diagnosis from the parent; this reviewer did not rerun the failed closure or invoke a login shell. No environment pin or control file was changed to accommodate the failure.

The preparation manifest hash and reviewed driver/control/guard/supervisor/seal/launch/audit/oracle/environment hashes remain unchanged. This bounded check does not rehash the entire accepted preparation package. The final publication list is deliberately not yet frozen; its future exact scope/membership and blobs remain subject to unchanged closure/publication gates. No closure, publication, Julia, numerical, or Git mutation command was executed by this review. Only this saved reviewer-owned Python text/hash/environment check ran.
'''
with (D/'closure-correction-review.md').open('x') as f:f.write(text)
names=['closure.py','closure-final.py','closure-final-2.py','publication.py','publication-final.py','closure-attempt-1.json','publication-names.json','environment.json','control.py','review.json','preparation-pins.json','reviewer-closure-correction-check.py','closure-correction-review.md']
out=dict(accepted=True,findings=[],scope='split BG bounded offline closure/publication correction',checks=checks,sha256={str(D/n):sha(D/n) for n in names},limitations=['Final publication-names-final.json is not yet frozen or reviewed; unchanged gates must verify final exact scope/membership/blobs.','No closure/publication/Julia execution or complete preparation rehash in this bounded review.'],numerical_allowance=False)
with (D/'closure-correction-review.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps(dict(accepted=True,findings=[],checks=len(checks),bindings=len(names))))
