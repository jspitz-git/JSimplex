from pathlib import Path
import json,hashlib,subprocess,time,tomllib
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-S-2'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def bound(o):return all(sha(p)==s for p,s in o['sha256'].items())
pins=rd(D/'pins.json');context=rd(D/'launch-context.json');host=rd(D/'host.json');prep=rd(D/'admission-review.json');seal=rd(D/'numerical-review.json')
indices=[i for i in (1,2,3) if (D/f'invocation-{i}.json').exists()]
if not indices or indices!=list(range(1,len(indices)+1)):raise SystemExit('Non-prefix attempt sequence')
processes=[rd(D/f'run-{i}/process.json') for i in indices];invs=[rd(D/f'invocation-{i}.json') for i in indices];audits=[rd(D/f'audit-{i}.json') for i in indices]
groups=set(context['groups']);rows=[];raws=[]
for i,p in zip(indices,processes):
 for role in ('runner','child'):groups.update([p[role]['pgid'],p[role]['sid']])
 samples=[json.loads(x) for x in (D/f'run-{i}/resources.jsonl').read_text().splitlines()]
 rows.append(samples+[p['terminal_memory']]);raws.append(tomllib.loads((D/f'run-{i}/raw.toml').read_text()))
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  f=(p/'stat').read_text().rsplit(')',1)[1].split();exe=(p/'exe').resolve().name
  if int(f[2]) in groups or int(f[3]) in groups or exe.startswith('julia'):matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,ProcessLookupError):pass
refs={k:git(*a) for k,a in {'head':['rev-parse','HEAD'],'master':['rev-parse','master'],'branch':['branch','--show-current'],'remote':['ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture']}.items()}
complete=len(indices)==3 and all(a['all_passed'] is True for a in audits)
agg=rd(D/'aggregate.json') if (D/'aggregate.json').exists() else None
checks={'pins4304':len(pins['inventory'])==4304 and all(sha(p)==v['sha256'] and str(Path(p).resolve())==v['resolved'] for p,v in pins['inventory'].items()),'membership':set(rd(D/'required-paths.json'))==set(pins['inventory'])==set(pins['files'])|{str(p) for root in pins['trees'] for p in Path(root).rglob('*') if p.is_file()},'prep_bindings':prep['accepted'] is True and prep['findings']==[] and bound(prep),'seal_bindings':seal['accepted'] is True and seal['findings']==[] and bound(seal),'audit_bindings':all(bound(a) for a in audits),'refs':refs==context['refs'],'source514':len(host['master_identity'])==514 and all(sha(R/p)==s for p,s in host['master_identity'].items()),'protected6':len(host['protected'])==6 and all(sha(p)==s for p,s in host['protected'].items()),'tracked_clean':not git('diff','--name-only','HEAD'),'full_groups_ANDsessions_noJulia':set(context['groups'])<=groups and not matches,'boot':boot==context['boot_id'] and all(p[r]['boot_id']==boot for p in processes for r in ('runner','child')),'prefix_stop':all(a['all_passed'] is True for a in audits[:-1]) and all(not (D/n).exists() for i in range(len(indices)+1,4) for n in [f'run-{i}',f'invocation-{i}.json',f'reservation-{i}.json']),'caps':all(0<p['elapsed_including_launch']<=v['elapsed_seconds']<=120 for p,v in zip(processes,invs)) and sum(v['elapsed_seconds'] for v in invs)<=360,'resources':all(len(ss)>=2 and all(s['available_kib']>=6*1024**2 and 0<=s['swap_used_kib']<=1024**2 for s in ss) for ss in rows),'aggregate_scope':(agg is not None and agg['qualification_pass'] is True and bound(agg)) if complete else agg is None,'recorded_outcome':all((p['returncode']==0 and v['returncode']==0) or a['all_passed'] is False for p,v,a in zip(processes,invs,audits)),'ambient':all(r['ambient_restored'] is True for r in raws),'old_failure_preserved':rd(D.with_name('MA-S')/'audit-1.json')['all_passed'] is False and not (D.with_name('MA-S')/'run-2').exists()}
summary=[]
for i,p,v,a,raw,ss in zip(indices,processes,invs,audits,raws,rows):
 ws=[w for c in raw['costs'] for w in c['windows']]
 summary.append(dict(index=i,returncode=p['returncode'],reason=p['reason'],elapsed_seconds=v['elapsed_seconds'],guard_seconds=p['elapsed_including_launch'],counts=raw['counts'],red=raw['red'],errors=raw['errors'],correctness_cases=len(raw['correctness']),cost_cases=len(raw['costs']),windows=len(ws),measured_windows=sum(w['phase']=='measured' for w in ws),gc_windows=sum(w['gc_seconds']>0 for w in ws),nonzero_measured_compile=sum((w['compile_seconds']!=0 or w['recompile_seconds']!=0) for w in ws if w['phase']=='measured'),audit_pass=a['all_passed'],false_gates=[k for k,x in a['checks'].items() if x is False],sample_count=len(ss)-1,min_available_kib=min(s['available_kib'] for s in ss),max_swap_kib=max(s['swap_used_kib'] for s in ss),load_seconds=raw['load_seconds'],definition_seconds=raw.get('candidate_definition_seconds'),runner=p['runner'],child=p['child']))
paths=[D/n for n in ['execution-preflight.py','execution-preflight.json','execution-postcheck.py','execution-ledger.md','launch-context.json','numerical-review.json','numerical-review.md','admission-review.json','sequence-reservation.json','sequence-execution.log','pins.json','required-paths.json','launcher.py','audit.py','guard.py','commands.json']]
for i in indices:
 paths.extend(D/n for n in [f'prelaunch-{i}.json',f'reservation-{i}.json',f'launcher-{i}.log',f'invocation-{i}.json',f'posthost-{i}.json',f'audit-{i}.json']);paths.extend(p for p in (D/f'run-{i}').rglob('*') if p.is_file())
if agg is not None:paths.append(D/'aggregate.json')
o=dict(time=time.time(),all_passed=all(checks.values()),checks=checks,qualification_complete=complete,qualification_accepted=bool(complete and agg['accepted']),host=dict(boot_id=boot,groups=sorted(groups),matches=matches,refs=refs),stages=summary,sha256={str(p):sha(p) for p in paths})
with (D/'execution-postcheck.json').open('x') as f:json.dump(o,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=o['all_passed'],checks=checks,qualification_complete=complete,qualification_accepted=o['qualification_accepted'],stages=summary,bindings=len(paths))))
if not o['all_passed']:raise SystemExit(1)
