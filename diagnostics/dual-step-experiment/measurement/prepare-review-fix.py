from pathlib import Path
import json,shutil,hashlib,importlib.util,sys,subprocess,ast
sys.dont_write_bytecode=True
W=Path('/home/jspitz/.codex/worktrees/dual-step-experiment/JSimplex.jl');D=W/'diagnostics/dual-step-experiment/measurement';B=D/'before-admission-review';B.mkdir();R=Path('/tmp/task6-qual-review');a=json.loads((R/'admission.json').read_text())
if a['accepted'] is not False:raise ValueError('original rejection')
for n,h in a['bindings'].items():
 with open(n,'rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
 if actual!=h:raise ValueError('initial reviewer binding '+n)
for src,dst in [('REVIEW.md','REVIEW.md'),('admission.json','admission.json')]:shutil.copyfile(R/src,B/dst)
mapping={}
for name in ('inspection.jl','audit.py','qualify-pins.json','parser-tests.py'):
 p=D/name;q=B/name;shutil.copyfile(p,q);mapping[str(p)]=dict(sha256=hashlib.sha256(q.read_bytes()).hexdigest(),preserved=str(q))
(D/'admission-before-map.json').write_text(json.dumps(mapping,indent=2))
p=D/'inspection.jl';s=p.read_text();s=s.replace('===@__MODULE__ ||','===(@__MODULE__) ||');p.write_text(s)
p=D/'audit.py';s=p.read_text();s=s.replace('import sys,json,math,statistics as S','import sys,json,math,statistics as S')
needle='def analyze(mode,log):\n'
ordinary='''def ordinary_summary(mode,log):
 lines=log.splitlines();found=[]
 for i,line in enumerate(lines[:-1]):
  if not line.startswith('Test Summary:') or '|' not in line:continue
  name,sep,raw=lines[i+1].rpartition('|')
  if name.strip()!='Task6 '+mode+' whole verified solves':continue
  labels=line.split('|',1)[1].split();values=raw.split()
  require(sep and len(labels)==len(values) and labels[-1]=='Time','ordinary root summary schema')
  counts={k:int(v) for k,v in zip(labels[:-1],values[:-1])};found.append(counts)
 expected=236 if mode=='qualify' else 749
 require(len(found)==1,'exactly one ordinary root summary')
 counts=found[0]
 require(counts.get('Pass')==counts.get('Total')==expected and all(counts.get(k,0)==0 for k in ('Fail','Error','Broken')),'exact ordinary Pass/Total with no failure/error/skip')
 return expected
'''
if s.count(needle)!=1:raise ValueError('analyze unique')
s=s.replace(needle,ordinary+needle+' assertions=ordinary_summary(mode,log)\n')
s=s.replace("require(len(r['PREP'])==16,'all input preparation records')","require([x['case'] for x in r['PREP']]==CASES,'all input preparation records exactly once in order')")
s=s.replace("require(len(r['QUAL'])==len(r['REFERENCE_WORK'])==16 and len(r['FALLBACK'])==1,'all qualification/whole reference count records')","require([x['case'] for x in r['QUAL']]==CASES and [x['case'] for x in r['REFERENCE_WORK']]==CASES and len(r['FALLBACK'])==1,'exact qualification/reference case identities')\n  require(all(x['case'] in CASES for x in r['INSPECT']),'no unknown inspection case')")
s=s.replace("require({x['stage'] for x in inspected}==({'setup','exit'} if int(q['imports']) else set()),'actual inspection stage membership')","require(len(inspected)==(2 if int(q['imports']) else 0) and {x['stage'] for x in inspected}==({'setup','exit'} if int(q['imports']) else set()),'actual exactly-once inspection stages')")
s=s.replace("require(len(r['SAMPLE'])==224 and len(r['CHECK'])==224 and len(r['PREP_GC'])==16,'224 complete windows/checks/16 separately recorded warm GCs')","require(len(r['SAMPLE'])==224 and len(r['CHECK'])==224 and [x['case'] for x in r['PREP_GC']]==CASES,'224 complete windows/checks/16 exact warm GCs')")
s=s.replace("return dict(accepted=True,mode=mode,records=r","return dict(accepted=True,mode=mode,assertions=assertions,records=r");p.write_text(s);ast.parse(s)
# Preserve the observed RED test entrypoint, add a new final entrypoint without rerunning it.
s=(D/'parser-tests.py').read_text();needle="raw=fixture('qualify');test('bad_capacity'"
extra="""raw=fixture('qualify')
test('duplicate_qualification_case','qualify',raw.replace('QUAL case=n16_dense','QUAL case=n16_sparse',1),False)
test('duplicate_reference_case','qualify',raw.replace('REFERENCE_WORK case=n16_dense','REFERENCE_WORK case=n16_sparse',1),False)
test('missing_ordinary_summary','qualify',raw.replace('Task6 qualify whole verified solves |','WRONG qualify |'),False)
test('ordinary_broken_not_pass','qualify',raw.replace('Pass Total Time','Pass Broken Total Time').replace('| 236 236 1.0s','| 235 1 236 1.0s'),False)
"""
if s.count(needle)!=1:raise ValueError('test insertion')
s=s.replace(needle,extra+needle);(D/'parser-tests-final.py').write_text(s)
r=subprocess.run([sys.executable,'-B',str(D/'parser-tests-final.py')],capture_output=True,text=True)
(D/'parser-green-result.json').write_text(json.dumps(dict(returncode=r.returncode,stdout=r.stdout,stderr=r.stderr,accepted=r.returncode==0),indent=2))
if r.returncode:raise ValueError(r.stderr)
sp=importlib.util.spec_from_file_location('task6newparser',D/'audit.py');A=importlib.util.module_from_spec(sp);sp.loader.exec_module(A)
manifest=dict(scope='Task6 same-policy whole-solve experiment only, no master promotion',cases=A.CASES,qualification_whole_calls=66,qualification_assertions=236,comparison_whole_calls=224,comparison_assertions=749,warm_per_arm=2,measured_pairs=5,order='reference,candidate on odd pair; candidate,reference on even pair',common_seconds_each_admission=1800,settings='Float64/native PFI/fixed Devex, same shared immutable options object per case; exact Task5 constructors/presolve/scaling; observer nothing; primary reference public solve, E original solve_experimental and mandatory counters',inputs=[str(W/'test/fixtures/solver'/n) for n in A.NAMES],large_inputs='runtime/fast0507 histories are not short qualified full-model schedules; conditionally excluded with no large-model speed claim',memory='Julia/BLAS1 heap2GiB hint VM8GiB minRAM6GiB maxswap1GiB')
(D/'manifest.json').write_text(json.dumps(manifest,indent=2));shutil.copyfile('/tmp/task6-fix.py',D/'prepare-review-fix.py')
(D/'ADMISSION-FIX.md').write_text('Initial607-pin admission withheld for an undelimited zero-argument Julia macro in the cold inspector and insufficient ordinary summary/case-membership gates. Parenthesize the macro; enforce one236/749 Pass/Total ordinary root with no Fail/Error/Broken and exact qualification/reference/preparation/inspection identities. New pure offline parser RED observed the missing ordinary-count rejection before the fix (exit1); separate final test entrypoint covers valid records and invalid counts/status/compilation/schedule/capacities/identities and passes. All initial source/pins/rejection/RED are preserved; no Julia has run and no E or production code changed. A new exact numerical admission is required.\n')
files={str(p) for p in D.rglob('*') if p.is_file() and p.name!='qualify-pins.json'}
files|=set(json.loads((B/'qualify-pins.json').read_text())['files']);files.discard(str(D/'qualify-pins.json'));files.add(str(B/'qualify-pins.json'))
spec=importlib.util.spec_from_file_location('task6newguard',D/'guard/guard_reviewed.py');G=importlib.util.module_from_spec(spec);spec.loader.exec_module(G)
pins=dict(files=sorted(files),trees=[],inventory=G.inventory(sorted(files),[]));(D/'qualify-pins.json').write_text(json.dumps(pins,indent=2))
print(r.stdout.strip());print('NEW PINS',len(files),hashlib.sha256((D/'qualify-pins.json').read_bytes()).hexdigest())
