from pathlib import Path
import sys,json,re,hashlib,importlib.util
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;W=D.parents[2];checks=[]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(v,m):
 checks.append(dict(check=m,passed=bool(v)))
 if not v:raise ValueError(m)
s=importlib.util.spec_from_file_location('finalrun',D/'run-green-final.py');L=importlib.util.module_from_spec(s);s.loader.exec_module(L)
expected='a66c91ae73c1a1d6b0dedbab677108a9ef5bc119c220e747138c18c074e92118'
check(sha(D/'green-final-pins.json')==expected,'exact174 final launch manifest')
p=read(D/'green-final-pins.json');check(len(p['files'])==174 and set(p['files'])==set(p['inventory']) and L.G.pins_match(p),'174 actual launch source/path pins unchanged')
check(read(D/'green-admission.json')['accepted'] is True and read(D/'green-admission.json')['pins_sha256']==expected,'bound final source/numerical admission')
resources=[];peaks={};runs={}
for stage,exitcode in [('red',1),('ownership-red',1),('green',0)]:
 r=read(D/(stage+'-run/result.json'));proc=read(D/(stage+'-run/guard/process.json'));sup=read(D/(stage+'-run/supervision.json'))
 check(r['accepted'] is True and r['exit']==exitcode and r['elapsed_seconds']<=1800 and r['pins_unchanged'],stage+' accepted expected exit/deadline/pins')
 check(proc['returncode']==exitcode and proc['reason']=='exit'+str(exitcode) and proc['pins_unchanged'] and sup['accepted'] is True,stage+' raw process/supervision')
 a=read(D/(stage+'-admission.json'));manifest=D/(stage+'-pins.json') if stage!='green' else D/'green-final-pins.json'
 check(a['accepted'] is True and a['pins_sha256']==sha(manifest),stage+' exact admitted manifest binding')
 log=(D/(stage+'-run/guard/run.log')).read_text()
 if stage=='red':check('0 passed, 16 failed, 0 errored, 0 broken' in log,'original16failure RED preserved')
 elif stage=='ownership-red':check('0 passed, 1 failed, 0 errored, 0 broken' in log,'ownership1failure RED preserved')
 else:
  summaries=re.findall(r'^([^|\n]+)\|\s+(\d+)\s+(\d+)\s+[\d.]+s$',log,re.M)
  check(len(summaries)==5 and sum(int(x[1]) for x in summaries)==106 and all(x[1]==x[2] for x in summaries),'ordinary five Test summaries106/106')
  check('DUAL_ENGINE_TASK1_COMPLETED' in log and 'Test Failed' not in log and 'Error During Test' not in log,'GREEN marker/no Test failure or error')
  runs['testsets']={name.strip():int(passed) for name,passed,total in summaries}
 samples=[json.loads(x) for x in (D/(stage+'-run/guard/resources.jsonl')).read_text().splitlines()]
 check(samples and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in samples),stage+' every RAM/swap sample')
 resources.extend(samples);runs[stage]=r
 for x in samples:
  for line in x.get('child_memory',[]):
   name,value=line.split(':',1);peaks[name]=max(peaks.get(name,0),int(value.split()[0]))
# Earlier executed pins are historical; changed source/test/doc bindings resolve
# only through proven byte-identical before-fix copies, never a retroactive pass.
mapping=read(D/'ownership-before-map.json')
for name in ('red-pins.json','ownership-red-pins.json','green-pins.json'):
 old=read(D/name);mapped=0
 for path,info in old['inventory'].items():
  if sha(Path(path))==info['sha256']:continue
  match=mapping.get(path);check(match is not None and match['sha256']==info['sha256'] and sha(Path(match['preserved']))==info['sha256'],name+' preserved original binding '+path);mapped+=1
 runs[name]={'files':len(old['files']),'preserved_changed_paths':mapped}
h=L.host();check(h['no_julia'] is True and h['conflicts']==[] and len(h['checked_groups'])==788,'fresh all788 historical/new groups ANDsessions/noJulia')
with (D/'terminal-host.json').open('x') as f:json.dump(h,f,indent=2)
check(not L.H.H.git(W,'diff','--name-only','--','src','test','Project.toml','.github') and not L.H.H.git(W,'diff','--cached','--name-only'),'no src/test/env/CI or staged mutation')
check(L.H.H.git(Path('/home/jspitz/JSimplex.jl'),'rev-parse','HEAD')=='9940bdabe149e922afa60b5364227a7e7393bc75','master unchanged')
result=dict(accepted=True,checks=checks,runs=runs,resource_samples=len(resources),minimum_available_kib=min(x['available_kib'] for x in resources),maximum_swap_kib=max(x['swap_used_kib'] for x in resources),maximum_sampled_child_kib=peaks)
with (D/'postcheck.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(dict(accepted=True,checks=len(checks),tests=106,groups=len(h['checked_groups']),resources=len(resources),max_sampled=peaks)))
