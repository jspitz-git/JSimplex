from pathlib import Path
import hashlib,json,subprocess,time,math,tomllib,statistics
D=Path(__file__).resolve().parent; R=D.parents[3]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def save(p,v):
 with Path(p).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def req(v,msg):
 if not v:raise ValueError(msg)
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
def host(groups):
 boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   f=(p/'stat').read_text().rsplit(')',1)[1].split()
   if int(f[2]) in groups or int(f[3]) in groups or (p/'exe').resolve().name.startswith('julia'):
    matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'),boot_id=boot))
  except (FileNotFoundError,ProcessLookupError):pass
 return dict(time=time.time(),boot_id=boot,groups=sorted(set(groups)),matches=matches,head=git('rev-parse','HEAD'),master=git('rev-parse','master'))
def validate_review(review,pins_sha,required):
 req(review.get('accepted') is True and review.get('findings')==[], 'review not accepted')
 req(review.get('pins_sha256')==pins_sha,'review pins')
 bindings=review.get('sha256',{})
 req(all(bindings.get(str(p))==sha(p) for p in required),'review required bindings')
def metric_ok(w):
 return all(isinstance(w[k],(int,float)) and not isinstance(w[k],bool) and math.isfinite(w[k]) and w[k]>=0 for k in ('seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds'))
def stage_audit(index,pins):
 out=D/f'run-{index}';raw=tomllib.loads((out/'raw.toml').read_text());proc=rd(out/'process.json');inv=rd(D/f'invocation-{index}.json');side=('reference','candidate','candidate','reference')[index-1]
 checks={'identity':raw['index']==index and raw['side']==side,'raw66':len(raw['checks'])==66 and all(v is True for v in raw['checks'].values()) and raw['all_passed'] is True and raw['errors']==[], 'process':proc['reason']=='exit0' and proc['returncode']==0 and proc['pins_unchanged'] is True,'supervisor':inv['supervisor']['accepted'] is True and inv['supervisor']['elapsed_seconds']<=90,'commands':proc['command']==rd(D/'commands.json')[str(index)]==inv['command'],'pins':proc['pins_sha256']==sha(D/'launch-pins.json') and rd(out/'pins.json')==pins,'loaded_sources':all(p in pins['inventory'] for p in raw['loaded_paths'].values()),'all_pins':all(Path(p).resolve().as_posix()==v['resolved'] and sha(p)==v['sha256'] for p,v in pins['inventory'].items())}
 configs=tomllib.loads((D/'cases.toml').read_text())['cases'];ids=[f['id'] for f in configs];coreids=ids+['sparse-repeated','sparse-unique','dense-repeated','dense-unique']
 for id in coreids:
  v=tomllib.loads((out/f'core-{id}.toml').read_text());ws=v['windows']
  checks['core_'+id]=v['id']==id and len(ws)==20 and {(w['side'],w['rep']) for w in ws}=={(s,r) for s in ('reference','candidate') for r in range(1,11)} and all(w['calls']==4 and w['measured']==(w['rep']>3) and w['outputs_equal'] is True and w['input_preserved'] is True and metric_ok(w) and (not w['measured'] or (w['compile_seconds']==0 and w['recompile_seconds']==0)) for w in ws)
 for f in configs:
  v=tomllib.loads((out/("solve-"+f['id']+'.toml')).read_text());ws=v['windows']
  checks['solve_'+f['id']]=v['id']==f['id'] and v['side']==side and v['status']=='OPTIMAL' and math.isclose(v['objective'],f['expected'],rel_tol=1e-7,abs_tol=1e-7) and metric_ok(v['cold']) and len(ws)==10 and {w['rep'] for w in ws}==set(range(1,11)) and all(w['measured']==(w['rep']>3) and w['outputs_equal'] is True and w['input_preserved'] is True and metric_ok(w) and (not w['measured'] or (w['compile_seconds']==0 and w['recompile_seconds']==0)) for w in ws)
 checks['file_completeness']={p.name for p in out.iterdir()}=={'raw.toml','pins.json','process.json','current.json','run.log','resources.jsonl'}|{f'core-{i}.toml' for i in coreids}|{f'solve-{i}.toml' for i in ids}
 resources=[json.loads(l) for l in (out/'resources.jsonl').read_text().splitlines()];resources.append(proc['terminal_memory'])
 checks['resources']=all(s['available_kib']>=6*1024**2 and s['swap_used_kib']<=1024**2 for s in resources)
 return dict(all_passed=all(checks.values()),checks=checks,sha256={str(p):sha(p) for p in out.iterdir() if p.is_file()},min_available_kib=min(s['available_kib'] for s in resources),max_swap_kib=max(s['swap_used_kib'] for s in resources))
