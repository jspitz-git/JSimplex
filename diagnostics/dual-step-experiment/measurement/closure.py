from pathlib import Path
import json,hashlib,importlib.util,sys,os
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;W=D.parents[2];checks=[];cache={}
def read(p):return json.loads(p.read_text())
def sha(p):
 p=str(p)
 if p not in cache:
  with open(p,'rb') as f:cache[p]=hashlib.file_digest(f,'sha256').hexdigest()
 return cache[p]
def check(v,m):
 checks.append(dict(check=m,passed=bool(v)))
 if not v:raise ValueError(m)
s=importlib.util.spec_from_file_location('task6closuredefs',D/'run.py');L=importlib.util.module_from_spec(s);s.loader.exec_module(L)
for mode,count in [('qualify',622),('compare',642)]:
 p=read(D/(mode+'-pins.json'));check(len(p['files'])==count and L.G.pins_match(p),mode+' all launchpins unchanged')
 a=read(D/(mode+'-admission.json'));check(a['accepted'] is True and a['pins_sha256']==sha(D/(mode+'-pins.json')),mode+' exact independent admission')
 r=read(D/(mode+'-run/result.json'));check(r['accepted'] is True and r['exit']==r['audit_exit']==0 and r['elapsed_seconds']<=1800,mode+' actual accepted outcome')
a=read(D/'result-review.json');check(a['accepted'] is True and a['pins_sha256']==sha(D/'compare-pins.json'),'exact final wholebranch/result independent review')
for n,h in a['bindings'].items():check(not n.startswith('/tmp/') and sha(n)==h,'actual persistent finalreview binding '+n)
p=read(D/'postcheck.json');check(p['accepted'] is True and p['ordinary_assertions']==985 and len(p['checks'])==9886 and all(x['passed'] for x in p['checks']),'985ordinary assertions and9886postchecks')
q=read(D/'qualify-run/audit.json');c=read(D/'compare-run/audit.json');check(q['assertions']==236 and c['assertions']==749,'actual236+749 ordinary Test counts')
check(len(c['records']['SAMPLE'])==224 and sum(x['phase']=='measure' for x in c['records']['SAMPLE'])==160,'actual64warm160measured whole solves')
active=[v for v in c['summary'].values() if v['activated']];check(len(active)==13 and all(v['paired_seconds']['median']>1 for v in active),'all13activated observed time medians slower, no manufactured win')
check(read(D/'before-admission-review/admission.json')['accepted'] is False and read(D/'parser-red-result.json')['expected_failure_observed'] is True,'initial rejection/offlineRED preserved')
for n,v in read(D/'admission-before-map.json').items():check(sha(v['preserved'])==v['sha256'],'original admission version '+n)
for n,v in read(D/'continuation-map.json').items():check(sha(v['preserved'])==v['sha256']==read(D.parent/'task5/closure.json')['bindings'][n],'Task5 exact continuation mapping')
for n,v in read(D.parent/'task5/qualified-sources.json').items():check(sha(n)==v['sha256']==sha(v['preserved']),'Task5 qualified source unchanged '+n)
check(not L.H.H.git(W,'diff','--name-only','--','src','test','experimental','Project.toml','Manifest.toml','.github','diagnostics/dual-step-experiment/task1','diagnostics/dual-step-experiment/task2','diagnostics/dual-step-experiment/task3','diagnostics/dual-step-experiment/task4','diagnostics/dual-step-experiment/task5','docs/superpowers/plans/2026-10-31-experimental-dual-engine.md','docs/superpowers/specs/2026-10-31-experimental-dual-engine-design.md'),'Task6 no source/tests/env/CI/old evidence/plan change')
report=(D/'REPORT.md').read_text();check('No integration proposal is accepted from this record' in report and 'first-window effect' in report and 'not confidence intervals' in report,'negative result,scatter and no promotion explicit')
aliases={str(D/'project/src'):os.readlink(D/'project/src')};check((D/'project/src').is_symlink() and (D/'project/src').resolve(strict=True)==W/'src','actual source directory alias')
h=L.host();check(h['no_julia'] and not h['conflicts'] and len(h['checked_groups'])==820,'fresh820 historicalgroupsANDsessions/noJulia/currentrefs')
with (D/'closure-host.json').open('x') as f:json.dump(h,f,indent=2)
files=sorted({x for x in D.rglob('*') if x.is_file() and not x.is_symlink()}|{W/'diagnostics/dual-step-experiment/README.md'})
with (D/'closure.json').open('x') as f:json.dump(dict(accepted=True,checks=checks,bindings={str(x):sha(x) for x in files},aliases=aliases,scope='Task6 observed negative same-policy whole-solve comparison, no promotion/master/CI change; userauthorized accumulated experimentalbranch push'),f,indent=2)
print(json.dumps(dict(accepted=True,checks=len(checks),bindings=len(files))))
