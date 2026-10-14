"""One-shot independent author postcheck; reads saved evidence, no auditor import."""
from pathlib import Path
import json,hashlib,tomllib,statistics,collections,subprocess,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-O'
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def require(v,m):
 if not v:raise ValueError(m)
pins=read(D/'pins.json');rev=read(D/'admission-review.json');agg=read(D/'aggregate.json');host=read(D/'host.json');checks={}
checks['all3924_launch_hashes_resolved']=len(pins['inventory'])==3924 and all(sha(p)==v['sha256'] and str(Path(p).resolve())==v['resolved'] for p,v in pins['inventory'].items())
checks['73_source_trees_complete']=len(pins['trees'])==73 and set(pins['inventory'])==set(pins['files'])|{str(p) for t in pins['trees'] for p in Path(t).rglob('*') if p.is_file()}
checks['admission27_and25_bindings']=rev['accepted'] is True and not rev['findings'] and len(rev['checks'])==27 and all(rev['checks'].values()) and rev['pins_sha256']==sha(D/'pins.json') and len(rev['sha256'])==25 and all(sha(p)==h for p,h in rev['sha256'].items())
raws=[tomllib.loads((D/f'run-{i}/raw.toml').read_text()) for i in (1,2,3)];groups=set(host['groups']);processes=[];all_samples=[]
for i,raw in enumerate(raws,1):
 out=D/f'run-{i}';audit=read(D/f'audit-{i}.json');proc=read(out/'process.json');inv=read(D/f'invocation-{i}.json');res=read(D/f'reservation-{i}.json')
 checks[f'run{i}_audit_and_actual_raw_bindings']=audit['all_passed'] is True and all(audit['checks'].values()) and all(sha(p)==h for p,h in audit['sha256'].items())
 checks[f'run{i}_process_cap_and_links']=proc['reason']=='exit0' and proc['returncode']==0 and proc['pins_unchanged'] is True and inv['returncode']==0 and inv['elapsed_seconds']<=120 and proc['elapsed_including_launch']<=114 and inv['reservation_sha256']==sha(D/f'reservation-{i}.json') and res['pins_sha256']==sha(D/'pins.json')==proc['pins_sha256'] and res['review_sha256']==sha(D/'admission-review.json') and res['host_sha256']==sha(D/f'prelaunch-{i}.json') and res['sequence_sha256']==sha(D/'sequence-reservation.json')
 checks[f'run{i}_exact_commands']=proc['command']==res['command']==read(D/'commands.json')[str(i)] and inv['command'][-len(proc['command']):]==proc['command'] and proc['cwd']==str(R)
 samples=[json.loads(x) for x in (out/'resources.jsonl').read_text().splitlines()];all_samples+=samples
 checks[f'run{i}_resource_samples']=all(s['available_kib']>=6*1024**2 and s['swap_used_kib']<=1024**2 for s in [*samples,proc['terminal_memory']]) and len(samples)>=2
 for who in ('runner','child'):groups.update([proc[who]['pgid'],proc[who]['sid']])
 processes.append(dict(index=i,runner=proc['runner'],child=proc['child'],invocation_seconds=inv['elapsed_seconds'],guard_seconds=proc['elapsed_including_launch'],sample_count=len(samples),terminal_memory=proc['terminal_memory'],load_seconds=raw['load_seconds'],qualification_seconds=raw['qualification_seconds'],first_calls_seconds=raw['first_calls_seconds'],cost_body_seconds=raw['cost_body_seconds']))
