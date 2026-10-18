"""Separate final closure after bounded review wording erratum; no old checker rerun."""
from control import *
checks={}
def ok(v,k):
 checks[k]=bool(v);require(v,k)
old=rd(D/'closure.json');ok(old['all_passed'] is True and bindings(old),'original_PASS_closure_and_all66bindings_preserved')
v=rd(D/'timing-erratum-acceptance.json')
ok(v.get('accepted') is True and v.get('findings')==[] and v.get('scope')=='block BG timing-count erratum' and bindings(v),'independent_timing_erratum')
ok(str(D/'cost.jl') in v['sha256'] and str(D/'review.md') in v['sha256'] and str(D/'timing-erratum-review.md') in v['sha256'],'erratum_source_review_binding')
ok(not (D/'runs').exists(),'no_numerical_activity')
h=full_host();save(D/'closure-final-host.json',h)
ok(not h['matches'] and len(h['groups'])==238 and h['head']==ENTRY and h['master']==MASTER,'fresh_groups_refs')
ok(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'no_tracked_or_staged_changes')
files=sorted(p for p in D.iterdir() if p.is_file());names=[str(p.relative_to(R)) for p in files]
ok(not any(p.is_symlink() for p in files) and names==rd(D/'closure-final-names.json')['names'],'exact_final_names')
save(D/'closure-final.json',dict(all_passed=True,checks=checks,sha256={str(p.relative_to(R)):sha(p) for p in files},scope='OFFLINE preparation plus timing-report erratum; no numerical admission'))
print('Final closure PASS',len(checks),'checks;',len(files),'bindings')
