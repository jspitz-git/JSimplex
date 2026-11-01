from pathlib import Path
import json,hashlib,importlib.util,sys
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;W=D.parents[2];checks=[]
def read(p):return json.loads(p.read_text())
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def check(v,m):
 checks.append(dict(check=m,passed=bool(v)))
 if not v:raise ValueError(m)
s=importlib.util.spec_from_file_location('task4closuredefs',D/'run2.py');L=importlib.util.module_from_spec(s);s.loader.exec_module(L)
p=read(D/'green2-pins.json');check(len(p['files'])==367 and L.G.pins_match(p),'367 actual unchanged GREEN2 launchpins')
a=read(D/'green2-admission.json');check(a['accepted'] is True and a['pins_sha256']==sha(D/'green2-pins.json'),'exact independent GREEN2 source/numerical admission')
a=read(D/'result-review.json');check(a['accepted'] is True and a['pins_sha256']==sha(D/'green2-pins.json'),'exact independent observed result review')
for n,h in a['bindings'].items():
 check(not n.startswith('/tmp/'),'persistent independent binding '+n)
 check(sha(n)==h,'actual independent result binding '+n)
q=read(D/'postcheck.json');check(q['accepted'] is True and len(q['checks'])==1080 and all(x['passed'] for x in q['checks']),'1080 new postexit checks accepted')
counts=q['runs']['green2']['testsets'];check(sum(counts.values())==q['runs']['green2']['assertions']==709,'709 ordinary Test assertions')
check(sum(v for n,v in counts.items() if n.startswith('Task4 '))==154,'154 new Task4 assertions')
check(sum(v for n,v in counts.items() if not n.startswith('Task4 '))==555,'555 unchanged prior assertions')
check(counts['Task4 BFRT correction retains row and entering direction']==12,'12 slot3 BFRT dependency/correction assertions')
for stage,accepted,exitcode in [('red',True,1),('green',False,1),('green2',True,0)]:
 r=read(D/(stage+'-run/result.json'));check(r['accepted'] is accepted and r['exit']==exitcode,stage+' actual preserved result')
check(read(D/'before-bfrt-review/admission.json')['accepted'] is False,'initial BFRT coverage rejection preserved')
for n,v in read(D/'qualified-sources.json').items():check(sha(n)==v['sha256']==sha(v['preserved']),'qualified source '+n)
for n,v in read(D/'continuation-map.json').items():
 check(sha(v['preserved'])==v['sha256'],'Task3 continuation bytes preserved')
 check(read(D.parent/'task3/closure.json')['bindings'][n]==v['sha256'],'exact Task3 closure continuation mapping')
 check(n in a['bindings'] and sha(n)==a['bindings'][n],'current README independently reviewed')
for n,v in read(D/'review-copy-map.json').items():check(sha(v['preserved'])==v['sha256'],'exact persistent reviewed-manifest mapping '+n)
h=L.host();check(h['no_julia'] is True and not h['conflicts'] and len(h['checked_groups'])==806,'fresh806groups ANDsessions/noJulia/currentrefs')
with (D/'closure-host.json').open('x') as f:json.dump(h,f,indent=2)
check(not L.H.H.git(W,'diff','--name-only','--','src','test','Project.toml','Manifest.toml','.github'),'production unchanged')
check(not L.H.H.git(W,'diff','--name-only','--','diagnostics/dual-step-experiment/task1','diagnostics/dual-step-experiment/task2','diagnostics/dual-step-experiment/task3','docs/superpowers/plans/2026-10-31-experimental-dual-engine.md','docs/superpowers/specs/2026-10-31-experimental-dual-engine-design.md'),'old evidence and approved plan/design frozen')
report=(D/'REPORT.md').read_text();check('16N+8m' in report and 'no speedup' in report.lower() and 'Tasks5–6 remain open' in report,'memory/no-speedup/open scope disclosed')
files=sorted(x for x in D.rglob('*') if x.is_file())+sorted((W/'experimental/dual_engine').rglob('*.jl'))+[W/'diagnostics/dual-step-experiment/README.md']
with (D/'closure.json').open('x') as f:json.dump(dict(accepted=True,checks=checks,bindings={str(x):sha(x) for x in files},scope='Task4 observed postexit closure only; no production promotion/retroactive pins'),f,indent=2)
print(json.dumps(dict(accepted=True,checks=len(checks),bindings=len(files))))
