from pathlib import Path
import hashlib,json,subprocess,time,tomllib
R=Path.cwd();X=R/'diagnostics/simplex-core-architecture/results/MA-X';D=X.with_name('MA-Y')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def save(p,o):
 with p.open('x') as f:json.dump(o,f,indent=2);f.write('\n')
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
h=rd(D/'host.json');pins=rd(X/'pins.json');groups=set(h['groups']);indices=[i for i in (1,2,3) if (X/f'invocation-{i}.json').exists()];processes=[];samples=[];raws=[];audits=[]
for i in indices:
 out=X/f'run-{i}';iv=rd(X/f'invocation-{i}.json');p=rd(out/'process.json') if (out/'process.json').exists() else {};a=rd(X/f'audit-{i}.json') if (X/f'audit-{i}.json').exists() else {};audits.append(a)
 for file in ('process.json','current.json'):
  if (out/file).exists():
   o=rd(out/file)
   for who in ('runner','child'):
    if who in o:groups.update([o[who]['pgid'],o[who]['sid']])
 ss=[json.loads(s) for s in (out/'resources.jsonl').read_text().splitlines()] if (out/'resources.jsonl').exists() else []
 if 'terminal_memory' in p:ss.append(p['terminal_memory'])
 samples+=ss
 try:raw=tomllib.loads((out/'raw.toml').read_text())
 except (FileNotFoundError,tomllib.TOMLDecodeError):raw={}
 raws.append(raw)
 processes.append(dict(index=i,invocation=iv,process=p,audit_pass=a.get('all_passed',False),audit_checks=a.get('checks',{}),audit_error=a.get('error'),cost_rows=a.get('process_costs',[]),raw_present=bool(raw),counts=raw.get('counts',{}),red=raw.get('red',{}),errors=raw.get('errors'),correctness_cases=len(raw.get('correctness',[])),cost_cases=len(raw.get('costs',[])),seconds={k:v for k,v in raw.items() if k.endswith('seconds')},setup_seconds=[dict(id=c['id'],seconds=c.get('bundle_snapshot_setup_seconds')) for c in raw.get('costs',[])],resource_samples=len(ss)))
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  f=(p/'stat').read_text().rsplit(')',1)[1].split()
  if int(f[2]) in groups or int(f[3]) in groups or (p/'exe').resolve().name.startswith('julia'):matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'),boot_id=boot))
 except (FileNotFoundError,ProcessLookupError):pass
refs={k:git(*a) for k,a in {'head':['rev-parse','HEAD'],'master':['rev-parse','master'],'branch':['branch','--show-current'],'remote':['ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture']}.items()}
mem={line.split(':')[0]:int(line.split()[1]) for line in Path('/proc/meminfo').read_text().splitlines()};memory=dict(available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree'])
aggregate=rd(X/'aggregate.json') if (X/'aggregate.json').exists() else None
accepted=len(indices)==3 and all(a.get('all_passed') is True for a in audits) and aggregate is not None and aggregate['accepted'] is True
checks=dict(refs=refs==h['refs'],host_noJulia=boot==h['boot_id'] and not matches and groups.issuperset(h['groups']),source514=all(sha(R/p)==v for p,v in h['master_identity'].items()),protected6=all(sha(p)==v for p,v in h['protected'].items()),pins4375=len(pins['inventory'])==4375 and all(sha(p)==v['sha256'] and str(Path(p).resolve())==v['resolved'] for p,v in pins['inventory'].items()),membership=set(pins['inventory'])==set(pins['files'])|{str(p) for root in pins['trees'] for p in Path(root).rglob('*') if p.is_file()},tracked_clean=not git('diff','--name-only','HEAD'),no_stage=not git('diff','--cached','--name-only'),one_bounded_sequence=bool(indices) and indices==list(range(1,len(indices)+1)) and all(p['invocation']['elapsed_seconds']<=90 and p['invocation']['cumulative_seconds']<=270 for p in processes),stop_after_failed_gate=all(audits[j].get('all_passed') is True for j in range(max(0,len(indices)-1))),no_later_reservation=all(not (X/f'reservation-{i}.json').exists() and not (X/f'run-{i}').exists() for i in (1,2,3) if i not in indices),memory=bool(samples) and all(s['available_kib']>=6*1024**2 and 0<=s['swap_used_kib']<=1024**2 for s in samples+[memory]))
for name in ('admission-review.json','numerical-review.json'):
 o=rd(X/name);checks[name]=o['accepted'] is True and o['findings']==[] and all(sha(p)==v for p,v in o['sha256'].items())
checks['audit_bindings']=bool(audits) and all('sha256' in a and all(sha(p)==v for p,v in a['sha256'].items()) for a in audits)
checks['aggregate_only_complete']=aggregate is None or len(indices)==3 and all(a.get('all_passed') is True for a in audits)
windows=[w for r in raws for c in r.get('costs',[]) for w in c['windows']];measured=[w for w in windows if w.get('phase')=='measured']
facts=dict(accepted=accepted,attempt_consumed=True,processes=processes,aggregate=aggregate,total_supervised_seconds=processes[-1]['invocation']['cumulative_seconds'] if processes else None,resource_min_available_kib=min((s['available_kib'] for s in samples),default=None),resource_max_swap_kib=max((s['swap_used_kib'] for s in samples),default=None),windows=len(windows),measured_windows=len(measured),warm_windows=len(windows)-len(measured),cost_calls=sum(w.get('calls',0) for w in windows),measured_gc_windows=sum(w['gc_seconds']>0 for w in measured),measured_compile_zero=bool(measured) and all(w['compile_seconds']==w['recompile_seconds']==0 for w in measured),failed_cases=[dict(process=p['index'],**r) for p in processes for r in p['cost_rows'] if not r['pass']])
save(D/'posthost.json',dict(time=time.time(),boot_id=boot,groups=sorted(groups),matches=matches,refs=refs,memory=memory))
save(D/'result-summary.json',facts)
paths=[D/'postcheck.py',D/'posthost.json',D/'result-summary.json',D/'launch.log',D/'launch-exit.json',X/'launch-context.json',X/'numerical-review.json',X/'numerical-review.md',X/'sequence-reservation.json']+[X/f'{n}-{i}.json' for i in indices for n in ('invocation','reservation','prelaunch','posthost','audit')]
if aggregate is not None:paths.append(X/'aggregate.json')
save(D/'postcheck.json',dict(all_passed=all(checks.values()),checks=checks,qualification_accepted=accepted,scope='Integrity/cleanup/stop verification is separate from numerical and cost acceptance; original failed gates preserved',sha256={str(p):sha(p) for p in paths}))
print(json.dumps(dict(checks=checks,accepted=accepted,processes=len(indices),seconds=facts['total_supervised_seconds'],failed_cases=facts['failed_cases'],counts=[p['counts'] for p in processes],windows=len(windows))))
if not all(checks.values()):raise SystemExit(1)
