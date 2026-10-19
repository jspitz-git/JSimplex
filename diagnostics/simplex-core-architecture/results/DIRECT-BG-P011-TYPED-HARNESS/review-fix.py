"""One offline repair of the new harness; preserve rejected inputs first."""
from pathlib import Path
import json,hashlib,tomllib
D=Path(__file__).resolve().parent
F=D.with_name('DIRECT-BG-BLOCKED-UPDATE-RED2-HARNESS')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def new(p,s):
 with p.open('x') as f:f.write(s)
def save(n,v):new(D/n,json.dumps(v,indent=2)+'\n')
review=json.loads((D/'review.json').read_text())
if review['accepted'] is not False or len(review['findings'])!=1:raise RuntimeError('Expected one rejected review finding')
names=['oracle.py','ADMISSION.md','REPORT.md','required-paths.json','preparation-pins.json','review.json','review.md']
before={}
for n in names:
 p=D/n;q=D/(n+'.before-review')
 with q.open('xb') as f:f.write(p.read_bytes())
 before[str(p)]={'preserved_path':str(q),'sha256':sha(q)}
raw=F/'runs/red300/output/unit-1.toml'
detail=tomllib.loads(raw.read_text())['records']['failures'][0]['detail']
source=str(F/'panel-tests.jl')
expected='Test Failed at '+source+':103\n  Expression: $(Expr(:escape, :(#= '+source+':103 =# @allocated(K._bgb_eligibility(f, 1)) == 0)))\n'
if detail!=expected:raise RuntimeError('Historical rendering differs')
if (F/'panel-tests.jl').read_text().splitlines()[102].strip()!='@check "P011" (@allocated K._bgb_eligibility(f,1)) == 0':raise RuntimeError('Source line differs')
p=D/'oracle.py';s=p.read_text()
s=s.replace('import math,re\n','import math,re\n# Exact saved rendering of the frozen original test source and recorder.\n# Any different expression/location/extra content fails closed; no byte count is prescribed.\nRED_FAILURE_DETAIL='+repr(detail)+'\n',1)
old="type(f['detail']) is str and bool(f['detail'])"
if s.count(old)!=1:raise RuntimeError('Detail selector')
s=s.replace(old,"type(f['detail']) is str and f['detail']==RED_FAILURE_DETAIL")
old="  detail=payload['unit-1.toml']['records']['failures'][0]['detail']\n  token='TEST FAILURE: P011 '+detail"
newtext="  detail=payload['unit-1.toml']['records']['failures'][0]['detail']\n  if detail!=RED_FAILURE_DETAIL:return True\n  # Check warning/error text before removing the exact expected Test rendering.\n  if re.search(r'warning|world.?age|method.*overwrit|LoadError|ERROR:|OutOfMemoryError',log,re.I):return True\n  token='TEST FAILURE: P011 '+detail"
if s.count(old)!=1:raise RuntimeError('Log selector')
s=s.replace(old,newtext);p.write_text(s)
s=(D/'tests.py').read_text()
old="detail='Test Failed at saved.jl:104\\n  Expression: measured == 0\\n   Evaluated: 208 == 0'"
if s.count(old)!=1:raise RuntimeError('Fixture selector')
s=s.replace(old,'detail=o.RED_FAILURE_DETAIL')
s=s.replace("('tests.py','oracle.py','audit.py','control.py','driver.jl')","('tests-reviewed.py','oracle.py','audit.py','control.py','driver.jl')")
s=s.replace("(D/'tests.json').open('x')","(D/'tests-reviewed.json').open('x')")
marker='# GREEN must stop at missing RED acceptance, even before a result-review lookup.'
extra='''# Fresh regression cases for the rejected overly broad failure-detail exception.
phase='p011-red300';p=fixture(phase)
for index,bad in enumerate([
 'arbitrary failure',o.RED_FAILURE_DETAIL.replace('_bgb_eligibility','unrelated_assertion'),
 o.RED_FAILURE_DETAIL.replace(':103',':104'),o.RED_FAILURE_DETAIL+'WARNING: method overwriting',
 o.RED_FAILURE_DETAIL+'\\nTest Failed at another.jl',o.RED_FAILURE_DETAIL+'\\nERROR: hidden',
 o.RED_FAILURE_DETAIL.replace(' == 0',' == 1'),o.RED_FAILURE_DETAIL.replace('P011','P095')+'extra',
 o.RED_FAILURE_DETAIL+'\\n   Evaluated: 208 == 0',o.RED_FAILURE_DETAIL.rstrip(),
]):
 q=deepcopy(p);q['unit-1.toml']['records']['failures'][0]['detail']=bad;q['raw.toml']['unit']=deepcopy(q['unit-1.toml'])
 refuse('strict_failure_detail_'+str(index),lambda q=q:validate(q,phase))
 check('log_standalone_rejects_detail_'+str(index),o.warning_log('TEST FAILURE: P011 '+bad+'\\n',q,phase))
 def mutate(run,out,payload,q=q,bad=bad):
  for name in ('unit-1.toml','raw.toml'):(payload/name).write_text(td(q[name]))
  (out/'run.log').write_text('TEST FAILURE: P011 '+bad+'\\n')
 full_case(phase,'strict_failure_full_'+str(index),mutate)
'''
if s.count(marker)!=1:raise RuntimeError('Regression insertion selector')
s=s.replace(marker,extra+marker);new(D/'tests-reviewed.py',s)
p=D/'ADMISSION.md';s=p.read_text();s+='\n## Review correction: exact RED failure rendering\n\nThe initial review rejected a permissive failure-detail exception. The canonical auditor now requires the exact saved original P011 expression, source location and recorder rendering, with no additional content. Warning/error detection occurs before removing that exact expected rendering from the log. No measured byte count is prescribed. A different future rendering rejects the run and is preserved for separate analysis; it is not accepted by widening the exception after the run. The historical RED2 unit is evidence for formatting only, not a substitute for new RED execution. Original oracle, documents, manifest and rejected review remain in explicit `.before-review` copies; original Python results remain unchanged.\n';p.write_text(s)
p=D/'REPORT.md';s=p.read_text();s+='\nInitial independent review rejected one Important auditor gap: an arbitrary P011-labelled failure detail could conceal an unrelated assertion or warning. The offline correction binds the exact original expression/location/rendering and checks warnings before any removal. New `tests-reviewed.py` adds full-auditor and standalone negative cases; its separate result and final independent review determine acceptance. The initial 864 checks and 756/759 independent result remain preserved, not retroactively passing evidence. No driver, candidate, stage or Julia test source changed in this correction.\n';p.write_text(s)
save('review-fix-provenance.json',dict(scope='One offline strict RED-rendering fix; no Julia or old script rerun',before=before,historical_rendering_source=str(raw),historical_rendering_sha256=sha(raw),expected_detail=detail,after_sha256={str(D/n):sha(D/n) for n in ['oracle.py','tests-reviewed.py','ADMISSION.md','REPORT.md']}))
print('Preserved seven initial files; corrected strict RED rendering and added new synthetic script.')
