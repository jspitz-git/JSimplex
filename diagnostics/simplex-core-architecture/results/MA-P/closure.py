"""One-shot closure of the bounded RHS diagnostic, not production admission."""
from pathlib import Path
import json,hashlib,subprocess,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-P';O=D.parent/'MA-O'
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def bound(x):return all(sha(p)==h for p,h in x['sha256'].items())
review=read(D/'result-review.json');post=read(D/'postcheck.json');pins=read(D/'pins.json');host=read(D/'host.json');agg=read(D/'aggregate.json');admission=read(D/'admission-review.json');names=read(D/'publication-names-final.json');checks={}
checks['independent_result_accepted']=review['accepted'] is True and not review['findings'] and all(review['checks'].values())
checks['result_review_bindings']=bound(review)
checks['postcheck17PASS_bindings']=post['all_passed'] is True and len(post['checks'])==17 and all(post['checks'].values()) and bound(post)
checks['launch4000hashes_current']=len(pins['inventory'])==4000 and all(sha(p)==v['sha256'] and str(Path(p).resolve())==v['resolved'] for p,v in pins['inventory'].items())
checks['73source_trees_complete']=len(pins['trees'])==73 and set(pins['inventory'])==set(pins['files'])|{str(p) for t in pins['trees'] for p in Path(t).rglob('*') if p.is_file()}
checks['admission_bindings']=admission['accepted'] is True and not admission['findings'] and admission['pins_sha256']==sha(D/'pins.json') and bound(admission)
checks['all3stageauditsPASS_currentraw']=all((v:=read(D/f'audit-{i}.json'))['all_passed'] is True and len(v['checks'])==14 and all(v['checks'].values()) and bound(v) for i in (1,2,3))
checks['diagnostic_5of64_no_general_promotion']=agg['qualification_pass'] is True and agg['accepted'] is False and len(agg['cases'])==64 and sum(r['accepted'] for r in agg['cases'])==5 and bound(agg)
checks['old_rejection_preserved']=read(O/'aggregate.json')['accepted'] is False and sum(r['accepted'] for r in read(O/'aggregate.json')['cases'])==26
checks['protected_unchanged']=all(sha(p)==h for p,h in host['protected'].items())
checks['refs_unchanged']=git('rev-parse','HEAD')==host['refs']['head'] and git('rev-parse','master')==host['refs']['master'] and git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture')==host['refs']['remote']
checks['no_production_change']=not git('diff','HEAD','--','src','test','Project.toml','.github')
status=R/'diagnostics/simplex-core-architecture/STATUS.md';road=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
for p,b,marker in ((status,D/'STATUS.md.before-MA-P','## Previous MA-N preparation (completed)'),(road,D/'roadmap.md.before-MA-P','### Previous MA-N preparation (completed)')):checks['history_'+p.name]=p.read_text().split(marker,1)[1]==b.read_text().split(marker,1)[1]
mapping=read(D/'continuation-map.json')['mapping'];old=[]
for name in ('continuation-map.json','closure.json','publication.json'):
 for p,h in read(O/name)['sha256'].items():
  a=str(Path(p) if Path(p).is_absolute() else R/p)
  if a in mapping:old.append(sha(mapping[a])==h)
checks['six_exact_old_continuation_bindings']=len(old)==6 and all(old)
checks['new_continuation_bindings']=bound(read(D/'continuation-map.json'))
groups=post['groups'];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();f=s[s.rfind(')')+2:].split()
  if int(f[2]) in groups or int(f[3]) in groups or (p/'comm').read_text().strip().lower().startswith('julia'):matches.append(dict(pid=p.name,pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except FileNotFoundError:pass
checks['all152groups_ANDsessions_noJulia']=len(groups)==152 and not matches
extra=[status,road,R/'diagnostics/simplex-core-architecture/MA-RHS-PROPAGATION.md']
expected={str(p.relative_to(R)) for p in D.rglob('*') if p.is_file()}|{str(p.relative_to(R)) for p in extra}|{str((D/n).relative_to(R)) for n in ('closure.json','publication.json')}
checks['exact_names_complete']=set(names)==expected and len(names)==len(set(names))
checks['index_empty']=not git('diff','--cached','--name-only')
ws=read(D/'whitespace-supplement.json');checks['exact_format_exceptions']=ws['all_passed'] and all(sha(R/e['path'])==e['sha256'] for e in ws['entries'])
checks['authored_diff_clean']=subprocess.run(['git','diff','--check'],capture_output=True).returncode==0
v=dict(all_passed=all(checks.values()),checks=checks,sha256={str(R/n):sha(R/n) for n in names if n not in (str((D/'closure.json').relative_to(R)),str((D/'publication.json').relative_to(R)))},host=dict(time=time.time(),boot_id=boot,groups=groups,matches=matches),scope='Diagnostic closure only. General candidate performance not accepted; only5descriptive case benefits.')
with(D/'closure.json').open('x') as f:json.dump(v,f,indent=2);f.write('\n')
print(json.dumps(checks,indent=2))
if not v['all_passed']:raise ValueError('closure failed; no commit/push')
