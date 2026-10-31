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
s=importlib.util.spec_from_file_location('task3closuredefs',D/'run.py');L=importlib.util.module_from_spec(s);s.loader.exec_module(L)
p=read(D/'green-pins.json');check(len(p['files'])==290 and L.G.pins_match(p),'290 actual unchanged launchpins')
a=read(D/'green-admission.json');check(a['accepted'] is True and a['pins_sha256']==sha(D/'green-pins.json'),'exact source/numerical admission')
a=read(D/'result-review.json');check(a['accepted'] is True and a['pins_sha256']==sha(D/'green-pins.json'),'exact independent resultreview')
for n,h in a['bindings'].items():check(sha(n)==h,'review actual artifact binding '+n)
q=read(D/'postcheck.json');check(q['accepted'] is True and all(x['passed'] for x in q['checks']),'all new postexit checks accepted')
check(q['runs']['green']['assertions']==sum(q['runs']['green']['testsets'].values())==555,'555 observed ordinary Test passes')
check(sum(v for n,v in q['runs']['green']['testsets'].items() if n.startswith('Task3 '))==184,'184 Task3 assertions')
check(sum(v for n,v in q['runs']['green']['testsets'].items() if n.startswith(('Task1 ','Task2 ')))==371,'371unchanged Task1/2 assertions')
for stage,exitcode in [('red',1),('underflow-red',1),('lifetime-red',1),('green',0)]:
 r=read(D/(stage+'-run/result.json'));check(r['accepted'] is True and r['exit']==exitcode,stage+' exact accepted exit')
check(read(D/'before-source-review/admission.json')['accepted'] is False,'original rejected review preserved')
for n,v in read(D/'qualified-sources.json').items():check(sha(n)==v['sha256']==sha(v['preserved']),'qualified source '+n)
for n,v in read(D/'continuation-map.json').items():
 check(sha(v['preserved'])==v['sha256'],'before continuation preserved')
 check(read(D.parent/'task2/closure.json')['bindings'][n]==v['sha256'],'exact Task2 closure continuation mapping')
for n,v in read(D/'completion-before-map.json').items():
 check(sha(v['preserved'])==v['sha256'],'pending continuation bytes preserved')
 check(n in a['bindings'] and sha(n)==a['bindings'][n],'current README bound by independent result review')
h=L.host();check(h['no_julia'] is True and not h['conflicts'] and len(h['checked_groups'])==800,'fresh800groups ANDsessions/noJulia/currentrefs')
with (D/'closure-host.json').open('x') as f:json.dump(h,f,indent=2)
check(not L.H.H.git(W,'diff','--name-only','--','src','test','Project.toml','.github'),'production unchanged')
check(not L.H.H.git(W,'diff','--name-only','--','diagnostics/dual-step-experiment/task1','diagnostics/dual-step-experiment/task2','docs/superpowers/plans/2026-10-31-experimental-dual-engine.md','docs/superpowers/specs/2026-10-31-experimental-dual-engine-design.md'),'old evidence and plan/design frozen')
report=(D/'REPORT.md').read_text();check('50N+28m' in report and 'no speedup' in report.lower() and 'Tasks4–6 remain open' in report,'work/memory/unfinished scope disclosed')
files=sorted(p for p in D.rglob('*') if p.is_file())+sorted((W/'experimental/dual_engine').rglob('*.jl'))+[W/'diagnostics/dual-step-experiment/README.md']
with (D/'closure.json').open('x') as f:json.dump(dict(accepted=True,checks=checks,bindings={str(p):sha(p) for p in files},scope='Task3 postexit closure only; no production promotion/retroactive pins'),f,indent=2)
print(json.dumps(dict(accepted=True,checks=len(checks),bindings=len(files))))
