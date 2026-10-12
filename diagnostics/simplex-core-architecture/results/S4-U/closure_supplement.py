from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';E=D/'results/S4-U';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();old=json.loads((E/'closure.json').read_text());review=D/'S4-ISOLATED-BOOTSTRAP-CONTRACT-REVIEW.md';text=review.read_text();a=json.loads((E/'source-contract.json').read_text());checks={}
checks['original_eight_true_one_false_preserved']=len(old['checks'])==9 and old['checks']['review_accepted'] is False and sum(old['checks'].values())==8 and old['all_passed'] is False
checks['failure_exactly_linebreak']='no unresolved Critical,\nImportant or Minor' in text and 'no unresolved Critical, Important or Minor' not in text
checks['normalized_review_acceptance']='no unresolved Critical, Important or Minor' in ' '.join(text.split())
checks['original_review_hash_unchanged']=sha(review)==old['final_sha256'][str(review)]
checks['original_all_closure_bound_hashes_unchanged']=all(sha(p)==h for p,h in old['final_sha256'].items())
checks['full627_pins_unchanged']=all(sha(p)==h for p,h in a['sha256'].items()) and len(a['sha256'])==627
checks['master_source_test_CI_unchanged']=not subprocess.check_output(['git','diff','master','--','src','test','.github']) and subprocess.check_output(['git','rev-parse','master'],text=True).strip()=='0eb75c3190096946b0e91e5360230ccd7166f298'
obj=dict(checks=checks,all_passed=all(checks.values()),original_closure_sha256=sha(E/'closure.json'),original_script_sha256=sha(E/'closure.py'),review_sha256=sha(review),scope='NEW separate offline correction: normalize whitespace only for acceptance text. Original false gate/exit1 and published ae874717 preserved; source/numerical evidence unchanged. Original script was not rerun.')
with (E/'closure-supplement.json').open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
print(json.dumps(obj));assert obj['all_passed']
