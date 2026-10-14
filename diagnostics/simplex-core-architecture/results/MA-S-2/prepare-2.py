from pathlib import Path
import json,hashlib,ast
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/MA-S-2';S=E.with_name('MA-S');L=E.with_name('MA-S-LOAD')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,o):
 with (E/n).open('x') as f:json.dump(o,f,indent=2);f.write('\n')
def write(n,s):
 with (E/n).open('x') as f:f.write(s)
def transform(old,new,pairs):
 s=(S/old).read_text();out=s;history=[]
 for a,b in pairs:
  positions=[];start=0
  while True:
   pos=out.find(a,start)
   if pos<0:break
   positions.append(pos);start=pos+len(a)
  if not positions:raise SystemExit('Missing source '+a)
  for pos in reversed(positions):
   out=out[:pos]+b+out[pos+len(a):];history.append((pos,a,b))
 inverse=out
 for pos,a,b in reversed(history):
  if inverse[pos:pos+len(b)]!=b:raise SystemExit('Inverse position drift')
  inverse=inverse[:pos]+a+inverse[pos+len(b):]
 if inverse!=s:raise SystemExit('Inverse failure '+new)
 write(new,out);return dict(original=str(S/old),candidate=str(E/new),replacements=pairs,inverse=True,edit_spans=history)
changes=[]
changes.append(transform('audit_reviewed.py','audit.py',[('MA-S fail-closed','MA-S-2 fail-closed'),("'pins-reviewed.json'","'pins.json'"),('len(groups)>=158','len(groups)>=160')]))
changes.append(transform('launcher-reviewed.py','launcher.py',[('MA-S one reserved','MA-S-2 one reserved'),('import audit_reviewed as audit','import audit'),('pins-reviewed.json','pins.json'),('required-paths-reviewed.json','required-paths.json'),('admission-review-final.json','admission-review.json'),('launcher-reviewed.py','launcher.py')]))
write('guard.py',(S/'guard.py').read_text())
commands=json.loads((S/'commands.json').read_text())
for i,c in commands.items():
 if c[-3:]!=[str(S/'driver.jl'),i,str(S/f'run-{i}')]:raise SystemExit('Unexpected old command')
 c[-3:]=[str(L/'driver.jl'),i,str(E/f'run-{i}')]
save('commands.json',commands)
tests=(S/'offline-tests-reviewed.py').read_text().replace('audit_reviewed','audit').replace('offline-tests-reviewed','offline-tests').replace('range(1,159)','range(1,161)')
extra='''
# New preparation-specific checks; only copied pure Python helpers.
check('stage_reject_only159groups',not A.passed(A.stage_scalars(proc,inv,res,samples,dict(post,groups=list(range(1,160))),ctx,seq)))
empty=copy.deepcopy(rs[0]);empty['costs']=[];empty['correctness']=[]
check('reject_empty_partial_MA_S_shape',not A.passed(A.validate_raw(empty,1)))
C=json.loads((D/'commands.json').read_text())
check('new_output_and_corrected_driver',all(c[-3:]==[str(D.with_name('MA-S-LOAD')/'driver.jl'),i,str(D/f'run-{i}')] for i,c in C.items()))
# validate_admission only: synthetic files/reviews in a temporary directory,
# no main(), host(), guard(), reservation, process, or numerical work.
L=module('launcher');oldD=L.D
with tempfile.TemporaryDirectory() as tmp:
 T=Path(tmp);L.D=T
 def put(n,o): (T/n).write_text(json.dumps(o))
 (T/'source').write_text('fixed')
 manifest=dict(files=[str(T/'source')],trees=[],inventory={str(T/'source'):dict(resolved=str((T/'source').resolve()),sha256=A.sha(T/'source'))})
 put('pins.json',manifest);put('launch-context.json',dict(standing_short_run_permission=True,maximum_processes=3,maximum_seconds_per_process=120))
 prep=dict(accepted=True,findings=[],pins_sha256=A.sha(T/'pins.json'),sha256={str(T/'source'):A.sha(T/'source')})
 put('admission-review.json',prep)
 seal=dict(accepted=True,findings=[],pins_sha256=A.sha(T/'pins.json'),context_sha256=A.sha(T/'launch-context.json'),preparation_review_sha256=A.sha(T/'admission-review.json'),sha256={str(T/n):A.sha(T/n) for n in ['pins.json','launch-context.json','admission-review.json']})
 context=json.loads((T/'launch-context.json').read_text())
 def accepts(p,s,c,required=None):
  try:L.validate_admission(manifest,list(manifest['inventory']) if required is None else required,p,s,c);return True
  except (ValueError,KeyError,FileNotFoundError):return False
 check('admission_synthetic_valid',accepts(prep,seal,context))
 for name,p,s,c in [
  ('prep_rejected',dict(prep,accepted=False),seal,context),
  ('seal_rejected',prep,dict(seal,accepted=False),context),
  ('seal_findings',prep,dict(seal,findings=['x']),context),
  ('old_manifest_hash',prep,dict(seal,pins_sha256='old'),context),
  ('wrong_context_hash',prep,dict(seal,context_sha256='old'),context),
  ('old_preparation_review',prep,dict(seal,preparation_review_sha256='old'),context),
  ('missing_seal_membership',prep,dict(seal,sha256={}),context),
  ('no_permission',prep,seal,dict(context,standing_short_run_permission=False)),
  ('wrong_limit',prep,seal,dict(context,maximum_seconds_per_process=121))]:
  check('admission_reject_'+name,not accepts(p,s,c))
 check('admission_reject_required_membership',not accepts(prep,seal,context,[]))
 (T/'source').write_text('drift')
 check('admission_reject_source_drift',not accepts(prep,seal,context))
L.D=oldD
'''
needle="obj={'scope':"
if tests.count(needle)!=1:raise SystemExit('Test insertion')
tests=tests.replace(needle,extra+'\n'+needle).replace("['audit.py','guard.py','offline-tests.py']","['audit.py','guard.py','offline-tests.py','launcher.py','commands.json']")
write('offline-tests.py',tests)
def fun(path,name):return ast.dump(next(n for n in ast.parse(Path(path).read_text()).body if isinstance(n,ast.FunctionDef) and n.name==name),include_attributes=False)
checks={'audit_inverse':changes[0]['inverse'],'launcher_inverse':changes[1]['inverse'],'guard_byte_identical':(E/'guard.py').read_bytes()==(S/'guard.py').read_bytes(),'aggregate_AST_identical':fun(E/'audit.py','aggregate')==fun(S/'audit_reviewed.py','aggregate'),'raw_validator_AST_identical':fun(E/'audit.py','validate_raw')==fun(S/'audit_reviewed.py','validate_raw'),'commands_only_driver_output_changed':all(c[:-3]==json.loads((S/'commands.json').read_text())[i][:-3] and c[-3:]==[str(L/'driver.jl'),i,str(E/f'run-{i}')] for i,c in commands.items()),'driver_is_accepted_exact':sha(L/'driver.jl')==json.loads((L/'review.json').read_text())['sha256'][str(L/'driver.jl')],'no_launch':not any((E/n).exists() for n in ['launch-context.json','numerical-review.json','sequence-reservation.json','run-1'])}
save('source-check.json',dict(all_passed=all(checks.values()),checks=checks,transformations=changes,sha256={str(E/n):sha(E/n) for n in ['prepare-2.py','audit.py','launcher.py','guard.py','commands.json','offline-tests.py']},scope='Python source/AST only. No Julia parse/import/compile/numerics. No launcher/guard main.'))
print(json.dumps(checks))
if not all(checks.values()):raise SystemExit(1)
