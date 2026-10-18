"""New synthetic control cases; no launch/seal/Julia. Only temporary fake files."""
from pathlib import Path
import copy,json,tempfile
import control as c
from oracle import test_results
D=Path(__file__).resolve().parent;checks={}
def ok(v,n):
 checks[n]=bool(v)
 if not v:raise RuntimeError(n)
def reject(fn,n):
 try:fn()
 except (RuntimeError,ValueError,KeyError,TypeError,FileNotFoundError,FileExistsError):ok(True,n)
 else:ok(False,n)
def node(name,p=0,f=0,e=0,b=0):return dict(name=name,**{'pass':p,'fail':f,'error':e,'broken':b},failures=['synthetic']*(f+e),children=[])
e=c.rd(D/'expected-tests.json')['green'];loaded=c.loaded_for(c.config('green300'));root=node('root');root['children']=[node(*row) for row in e['groups']]
r=dict(phase='green300',complete=True,fatal='',loaded=loaded,threads=1,blas_threads=1,tests=root)
for action in ('missing','extra','malformed'):
 x=copy.deepcopy(r)
 if action=='missing':x['loaded'].pop('Test')
 elif action=='extra':x['loaded']['Unexpected']='/extra'
 else:x['loaded']['Test']=None
 reject(lambda:test_results(x,e,loaded,'green300'),'loaded_'+action)
for title in ('explicit_zero_order','checked_limits','Seven fixed fixtures, two policies, direct reference','Block boundaries, diagonals and contiguous solve order'):
 x=copy.deepcopy(r);t=next(t for t in x['tests']['children'] if t['name']==title);t['pass']-=1;t['fail']=1;t['failures']=['synthetic signed-zero/policy/overflow mismatch']
 reject(lambda:test_results(x,e,loaded,'green300'),'failed_contract_'+title)
x=copy.deepcopy(r);x['tests']['children'].pop();reject(lambda:test_results(x,e,loaded,'green300'),'missing_group')
x=copy.deepcopy(r);x['tests']['children'].append(node('extra',1));reject(lambda:test_results(x,e,loaded,'green300'),'extra_group')
# Exact filesystem membership uses the same expression as validate_sources; inject
# tiny fake stages into that real function, suppress only unrelated prechecks.
original=(c.rd,c.git,c.subprocess.run,c.guard.inventory)
with tempfile.TemporaryDirectory(prefix='block-offline-') as tmp:
 rootpath=Path(tmp);f=rootpath/'fixed';f.write_text('fixed');manifest={'path':str(rootpath),'sha256':{'fixed':c.sha(f)}}
 def rd(p):
  n=Path(p).name
  if n=='baseline.json':return {'diagnostic':{},'production':{}}
  if n=='stages.json':return {'green':manifest}
  if n=='runtime-inputs-complete.json':return {'inventory':{}}
  raise ValueError(n)
 def git(*a,**kw):
  if a[0]=='rev-parse':return c.MASTER
  if a[0]=='ls-remote':return c.MASTER+'\trefs/heads/master'
  if a[0]=='ls-files':return ''
  raise ValueError(a)
 c.rd=rd;c.git=git;c.subprocess.run=lambda *a,**k:type('Result',(),{'returncode':0})();c.guard.inventory=lambda *a:{}
 try:
  c.validate_sources();ok(True,'stage_positive')
  f.rename(rootpath/'other');reject(c.validate_sources,'stage_missing_extra');(rootpath/'other').rename(f)
  f.write_text('changed');reject(c.validate_sources,'stage_hash');f.write_text('fixed')
  extra=rootpath/'extra';extra.write_text('extra');reject(c.validate_sources,'stage_extra');extra.unlink()
  extra.symlink_to(f);reject(c.validate_sources,'stage_symlink');extra.unlink()
  manifest['sha256']['fixed']='malformed';reject(c.validate_sources,'stage_malformed_hash');manifest['sha256']['fixed']=c.sha(f)
 finally:c.rd,c.git,c.subprocess.run,c.guard.inventory=original
 reservation=rootpath/'reservation';c.save(reservation,{'one_attempt':True});reject(lambda:c.save(reservation,{'one_attempt':True}),'exclusive_extra_attempt')
 review=dict(accepted=True,findings=[],scope='test',phase='red300',pins_sha256=c.sha(f),sha256={str(f):c.sha(f)})
 review['sha256'][str(rootpath/'nonexistent')]='0'*64
 reject(lambda:c.verify_review(review,f,[str(f)],'test','red300'),'review_extra_path')
 review['sha256']={str(f):'bad'};reject(lambda:c.verify_review(review,f,[str(f)],'test','red300'),'review_malformed_hash')
 reject(lambda:c.verify_review(review,f,[str(f)],'test','green300'),'review_wrong_phase')
# Cost compilation windows/cells are deliberately absent: GREEN is correctness.
# Their future parser is not purportedly covered by these synthetic Test records.
ok(not (D/'runs').exists(),'no_phase_activity')
c.save(D/'negative-supplement.json',dict(all_passed=all(checks.values()),checks=checks,scope='Additional pure parser and temporary stage/admission tests; no Julia/launcher'))
print('Supplement PASS',len(checks))
