from pathlib import Path
import json,tomllib,hashlib,math
D=Path(__file__).resolve().parent

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def finite(x):return type(x) in (int,float) and math.isfinite(x) and x>=0

def stage(index):
 out=D/f'run-{index}';checks={};error=None
 try:
  inv=read(D/f'invocation-{index}.json');res=read(D/f'reservation-{index}.json');proc=read(out/'process.json');pins=read(D/'pins.json');cmd=read(D/'commands.json')[str(index)]
  checks['process']=proc['reason']=='exit0' and proc['returncode']==0 and proc['pins_unchanged'] is True and inv['returncode']==0
  checks['command']=proc['command']==cmd and proc['cwd']==str(D.parents[3]) and res['command']==cmd and inv['command'][-len(cmd):]==cmd
  checks['links']=inv['reservation_sha256']==sha(D/f'reservation-{index}.json') and res['pins_sha256']==sha(D/'pins.json')==proc['pins_sha256'] and res['review_sha256']==sha(D/'admission-review.json') and res['host_sha256']==sha(D/f'prelaunch-{index}.json')
  checks['hard_cap']=finite(inv['elapsed_seconds']) and inv['elapsed_seconds']<=120 and proc['elapsed_including_launch']<=114
  checks['pins']=read(out/'pins.json')==pins and all(sha(p)==v['sha256'] and str(Path(p).resolve())==v['resolved'] for p,v in pins['inventory'].items())
  samples=[json.loads(s) for s in (out/'resources.jsonl').read_text().splitlines()]+[proc['terminal_memory']]
  checks['memory']=len(samples)>=2 and all(s['available_kib']>=6*1024**2 and s['swap_used_kib']<=1024**2 for s in samples)
  raw=tomllib.loads((out/'raw.toml').read_text());checks['header']=raw['index']==index and raw['errors']==[] and raw['ambient_restored'] is True
  checks['loaded_paths_pinned']=bool(raw['loaded_paths']) and all(str(Path(p).resolve()) in {v['resolved'] for v in pins['inventory'].values()} for p in raw['loaded_paths'].values())
  cases=[f for f in tomllib.loads((D/'cases.toml').read_text())['cases'] if index in f['stages']]
  checks.update(cases=True,windows=True,compile_zero=True,profiles=True)
  for f in cases:
   c=tomllib.loads((out/(f['id']+'.toml')).read_text());ws=c['windows'];pr=c['profile'];st=tomllib.loads((out/(f['id']+'-stacks.toml')).read_text())
   checks['cases'] &= c['id']==f['id'] and c['status']=='OPTIMAL' and len(c['checks'])==8 and all(x is True for x in c['checks']) and len(c['cold'])==2 and c['rows']>0 and c['columns']>0 and c['nnz']>0
   expected=[(r,m) for r in (1,2,3) for m in (('plain','diagnosed') if r%2 else ('diagnosed','plain'))]
   checks['windows'] &= len(ws)==6 and [(w['rep'],w['mode']) for w in ws]==expected and all(w['endpoint_equal'] is True and w['input_preserved'] is True and all(finite(w[k]) for k in ('seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds')) for w in ws)
   checks['compile_zero'] &= all(w['compile_seconds']==w['recompile_seconds']==0 for w in ws) and pr['compile_seconds']==pr['recompile_seconds']==0
   checks['profiles'] &= pr['calls']==(64 if index==1 else 8) and pr['buffer_full'] is False and pr['endpoints_equal'] is True and pr['input_preserved'] is True and len(st['data'])>0 and all(ip=='0' or ip in st['frames'] for ip in st['data']) and st['data'][-1]=='0'
 except Exception as e:error=repr(e);checks['complete_schema']=False
 return dict(all_passed=bool(checks) and all(checks.values()),checks=checks,error=error,sha256={str(p):sha(p) for p in out.rglob('*') if p.is_file()})
