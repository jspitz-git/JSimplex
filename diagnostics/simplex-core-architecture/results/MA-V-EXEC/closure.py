from pathlib import Path
import json,hashlib,subprocess,time
R=Path.cwd();V=R/'diagnostics/simplex-core-architecture/results/MA-V';E=V.with_name('MA-V-EXEC')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def bound(o):return all(sha(p)==h for p,h in o['sha256'].items())
maps=rd(E/'continuation-map.json')['old_bindings'];h=rd(E/'posthost.json');entry=rd(E/'host.json');pins=rd(V/'pins.json');rev=rd(E/'result-review.json')
def oldbound(p):
 allmaps=maps+rd(E/'reviewer-continuation-map.json')['old_bindings']
 mm={m['path']:m['preserved'] for m in allmaps if m['source']==str(p)}
 return all(sha(mm.get(n,n))==v for n,v in rd(p)['sha256'].items())
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  st=(p/'stat').read_text().rsplit(')',1)[1].split()
  if int(st[2]) in h['groups'] or int(st[3]) in h['groups'] or (p/'exe').resolve().name.startswith('julia'):
   matches.append(dict(pid=int(p.name),pgid=int(st[2]),sid=int(st[3]),start_ticks=int(st[19]),boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,ProcessLookupError):pass
pm={m['path']:m['preserved'] for m in maps if m['source']==str(V/'pins.json')}
checks=dict(result_review=rev['accepted'] is True and rev['findings']==[] and rev['all_computed_checks_passed'] is True and len(rev['computed_checks'])==42 and all(v is True for v in rev['computed_checks'].values()) and len(rev['finalization_computed_checks'])==7 and all(v is True for v in rev['finalization_computed_checks'].values()) and bound(rev),postcheck=rd(E/'postcheck.json')['all_passed'] is True and bound(rd(E/'postcheck.json')),entry=rd(E/'entry.json')['all_passed'] is True and bound(rd(E/'entry.json')),numerical_seal=rd(V/'numerical-review.json')['accepted'] is True and bound(rd(V/'numerical-review.json')),aggregate=rd(V/'aggregate.json')['accepted'] is True and bound(rd(V/'aggregate.json')),stages=all(rd(V/f'audit-{i}.json')['all_passed'] is True and bound(rd(V/f'audit-{i}.json')) for i in (1,2)),eight_maps=len(maps)==8 and all(sha(m['preserved'])==m['sha256']==(rd(m['source'])['inventory'][m['path']]['sha256'] if m['kind']=='inventory' else rd(m['source'])['sha256'][m['path']]) for m in maps),prior_preparation=all(oldbound(V/n) for n in ('admission-review.json','closure.json','publication.json')),pins4342=len(pins['inventory'])==4342 and all(sha(pm.get(p,p))==v['sha256'] for p,v in pins['inventory'].items()),source514=len(entry['master_identity'])==514 and all(sha(R/p)==v for p,v in entry['master_identity'].items()),protected6=len(entry['protected'])==6 and all(sha(p)==v for p,v in entry['protected'].items()),host170=len(h['groups'])==170 and boot==h['boot_id'] and not matches,refs=git('rev-parse','HEAD')==h['refs']['head'] and git('rev-parse','master')==h['refs']['master'] and git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture')==h['refs']['remote'],tracked_scope=set(git('diff','--name-only','HEAD').splitlines())=={'diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'},no_stage=not git('diff','--cached','--name-only'),old_rejection=rd(V.with_name('MA-S-2')/'aggregate.json')['accepted'] is False,tracked_whitespace=subprocess.run(['git','diff','--check'],capture_output=True).returncode==0)
checks['reviewer42']=rd(E/'reviewer-check.json')['all_computed_checks_passed'] is True and len(rd(E/'reviewer-check.json')['computed_checks'])==42 and oldbound(E/'reviewer-check.json')
checks['reviewer_maps']=len(rd(E/'reviewer-continuation-map.json')['old_bindings'])==2 and all(sha(m['preserved'])==m['sha256']==rd(m['source'])['sha256'][m['path']] for m in rd(E/'reviewer-continuation-map.json')['old_bindings'])
checks['report_amendment']=rd(E/'report-amendment.json')['all_passed'] is True and bound(rd(E/'report-amendment.json'))
checks['continuation']=all(rd(E/'continuation.json')['checks'].values()) and bound(rd(E/'continuation.json'))
checks['run_pin_copies']=all(sha(V/f'run-{i}/pins.json')==sha(V/'pins.json') for i in (1,2)) # byte-identical inventories inherit the canonical eight-map reconciliation
names=rd(E/'publication-names.json');paths=[R/n for n in names if n not in {str((E/'closure.json').relative_to(R)),str((E/'publication.json').relative_to(R))}]
o=dict(all_passed=all(checks.values()),checks=checks,local_guard_accepted=True,complete_candidate_accepted=False,host=dict(time=time.time(),boot_id=boot,groups=h['groups'],matches=matches),sha256={str(p):sha(p) for p in paths})
with (E/'closure.json').open('x') as f:json.dump(o,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=o['all_passed'],checks=checks,bindings=len(paths))))
if not o['all_passed']:raise SystemExit(1)
