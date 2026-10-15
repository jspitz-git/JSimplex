"""Independent OFFLINE source/hash review; executes no Julia or prior checker."""
from pathlib import Path
import hashlib,json,re,subprocess
D=Path(__file__).resolve().parent;R=D.parents[3];Q=D.parent/'NATIVE-PIVOT-QUALIFICATION'
J=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True).strip()
pins=rd(D/'pins.json')['sha256'];inv=rd(D/'inverse.json');reg=(D/'regression.jl').read_text()
s=(D/'test-support-fixed.jl').read_text();t=(D/'test-driver-fixed.jl').read_text()
u=s.replace(inv['helper'],'')
for old,new in inv['support_changes']:u=u.replace(new,old)
v=t
for old,new in inv['driver_routes']:v=v.replace(new,old)
manifest=rd(D.parent/'NATIVE-PIVOT-PREPARATION/overlay-manifest.json')
api=(J/'stdlib/v1.13/SparseArrays/src/SparseArrays.jl').read_text()
export=api.split('export AbstractSparseArray',1)[1].split('\n\n',1)[0]
sv=(J/'stdlib/v1.13/SparseArrays/src/sparsevector.jl').read_text()
mp=(J/'base/mpfr.jl').read_text();num=(J/'base/number.jl').read_text();rat=(J/'base/rational.jl').read_text()
budget=rd(Q/'budget.json')
checks={
'33_original_pins_match':len(pins)==33 and all(sha(p)==h for p,h in pins.items()),
'whole_support_inverse':u==(Q/'test-support.jl').read_text(),
'one_helper_four_sites':s.count(inv['helper'])==1 and len(inv['support_changes'])==4 and all(s.count(b)==1 and a not in s for a,b in inv['support_changes']),
'whole_driver_inverse_four_routes':v==(Q/'test-driver-reviewed.jl').read_text() and len(inv['driver_routes'])==4,
'candidate75_reference73_unchanged':len(manifest['candidate'])==75 and len(manifest['reference'])==73 and all(sha(e['source'])==e['sha256'] for arm in ('candidate','reference') for e in manifest[arm]),
'original_counts':budget['green_assertions']==6858 and sum(budget['main'].values())+sum(budget['neighbors'].values())==792,
'prospective_regression_counts':len(re.findall(r'^\s*@test ',reg,re.M))==13 and len(re.findall(r'^\s*@test_throws ',reg,re.M))==1 and 12*9+4*2+1+2==inv['regression_assertions']==119 and inv['prospective_helper_calls']==16,
'regression_unwired': 'regression.jl' not in t and 'DenseTokenRegression' not in t,
'finding1_unqualified_nonexported_api':'copy(nonzeroinds(v))' in reg and 'nonzeroinds' not in export and 'SparseArrays.nonzeroinds' not in reg,
'finding2_identity_of_implicit_zeros': 'for x in v]' in reg and '(sparsevec(bf),nothing)' in reg and '(sparsevec(rb),nothing)' in reg and 'nzval[ii] : zero(Tv)' in sv and 'zero(::Type{T}) where {T<:Number} = convert(T,0)' in num and 'd = Memory{Limb}(undef, nl % Int)' in mp and 'unsafe_rational(T, T(x), T(one(x)))' in rat,
'failed_green_preserved':rd(Q/'runs/green/audit.json')['all_passed'] is False and rd(Q/'runs/green/result-review.json')['qualification_accepted'] is False,
'13_original_static_checks_bound':len(rd(D/'check.json')['checks'])==13 and len(rd(D/'check.json')['sha256'])==20 and all(sha(p)==h for p,h in rd(D/'check.json')['sha256'].items()),
'head_master':git('rev-parse','HEAD')=='ca987752f362c66e482a9c4f429c60110f93dce8' and git('rev-parse','master')=='6f68e24e8ddac42b948da8fcc2d636c010751194',
'no_tracked_or_staged_change':not git('diff','--name-only') and not git('diff','--cached','--name-only'),
'no_new_run_or_stage':{p.name for p in (Q/'runs').iterdir()}=={'red','green'} and {p.name for p in (R/'.superpowers/native-pivot-qualification').iterdir()}=={'red','green'},
'continuation_preimages':sha(D/'STATUS.md.before-fix')==sha(R/'diagnostics/simplex-core-architecture/STATUS.md') and sha(D/'roadmap.md.before-fix')==sha(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'),
}
supp=[J/'base'/n for n in ('mpfr.jl','gmp.jl','rational.jl','number.jl')]+[J/'stdlib/v1.13/SparseArrays/src/solvers/umfpack.jl',Q/'control_reviewed.py',Q/'red-contract.jl',Path(__file__)]
result=dict(all_passed=all(checks.values()),checks=checks,review_accepted=False,scope='Independent offline integrity and defect confirmation only; no Julia regression execution',pins_sha256=sha(D/'pins.json'),sha256={**pins,str(D/'pins.json'):sha(D/'pins.json')},supplemental_sha256={str(p):sha(p) for p in supp},candidate_reference_entries_checked=148)
with (D/'reviewer-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=result['all_passed'],checks=checks,bound_inputs=len(result['sha256']),supplemental_bindings=len(supp))))
if not result['all_passed']:raise SystemExit(1)
