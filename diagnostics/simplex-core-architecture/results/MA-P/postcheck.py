"""Post-exit independent recomputation; not a retroactive launch pin."""
from pathlib import Path
import json,tomllib,hashlib,statistics,subprocess,time,math
D=Path(__file__).resolve().parent;R=D.parents[3]
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True).strip()
host=read(D/'host.json');pins=read(D/'pins.json');agg=read(D/'aggregate.json');checks={};raws=[tomllib.loads((D/f'run-{i}/raw.toml').read_text()) for i in (1,2,3)]
checks['all_pins_current']=all(sha(p)==v['sha256'] and str(Path(p).resolve())==v['resolved'] for p,v in pins['inventory'].items())
checks['trees_complete']=set(pins['inventory'])==set(pins['files'])|{str(p) for t in pins['trees'] for p in Path(t).rglob('*') if p.is_file()}
checks['protected_unchanged']=all(sha(p)==h for p,h in host['protected'].items())
checks['master_and_HEAD_unchanged']=git('rev-parse','HEAD')==host['refs']['head'] and git('rev-parse','master')==host['refs']['master']
checks['remote_unchanged']=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture')==host['refs']['remote']
checks['source_test_CI_unchanged']=not git('diff','HEAD','--','src','test','Project.toml','.github')
checks['stage_audit_bindings']=all((s:=read(D/f'audit-{i}.json'))['all_passed'] and all(sha(p)==h for p,h in s['sha256'].items()) for i in (1,2,3))
checks['aggregate_bindings']=all(sha(p)==h for p,h in agg['sha256'].items())
checks['1133flags117records']=len(raws[0]['checks'])==117 and sum(len(c['flags']) for c in raws[0]['checks'])==1133 and all(v is True for c in raws[0]['checks'] for v in c['flags'].values())
checks['no_later_correctness']=all(r['checks']==[] for r in raws[1:])
ws=[w for r in raws for c in r['costs'] for w in c['windows']]
checks['window_budget']=len(ws)==3840 and sum(w['phase']=='measured' for w in ws)==2688 and agg['total_timed_calls']==len(ws)*16==61440
checks['compile_zero']=all(w['compile_seconds']==w['recompile_seconds']==0 for w in ws if w['phase']=='measured')
checks['all_GC_retained']=agg['gc_windows']==sum(w['gc_seconds']>0 for w in ws)
checks['independent_all64_statistics']=len(agg['cases'])==64
for ci,row in enumerate(agg['cases']):
 ratios=[];ps=[]
 for raw in raws:
  c=raw['costs'][ci];by={(w['pair'],w['side']):w for w in c['windows']};ref=[by[(p,'reference')] for p in range(4,11)];cand=[by[(p,'candidate')] for p in range(4,11)];rs=[b['seconds']/a['seconds'] for a,b in zip(ref,cand)];ratios+=rs
  pr=dict(ratio=statistics.median(rs),reference_bytes=statistics.median(w['bytes'] for w in ref),candidate_bytes=statistics.median(w['bytes'] for w in cand),reference_events=statistics.median(w['events'] for w in ref),candidate_events=statistics.median(w['events'] for w in cand));pr['pass']=pr['ratio']<1 and pr['candidate_bytes']<pr['reference_bytes'] and pr['candidate_events']<pr['reference_events'];ps.append(pr)
 med=statistics.median(ratios);wins=sum(r<1 for r in ratios);expected=dict(median_ratio=med,min_ratio=min(ratios),max_ratio=max(ratios),mad=statistics.median(abs(r-med) for r in ratios),faster_pairs=wins,processes=ps,accepted=all(p['pass'] for p in ps) and med<=.95 and wins>=18)
 checks['independent_all64_statistics'] &= all(row[k]==v for k,v in expected.items())
groups=set(host['groups']);identities=[];samples=[];durations=[]
for i in (1,2,3):
 p=read(D/f'run-{i}/process.json');durations.append(read(D/f'invocation-{i}.json')['elapsed_seconds'])
 for who in ('runner','child'):
  identities.append(p[who]);groups.update((p[who]['pgid'],p[who]['sid']))
 samples += [json.loads(s) for s in (D/f'run-{i}/resources.jsonl').read_text().splitlines()]+[p['terminal_memory']]
checks['inclusive_caps']=all(x<=120 for x in durations) and sum(durations)<=360
checks['resource_guards']=all(s['available_kib']>=6*1024**2 and s['swap_used_kib']<=1024**2 for s in samples)
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();f=s[s.rfind(')')+2:].split()
  if int(f[2]) in groups or int(f[3]) in groups or (p/'comm').read_text().strip().lower().startswith('julia'):matches.append(dict(pid=p.name,pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except FileNotFoundError:pass
checks['full_groups_ANDsessions_noJulia']=not matches
v=dict(all_passed=all(checks.values()),checks=checks,time=time.time(),boot_id=boot,groups=sorted(groups),matches=matches,identities=identities,durations=durations,min_available_kib=min(s['available_kib'] for s in samples),max_swap_kib=max(s['swap_used_kib'] for s in samples),resource_samples=len(samples),sha256={str(p):sha(p) for p in [D/'aggregate.json',D/'postcheck.py',*[D/f'audit-{i}.json' for i in (1,2,3)]]})
with (D/'postcheck.json').open('x') as f:json.dump(v,f,indent=2);f.write('\n')
print(json.dumps(checks,indent=2))
if not v['all_passed']:raise ValueError('postcheck failed')
