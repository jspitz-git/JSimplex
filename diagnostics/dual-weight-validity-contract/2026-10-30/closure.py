from pathlib import Path
import json,hashlib,subprocess
D=Path(__file__).resolve().parent;W=D.parents[2];M=Path('/home/jspitz/JSimplex.jl');checks={};bindings={}
def read(p):
 p=Path(p);b=p.read_bytes();bindings[str(p)]=hashlib.sha256(b).hexdigest();return b
def require(k,v):
 checks[k]=bool(v)
 if not v:raise RuntimeError(k)
def verify(mapping,prefix):
 for p,e in mapping.items():
  sha=e if isinstance(e,str) else e['sha256'];require(prefix+':'+p,hashlib.sha256(read(p)).hexdigest()==sha)
a=json.loads(read(D/'source-evidence.json'));require('source_only_assessment',a['accepted'] and len(a['checks'])==96 and all(a['checks'].values()));verify(a['bindings'],'source')
f=json.loads(read(D/'review-fix.json'));require('ledger_fix',f['accepted'] and all(f['checks'].values()));verify(f['bindings'],'fix')
initial=json.loads(read(D/'review-initial.json'));require('initial_finding_preserved',initial['accepted'] is False and initial['checks']['work_ledger_dimension_complete'] is False)
for p,sha in initial['bindings'].items():
 require('initial_report_mapping',p==str(D/'REPORT.md') and hashlib.sha256(read(D/'REPORT.before-review.md')).hexdigest()==sha)
r=json.loads(read(D/'review-final.json'));require('final_independent_review',r.get('accepted') is True and bool(r['checks']) and all(r['checks'].values()));verify(r['bindings'],'review')
h=json.loads(read(D/'host.json'));require('host_record',not h['conflicts'] and len(h['checked_groups'])==727)
for p in (M/'src').rglob('*.jl'):require('production_unchanged:'+str(p.relative_to(M)),read(p)==read(W/p.relative_to(M)))
for ref in ['HEAD','master','origin/master']:require('master_'+ref,subprocess.check_output(['git','-C',str(M),'rev-parse',ref],text=True).strip()=='c0fa748ffa61ccb7c1caaf248c40324f60bc737b')
require('diagnostic_start',subprocess.check_output(['git','-C',str(W),'rev-parse','HEAD'],text=True).strip()=='aad722caf65fbefc09e9a38eca887ab2a1a89581')
require('tracked_untouched',subprocess.run(['git','-C',str(W),'diff','--quiet','HEAD','--']).returncode==0)
require('no_new_Julia_candidate_or_driver',not list(D.rglob('*.jl')))
read(D/'REPORT.md');read(D/'REVIEW-FINAL.md');read(D/'REVIEW-INITIAL.md');read(D/'closure.py')
(D/'closure.json').write_text(json.dumps(dict(accepted=True,production_admission=False,numerical_admission=False,scope='source-only decision record; prospective Devex route needs own design/tests',checks=checks,bindings=bindings),indent=2)+'\n');print(json.dumps({'accepted':True,'checks':len(checks),'bindings':len(bindings)}))
