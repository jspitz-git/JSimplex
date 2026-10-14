"""One-shot closure of failed MA-M diagnostic; no numerical qualification claim."""
from pathlib import Path
import hashlib,json,subprocess,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-M'
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def require(ok,msg):
 if not ok:raise ValueError(msg)
checks={};host=read(D/'host.json');review=read(D/'result-review.json')
checks['result_review_accepts_diagnostic']=review['accepted'] is True and not review['findings'] and all(review['checks'].values())
checks['review_bindings']=all(sha(p)==v for p,v in review['sha256'].items())
pins=read(D/'pins-reviewed.json')
checks['3814_launch_pins_unchanged']=len(pins['inventory'])==3814 and all(sha(p)==v['sha256'] and str(Path(p).resolve())==v['resolved'] for p,v in pins['inventory'].items())
checks['71_tree_membership']=len(pins['trees'])==71 and set(pins['inventory'])==set(pins['files'])|{str(p) for root in pins['trees'] for p in Path(root).rglob('*') if p.is_file()}
checks['admission_accepted_before_launch']=read(D/'admission-review-final.json')['accepted'] is True and read(D/'reservation-1.json')['review_sha256']==sha(D/'admission-review-final.json')
checks['failed_raw_audit_preserved']=read(D/'audit-1.json')['all_passed'] is False and read(D/'run-1/process.json')['returncode']==1
analysis=read(D/'failure-analysis.json');checks['15of16_false_preserved']=analysis['all_passed'] is False and len(analysis['checks'])==16 and sum(analysis['checks'].values())==15 and analysis['checks']['loaded_module_paths_pinned'] is False
supp=read(D/'loaded-path-supplement.json');checks['separate_limitation_supplement']=supp['all_passed'] is True and all(supp['checks'].values()) and all(sha(p)==v for p,v in supp['sha256'].items())
checks['no_retry_or_promotion']=all(not (D/n).exists() for n in ('run-2','run-3','reservation-2.json','reservation-3.json','aggregate.json','run-1/green.toml'))
checks['refs_unchanged']=git('rev-parse','HEAD')==host['refs']['head'] and git('rev-parse','master')==host['refs']['master'] and git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture')==host['refs']['remote']
checks['protected_unchanged']=all(sha(p)==v for p,v in host['protected'].items())
checks['production_unchanged']=not git('diff','HEAD','--','src','test','Project.toml','.github')
status=R/'diagnostics/simplex-core-architecture/STATUS.md';road=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
for target,before,needle in ((status,D/'STATUS.md.before-MA-M','## Previous MA-K plan (completed)'),(road,D/'roadmap.md.before-MA-M','### Previous MA-K plan (completed)')):
 checks['history_'+target.name]=target.read_text().split(needle,1)[1]==before.read_text().split(needle,1)[1]
mapping={str(status):str(D/'STATUS.md.before-MA-M'),str(road):str(D/'roadmap.md.before-MA-M')};old=[]
for name in ('closure-fix-review.json','continuation-map.json','closure.json','publication.json'):
 for p,v in read(D.parent/'MA-L'/name)['sha256'].items():
  absolute=str(Path(p) if Path(p).is_absolute() else R/p)
  if absolute in mapping:old.append(sha(mapping[absolute])==v)
checks['eight_old_current_bindings']=len(old)==8 and all(old)
checks['new_continuation_bindings']=all(sha(p)==v for p,v in read(D/'continuation-map.json')['sha256'].items())
groups=analysis['host']['groups'];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();f=s[s.rfind(')')+2:].split()
  if int(f[2]) in groups or int(f[3]) in groups or (p/'comm').read_text().strip().lower().startswith('julia'):
   matches.append(dict(pid=p.name,pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except FileNotFoundError:pass
checks['full140groups_ANDsessions_noJulia']=len(groups)==140 and not matches
names=read(D/'publication-names.json');extra=[status,road,R/'diagnostics/simplex-core-architecture/MA-PRESOLVE-SELECTIVE-QUALIFICATION.md',R/'docs/superpowers/plans/2026-10-14-ma-presolve-qualification-harness-repair.md']
expected={str(p.relative_to(R)) for p in D.rglob('*') if p.is_file()}|{str(p.relative_to(R)) for p in extra}|{str((D/n).relative_to(R)) for n in ('closure.json','publication.json')}
checks['complete_exact_names']=set(names)==expected and len(names)==len(set(names))
checks['empty_index']=not git('diff','--cached','--name-only')
checks['authored_diff_clean']=subprocess.run(['git','diff','--check'],capture_output=True).returncode==0
record=dict(all_passed=all(checks.values()),checks=checks,sha256={str(R/n):sha(R/n) for n in names if Path(n).name not in ('closure.json','publication.json')},host=dict(time=time.time(),boot_id=boot,groups=groups,matches=matches),old_current_binding_count=len(old),scope='PASS diagnostic closure only. Qualification NOT ACCEPTED; GREEN/cost unexecuted. Failed raw and analysis gates remain false.')
with (D/'closure.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps(checks,indent=2));require(record['all_passed'],'closure failed; no staging/commit')