red=tomllib.loads((D/'run-1/red.toml').read_text())['records'];green=tomllib.loads((D/'run-1/green.toml').read_text())['records']
checks['RED8pass2exact_expected_fail']=len(red)==10 and collections.Counter(r['type'] for r in red)==dict(Pass=8,Fail=2) and all(r['type']=='Pass' or r['expression']=='(MAL_TRACE[]).scratch == 1' for r in red)
checks['GREEN3787pass']=len(green)==3787 and all(r['type']=='Pass' for r in green)
checks['all_input_output_preservation']=all(not r['errors'] and r['ambient_restored'] and r['trace_cleared'] and len(r['costs'])==76 and all(c['preservation_checks']==22 and all(f['result'] is c['expected'] for f in c['first']) and all(w['true_count']==128*int(c['expected']) for w in c['windows']) for c in r['costs']) for r in raws)
windows=[w for r in raws for c in r['costs'] for w in c['windows']];measured=[w for w in windows if w['phase']=='measured']
checks['4560windows_3192measured_1368warm']=len(windows)==4560 and len(measured)==3192 and len(windows)-len(measured)==1368
checks['all_measured_compile_recompile_zero']=all(w['compile_seconds']==0 and w['recompile_seconds']==0 for w in measured)
checks['456_first_calls']=sum(len(c['first']) for r in raws for c in r['costs'])==456
checks['runtime_module_paths_bound']=all(raw['loaded_paths'] and all(str(Path(p).resolve()) in {v['resolved'] for v in pins['inventory'].values()} for p in raw['loaded_paths'].values()) for raw in raws)
recomputed=[]
for ci in range(76):
 target=raws[0]['costs'][ci]['class']=='target';ratios=[];per=[]
 for raw in raws:
  c=raw['costs'][ci];pairs={k:{w['side']:w for w in c['windows'] if w['pair']==k} for k in range(4,11)}
  local=[v['candidate']['seconds']/v['reference']['seconds'] for v in pairs.values()];ratios+=local
  p={'ratio':statistics.median(local)}
  for side in ('reference','candidate'):
   for field in ('bytes','events'):p[side+'_'+field]=statistics.median(v[side][field] for v in pairs.values())
  p['pass']=(p['ratio']<1 and p['candidate_bytes']<p['reference_bytes'] and p['candidate_events']<p['reference_events']) if target else (p['ratio']<=1.02 and p['candidate_bytes']<=p['reference_bytes'] and p['candidate_events']<=p['reference_events'])
  per.append(p)
 median=statistics.median(ratios);wins=sum(v<1 for v in ratios)
 recomputed.append(dict(id=raws[0]['costs'][ci]['id'],target=target,median_ratio=median,min_ratio=min(ratios),max_ratio=max(ratios),mad=statistics.median(abs(x-median) for x in ratios),faster_pairs=wins,processes=per,accepted=all(p['pass'] for p in per) and (median<=.95 and wins>=18 if target else median<=1)))
checks['all76_aggregate_rows_independently_recomputed']=recomputed==agg['cases']
checks['recorded_NOT_ACCEPTED_26of76']=agg['qualification_pass'] is True and agg['accepted'] is False and sum(r['accepted'] for r in recomputed)==26 and all(sha(p)==h for p,h in agg['sha256'].items())
summary={}
for target in (True,False):
 rows=[r for r in recomputed if r['target']==target];causes=collections.Counter()
 for r in rows:
  if r['median_ratio']>(.95 if target else 1):causes['pooled_time']+=1
  if target and r['faster_pairs']<18:causes['faster_pairs']+=1
  if any(p['ratio']>=1 if target else p['ratio']>1.02 for p in r['processes']):causes['process_time']+=1
  for field in ('bytes','events'):
   if any(p['candidate_'+field]>=p['reference_'+field] if target else p['candidate_'+field]>p['reference_'+field] for p in r['processes']):causes[field]+=1
 summary['target' if target else 'control']=dict(cases=len(rows),accepted=sum(r['accepted'] for r in rows),pooled_ratio_range=[min(r['median_ratio'] for r in rows),max(r['median_ratio'] for r in rows)],overlapping_failure_causes=dict(causes),bytes_ratio_range=[min(p['candidate_bytes']/p['reference_bytes'] for r in rows for p in r['processes']),max(p['candidate_bytes']/p['reference_bytes'] for r in rows for p in r['processes'])],events_ratio_range=[min(p['candidate_events']/p['reference_events'] for r in rows for p in r['processes']),max(p['candidate_events']/p['reference_events'] for r in rows for p in r['processes'])])
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();f=s[s.rfind(')')+2:].split()
  if int(f[2]) in groups or int(f[3]) in groups or (p/'comm').read_text().strip().lower().startswith('julia'):matches.append(dict(pid=p.name,pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except FileNotFoundError:pass
checks['full146groups_ANDsessions_absent_noJulia']=len(groups)==146 and not matches
checks['protected_files_unchanged']=all(sha(p)==h for p,h in host['protected'].items())
checks['no_production_test_env_CI_changes']=not subprocess.check_output(['git','diff','HEAD','--','src','test','Project.toml','.github']).strip()
checks['three_processes_within360seconds']=sum(p['invocation_seconds'] for p in processes)<=360 and all(not(D/f'run-{i}').exists() for i in (4,5))
v=dict(all_passed=all(checks.values()),checks=checks,summary=summary,processes=processes,groups=sorted(groups),boot_id=boot,matches=matches,resource_samples=len(all_samples),minimum_available_kib=min(s['available_kib'] for s in all_samples),maximum_swap_kib=max(s['swap_used_kib'] for s in all_samples),gc_windows=sum(w['gc_seconds']>0 for w in windows),measured_gc_windows=sum(w['gc_seconds']>0 for w in measured),sha256={str(p):sha(p) for p in D.rglob('*') if p.is_file()},scope='Postexit supplemental verification, not a launch pin; no old/new auditor imported or rerun. Correctness passes, performance proposal NOT ACCEPTED.')
with(D/'postcheck.json').open('x') as f:json.dump(v,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=v['all_passed'],checks=len(checks),summary=summary,groups=len(groups),samples=v['resource_samples'],gc_windows=v['gc_windows'],measured_gc_windows=v['measured_gc_windows']),indent=2));require(v['all_passed'],'postcheck failed')
