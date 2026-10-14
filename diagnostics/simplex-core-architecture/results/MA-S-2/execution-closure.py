from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-S-2'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rd(n):return json.loads((D/n).read_text())
def bound(o):return all(sha(p)==s for p,s in o['sha256'].items())
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
rev=rd('result-review.json');post=rd('execution-postcheck.json');analysis=rd('result-analysis.json');agg=rd('aggregate.json');host=rd('host.json');context=rd('launch-context.json');maps=rd('execution-continuation-map.json')['old_bindings']
def mapped(n):
 m={x['path']:x['preserved'] for x in maps if x['source']==str(D/n)}
 return all(sha(m.get(p,p))==s for p,s in rd(n)['sha256'].items())
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[];groups=post['host']['groups']
for p in Path('/proc').glob('[0-9]*'):
 try:
  f=(p/'stat').read_text().rsplit(')',1)[1].split()
  if int(f[2]) in groups or int(f[3]) in groups or (p/'exe').resolve().name.startswith('julia'):matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'),boot_id=boot))
 except (FileNotFoundError,ProcessLookupError):pass
checks={'result_review':rev['accepted'] is True and rev['findings']==[] and rev['qualification_accepted'] is False and bound(rev),'postcheck18':len(post['checks'])==18 and post['all_passed'] is True and all(post['checks'].values()) and post['qualification_complete'] is True and post['qualification_accepted'] is False and bound(post),'analysis16':len(analysis['checks'])==16 and analysis['all_passed'] is True and all(analysis['checks'].values()) and bound(analysis),'aggregate_false48':agg['qualification_pass'] is True and agg['accepted'] is False and sum(r['accepted'] for r in agg['cases'])==48 and len(agg['cases'])==52 and bound(agg),'all_stage_audits':all(rd(f'audit-{i}.json')['all_passed'] is True and bound(rd(f'audit-{i}.json')) for i in (1,2,3)),'all_exit0':all(rd(f'run-{i}/process.json')['returncode']==rd(f'invocation-{i}.json')['returncode']==0 for i in (1,2,3)),'old_reviews_preserved_mapped':all(mapped(n) for n in ['admission-review.json','numerical-review.json','closure.json','publication.json']),'eight_continuation_maps':len(maps)==8 and all(sha(x['preserved'])==x['sha256']==json.loads(Path(x['source']).read_text())['sha256'][x['path']] for x in maps),'master514':len(host['master_identity'])==514 and all(sha(R/p)==s for p,s in host['master_identity'].items()),'protected6':len(host['protected'])==6 and all(sha(p)==s for p,s in host['protected'].items()),'refs':git('rev-parse','HEAD')==context['refs']['head'] and git('rev-parse','master')==context['refs']['master'],'full166groups_ANDsessions_noJulia':len(groups)==166 and not matches and boot==context['boot_id'],'tracked_scope':set(git('diff','--name-only','HEAD').splitlines())=={'diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'},'diff_clean':subprocess.run(['git','diff','--check'],capture_output=True).returncode==0,'no_prior_stage':not git('diff','--cached','--name-only'),'old_failure_false':json.loads((D.with_name('MA-S')/'audit-1.json').read_text())['all_passed'] is False}
# Literal complete artifact list frozen in execution-publication.py before closure.
import ast
module=ast.parse((D/'execution-publication.py').read_text());names=ast.literal_eval(next(n.value for n in module.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='NAMES' for t in n.targets)))
paths=[R/n for n in names if n not in {str((D/'execution-closure.json').relative_to(R)),str((D/'execution-publication.json').relative_to(R))}]
o=dict(all_passed=all(checks.values()),qualification_accepted=False,checks=checks,host=dict(boot_id=boot,groups=groups,matches=matches),sha256={str(p):sha(p) for p in paths},scope='Diagnostic closure of completed correctness and rejected whole allocation/cost qualification. No promotion.')
with (D/'execution-closure.json').open('x') as f:json.dump(o,f,indent=2);f.write('\n')
print(json.dumps(dict(checks=checks,all_passed=o['all_passed'],bindings=len(paths))))
if not o['all_passed']:raise SystemExit(1)
