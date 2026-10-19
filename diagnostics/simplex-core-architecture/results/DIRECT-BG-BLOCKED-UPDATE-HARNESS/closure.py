"""Separate final offline closure; never executes Julia, outer, seal, guard or launcher."""
from control import *

def main():
 checks={}
 def ck(n,v):
  checks[n]=bool(v)
  require(v,n)
 validate_environment();validate_sources();preparation()
 ck('current_preparation_and_review',True)
 h=full_host();save(D/'host-closure.json',h)
 ck('fresh_host',host_safe(h) and len(h['groups'])==268)
 ck('entry_refs',h['head']==ENTRY and h['master']==MASTER and git('branch','--show-current')=='codex/simplex-core-architecture')
 ck('no_tracked_changes',not git('diff','HEAD','--name-only') and not git('diff','--cached','--name-only'))
 ck('no_launch_artifacts',not (D/'runs').exists() and not (D/'outers').exists())
 ck('entry_candidate_frozen',bindings(rd(D/'entry.json')))
 ck('review_scope',rd(D/'review.json')['launch_admitted'] is False and rd(D/'review.json')['runtime_acceptance'] is False and rd(D/'review.json')['numerical_acceptance'] is False and rd(D/'review.json')['performance_acceptance'] is False)
 for n in ['synthetic.json','source-check-2.json','full-audit-tests.json','synthetic-reviewed.json','full-audit-tests-reviewed.json','source-check-final.json','reviewer-final-check.json']:
  ck('passed_'+n,rd(D/n)['all_passed'] is True)
 for n,mapping in rd(D/'review-fix-bindings.json')['maps'].items():
  ck('historical_'+n,all(sha(mapping.get(p,p))==v for p,v in rd(D/n)['sha256'].items()))
 ck('final_source_bindings',bindings(rd(D/'source-check-final.json')))
 ck('review_fix_bindings',bindings(rd(D/'review-fix-bindings.json')))
 ck('reviewer_check_bindings',bindings(rd(D/'reviewer-final-check.json')))
 names=rd(D/'publication-names.json')['paths']
 actual={str(p.relative_to(R)) for p in D.rglob('*') if p.is_file()}
 expected=set(names)-{str((D/n).relative_to(R)) for n in ['closure.json','publication.json']}
 ck('exact_package',actual==expected and len(names)==len(set(names)))
 save(D/'closure.json',dict(all_passed=True,checks=checks,sha256={n:sha(R/n) for n in sorted(actual)},scope=__doc__))
 print('Offline closure PASS',len(checks),'bindings',len(actual))
if __name__=='__main__':main()
