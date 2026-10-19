"""Fresh offline review of the lineage correction, preserving rejected checks."""
from pathlib import Path
import hashlib,json,difflib,subprocess
D=Path(__file__).resolve().parent;R=D.parents[3];G=D.with_name('DIRECT-BG-EXPORT-WORKSPACE-GREEN2-PREPARATION')
Q=R/'docs/superpowers/plans/2026-10-19-direct-bg-export-specialization.md';S=R/'docs/superpowers/specs/2026-10-19-direct-bg-export-specialization.md'
A=D/'SELF-REVIEW.md';mapping={str(Q):str(D/'plan.before-review.md'),str(A):str(D/'self-review.before-review.md')}
checks={};hashes={}
def data(p):
 p=Path(p);b=p.read_bytes();hashes[str(p)]=hashlib.sha256(b).hexdigest();return b
def tx(p):return data(p).decode()
def rd(p):return json.loads(data(p))
def ck(k,v):checks[k]=bool(v)
def bindings(m,historical=False):
 for k,v in m.items():
  p=Path(mapping.get(k,k) if historical else k)
  if hashlib.sha256(data(p)).hexdigest()!=v:return False
 return True
initial=rd(D/'independent-check.json');rejected=rd(D/'review-rejected.json');author=rd(D/'source-check.json');fix=rd(D/'review-fix.json')
ck('initial_rejection_preserved',not initial['all_passed'] and sum(initial['checks'].values())==25 and len(initial['checks'])==26 and not rejected['accepted'] and len(rejected['findings'])==1)
ck('all_initial_review_bindings_preserved',bindings(rejected['sha256'],True))
ck('all_initial_check_bindings_preserved',bindings(initial['sha256'],True))
ck('all185_author_bindings_preserved',len(author['sha256'])==185 and bindings(author['sha256'],True))
ck('author_fix_bindings',fix['all_passed'] and len(fix['checks'])==9 and bindings(fix['sha256']))
ck('mapping_exact',fix['historical_path_map']==mapping)
oldq,newq=tx(D/'plan.before-review.md'),tx(Q)
olda,newa=tx(D/'self-review.before-review.md'),tx(A)
def edits(a,b):return [(tag,i,j,k,l) for tag,i,j,k,l in difflib.SequenceMatcher(None,a.splitlines(),b.splitlines(),autojunk=False).get_opcodes() if tag!='equal']
qe,ae=edits(oldq,newq),edits(olda,newa)
ck('only_one_plan_paragraph_replaced',len(qe)==1 and qe[0][0]=='replace' and qe[0][2]-qe[0][1]==qe[0][4]-qe[0][3]==1 and oldq.splitlines()[qe[0][1]].startswith('**Consumes:**') and newq.splitlines()[qe[0][3]].startswith('**Consumes:**'))
ck('only_one_author_paragraph_replaced',len(ae)==1 and ae[0][0]=='replace' and ae[0][2]-ae[0][1]==ae[0][4]-ae[0][3]==1)
inv=rd(G/'inverse.json');am=Path(inv['amended']);orig=Path(inv['original']);driver=tx(G/'driver.jl');seal=rd(G/'runs/green2-300/sealed.json')
amended,original=tx(am),tx(orig)
ck('amendment_is_single_import_reducer',am.name==orig.name=='import-tests.jl' and original.count(inv['before'])==1 and amended.count(inv['after'])==1 and amended.replace(inv['after'],inv['before'])==original)
ck('test_exact_hash',hashes[str(am)]==inv['amended_sha256']=='628a74265bc5ed75e0a9507b9a7f3f453ba76d413ccbcb8a90e177e9e2329260' and hashes[str(orig)]==inv['original_sha256'])
tests=[am,R/'diagnostics/direct-bg-export-workspace/reproduce/workspace-tests.jl',R/'diagnostics/direct-bg-export-workspace/reproduce/lifecycle-tests.jl']
ck('all_three_actual_driver_test_includes',all('include("'+str(p)+'")' in driver for p in tests) and 'include("'+str(orig)+'")' not in driver)
ck('all_three_tests_and_driver_match_seal',all(hashlib.sha256(data(p)).hexdigest()==seal['inventory'][str(p)]['sha256'] for p in tests+[G/'driver.jl']))
ck('new_plan_correctly_selects_test',str(am.relative_to(R)) in newq and inv['amended_sha256'] in newq and 'unchanged `workspace-tests.jl` and `lifecycle-tests.jl`' in newq and 'separately included test file, not part of the 79-file GREEN stage' in newq and 'GREEN2 lifecycle test source' not in newq)
ck('spec_unchanged',hashlib.sha256(data(S)).hexdigest()==initial['sha256'][str(S)])
ck('still_no_candidate_or_tracked_change',not (R/'diagnostics/direct-bg-export-specialized').exists() and not subprocess.check_output(['git','diff','HEAD','--name-only'],cwd=R,text=True).strip())
data(Path(__file__))
out={'all_passed':all(checks.values()),'checks':checks,'sha256':hashes,'historical_path_map':mapping,'scope':'New independent offline amendment checks; no Julia, no old checker execution/import, no runtime admission'}
with (D/'independent-amendment-check.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({'all_passed':out['all_passed'],'checks':len(checks),'bindings':len(hashes),'failed':[k for k,v in checks.items() if not v]}))
if not out['all_passed']:raise SystemExit(1)
