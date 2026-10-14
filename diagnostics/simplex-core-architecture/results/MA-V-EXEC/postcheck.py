from pathlib import Path
import hashlib,json,subprocess,time,tomllib,statistics
R=Path.cwd();V=R/'diagnostics/simplex-core-architecture/results/MA-V';E=V.with_name('MA-V-EXEC')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def save(p,o):
 with p.open('x') as f:json.dump(o,f,indent=2);f.write('\n')
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
h=rd(E/'host.json');pins=rd(V/'pins.json');groups=set(h['groups']);procs=[rd(V/f'run-{i}/process.json') for i in (1,2)];invs=[rd(V/f'invocation-{i}.json') for i in (1,2)];raws=[tomllib.loads((V/f'run-{i}/raw.toml').read_text()) for i in (1,2)];a=rd(V/'aggregate.json')
for p in procs:
 for who in ('runner','child'):
  groups.update([p[who]['pgid'],p[who]['sid']])
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  f=(p/'stat').read_text().rsplit(')',1)[1].split()
  if int(f[2]) in groups or int(f[3]) in groups or (p/'exe').resolve().name.startswith('julia'):
   matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'),boot_id=boot))
 except (FileNotFoundError,ProcessLookupError):pass
refs={k:git(*args) for k,args in {'head':['rev-parse','HEAD'],'master':['rev-parse','master'],'branch':['branch','--show-current'],'remote':['ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture']}.items()}
mem={line.split(':')[0]:int(line.split()[1]) for line in Path('/proc/meminfo').read_text().splitlines()};memory=dict(available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree'])
checks=dict(refs=refs==h['refs'],host170=len(groups)==170 and boot==h['boot_id'] and not matches,source514=len(h['master_identity'])==514 and all(sha(R/p)==s for p,s in h['master_identity'].items()),protected6=len(h['protected'])==6 and all(sha(p)==s for p,s in h['protected'].items()),all4342=len(pins['inventory'])==4342 and all(sha(p)==v['sha256'] and str(Path(p).resolve())==v['resolved'] for p,v in pins['inventory'].items()),tracked_clean=not git('diff','--name-only','HEAD'),no_stage=not git('diff','--cached','--name-only'),limits=all(v['elapsed_seconds']<=90 and v['returncode']==0 and v['supervisor']['accepted'] is True for v in invs) and invs[-1]['cumulative_seconds']<=180,aggregate=a['accepted'] is True and len(a['cases'])==12 and all(x['accepted'] is True for x in a['cases']),correctness=raws[0]['correctness']['counts']==dict(pass_=0) if False else raws[0]['correctness']['counts']=={'pass':25861,'fail':0,'error':0,'broken':0},no_extra_tests=raws[1]['correctness']=={} and raws[1]['red']==[],restored=all(r['ambient_restored'] is True and r['errors']==[] for r in raws))
for name in ('admission-review.json','numerical-review.json','aggregate.json','audit-1.json','audit-2.json'):
 o=rd(V/name);checks[name]=all(sha(p)==s for p,s in o['sha256'].items()) and (o.get('all_passed',o.get('accepted')) is True)
samples=[];processes=[]
for i,(p,iv,r) in enumerate(zip(procs,invs,raws),1):
 ss=[json.loads(x) for x in (V/f'run-{i}/resources.jsonl').read_text().splitlines()];samples+=ss+[p['terminal_memory']]
 processes.append(dict(index=i,resource_samples=len(ss),guard_seconds=p['elapsed_including_launch'],supervised_seconds=iv['elapsed_seconds'],seconds={k:x for k,x in r.items() if k.endswith('seconds')},journal_records=len(tomllib.loads((V/f'run-{i}/partial-windows.toml').read_text())['records']),runner=p['runner'],child=p['child']))
checks['memory']=all(s['available_kib']>=6*1024**2 and s['swap_used_kib']<=1024**2 for s in samples+[memory])
windows=[w for r in raws for name in ('red','micro','costs') for c in r[name] for w in c['windows'] if w['phase']=='measured']
checks['measured_compile_zero']=all(w['compile_seconds']==w['recompile_seconds']==0 for w in windows)
checks['micro_zero']=all(w['bytes']==w['events']==0 for r in raws for c in r['micro'] for w in c['windows'] if w['side']=='candidate' and w['phase']=='measured')
micro=[]
for ci,c in enumerate(raws[0]['micro']):
 row=dict(id=c['id'])
 for side in ('reference','candidate'):
  ws=[w for r in raws for w in r['micro'][ci]['windows'] if w['phase']=='measured' and w['side']==side]
  row[side]=dict(seconds_per_call=statistics.median(w['seconds']/256 for w in ws),bytes_per_window=statistics.median(w['bytes'] for w in ws),events_per_window=statistics.median(w['events'] for w in ws))
 micro.append(row)
facts=dict(processes=processes,total_supervised_seconds=invs[-1]['cumulative_seconds'],resource_min_available_kib=min(s['available_kib'] for s in samples),resource_max_swap_kib=max(s['swap_used_kib'] for s in samples),measured_windows=len(windows),measured_gc_windows=sum(w['gc_seconds']>0 for w in windows),correctness_counts=raws[0]['correctness']['counts'],no_scope_available=raws[0]['correctness']['no_scope_available'],predicates=len(raws[0]['correctness']['predicates']),transitions=len(raws[0]['correctness']['transitions']),whole_cases=len(raws[0]['correctness']['whole']),calls_per_arm=sum(c['calls_per_side'] for c in raws[0]['correctness']['whole']),old_RED=a['old_RED'],costs=a['cases'],micro=micro,code=[r['code'] for r in raws])
save(E/'posthost.json',dict(time=time.time(),boot_id=boot,groups=sorted(groups),matches=matches,refs=refs,memory=memory))
save(E/'result-summary.json',facts)
bound=[E/'postcheck.py',E/'posthost.json',E/'result-summary.json',E/'launch.log',V/'aggregate.json',V/'numerical-review.json',V/'numerical-review.md']+[V/f'{n}-{i}.json' for i in (1,2) for n in ('invocation','reservation','audit','posthost')]
save(E/'postcheck.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(p):sha(p) for p in bound}))
print(json.dumps(dict(checks=checks,process_seconds=[x['supervised_seconds'] for x in processes],old_RED=facts['old_RED'],micro=micro,costs=[dict(id=x['id'],target=x['target'],ratio=x['pooled_ratio'],R_us=x['reference_seconds_per_call']*1e6,C_us=x['candidate_seconds_per_call']*1e6,bytes=[(p['reference_bytes'],p['candidate_bytes']) for p in x['processes']],events=[(p['reference_events'],p['candidate_events']) for p in x['processes']]) for x in facts['costs']],measured_gc=facts['measured_gc_windows'])))
if not all(checks.values()):raise SystemExit(1)
