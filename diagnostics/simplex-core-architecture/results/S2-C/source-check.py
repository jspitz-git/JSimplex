from pathlib import Path
import hashlib,json,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/S2-C';B=D.parent/'S2-B'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
s=(R/'src/primal_updates.jl').read_text();c=(D/'candidate-primal-updates.jl').read_text();h=(D/'adapter.jl.txt').read_text();t=(D/'candidate-tests.jl').read_text();integration=(D/'integration-original.jl').read_text();bind=json.loads((D/'integration-binding.json').read_text())
old=json.loads((B/'source-check.json').read_text());print('B keys:',list(old))
paths=[R/p for p in subprocess.check_output(['git','ls-files','src','test','.github'],text=True).splitlines()]
paths += [R/'Project.toml',R/'Manifest.toml',R/'LocalPreferences.toml',R/'.vscode/settings.json']
main=Path('/home/jspitz/JSimplex.jl');paths += [main/p for p in ['Manifest.toml','LocalPreferences.toml','.vscode/settings.json']]
paths += [R/'docs/superpowers/plans/2026-10-13-price-audit-values-preparation.md',R/'diagnostics/simplex-core-architecture/S2-PRICE-AUDIT-STORAGE.md',B/'closure.json',B/'final-review.md',B/'final-review-check.json']
paths += sorted(p for p in D.iterdir() if p.is_file())
pins={str(p):sha(p) for p in paths}
comparisons={str(p.relative_to(R)):p.read_bytes()==subprocess.check_output(['git','show','master:'+str(p.relative_to(R))]) for p in paths if any(p.is_relative_to(R/k) for k in ['src','test','.github'])}
checks={
 'inverse_exact':c.replace(h,'',1).replace('values = _price_audit_values(ws.scratch.rho,predicted)','values = vcat(ws.scratch.rho,predicted)')==s,
 'saved_original_exact':(D/'original-primal-updates.jl').read_bytes()==(R/'src/primal_updates.jl').read_bytes(),
 'one_replacement':c.count('values = _price_audit_values(ws.scratch.rho,predicted)')==1,
 'exact_factories':h.count('function _price_audit_values(')==2 and all('dual::Vector{'+T+'}, predicted::Vector{'+T+'}' in h for T in ['Float32','Float64']),
 'empty_fallback_twice':h.count('(isempty(dual) || isempty(predicted)) && return vcat(dual, predicted)')==2,
 'inner_domain': 'return new{T}(dual, predicted)' in h and '(T === Float32 || T === Float64)' in h and 'throw(ArgumentError("price audit borrowing requires nonempty parents"))' in h,
 'parents_and_aliases': 'dual::Vector{T}\n    predicted::Vector{T}' in h and 'Base.dataids(v.dual)..., Base.dataids(v.predicted)...' in h,
 'bounds_readonly': '@boundscheck checkbounds(v, i)' in h and not any(x in h for x in ['setindex!','pointer(','unsafe_','resize!']),
 'fresh_scratch_preserved':'scratch = SolveQualityScratch(T,length(ws.costs))' in c,
 'integration_exact': t.endswith(integration) and (R/bind['source']).read_bytes()[bind['start_byte']:bind['end_byte']]==integration.encode(),
 'integration_three_testsets':integration.count('@testset ')==3,
 'all_four_quality_fields':'(:absolute_error,:relative_error,:finite,:reliable)' in t,
 'all_initialized_scratch_fields':'for field in fieldnames(typeof(scratch))' in t,
 'hardware_bitwise':'reinterpret(UInt32,a) == reinterpret(UInt32,b)' in t and 'reinterpret(UInt64,a) == reinterpret(UInt64,b)' in t,
 'nonfinite_early_state':'isempty(scratch.compensation) && isempty(scratch.error_sum)' in t,
 'transposed_and_empty':'transposed=true' in t and 'spzeros(T,0,0)' in t and 'spzeros(T,0,2)' in t,
 'union_mixed_fallback':'Union{Float32,Float64}[1f0]' in t and 'Float32[1],Float64[2]' in t,
 'alias_both_parents':'side in (:dual,:predicted)' in t,
 'stored_precision': 'JSimplex._stored_quality_bits' in t and 'setprecision(BigFloat,64)' in t,
 'actual_source_test_ci_unchanged':all(comparisons.values()) and len(comparisons)==513,
 'unexecuted_label':t.startswith('# UNEXECUTED S2-C source.'),
}
for n,o in [('pins.json',pins),('source-check.json',{'checks':checks,'all_passed':all(checks.values()),'source_comparisons':comparisons,'pin_count':len(pins),'scope':'Python text checks only; NO Julia parsing, dispatch, numerics or performance acceptance'})]:
 with (D/n).open('x') as f:json.dump(o,f,indent=2);f.write('\n')
print(json.dumps({'checks':len(checks),'pins':len(pins),'comparisons':len(comparisons),'all_passed':all(checks.values())}));assert all(checks.values())
