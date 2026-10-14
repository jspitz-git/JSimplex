from pathlib import Path
import json,hashlib,subprocess,time,tomllib
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/MA-S'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(n):return json.loads((E/n).read_text())
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def save(n,v):
 with (E/n).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
pins=read('pins-reviewed.json');h=read('host.json');context=read('launch-context.json');process=read('run-1/process.json');inv=read('invocation-1.json');audit=read('audit-1.json');seal=read('numerical-review.json');prep=read('admission-review-final.json')
raw=tomllib.loads((E/'run-1/raw.toml').read_text());log=(E/'run-1/run.log').read_text();driver=(E/'driver.jl').read_text();rows=[json.loads(x) for x in (E/'run-1/resources.jsonl').read_text().splitlines()]
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();groups=set(context['groups'])
for role in ['runner','child']:
 groups.update([process[role]['pgid'],process[role]['sid']])
matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  f=(p/'stat').read_text().rsplit(')',1)[1].split();pgid,sid=int(f[2]),int(f[3]);exe=(p/'exe').resolve().name
  if pgid in groups or sid in groups or exe.startswith('julia'):matches.append(dict(pid=int(p.name),pgid=pgid,sid=sid,start_ticks=int(f[19]),boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,ProcessLookupError):pass
refs={k:git(*a) for k,a in {'head':['rev-parse','HEAD'],'master':['rev-parse','master'],'branch':['branch','--show-current'],'remote':['ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture']}.items()}
checks={
 'full4262pins':len(pins['inventory'])==4262 and all(sha(p)==v['sha256'] and str(Path(p).resolve())==v['resolved'] for p,v in pins['inventory'].items()),
 'exact_membership':set(read('required-paths-reviewed.json'))==set(pins['inventory'])==set(pins['files'])|{str(p) for root in pins['trees'] for p in Path(root).rglob('*') if p.is_file()},
 'seal39':seal['accepted'] is True and seal['findings']==[] and len(seal['sha256'])==39 and all(sha(p)==s for p,s in seal['sha256'].items()),
 'prep23':prep['accepted'] is True and len(prep['sha256'])==23 and all(sha(p)==s for p,s in prep['sha256'].items()),
 'audit6bindings':len(audit['sha256'])==6 and all(sha(p)==s for p,s in audit['sha256'].items()),
 'refs_unchanged':refs==context['refs'],
 'protected6':len(h['protected'])==6 and all(sha(p)==s for p,s in h['protected'].items()),
 'master514':len(h['master_identity'])==514 and all(sha(R/p)==s for p,s in h['master_identity'].items()),
 'tracked_clean':not git('diff','--name-only','HEAD'),
 'full160groups_ANDsessions_noJulia':len(groups)==160 and not matches,
 'boot_identity':boot==context['boot_id']==process['runner']['boot_id']==process['child']['boot_id'],
 'failure_preserved':process['returncode']==1 and process['reason']=='exit1' and inv['returncode']==1 and audit['all_passed'] is False,
 'stop_no_retry':all(not (E/n).exists() for n in ['run-2','run-3','reservation-2.json','reservation-3.json','invocation-2.json','invocation-3.json','aggregate.json']),
 'short_cap':0<process['elapsed_including_launch']<=inv['elapsed_seconds']<=120 and inv['cumulative_seconds']==inv['elapsed_seconds'],
 'resources':len(rows)==8 and all(x['available_kib']>=6*1024**2 and 0<=x['swap_used_kib']<=1024**2 for x in rows+[process['terminal_memory']]),
 'reference_smoke':raw['counts']['smoke']=={'pass':16,'fail':0,'error':0,'broken':0},
 'exact_expected_RED':raw['red']=={'pass':0,'fail':2,'error':0,'broken':0,'missing_route_only':True,'failure_expressions':['isdefined(P, :_dense_ma_eligible)','isdefined(P, :candidate_forward!) && isdefined(P, :candidate_transpose!)']},
 'incomplete_not_numerical_pass':raw['correctness']==[] and raw['costs']==[] and len(raw['errors'])==1 and '15 passed, 0 failed, 2 errored' in raw['errors'][0],
 'world_age_evidence':'running in world age 42871, while current world is 42908' in log and 'no method matching reset_route_counts!()' in log and 'no method matching _dense_ma_eligible' in log,
 'source_order':driver.index('function main()')<driver.index('Base.include(P,joinpath(RD,"candidate.jl"))')<driver.index('records[]=TST.qualification()')<driver.index('raw["costs"]=costs(index)'),
 'ambient_restored':raw['ambient_restored'] is True,
 'continuation6':len(read('execution-continuation-map.json')['old_bindings'])==6 and all(sha(x['preserved'])==x['sha256']==json.loads(Path(x['source']).read_text())['sha256'][x['path']] for x in read('execution-continuation-map.json')['old_bindings'])
}
# These are diagnostic/provenance checks, never a qualification PASS.
names=['execution-postcheck.py','execution-entry.py','execution-entry.json','execution-continuation-map.json','launch-context.json','numerical-review.md','numerical-review.json','sequence-execution.log','sequence-reservation.json','prelaunch-1.json','reservation-1.json','launcher-1.log','invocation-1.json','posthost-1.json','audit-1.json','run-1/process.json','run-1/raw.toml','run-1/pins.json','run-1/current.json','run-1/resources.jsonl','run-1/run.log','driver.jl','launcher-reviewed.py','audit_reviewed.py','guard.py','pins-reviewed.json','admission-review-final.json','../MA-R/tests.jl','../MA-R/candidate.jl','../MA-R/instrumented.jl']
result=dict(time=time.time(),checks=checks,all_passed=all(checks.values()),qualification_accepted=False,host=dict(boot_id=boot,groups=sorted(groups),matches=matches,refs=refs),resource_summary=dict(samples=len(rows),minimum_available_kib=min(x['available_kib'] for x in rows),maximum_swap_kib=max(x['swap_used_kib'] for x in rows),terminal=process['terminal_memory']),sha256={str((E/n).absolute()):sha(E/n) for n in names})
save('execution-postcheck.json',result)
print(json.dumps({'checks':checks,'all_passed':result['all_passed'],'resources':result['resource_summary']}))
if not result['all_passed']:raise SystemExit(1)
