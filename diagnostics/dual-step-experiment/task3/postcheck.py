from pathlib import Path
import sys,json,hashlib,re,importlib.util
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;W=D.parents[2];checks=[]
def read(p):return json.loads(p.read_text())
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def require(v,m):
 checks.append(dict(check=m,passed=bool(v)))
 if not v:raise ValueError(m)
def historical(n,expected):
 p=Path(n)
 if sha(p)==expected:return p
 maps=[D/'task2-before-map.json',D.parent/'task2/task1-before-map.json',D/'before-source-review-map.json',D/'attempt-counter-before-map.json',D/'budget-tests-before-map.json',D/'generation-expiry-before-map.json',D/'lifetime-before-map.json',D/'lifetime-fix-before-map.json']
 for m in maps:
  v=read(m)
  if n in v and v[n]['sha256']==expected and sha(v[n]['preserved'])==expected:return Path(v[n]['preserved'])
 for b in [D/'before-green-tests',D/'before-red-contract',D.parent/'task2/before-coverage-review',D.parent/'task2/before-canceled-row']:
  q=b/p.name
  if q.is_file() and sha(q)==expected:return q
 raise ValueError('missing exact before mapping: '+n)
s=importlib.util.spec_from_file_location('task3defs',D/'run.py');L=importlib.util.module_from_spec(s);s.loader.exec_module(L)
p=read(D/'green-pins.json');require(L.G.pins_match(p),'all actual GREEN pins unchanged')
a=read(D/'green-admission.json');require(a['accepted'] is True and a['pins_sha256']==sha(D/'green-pins.json'),'exact bound independent GREEN admission')
oldmanifests=[D/'red-pins.json',D/'before-red-contract/red-pins.json',D/'before-source-review/diagnostics/dual-step-experiment/task3/green-pins.json',D/'underflow-red-pins.json',D/'before-attempt-counter/green-pins.json',D/'before-budget-tests/green-pins.json',D/'before-generation-expiry/green-pins.json',D/'lifetime-red-pins.json',D/'before-lifetime/green-pins.json',D.parent/'task2/green-pins.json']
for path in oldmanifests:
 for n,v in read(path)['inventory'].items():
  q=historical(n,v['sha256']);require(sha(q)==v['sha256'],'historical binding '+str(path.relative_to(D.parent))+': '+n)
require(read(D/'before-source-review/admission.json')['accepted'] is False,'initial GREEN rejection preserved')
runs={}
for stage,expected_failures in [('red',4),('underflow-red',1),('lifetime-red',4),('green',0)]:
 out=D/(stage+'-run');r=read(out/'result.json');pr=read(out/'guard/process.json');cfg=read(D/(stage+'-contract.json'));log=(out/'guard/run.log').read_text()
 require(r['accepted'] is True and r['exit']==cfg['exit'] and pr['returncode']==cfg['exit'] and pr['reason']=='exit'+str(cfg['exit']),stage+' accepted expected exit')
 require(r['pins_unchanged'] and pr['pins_unchanged'] and r['elapsed_seconds']<=r['limit_seconds']==1800,stage+' pins/time bounds')
 require(pr['command']==cfg['command'],stage+' actual exact command')
 review=read(D/(stage+'-admission.json'));require(review['accepted'] is True and review['pins_sha256']==sha(D/(stage+'-pins.json')),stage+' exact independent admission')
 samples=[json.loads(x) for x in (out/'guard/resources.jsonl').read_text().splitlines()]
 require(samples and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in samples),stage+' sampled memory bounds')
 require(pr['terminal_memory']['available_kib']>=6*1024**2 and pr['terminal_memory']['swap_used_kib']<=1024**2,stage+' terminal memory bounds')
 h=read(out/'terminal-host.json');require(h['no_julia'] is True and not h['conflicts'],stage+' full group/session closure')
 summary=dict(elapsed_seconds=r['elapsed_seconds'],samples=len(samples),min_available_kib=min(x['available_kib'] for x in samples),max_swap_kib=max(x['swap_used_kib'] for x in samples),child_maxrss_kib=pr['child_maxrss_kib'])
 if expected_failures:
  setup_passes=3 if stage=='lifetime-red' else 0
  require(f'{setup_passes} passed, {expected_failures} failed, 0 errored, 0 broken' in log,stage+' exact expected failure count')
  if stage=='underflow-red':require('No exception thrown' in log and 'Expected: ArgumentError' in log,'underflow RED proves missing exception, not setup error')
 else:
  require('DUAL_ENGINE_TASK3_COMPLETED' in log and 'Test Failed' not in log and 'Error During Test' not in log,'GREEN ordinary Test completed')
  rows=re.findall(r'^(.+?)\s*\|\s+(\d+)\s+(\d+)\s+[\d.]+s\s*$',log,re.M)
  require(rows and all(int(a)==int(b) for _,a,b in rows),'ordinary Test summaries all passed')
  summary['testsets']={n.strip():int(a) for n,a,b in rows};summary['assertions']=sum(summary['testsets'].values())
 runs[stage]=summary
h=L.host();require(h['no_julia'] is True and not h['conflicts'],'fresh current refs/full groupsANDsessions/noJulia')
with (D/'postcheck-host.json').open('x') as f:json.dump(h,f,indent=2)
require(not L.H.H.git(W,'diff','--name-only','--','src','test','Project.toml','.github'),'production source/test/env/CI unchanged')
for p in (W/'src').rglob('*.jl'):require(sha(p)==sha(Path('/home/jspitz/JSimplex.jl')/p.relative_to(W)),'actual master source equality '+str(p.relative_to(W)))
result=dict(accepted=True,checks=checks,runs=runs,pins_sha256=sha(D/'green-pins.json'),scope='new Task3 postexit audit, no Julia/oldscript rerun, no retroactive launch pins')
with (D/'postcheck.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(dict(accepted=True,checks=len(checks),runs=runs)))
