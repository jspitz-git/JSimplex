from pathlib import Path
import json,hashlib,subprocess,tomllib
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/MA-S'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rd(n):return json.loads((E/n).read_text())
def bound(d):return all(sha(p)==s for p,s in d['sha256'].items())
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
rev=rd('result-review.json');post=rd('execution-postcheck.json');seal=rd('numerical-review.json');audit=rd('audit-1.json');host=rd('host.json');raw=tomllib.loads((E/'run-1/raw.toml').read_text());context=rd('launch-context.json')
checks={
 'result_review_accepted':rev['accepted'] is True and rev['findings']==[] and bound(rev),
 'postcheck22':len(post['checks'])==22 and post['all_passed'] is True and all(post['checks'].values()) and post['qualification_accepted'] is False and bound(post),
 'numerical_seal39':len(seal['sha256'])==39 and seal['accepted'] is True and bound(seal),
 'original_audit_false':audit['all_passed'] is False and sum(audit['checks'].values())==17 and len(audit['checks'])==23 and bound(audit),
 'reference16':raw['counts']['smoke']=={'pass':16,'fail':0,'error':0,'broken':0},
 'expected_RED':raw['red']['missing_route_only'] is True and [raw['red'][k] for k in ['pass','fail','error','broken']]==[0,2,0,0],
 'no_cost_claim':raw['costs']==[] and raw['correctness']==[] and len(raw['errors'])==1,
 'no_retry':all(not (E/n).exists() for n in ['run-2','run-3','reservation-2.json','reservation-3.json','aggregate.json']),
 'failure_exit':rd('run-1/process.json')['returncode']==1 and rd('invocation-1.json')['returncode']==1,
 'master514':len(host['master_identity'])==514 and all(sha(R/p)==s for p,s in host['master_identity'].items()),
 'protected6':len(host['protected'])==6 and all(sha(p)==s for p,s in host['protected'].items()),
 'refs':git('rev-parse','HEAD')==context['refs']['head'] and git('rev-parse','master')==context['refs']['master'],
 'only_continuation_tracked_changes':set(git('diff','--name-only','HEAD').splitlines())=={'diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'},
 'six_continuation_maps':len(rd('execution-continuation-map.json')['old_bindings'])==6 and all(sha(x['preserved'])==x['sha256']==json.loads(Path(x['source']).read_text())['sha256'][x['path']] for x in rd('execution-continuation-map.json')['old_bindings']),
 'authored_diff_clean':subprocess.run(['git','diff','--check'],capture_output=True).returncode==0,
 'no_prior_stage':not git('diff','--cached','--name-only')
}
names=['execution-closure.py','execution-publication.py','execution-entry.py','execution-entry.json','execution-continuation-map.json','execution-ledger.md','execution-postcheck.py','execution-postcheck.json','numerical-review.md','numerical-review.json','result-review.md','result-review.json','launch-context.json','STATUS.md.before-MA-S-execution','roadmap.md.before-MA-S-execution','sequence-execution.log','sequence-reservation.json','prelaunch-1.json','reservation-1.json','launcher-1.log','invocation-1.json','posthost-1.json','audit-1.json','run-1/current.json','run-1/pins.json','run-1/process.json','run-1/raw.toml','run-1/resources.jsonl','run-1/run.log']
paths=[E/n for n in names]+[R/'diagnostics/simplex-core-architecture/STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',R/'diagnostics/simplex-core-architecture/MA-DENSELU-BIGFLOAT-QUALIFICATION.md']
o=dict(all_passed=all(checks.values()),qualification_accepted=False,checks=checks,sha256={str(p):sha(p) for p in paths},scope='Diagnostic failure closure only. Original numerical audit remains false. No repeat.')
with (E/'execution-closure.json').open('x') as f:json.dump(o,f,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'bindings':len(paths),'all_passed':o['all_passed']}))
if not o['all_passed']:raise SystemExit(1)
