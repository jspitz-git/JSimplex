"""One bounded offline closure-gate correction; never execute closure/Julia."""
from control import *
import ast,copy,tempfile
for name in ['close.py','REPORT.md','required-paths.json','preparation-pins.json']:
 p=D/name
 with (D/(name+'.before-review')).open('xb') as f:f.write(p.read_bytes())
p=D/'close.py';s=p.read_text();old="v=rd(P/'review.json');need(v['accepted'] is True and v['findings']==[] and v['scope']=='direct adapter driver preparation','Review acceptance')\nfor key in ['sha256','evidence_sha256']:\n for n,h in v.get(key,{}).items():need(sha(Path(n) if Path(n).is_absolute() else R/n)==h,'Review binding '+n)"
require(s.count(old)==1,'Unique rejected gate')
s=s.replace('from control import full_host','from control import full_host, preparation').replace(old,'preparation()  # Canonical exact membership, manifest hash and independent review BEFORE writes.')
p.write_text(s)
p=D/'REPORT.md';p.write_text(p.read_text()+'''\n## Independent review correction\n\nInitial review rejected one closure gate: accepted-shaped review data with omitted\nor empty bindings could bypass its local loops. The initial review, four before\nversions and original69-pin inventory remain preserved. close.py now calls the\ncanonical control.preparation() before any write; exact required membership,\nmanifest identity and every independent review hash are mandatory. Separate pure\nPython negative checks exercise missing/empty/extra bindings and missing/wrong\nmanifest hash. No closure, seal, launcher, guard or Julia runs in this correction.\nThe revised preparation inventory includes the rejected evidence and correction;\ninitial69 bindings map only changed paths to their explicit before-review copies.\n''')
checks={}
oldtree=ast.parse((D/'close.py.before-review').read_text());newtree=ast.parse(s)
checks['red_old_missing_canonical_gate']=not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='preparation' for n in ast.walk(oldtree))
call=next(n for n in ast.walk(newtree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='preparation')
writes=[n.lineno for n in ast.walk(newtree) if isinstance(n,ast.Call) and ((isinstance(n.func,ast.Name) and n.func.id=='save') or (isinstance(n.func,ast.Attribute) and n.func.attr=='write_text'))]
checks['green_canonical_gate_before_writes']=call.lineno<min(writes)
with tempfile.TemporaryDirectory(prefix='direct-adapter-review-') as td:
 t=Path(td);m=t/'pins.json';f=t/'source';f.write_text('fixture');m.write_text('{}');required=[str(f),str(m)]
 valid=dict(accepted=True,findings=[],scope='direct adapter driver preparation',pins_sha256=sha(m),sha256={n:sha(n) for n in required})
 verify_review(valid,m,required,valid['scope']);checks['complete_review_accepted']=True
 for case in ['missing_bindings','empty_bindings','extra_binding','missing_manifest','wrong_manifest','changed_source']:
  v=copy.deepcopy(valid)
  if case=='missing_bindings':v.pop('sha256')
  if case=='empty_bindings':v['sha256']={}
  if case=='extra_binding':v['sha256'][str(t/'unexpected')]='0'*64
  if case=='missing_manifest':v.pop('pins_sha256')
  if case=='wrong_manifest':v['pins_sha256']='0'*64
  if case=='changed_source':v['sha256'][str(f)]='0'*64
  try:verify_review(v,m,required,valid['scope'])
  except RuntimeError:checks[case+'_rejected']=True
  else:checks[case+'_rejected']=False
maps=[]
for n,h in rd(D/'preparation-pins.json.before-review')['sha256'].items():
 p=Path(n);target=p
 if p.parent==D and p.name in ['close.py','REPORT.md','required-paths.json']:target=D/(p.name+'.before-review')
 require(sha(target)==h,'Initial inventory drift '+n)
 if target!=p:maps.append(dict(original=n,preserved=str(target),sha256=h))
checks['initial69_preserved']=len(rd(D/'preparation-pins.json.before-review')['sha256'])==69
checks['no_run_created']=not (D/'runs').exists()
require(all(checks.values()),'Correction failed')
save(D/'review-fix.json',dict(all_passed=True,checks=checks,initial_maps=maps,julia_executed=False))
# Preserve and replace canonical inventory, including rejected review and this script.
files=set(rd(D/'required-paths.json.before-review')['paths'])|{str(p) for p in D.iterdir() if p.is_file()}
files.discard(str(D/'preparation-pins.json'))
paths=sorted(files)
(D/'required-paths.json').write_text(json.dumps(dict(paths=paths),indent=2)+'\n')
(D/'preparation-pins.json').write_text(json.dumps(dict(scope='OFFLINE revised driver preparation, not phase/launch admission',sha256={n:sha(n) for n in paths}),indent=2)+'\n')
require(bindings(rd(D/'preparation-pins.json')),'Revised bindings')
print('Correction',len(checks),'PASS; canonical',len(paths),'pins; no Julia/closure/launch')
