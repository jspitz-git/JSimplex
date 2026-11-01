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
 if p.is_file() and sha(p)==expected:return p
 for m in [D/'task3-before-map.json',*sorted(D.glob('*before-map.json'))]:
  v=read(m)
  if n in v and v[n]['sha256']==expected and sha(v[n]['preserved'])==expected:return Path(v[n]['preserved'])
 for b in [D/'before-green-tests']:
  q=b/p.name
  if q.is_file() and sha(q)==expected:return q
 raise ValueError('missing exact preserved binding: '+n)
s=importlib.util.spec_from_file_location('task4defs',D/'run2.py');L=importlib.util.module_from_spec(s);s.loader.exec_module(L)
p=read(D/'green2-pins.json');require(L.G.pins_match(p),'all actual GREEN pins unchanged')
for n,v in read(D/'red-pins.json')['inventory'].items():require(sha(historical(n,v['sha256']))==v['sha256'],'original RED binding '+n)
for n,v in read(D/'before-bfrt-review/green-pins.json')['inventory'].items():require(sha(historical(n,v['sha256']))==v['sha256'],'original rejected GREEN binding '+n)
require(read(D/'before-bfrt-review/admission.json')['accepted'] is False,'original missing-BFRT coverage rejection preserved')
runs={}
for n,v in read(D/'green-pins.json')['inventory'].items():require(sha(historical(n,v['sha256']))==v['sha256'],'original parsed-failed GREEN binding '+n)
failed=read(D/'green-run/result.json');failed_proc=read(D/'green-run/guard/process.json');failed_log=(D/'green-run/guard/run.log').read_text()
require(failed['accepted'] is False and failed['exit']==failed_proc['returncode']==1 and failed['pins_unchanged'] and failed_proc['pins_unchanged'],'original GREEN loading failure preserved unchanged')
require('ParseError' in failed_log and 'export=false' in failed_log and 'Test Summary:' not in failed_log,'original reserved-keyword failure occurred before tests')
require(failed['elapsed_seconds']<1800 and read(D/'green-run/terminal-host.json')['no_julia'],'original failed GREEN closed within budget')
for stage,failures in [('red',6),('green2',0)]:
 out=D/(stage+'-run');r=read(out/'result.json');pr=read(out/'guard/process.json');cfg=read(D/(stage+'-contract.json'));log=(out/'guard/run.log').read_text()
 require(r['accepted'] is True and r['exit']==cfg['exit'] and pr['returncode']==cfg['exit'] and pr['reason']=='exit'+str(cfg['exit']),stage+' accepted expected exit')
 require(r['pins_unchanged'] and pr['pins_unchanged'] and r['elapsed_seconds']<=r['limit_seconds']==1800,stage+' pins/time bounds')
 require(pr['command']==cfg['command'],stage+' actual exact command')
 review=read(D/(stage+'-admission.json'));require(review['accepted'] is True and review['pins_sha256']==sha(D/(stage+'-pins.json')),stage+' exact independent admission')
 for n,h in review.get('bindings',{}).items():require(sha(historical(n,h))==h,stage+' independent binding '+n)
 for n,v in review.get('source_driver_runtime_path_hash_bindings',{}).items():require(sha(historical(n,v['sha256']))==v['sha256'],stage+' source admission binding '+n)
 samples=[json.loads(x) for x in (out/'guard/resources.jsonl').read_text().splitlines()]
 require(samples and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in samples),stage+' sampled memory bounds')
 require(pr['terminal_memory']['available_kib']>=6*1024**2 and pr['terminal_memory']['swap_used_kib']<=1024**2,stage+' terminal memory bounds')
 h=read(out/'terminal-host.json');require(h['no_julia'] is True and not h['conflicts'],stage+' full group/session closure')
 summary=dict(elapsed_seconds=r['elapsed_seconds'],samples=len(samples),min_available_kib=min(x['available_kib'] for x in samples),max_swap_kib=max(x['swap_used_kib'] for x in samples),child_maxrss_kib=pr['child_maxrss_kib'])
 if failures:require(f'0 passed, {failures} failed, 0 errored, 0 broken' in log,stage+' exact expected failure count')
 else:
  require('DUAL_ENGINE_TASK4_COMPLETED' in log and 'Test Failed' not in log and 'Error During Test' not in log,'GREEN ordinary Test completed')
  rows=re.findall(r'^(.+?)\s*\|\s+(\d+)\s+(\d+)\s+[\d.]+s\s*$',log,re.M)
  require(rows and all(int(a)==int(b) for _,a,b in rows),'ordinary summaries all passed')
  summary['testsets']={n.strip():int(a) for n,a,b in rows};summary['assertions']=sum(summary['testsets'].values())
  old=read(D.parent/'task3/postcheck.json')['runs']['green']['testsets']
  require(all(summary['testsets'].get(n)==a for n,a in old.items()) and sum(old.values())==555,'unchanged complete 555 assertion Task1/2/3 prefix')
 runs[stage]=summary
h=L.host();require(h['no_julia'] is True and not h['conflicts'],'fresh current refs/full groupsANDsessions/noJulia')
with (D/'postcheck-host.json').open('x') as f:json.dump(h,f,indent=2)
require(not L.H.H.git(W,'diff','--name-only','--','src','test','Project.toml','Manifest.toml','.github'),'production source/test/env/CI unchanged')
for p in (W/'src').rglob('*.jl'):require(sha(p)==sha(Path('/home/jspitz/JSimplex.jl')/p.relative_to(W)),'actual master source equality '+str(p.relative_to(W)))
result=dict(accepted=True,checks=checks,runs=runs,pins_sha256=sha(D/'green2-pins.json'),scope='new Task4 postexit audit, no Julia/oldscript rerun, postexit bindings not launch pins')
with (D/'postcheck.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(dict(accepted=True,checks=len(checks),runs=runs)))
