from pathlib import Path
import tempfile,json,hashlib,ast
D=Path(__file__).resolve().parent
text=(D/'publication.py').read_text();start=text.index("closure=json.loads");end=text.index("required={",start);guard=text[start:end];code=compile(ast.parse(guard),'exact-publication-evidence-prefix','exec')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def require(v,m):
 if not v:raise ValueError(m)
checks=[]
with tempfile.TemporaryDirectory(prefix='task4-publication-') as td:
 p=Path(td);artifact=p/'bound.txt';artifact.write_text('reviewed');files=[]
 for i in range(367):
  f=p/('launch-'+str(i));f.write_text('pinned');files.append(f)
 def reset():
  artifact.write_text('reviewed')
  for f in files:f.write_text('pinned')
  c=dict(accepted=True,checks=[dict(passed=True)],bindings={str(artifact):sha(artifact)})
  pins=dict(files=[str(f) for f in files],inventory={str(f):dict(resolved=str(f.resolve()),sha256=sha(f)) for f in files})
  return c,pins
 for case in ['valid','closure_artifact_changed','launch_only_changed','closure_rejected','closure_check_failed','pin_membership_changed','pin_resolved_changed']:
  c,pins=reset()
  if case=='closure_artifact_changed':artifact.write_text('unreviewed')
  if case=='launch_only_changed':files[-1].write_text('unreviewed')
  if case=='closure_rejected':c['accepted']=False
  if case=='closure_check_failed':c['checks'][0]['passed']=False
  if case=='pin_membership_changed':pins['files'].pop()
  if case=='pin_resolved_changed':pins['inventory'][str(files[-1])]['resolved']=str(p/'wrong')
  (p/'closure.json').write_text(json.dumps(c));(p/'green2-pins.json').write_text(json.dumps(pins))
  error=None
  try:exec(code,dict(D=p,Path=Path,json=json,hashlib=hashlib,require=require))
  except ValueError as ex:error=str(ex)
  passed=(error is None)==(case=='valid');checks.append(dict(case=case,passed=passed,error=error))
  if not passed:raise ValueError('synthetic case '+case)
result=dict(accepted=True,checks=checks,scope='exact extracted unexecuted publication evidence guard only;367tiny temporary files;no Git/staging/Julia',bindings={str(D/'publication.py'):sha(D/'publication.py'),str(Path(__file__).resolve()):sha(Path(__file__).resolve())})
with (D/'publication-fix-tests.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(dict(accepted=True,cases=len(checks))))
