"""NEW final independent OFFLINE checker. Does not import or execute prior scripts."""
from pathlib import Path
import json,hashlib,re,subprocess
D=Path(__file__).resolve().parent;R=D.parents[3];Q=D.parent/'NATIVE-PIVOT-QUALIFICATION'
def rd(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bound(z):return all(sha(p)==h for p,h in z['sha256'].items())
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True).strip()
pins=rd(D/'pins-reviewed.json');initial=rd(D/'pins.json');a=(D/'regression.jl').read_text();b=(D/'regression-reviewed.jl').read_text()
edits=[('copy(nonzeroinds(v))','copy(SparseArrays.nonzeroinds(v))'),('nothing for x in v]','nothing for x in (v isa SparseVector ? nonzeros(v) : v)]')]
undo=b
for old,new in edits:undo=undo.replace(new,old)
sv=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/stdlib/v1.13/SparseArrays/src/sparsevector.jl').read_text()
f=(D/'finalize-reviewed.py').read_text();pub=(D/'publication.py').read_text();control=(Q/'control_reviewed.py').read_text()
inv=rd(D/'inverse.json');support=(D/'test-support-fixed.jl').read_text();driver=(D/'test-driver-fixed.jl').read_text();s=support.replace(inv['helper'],'');t=driver
for old,new in inv['support_changes']:s=s.replace(new,old)
for old,new in inv['driver_routes']:t=t.replace(new,old)
manifest=rd(D.parent/'NATIVE-PIVOT-PREPARATION/overlay-manifest.json')
checks={
'46_final_pins':len(pins['sha256'])==46 and bound(pins),
'initial33_identical_subset':len(initial['sha256'])==33 and all(pins['sha256'].get(p)==h for p,h in initial['sha256'].items()) and bound(initial),
'exact_two_edit_inverse':undo==a and all(a.count(old)==1 and b.count(new)==1 and old not in b for old,new in edits),
'qualified_API_definition':'nonzeroinds(x::SparseVector) = getfield(x, :nzind)' in sv,
'stored_owners_definition':'nonzeros(x::SparseVector) = getfield(x, :nzval)' in sv and edits[1][1] in b,
'assertion_predicates_unchanged':re.findall(r'^\s*@test.*$',a,re.M)==re.findall(r'^\s*@test.*$',b,re.M),
'119_prospective_assertions':len(re.findall(r'^\s*@test ',b,re.M))==13 and b.count('@test_throws')==1 and 12*9+4*2+1+2==119 and b.count('dense_tokens(')==2,
'helper_driver_whole_inverse':s==(Q/'test-support.jl').read_text() and t==(Q/'test-driver-reviewed.jl').read_text(),
'candidate75_reference73':len(manifest['candidate'])==75 and len(manifest['reference'])==73 and all(sha(e['source'])==e['sha256'] for arm in ('candidate','reference') for e in manifest[arm]),
'original_rejection_and_errata_preserved':rd(D/'review.json')['accepted'] is False and len(rd(D/'review.json')['findings'])==2 and bound(rd(D/'review-errata.json')),
'11_fix_checks_15_bindings':len(rd(D/'review-fix.json')['checks'])==11 and all(rd(D/'review-fix.json')['checks'].values()) and len(rd(D/'review-fix.json')['sha256'])==15 and bound(rd(D/'review-fix.json')),
'prior_supplemental_source_unchanged':all(sha(p)==h for p,h in rd(D/'reviewer-check.json')['supplemental_sha256'].items()),
'finalizer_routes_final_review':"pins=D/'pins-reviewed.json';review=rd(D/'review-final.json')" in f and "text=(D/'continuation-text-reviewed.md').read_text()" in f and "require(rd(D/'review-fix.json')['all_passed'] is True and bound(rd(D/'review-fix.json'))" in f,
'finalizer_exact_review_gate':"verify_review(review,pins,list(rd(pins)['sha256'])+[str(pins)],'offline observer correction')" in f and "review.get('accepted') is True and review.get('findings')==[]" in control and "set(review.get('sha256',{}))==set(required)" in control,
'publication_closure_and_exact_stage_gate':"c['all_passed'] is True and all(sha(R/n)==v for n,v in c['sha256'].items())" in pub and "set(git('diff','--cached','--name-only').splitlines())==set(names)" in pub,
'regression_not_yet_wired':'DenseTokenRegression' not in driver and 'regression' not in driver,
'no_finalization_or_new_stage':all(not (D/n).exists() for n in ['closure-host.json','continuation-mappings.json','closure.json','publication.json']) and {p.name for p in (Q/'runs').iterdir()}=={'red','green'} and {p.name for p in (R/'.superpowers/native-pivot-qualification').iterdir()}=={'red','green'},
'clean_tracked_index_and_refs':not git('diff','--name-only') and not git('diff','--cached','--name-only') and git('rev-parse','HEAD')=='ca987752f362c66e482a9c4f429c60110f93dce8' and git('rev-parse','master')=='6f68e24e8ddac42b948da8fcc2d636c010751194',
}
result=dict(all_passed=all(checks.values()),checks=checks,scope='Independent final offline integrity checks only; Julia unexecuted',pins_sha256=sha(D/'pins-reviewed.json'),sha256={**pins['sha256'],str(D/'pins-reviewed.json'):sha(D/'pins-reviewed.json')},checker_sha256=sha(__file__))
with (D/'reviewer-final-check.json').open('x') as out:json.dump(result,out,indent=2);out.write('\n')
print(json.dumps(dict(all_passed=result['all_passed'],checks=checks,bindings=len(result['sha256']))))
if not result['all_passed']:raise SystemExit(1)
