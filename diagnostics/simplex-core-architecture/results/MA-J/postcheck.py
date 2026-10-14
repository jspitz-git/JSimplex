"""New post-exit audit, no numerical execution or old auditor imports."""
from pathlib import Path
import hashlib,json,tomllib,statistics,subprocess,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-J';O=D/'run-1'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def save(n,v):
 with (D/n).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
p=read(O/'process.json');h=read(D/'host.json');pins=read(D/'pins.json');res=read(D/'reservation.json');inv=read(D/'invocation.json');checks={}
groups=set(h['groups']);groups.update(p[k][x] for k in ('runner','child') if k in p for x in ('pgid','sid'));matches=[];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
for proc in Path('/proc').glob('[0-9]*'):
 try:
  st=(proc/'stat').read_text();f=st[st.rfind(')')+2:].split()
  if int(f[2]) in groups or int(f[3]) in groups or (proc/'comm').read_text().strip().lower().startswith('julia'):matches.append(dict(pid=int(proc.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),boot_id=boot,command=(proc/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except FileNotFoundError:pass
checks['groups_ANDsessions_noJulia']=not matches
checks['pins_unchanged']=p['pins_unchanged'] is True and all(sha(k)==v['sha256'] and str(Path(k).resolve())==v['resolved'] for k,v in pins['inventory'].items())
checks['command_and_review_bound']=p['command']==res['command'] and p['pins_sha256']==res['pins_sha256']==sha(D/'pins.json') and res['review_sha256']==sha(D/'admission-review.json') and inv['reservation_sha256']==sha(D/'reservation.json') and sha(O/'pins.json')==sha(D/'pins.json')
checks['process_exit0']=p['reason']=='exit0' and p['returncode']==0 and inv['returncode']==0 and p['elapsed_including_launch']<=180
checks['production_unchanged']=not git('diff','HEAD','--','src','test','Project.toml','.github')
checks['protected_unchanged']=all(sha(k)==v for k,v in h['protected'].items())
checks['refs_unchanged']=git('rev-parse','HEAD')==h['refs']['head'] and git('rev-parse','master')==h['refs']['master'] and subprocess.check_output(['git','-C','/home/jspitz/JSimplex.jl','rev-parse','HEAD'],text=True).strip()==h['refs']['master']
samples=[json.loads(x) for x in (O/'resources.jsonl').read_text().splitlines()]+[p['terminal_memory']]
checks['resource_bounds']=bool(samples) and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in samples)
raw=tomllib.loads((O/'raw.toml').read_text()) if (O/'raw.toml').exists() else {}
checks['raw_complete']=not raw.get('errors',['absent']) and raw.get('ambient_restored') is True and len(raw.get('tests',[]))==1126 and len(raw.get('costs',[]))==48
checks['all_correct_preserved']=checks['raw_complete'] and all(x['pass'] and x['inputs_preserved'] for x in raw['tests']) and all(w['correct'] and w['inputs_preserved'] for x in raw['costs'] for w in x['windows'])
measurements=[];compile_bad=[];gc=[]
for case in raw.get('costs',[]):
 windows=case['windows'];measured=[w for w in windows if w['phase']=='measured'];pairs=[]
 for pair in range(4,11):
  r=next(w for w in measured if w['pair']==pair and w['side']=='reference');c=next(w for w in measured if w['pair']==pair and w['side']=='candidate');pairs.append(dict(pair=pair,ratio=c['seconds']/r['seconds'],reference=r,candidate=c))
 ratios=[x['ratio'] for x in pairs];median=statistics.median(ratios)
 sides={side:{key:statistics.median(w[key]/32 for w in measured if w['side']==side) for key in ('seconds','bytes','events')} for side in ('reference','candidate')}
 measurements.append(dict(scalar=case['scalar'],n=case['n'],style=case['style'],median_ratio=median,min_ratio=min(ratios),max_ratio=max(ratios),MAD=statistics.median(abs(x-median) for x in ratios),faster_pairs=sum(x<1 for x in ratios),per_call=sides,local_benefit=median<=.95 and sum(x<1 for x in ratios)>=6 and all(sides['candidate'][k]<sides['reference'][k] for k in ('bytes','events')),pairs=pairs))
 for w in measured:
  if w['compile_seconds']!=0 or w['recompile_seconds']!=0:compile_bad.append({k:case[k] for k in ('scalar','n','style')}|w)
  if w['gc_seconds']!=0:gc.append({k:case[k] for k in ('scalar','n','style')}|w)
checks['measured_compile_zero']=not compile_bad and checks['raw_complete']
save('postcheck.json',dict(all_passed=all(checks.values()),checks=checks,case_count=len(raw.get('tests',[])),cost_cases=len(measurements),measurements=measurements,compile_bad=compile_bad,gc_windows=gc,errors=raw.get('errors'),host=dict(time=time.time(),boot_id=boot,groups=sorted(groups),matches=matches),resources=dict(samples=len(samples),minimum_available_kib=min(x['available_kib'] for x in samples),maximum_swap_kib=max(x['swap_used_kib'] for x in samples),inclusive_seconds=p['elapsed_including_launch']),sha256={str(x):sha(x) for x in sorted(O.iterdir()) if x.is_file()},scope='component validation only; local benefit gates do not authorize promotion; postcheck is supplemental post-exit evidence'))
print(json.dumps(dict(checks=checks,cases=len(raw.get('tests',[])),cost_cases=len(measurements),benefit=sum(m['local_benefit'] for m in measurements),gc_windows=len(gc),errors=raw.get('errors')),indent=2))
if not all(checks.values()):raise SystemExit(1)
