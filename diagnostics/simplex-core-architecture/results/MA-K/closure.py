"""One-shot documentation closure. No old script imports or numerical work."""
from pathlib import Path
import hashlib,json,subprocess,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-K'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],text=True).strip()
def require(ok,msg):
 if not ok:raise ValueError(msg)
host=read(D/'host.json'); review=read(D/'review-final.json' if (D/'review-final.json').exists() else D/'review.json')
checks={}
checks['independent_review_accepted']=review['accepted'] is True and not review.get('findings',review.get('unresolved_findings',['missing']))
checks['review_bindings']=all(sha(p)==v for p,v in review['sha256'].items())
source=read(D/'source-check.json'); remap=read(D/'review-fix.json').get('original_mapping',{}) if (D/'review-fix.json').exists() else {}
checks['initial_source_checks']=source['all_passed'] is True and all(source['checks'].values())
checks['source_bindings_preserved']=all(sha(remap.get(p,p))==v for p,v in source['sha256'].items())
checks['refs_unchanged']=git('rev-parse','HEAD')==host['refs']['head'] and git('rev-parse','master')==host['refs']['master'] and git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture')==host['refs']['remote']
checks['protected_unchanged']=all(sha(p)==v for p,v in host['protected'].items())
checks['production_unchanged']=not git('diff','HEAD','--','src','test','Project.toml','.github')
status=R/'diagnostics/simplex-core-architecture/STATUS.md';road=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
for target,before,needle in ((status,D/'STATUS.md.before-MA-K','## Previous MA-I decision (completed)'),(road,D/'roadmap.md.before-MA-K','### Previous MA-I decision (completed)')):
 checks['history_'+target.name]=target.read_text().split(needle,1)[1]==before.read_text().split(needle,1)[1]
mapping={str(status):str(D/'STATUS.md.before-MA-K'),str(road):str(D/'roadmap.md.before-MA-K')}
old=[]
for name in ('result-review.json','continuation-map.json','closure.json','publication.json'):
 for p,v in read(D.parent/'MA-J'/name)['sha256'].items():
  absolute=str(Path(p) if Path(p).is_absolute() else R/p)
  if absolute in mapping:old.append(sha(mapping[absolute])==v)
checks['old_current_bindings_preserved']=len(old)==8 and all(old)
checks['new_continuation_bindings']=all(sha(p)==v for p,v in read(D/'continuation-map.json')['sha256'].items())
groups=host['groups'];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();f=s[s.rfind(')')+2:].split()
  if int(f[2]) in groups or int(f[3]) in groups or (p/'comm').read_text().strip().lower().startswith('julia'):
   matches.append(dict(pid=p.name,pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except FileNotFoundError:pass
checks['full138groups_ANDsessions_noJulia']=len(groups)==138 and not matches
names=read(D/'publication-names.json')
extra=[status,road,R/'docs/superpowers/plans/2026-10-14-ma-presolve-selective-routing.md',R/'docs/superpowers/specs/2026-10-14-ma-presolve-selective-routing-design.md']
expected={str(p.relative_to(R)) for p in D.rglob('*') if p.is_file()}|{str(p.relative_to(R)) for p in extra}|{str((D/n).relative_to(R)) for n in ('closure.json','publication.json')}
checks['complete_exact_names']=set(names)==expected and len(names)==len(set(names))
checks['no_candidate_or_execution']=not any(p.suffix=='.jl' for p in D.rglob('*'))
checks['empty_index']=not git('diff','--cached','--name-only')
checks['authored_diff_clean']=subprocess.run(['git','diff','--check'],capture_output=True).returncode==0
record=dict(all_passed=all(checks.values()),checks=checks,sha256={str(R/n):sha(R/n) for n in names if Path(n).name not in ('closure.json','publication.json')},host=dict(time=time.time(),boot_id=boot,groups=groups,matches=matches),old_current_binding_count=len(old),scope='Plan/review closure only. No Julia, numerical experiment, candidate, production or environment changes.')
with (D/'closure.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps(checks,indent=2));require(record['all_passed'],'closure failed; do not stage/commit')
