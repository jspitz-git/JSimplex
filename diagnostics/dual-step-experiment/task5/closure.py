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
s=importlib.util.spec_from_file_location('task5closuredefs',D/'public-run.py');L=importlib.util.module_from_spec(s);s.loader.exec_module(L)
p=read(D/'public-green-pins.json');check(len(p['files'])==590 and L.G.pins_match(p),'590 actual unchanged completion pins')
a=read(D/'result-review.json');check(a['accepted'] is True and a['pins_sha256']==sha(D/'public-green-pins.json'),'exact independent whole branch/result review')
for n,h in a['bindings'].items():
 check(not n.startswith('/tmp/'),'persistent review binding '+n);check(sha(n)==h,'actual review binding '+n)
q=read(D/'postcheck.json');g=q['qualification'];check(q['accepted'] is True and len(q['checks'])==3699 and all(x['passed'] for x in q['checks']),'3699 offline composite checks')
check(g['accepted'] is True and g['assertions']==4669 and g['skipped']==0 and g['public_repeated_passes']==424,'4669 unique ordinary assertions/no skips,424 repeated deduplicated')
check(sum(g['testsets'].values())==4669 and sum(v for n,v in g['testsets'].items() if n.startswith('Task5 '))==146,'146 newTask5 and complete observed totals')
old=read(D.parent/'task4/postcheck.json')['runs']['green2']['testsets'];check(sum(old.values())==709 and all(g['testsets'].get(n)==v for n,v in old.items()),'709 unchanged prior assertions')
for stage,accepted,exitcode in [('red',True,1),('boundary-red',True,1),('green',False,1),('green2',False,1),('public-green',True,0)]:
 r=read(D/(stage+'-run/result.json'));check(r['accepted'] is accepted and r['exit']==exitcode,stage+' actual result preserved')
check(read(D/'before-loader-review/admission.json')['accepted'] is False and read(D/'before-source-review/admission.json')['accepted'] is False,'both initial review rejections preserved')
for n,v in read(D/'qualified-sources.json').items():check(sha(n)==v['sha256']==sha(v['preserved']),'qualified source '+n)
for n,v in read(D/'continuation-map.json').items():
 check(sha(v['preserved'])==v['sha256']==read(D.parent/'task4/closure.json')['bindings'][n],'exact Task4 continuation mapping')
 check(a['bindings'].get(n)==sha(n),'current continuation independently reviewed')
for n,target in read(D/'source-aliases.json').items():check(Path(n).is_symlink() and os.readlink(n)==target and Path(n).resolve(strict=True)==W/'src','exact source directory alias')
h=L.host();check(h['no_julia'] is True and not h['conflicts'] and len(h['checked_groups'])==816,'fresh816groups ANDsessions/noJulia/currentrefs')
with (D/'closure-host.json').open('x') as f:json.dump(h,f,indent=2)
check(L.H.H.git(W,'diff','--name-only','--','src').splitlines()==['src/dual_simplex.jl','src/solver.jl'],'only two planned internal hook production files')
check(not L.H.H.git(W,'diff','--name-only','--','test','Project.toml','Manifest.toml','.github','diagnostics/dual-step-experiment/task1','diagnostics/dual-step-experiment/task2','diagnostics/dual-step-experiment/task3','diagnostics/dual-step-experiment/task4','docs/superpowers/plans/2026-10-31-experimental-dual-engine.md','docs/superpowers/specs/2026-10-31-experimental-dual-engine-design.md'),'old tests/env/CI/evidence/approvedplan frozen')
report=(D/'REPORT.md').read_text();check('composite' in report.lower() and 'Task6 remains open' in report and 'no speedup' in report.lower() and '4148Pass/1Error' in report,'composite/no-speedup/failedmain/open scope disclosed')
files=sorted({x for x in D.rglob('*') if x.is_file() and not x.is_symlink()}|set((W/'experimental/dual_engine').rglob('*.jl'))|{W/'src/solver.jl',W/'src/dual_simplex.jl',W/'diagnostics/dual-step-experiment/README.md'})
with (D/'closure.json').open('x') as f:json.dump(dict(accepted=True,checks=checks,bindings={str(x):sha(x) for x in files},aliases=read(D/'source-aliases.json'),scope='Task5 explicitly composite observed qualification, original GREEN2 remains failed; local branch only/no master/push/Task6'),f,indent=2)
print(json.dumps(dict(accepted=True,checks=len(checks),bindings=len(files))))
