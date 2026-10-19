from pathlib import Path
import sys,json
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');P=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-SPECIALIZATION-COST';Q=P.with_name('DIRECT-BG-BLOCKED-UPDATE-TASK2');C=R/'diagnostics/direct-bg-blocked-update/reproduce'
sys.path.insert(0,str(P));import control as c
frozen={'panel.jl','panel-tests.jl','work-memory-ledger.md','source-map.json'}
def bindings(file,kind='current'):
 j=c.rd(Q/file);mapping={}
 for n,h in j['sha256'].items():
  p=c.path(n)
  if c.sha(p)==h:continue
  name=p.name
  if kind=='tests-first' and p.parent==C and name in {'numerical-tests.jl','lifecycle-tests.jl'}:old=Q/(name+'.before-author-fix')
  elif kind=='review-fix' and p==C/'adapter-work-memory.md':old=Q/'adapter-work-memory.md.before-cold-budget'
  elif kind=='before-review' and (p.parent==C and name in {'factor.jl','factor-fault.jl','adapter-source-map.json','lifecycle-tests.jl','adapter-work-memory.md'} or p==Q/'REPORT.md'):old=Q/(name+'.before-review')
  else:return False
  if not old.is_file() or c.sha(old)!=h:return False
  mapping[n]=str(old)
 return True
h=c.full_host(c.rd(Q/'host-entry.json')['groups']);h.update(remote=c.git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'));c.save(Q/'host-closure.json',h)
v=c.rd(Q/'review.json');names=c.rd(Q/'publication-names.json')['paths'];actual={str(p.relative_to(R)) for p in Q.rglob('*') if p.is_file()}|{str(p.relative_to(R)) for p in C.iterdir() if p.name not in frozen}
expected=set(names)-{str((Q/n).relative_to(R)) for n in ['closure.json','publication.json']}
manifest=c.rd(C/'overlay-manifest.json');stage=Path(manifest['stage'])
checks={
'fresh_host':c.host_safe(h) and len(h['groups'])==268,
'refs':h['head']=='55c5fad5dfa8796b53a38b53c85ff3b024265e2e' and h['master']==c.MASTER,
'remotes':h['head']+'\trefs/heads/codex/simplex-core-architecture' in h['remote'] and c.MASTER+'\trefs/heads/master' in h['remote'],
'branch':c.git('branch','--show-current')=='codex/simplex-core-architecture',
'production_checkout':c.git('rev-parse','HEAD',cwd=c.W)==c.MASTER,
'no_tracked_changes':not c.git('diff','HEAD','--name-only') and not c.git('diff','--cached','--name-only'),
'entry_bindings':bindings('entry.json'),
'initial_tests_preserved':bindings('tests-first.json','tests-first'),
'author_fix_preserved':bindings('author-fix.json','before-review'),
'old_source_check_preserved':c.rd(Q/'source-check.json')['all_passed'] and bindings('source-check.json','before-review'),
'fixture_preparation':c.rd(Q/'fixture-preparation.json')['all_passed'] and bindings('fixture-preparation.json'),
'fix_checks':c.rd(Q/'review-fix.json')['all_passed'] and bindings('review-fix.json','review-fix'),
'rejected_review_preserved':c.rd(Q/'review-first.json')['accepted'] is False and bindings('review-first.json','before-review'),
'final_review':v.get('accepted') is True and v.get('findings')==[] and v.get('runtime_acceptance') is False and bindings('review.json'),
'candidate_review_membership':all(str(x) in v['sha256'] or str(x.relative_to(R)) in v['sha256'] for x in C.iterdir()),
'ordinary_stage':all(c.sha(stage/n)==hh for n,hh in manifest['stage_sha256'].items()),
'exact_package':actual==expected and len(names)==len(set(names)),
'no_driver_or_launcher':not any(p.name in {'driver.jl','launch.py','guard.py','ADMISSION.md'} for p in Q.iterdir()),
}
result=dict(all_passed=all(checks.values()),checks=checks,sha256={n:c.sha(R/n) for n in sorted(actual)},historical_mapping='Only exact named before-author-fix for initial tests; before-review for modified initial source/review/report/author receipts; before-cold-budget solely for review-fix ledger. Frozen Task1 remains live byte-identical. Initial failed review and failed reviewer final check remain preserved.',scope='Task2 offline source preparation closure; no Julia/runtime/performance acceptance')
c.save(Q/'closure.json',result);print(json.dumps(checks));c.require(result['all_passed'],'Closure failure: stop publication')
