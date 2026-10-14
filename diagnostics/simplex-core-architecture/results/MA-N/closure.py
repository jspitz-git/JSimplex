"""One-shot closure of offline MA-N preparation, never numerical execution."""
from pathlib import Path
import hashlib,json,subprocess,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-N'
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def require(ok,s):
 if not ok:raise ValueError(s)
checks={};host=read(D/'host.json');review=read(D/'review.json')
checks['offline_review_accepted']=review['accepted'] is True and not review['findings'] and all(review['checks'].values())
checks['review_bindings']=all(sha(p)==v for p,v in review['sha256'].items())
pins=read(D/'pins.json');prior=read(D.parent/'MA-M/pins-reviewed.json')
checks['all3884_readtime_pins']=len(pins['inventory'])==3884 and all(sha(p)==v['sha256'] and str(Path(p).resolve())==v['resolved'] for p,v in pins['inventory'].items())
checks['all3814_old_inputs_preserved']=all(pins['inventory'][p]==v for p,v in prior['inventory'].items())
checks['73_tree_membership']=len(pins['trees'])==73 and set(prior['trees'])<=set(pins['trees']) and set(pins['inventory'])==set(pins['files'])|{str(p) for root in pins['trees'] for p in Path(root).rglob('*') if p.is_file()}
repair=read(D/'repair-check.json');checks['42_offline_checks']=repair['all_passed'] is True and len(repair['checks'])==42 and all(repair['checks'].values()) and all(sha(p)==v for p,v in repair['sha256'].items())
inventory=read(D/'inventory-check.json');checks['4_inventory_checks']=inventory['all_passed'] is True and len(inventory['checks'])==4 and all(inventory['checks'].values()) and all(sha(p)==v for p,v in inventory['sha256'].items())
checks['old_failed_result_preserved']=read(D.parent/'MA-M/audit-1.json')['all_passed'] is False and read(D.parent/'MA-M/failure-analysis.json')['all_passed'] is False
checks['no_launch_or_output']=all(not (D/n).exists() for n in ('run-1','run-2','run-3','sequence-reservation.json','admission-review.json'))
checks['refs_unchanged']=git('rev-parse','HEAD')==host['refs']['head'] and git('rev-parse','master')==host['refs']['master'] and git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture')==host['refs']['remote']
checks['protected_unchanged']=all(sha(p)==v for p,v in host['protected'].items())
checks['production_unchanged']=not git('diff','HEAD','--','src','test','Project.toml','.github')
status=R/'diagnostics/simplex-core-architecture/STATUS.md';road=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
for target,before,needle in ((status,D/'STATUS.md.before-MA-N','## Previous MA-L preparation (completed)'),(road,D/'roadmap.md.before-MA-N','### Previous MA-L preparation (completed)')):
 checks['history_'+target.name]=target.read_text().split(needle,1)[1]==before.read_text().split(needle,1)[1]
mapping={str(status):str(D/'STATUS.md.before-MA-N'),str(road):str(D/'roadmap.md.before-MA-N')};old=[]
for name in ('continuation-map.json','closure.json','publication.json'):
 for p,v in read(D.parent/'MA-M'/name)['sha256'].items():
  absolute=str(Path(p) if Path(p).is_absolute() else R/p)
  if absolute in mapping:old.append(sha(mapping[absolute])==v)
checks['six_old_current_bindings']=len(old)==6 and all(old)
checks['new_continuation_bindings']=all(sha(p)==v for p,v in read(D/'continuation-map.json')['sha256'].items())
groups=host['groups'];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();f=s[s.rfind(')')+2:].split()
  if int(f[2]) in groups or int(f[3]) in groups or (p/'comm').read_text().strip().lower().startswith('julia'):
   matches.append(dict(pid=p.name,pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except FileNotFoundError:pass
checks['full140groups_ANDsessions_noJulia']=len(groups)==140 and not matches
names=read(D/'publication-names.json');extra=[status,road,R/'diagnostics/simplex-core-architecture/MA-PRESOLVE-HARNESS-REPAIR.md',R/'docs/superpowers/plans/2026-10-14-ma-presolve-repaired-qualification.md']
expected={str(p.relative_to(R)) for p in D.rglob('*') if p.is_file()}|{str(p.relative_to(R)) for p in extra}|{str((D/n).relative_to(R)) for n in ('closure.json','publication.json')}
checks['complete_exact_names']=set(names)==expected and len(names)==len(set(names))
checks['empty_index']=not git('diff','--cached','--name-only')
checks['authored_diff_clean']=subprocess.run(['git','diff','--check'],capture_output=True).returncode==0
v=dict(all_passed=all(checks.values()),checks=checks,sha256={str(R/n):sha(R/n) for n in names if Path(n).name not in ('closure.json','publication.json')},host=dict(time=time.time(),boot_id=boot,groups=groups,matches=matches),old_current_binding_count=len(old),scope='Offline repair preparation only. No Julia or executable launch admission. MA-M qualification remains NOT ACCEPTED.')
with (D/'closure.json').open('x') as f:json.dump(v,f,indent=2);f.write('\n')
print(json.dumps(checks,indent=2));require(v['all_passed'],'closure failed; no stage/commit')
