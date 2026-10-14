"""One-shot MA-L offline closure; no Julia or old script execution/import."""
from pathlib import Path
import hashlib,json,subprocess,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-L'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def require(ok,msg):
 if not ok:raise ValueError(msg)
checks={};host=read(D/'host.json');review=read(D/'review.json')
checks['review_accepted22']=review['accepted'] is True and not review['findings'] and len(review['checks'])==22 and all(review['checks'].values())
checks['review57_bindings']=len(review['sha256'])==57 and all(sha(p)==v for p,v in review['sha256'].items())
source=read(D/'source-check-final.json')
checks['source29_pass']=source['all_passed'] is True and len(source['checks'])==29 and all(source['checks'].values())
checks['source37_bindings']=len(source['sha256'])==37 and all(sha(p)==v for p,v in source['sha256'].items())
initial=read(D/'source-check.json')
checks['initial_false_preserved']=initial['all_passed'] is False and sum(initial['checks'].values())==28 and initial['checks']['all_route_expectations'] is False
for name in ('route-fix.json','input-bindings.json','author-check.json'):
 obj=read(D/name)
 checks[name+'_pass']=(len(obj['checks'])==4 and all(obj['checks'].values())) if name=='route-fix.json' else (obj['all_passed'] is True and all(obj['checks'].values()))
 checks[name+'_bindings']=all(sha(p)==v for p,v in obj.get('sha256',{}).items())
inputs=read(D/'qualification-inputs.json');counts=review['counts']
checks['prospective_counts']=inputs['green_expected_assertions']==counts['prospective_green_assertions']==3787 and inputs['correctness_fixtures']==counts['fixtures']==222 and inputs['cost_cases']==counts['cost_cases']==76 and inputs['red_expected_pass']==8 and inputs['red_expected_fail']==2
checks['refs_unchanged']=git('rev-parse','HEAD')==host['refs']['head'] and git('rev-parse','master')==host['refs']['master'] and git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture')==host['refs']['remote']
checks['protected_unchanged']=all(sha(p)==v for p,v in host['protected'].items())
checks['production_unchanged']=not git('diff','HEAD','--','src','test','Project.toml','.github')
status=R/'diagnostics/simplex-core-architecture/STATUS.md';road=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
for target,before,needle in ((status,D/'STATUS.md.before-MA-L','## Previous MA-J qualification (completed)'),(road,D/'roadmap.md.before-MA-L','### Previous MA-J qualification (completed)')):
 checks['history_'+target.name]=target.read_text().split(needle,1)[1]==before.read_text().split(needle,1)[1]
mapping={str(status):str(D/'STATUS.md.before-MA-L'),str(road):str(D/'roadmap.md.before-MA-L')};old=[]
for name in ('continuation-map.json','closure.json','publication.json'):
 for p,v in read(D.parent/'MA-K'/name)['sha256'].items():
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
checks['full138groups_ANDsessions_noJulia']=len(groups)==138 and not matches
names=read(D/'publication-names-final.json');extra=[status,road,R/'diagnostics/simplex-core-architecture/MA-PRESOLVE-SELECTIVE-PREPARATION.md']
expected={str(p.relative_to(R)) for p in D.rglob('*') if p.is_file()}|{str(p.relative_to(R)) for p in extra}|{str((D/n).relative_to(R)) for n in ('closure.json','publication.json')}
checks['complete_exact_names']=set(names)==expected and len(names)==len(set(names))
checks['no_launch_or_output']=not any(p.name.startswith(('launcher','driver','qualification-','run-')) and p.name!='qualification-inputs.json' for p in D.rglob('*'))
checks['empty_index']=not git('diff','--cached','--name-only')
checks['authored_diff_clean']=subprocess.run(['git','diff','--check'],capture_output=True).returncode==0
record=dict(all_passed=all(checks.values()),checks=checks,sha256={str(R/n):sha(R/n) for n in names if Path(n).name not in ('closure.json','publication.json')},host=dict(time=time.time(),boot_id=boot,groups=groups,matches=matches),old_current_binding_count=len(old),scope='Offline candidate/test preparation only. No Julia, runtime or performance acceptance. All assertions remain prospective.')
with (D/'closure.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps(checks,indent=2));require(record['all_passed'],'closure failed; do not stage/commit')
