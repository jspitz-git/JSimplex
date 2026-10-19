from pathlib import Path
import sys,json
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');P=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-SPECIALIZATION-COST';Q=P.with_name('DIRECT-BG-BLOCKED-UPDATE-TASK1');C=R/'diagnostics/direct-bg-blocked-update/reproduce'
sys.path.insert(0,str(P));import control as c

def bindings(file,historical=False):
 j=c.rd(Q/file)
 for n,h in j['sha256'].items():
  path=c.path(n)
  if historical and path.parent==C:path=Q/(path.name+'.before-review')
  if c.sha(path)!=h:return False
 return True
h=c.full_host(c.rd(Q/'host-entry.json')['groups']);h.update(remote=c.git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'));c.save(Q/'host-closure.json',h)
v=c.rd(Q/'review.json');names=c.rd(Q/'publication-names.json')['paths'];expected=set(names)-{str((Q/n).relative_to(R)) for n in ['closure.json','publication.json']};actual={str(p.relative_to(R)) for root in [Q,C] for p in root.rglob('*') if p.is_file()}
checks={
'fresh_host':c.host_safe(h) and len(h['groups'])==268,
'refs':h['head']=='982b56980e38f4438f3c3c6746bd490a60c5eded' and h['master']==c.MASTER,
'remotes':h['head']+'\trefs/heads/codex/simplex-core-architecture' in h['remote'] and c.MASTER+'\trefs/heads/master' in h['remote'],
'branch':c.git('branch','--show-current')=='codex/simplex-core-architecture',
'production_checkout':c.git('rev-parse','HEAD',cwd=c.W)==c.MASTER,
'no_tracked_changes':not c.git('diff','HEAD','--name-only') and not c.git('diff','--cached','--name-only'),
'entry_bindings':bindings('entry.json'),
'old_source_check_preserved':c.rd(Q/'source-check.json')['all_passed'] and bindings('source-check.json',True),
'fix_checks':c.rd(Q/'fix-check.json')['all_passed'] and bindings('fix-check.json'),
'rejected_review_preserved':c.rd(Q/'review-initial.json')['accepted'] is False and bindings('review-initial.json',True),
'final_review':v.get('accepted') is True and v.get('findings')==[] and v.get('scope')=='BG blocked U Task1 offline candidate' and bindings('review.json'),
'candidate_review_membership':all(str(x) in v['sha256'] or str(x.relative_to(R)) in v['sha256'] for x in C.iterdir()),
'exact_package':actual==expected and len(names)==len(set(names)),
'four_candidate_files':set(p.name for p in C.iterdir())=={'panel.jl','panel-tests.jl','work-memory-ledger.md','source-map.json'},
'only_offline':'UNEXECUTED' in v.get('execution','') and 'no numerical/performance acceptance' in v.get('execution',''),
}
result={'all_passed':all(checks.values()),'checks':checks,'sha256':{n:c.sha(R/n) for n in sorted(actual)},'historical_mapping':'Only source-check.json and review-initial.json candidate files map to exact matching Q/<name>.before-review; other paths unchanged','scope':'Task1 offline preparation closure, no Julia execution or runtime acceptance'}
c.save(Q/'closure.json',result);print(json.dumps(checks));c.require(result['all_passed'],'Closure failure: stop publication')
