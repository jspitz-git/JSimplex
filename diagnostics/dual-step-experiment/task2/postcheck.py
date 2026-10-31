from pathlib import Path
import json,hashlib,re,sys,importlib.util
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;W=D.parents[2];checks=[]
def read(p):return json.loads(p.read_text())
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def require(v,m):
 checks.append(dict(check=m,passed=bool(v)))
 if not v:raise ValueError(m)
def historical(path,expected):
 p=Path(path)
 if sha(p)==expected:return p
 before=read(D/'task1-before-map.json')
 if path in before and before[path]['sha256']==expected:return Path(before[path]['preserved'])
 for directory in ['before-coverage-review','before-canceled-row']:
  b=D/directory/p.name
  if b.is_file() and sha(b)==expected:return b
 raise ValueError('No exact historical mapping: '+path)
s=importlib.util.spec_from_file_location('task2definitions',D/'run.py');L=importlib.util.module_from_spec(s);s.loader.exec_module(L)
p=read(D/'green-pins.json');require(L.G.pins_match(p),'all actual GREEN launchpins unchanged')
a=read(D/'green-admission.json');require(a['accepted'] is True and a['pins_sha256']==sha(D/'green-pins.json'),'independent GREEN admission bound to exact manifest')
for name in ['red-pins.json','before-coverage-review/green-pins.json','before-canceled-row/green-pins.json']:
 old=read(D/name)
 for n,v in old['inventory'].items():
  q=historical(n,v['sha256']);require(sha(q)==v['sha256'],'historical exact binding '+name+': '+n)
require(read(D/'before-coverage-review/admission.json')['accepted'] is False,'initial rejected source review preserved')
runs={}
for stage in ['red','green']:
 out=D/(stage+'-run');r=read(out/'result.json');pr=read(out/'guard/process.json');cfg=read(D/(stage+'-contract.json'));log=(out/'guard/run.log').read_text()
 require(r['accepted'] is True and r['exit']==cfg['exit'] and pr['returncode']==cfg['exit'] and pr['reason']=='exit'+str(cfg['exit']),stage+' expected guarded termination')
 require(pr['pins_unchanged'] and r['pins_unchanged'] and r['elapsed_seconds']<=r['limit_seconds']==1800,stage+' unchanged pins/common time bound')
 require(pr['command']==cfg['command'],stage+' actual exact command')
 samples=[json.loads(line) for line in (out/'guard/resources.jsonl').read_text().splitlines()]
 require(samples and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in samples),stage+' sampled RAM/swap guards')
 require(pr['terminal_memory']['available_kib']>=6*1024**2 and pr['terminal_memory']['swap_used_kib']<=1024**2,stage+' terminal RAM/swap guards')
 h=read(out/'terminal-host.json');require(h['no_julia'] is True and not h['conflicts'],stage+' terminal groups ANDsessions/noJulia')
 summary=dict(elapsed_seconds=r['elapsed_seconds'],samples=len(samples),min_available_kib=min(x['available_kib'] for x in samples),max_swap_kib=max(x['swap_used_kib'] for x in samples),child_maxrss_kib=pr['child_maxrss_kib'])
 if stage=='red':require('0 passed, 6 failed, 0 errored, 0 broken' in log,'six expected missing-interface RED failures/zero errors')
 else:
  require('DUAL_ENGINE_TASK2_COMPLETED' in log and 'Test Failed' not in log and 'Error During Test' not in log,'ordinary GREEN completed without failures/errors')
  rows=re.findall(r'^(.+?)\s*\|\s+(\d+)\s+(\d+)\s+[\d.]+s\s*$',log,re.M)
  require(bool(rows) and all(int(a)==int(b) for _,a,b in rows),'ordinary Test per-testset pass totals')
  summary['testsets']={n.strip():int(a) for n,a,b in rows};summary['assertions']=sum(summary['testsets'].values())
 runs[stage]=summary
h=L.host();require(h['no_julia'] is True and not h['conflicts'],'fresh full groups ANDsessions/noJulia and branch/master refs')
with (D/'postcheck-host.json').open('x') as f:json.dump(h,f,indent=2)
require(not L.H.H.git(W,'diff','--name-only','--','src','test','Project.toml','.github'),'production src/test/environment/CI unchanged')
for p in (W/'src').rglob('*.jl'):require(sha(p)==sha(Path('/home/jspitz/JSimplex.jl')/p.relative_to(W)),'actual loaded production source comparison '+str(p.relative_to(W)))
result=dict(accepted=True,checks=checks,runs=runs,launch_manifest=sha(D/'green-pins.json'),scope='postexit checks, not retroactive launch pins; no rerun')
with (D/'postcheck.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(dict(accepted=True,checks=len(checks),runs=runs)))
