"""MA-J documentation closure; no numerical execution and no old control imports."""
from pathlib import Path
import hashlib,json,subprocess,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-J';B=R/'diagnostics/simplex-core-architecture';report=B/'MA-PRESOLVE-EQUALITY-QUALIFICATION.md'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def require(x,msg):
 if not x:raise ValueError(msg)
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
checks={};post=read(D/'postcheck-2.json');first=read(D/'postcheck.json');review=read(D/'result-review.json');pins=read(D/'pins-2.json');host=read(D/'host.json')
checks['result_review_accepted']=review['accepted'] is True and review['unresolved_findings']==[]
checks['review_bindings']=all(sha(p)==v for p,v in review['sha256'].items())
checks['postcheck11']=post['all_passed'] is True and len(post['checks'])==11 and all(post['checks'].values())
checks['raw_bindings']=all(sha(p)==v for x in (post,first) for p,v in x['sha256'].items())
checks['first_failure_preserved']=first['all_passed'] is False and first['case_count']==280 and first['cost_cases']==0 and read(D/'run-1/process.json')['returncode']==1
checks['pins217']=len(pins['inventory'])==217 and all(sha(p)==v['sha256'] and str(Path(p).resolve())==v['resolved'] for p,v in pins['inventory'].items())
checks['one_record_type_fix']=(D/'driver-2.jl').read_text().replace('return Dict{String,Any}("seconds"=>t.time','return Dict("seconds"=>t.time')==(D/'driver.jl').read_text()
checks['references_unchanged']=git('rev-parse','HEAD')==host['refs']['head'] and git('rev-parse','master')==host['refs']['master'] and git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture')==host['refs']['remote']
checks['protected_unchanged']=all(sha(p)==v for p,v in host['protected'].items())
checks['production_unchanged']=not git('diff','HEAD','--','src','test','Project.toml','.github')
checks['no_promotion_claim']='not accepted as an unconditional replacement' in report.read_text() and 'unconditional deployment would impose avoidable work' in report.read_text()
# Validate old current continuation binding hashes by exact before copies only.
status=B/'STATUS.md';road=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md';mapping={str(status):D/'STATUS.md.before-MA-J',str(road):D/'roadmap.md.before-MA-J'}
oldchecks=[]
for name in ('closure.json','publication.json','closure-review-final.json','continuation-fix.json'):
 x=read(B/'results/MA-I'/name)
 for p,v in x.get('sha256',{}).items():
  absolute=str(Path(p) if Path(p).is_absolute() else R/p)
  if absolute in mapping:oldchecks.append(sha(mapping[absolute])==v)
checks['old_current_bindings_preserved']=len(oldchecks)>=7 and all(oldchecks)
needle='### Previous S4-AD integration (completed)'
checks['historical_roadmap_exact']=road.read_text().split(needle,1)[1]==(D/'roadmap.md.before-MA-J').read_text().split(needle,1)[1]
checks['continuation_map']=all(sha(p)==v for p,v in read(D/'continuation-map.json')['sha256'].items())
# Fresh full group/session scan at closure.
groups=post['host']['groups'];matches=[];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();f=s[s.rfind(')')+2:].split()
  if int(f[2]) in groups or int(f[3]) in groups or (p/'comm').read_text().strip().lower().startswith('julia'):matches.append(dict(pid=p.name,pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except FileNotFoundError:pass
checks['groups138_ANDsessions_noJulia']=len(groups)==138 and not matches
names=read(D/'publication-names.json');expected={str(p.relative_to(R)) for p in D.rglob('*') if p.is_file() and '__pycache__' not in str(p)}|{str(p.relative_to(R)) for p in (status,road,report)}|{str((D/n).relative_to(R)) for n in ('closure.json','publication.json')}
checks['complete_exact_names']=set(names)==expected and len(names)==len(set(names))
checks['empty_index']=not git('diff','--cached','--name-only')
paths=[R/n for n in names if Path(n).name not in ('closure.json','publication.json')]
record=dict(all_passed=all(checks.values()),checks=checks,sha256={str(p):sha(p) for p in paths},host=dict(time=time.time(),boot_id=boot,groups=groups,matches=matches),old_current_binding_count=len(oldchecks),scope='Diagnostic closure only; full plan remains open; frozen failed records preserved')
with (D/'closure.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps(checks,indent=2));require(record['all_passed'],'closure failed; do not stage/commit')
