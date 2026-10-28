from pathlib import Path
import sys,json,re
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));n=__import__('negative-common')
checks={}
def check(k,v):n.need(v,k);checks[k]=True
review=n.read('negative-final-review.json');check('independent_negative_final_review',review['accepted'] is True and review['findings']==[])
n.refs();n.baseline_and_backup();n.protected(True);checks['restored_master_and_preserved_candidate_userfiles']=True
hist=n.Historical();counts={p:hist.manifest(p) for p in n.MANIFESTS};checks['every_phase_manifest_and_exact_beforeimage']=True
# Check bindings of accepted AND rejected reviews; acceptance is never rewritten.
reviews=[]
for p in sorted(D.rglob('*.json')):
 if p.relative_to(D).parts[0] in n.PRIVATE:continue
 x=json.loads(p.read_text())
 if not isinstance(x,dict) or not isinstance(x.get('bindings'),dict):continue
 for key,h in x['bindings'].items():
  if isinstance(h,str) and re.fullmatch('[0-9a-f]{64}',h):hist.resolve(key,h)
 reviews.append(str(p.relative_to(D)))
source=n.read('source-review.json');check('original_source_review_acceptance',source['findings']==[] and source['decision'].startswith('ACCEPT'))
for p,h in source['sha256'].items():hist.resolve(D/p,h)
checks['all_review_bindings_and_exact_historical_maps']=True
cmp=n.read('audit.json');red=n.read('RED-run/audit.json');green=n.read('GREEN-run/audit.json');master=n.read('MASTER-run/failure-audit.json');cc=n.read('counter-capture/audit.json');gc=n.read('counter-gc-preparation/audit.json')
check('supported_measurement_not_original_pass',cmp['accepted'] is True and cmp['original_root_accepted'] is False and cmp['original_root_pass']==55626 and cmp['original_root_fail']==1 and cmp['original_root_errors']==2 and cmp['cases']==1226 and cmp['windows']==22068 and cmp['measured_compile_zero'] is True)
check('separate_missing_cells_only',n.read('remaining-qualified/audit.json')['assertions']==1428)
check('original_RED_and_private_GREEN',red['accepted'] is True and red['passed']==7325 and red['expected_failures']==12 and red['total']==7337 and green['accepted'] is True and green['passed']==green['total']==380372 and green['expected_failures']==0)
check('actual_MASTER_failure_preserved',master['accepted'] is False and master['audit_completed'] is True and master['production_qualification_rejected'] is True and master['passed']==380370 and master['actual_failures']==2 and master['total']==380372 and n.read('MASTER-run/result-review.json')['accepted'] is False)
check('data_only_counter_diagnostics_still_fail',cc['accepted'] is True and cc['ordinary_test_passed']==23661 and cc['ordinary_test_failed']==2 and gc['accepted'] is True and gc['ordinary_test_passed']==23662 and gc['ordinary_test_failed']==1 and cc['original_MASTER_still_rejected'] is True and gc['original_MASTER_still_rejected'] is True)
decision=n.read('gc-preparation-decision.json');check('stop_no_GC_fix_waiver_or_further_tuning',decision['production_candidate_admitted'] is False and decision['further_adaptive_tuning_authorized'] is False and decision['permanent_GC_test_change_approved'] is False and decision['historical_7e306_exception_reused'] is False)
check('same_complete_GREEN_MASTER_testfiles',n.read('GREEN-run/contract.json')['files']==n.read('MASTER-run/contract.json')['files'] and len(n.read('MASTER-run/contract.json')['files'])==83)
for p in ['generic_dual_comparisons_tests.jl','generic_unit_perturb_residual_tests.jl']:check('old_'+p+'_unchanged',(n.M/'test'/p).read_bytes()==(D/'baseline/test'/p).read_bytes())
check('no_false_production_publication',not (D/'publication.json').exists() and not (D/'MASTER-run/completed.json').exists())
from publication_checks import verify_historical_maps
im=n.read('integration-historical-path-map.json');hm=n.read('negative-historical-map.json');mi=n.git(['rev-parse','--path-format=absolute','--git-path','index']);verify_historical_maps(D,n.M,mi,n.BASE,n.read('production-commit.json')['names'],im,hm,n.read('protected-before.json'),n.read('baseline-tree.json'),n.need,n.sha)
rb=n.read('rollback-before.json');check('exact_rollback_map',hm['unpromoted_source_before']==rb['source_before'] and hm['unpromoted_index_before']==rb['index_before'])
for mapping in [rb['source_before'],rb['index_before'],hm['continuation_before'],n.read('negative-diagnostic-index-before.json')]:
 for p,v in mapping.items():n.need(n.sha(v['before'])==v['sha256'],'exact before bytes '+p)
checks['beforeimages_and_all_older_maps_preserved']=True
h=n.host();n.put('negative-closure-host.json',h);checks['fresh_full_groups_AND_sessions_noJulia']=True
bindings={str(p):n.sha(p) for p in n.artifacts()};bindings.update({p:n.sha(p) for p in hm['continuation_before']})
n.put('negative-closure.json',dict(accepted=True,scope='PASS truthful negative-result preservation/closure; NOT production acceptance',production_accepted=False,master_restored=n.BASE,candidate_unpromoted=n.CAND,checks=checks,manifest_counts=counts,review_files=reviews,bindings=bindings,historical_before_resolutions=hist.used,closure_self_excluded=True,no_new_numerics=True))
print(json.dumps(dict(accepted=True,production_accepted=False,checks=len(checks),bindings=len(bindings),historical_resolutions=len(hist.used),groups=len(h['groups']))))
