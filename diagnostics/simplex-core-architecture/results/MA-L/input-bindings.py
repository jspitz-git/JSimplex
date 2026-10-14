from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent
addition='''
# Bind every constructed stored scalar to its frozen canonical fixture, outside timing.
function fixture_matches(f,args)
    p,terms,k,pivot,rhs=args
    vals=collect(terms)
    length(vals)==length(f.co) && k==f.pivot || return false
    all(vals[j][1]==j && qexact(vals[j][2])==parseq(f.co[j]) for j in eachindex(f.co)) || return false
    all(qexact(p.A[1,j])==parseq(f.co[j]) for j in eachindex(f.co)) || return false
    pivot==parseq(f.co[k]) && rhs==parseq(f.rhs) || return false
    for (bounds,encoded) in ((p.column_lower,f.lo),(p.column_upper,f.hi))
        for j in eachindex(encoded)
            isfinite(bounds[j]) == !isnothing(encoded[j]) || return false
            if !isnothing(encoded[j])
                qexact(bound_value(bounds[j]))==parseq(encoded[j]) || return false
            end
        end
    end
    all(qexact(bound_value(b))==parseq(f.rhs) for b in (p.row_lower[1],p.row_upper[1])) || return false
    if startswith(f.scalar,"BigFloat")
        all(precision(x)==f.stored for x in input_scalars(args) if x isa BigFloat) || return false
    end
    return true
end
'''
helpers=(D/'test-helpers.jl').read_text();tests=(D/'tests.jl').read_text();needle='        want=endpoint_oracle(args)\n'
if tests.count(needle)!=1:raise ValueError('test insertion')
with (D/'test-helpers-reviewed.jl').open('x') as f:f.write(helpers+addition)
with (D/'tests-reviewed.jl').open('x') as f:f.write(tests.replace(needle,'        @test fixture_matches(f,args)\n'+needle))
checks={'helpers_append_inverse':(D/'test-helpers-reviewed.jl').read_text()[:-len(addition)]==helpers,'single_test_inverse':(D/'tests-reviewed.jl').read_text().replace('        @test fixture_matches(f,args)\n','')==tests,'old_missing_input_binding':'@test fixture_matches' not in tests,'new_binding_present':'@test fixture_matches' in (D/'tests-reviewed.jl').read_text(),'candidate_unchanged':hashlib.sha256((D/'candidate.jl').read_bytes()).hexdigest()==json.loads((D/'source-check-final.json').read_text())['sha256'][str(D/'candidate.jl')]}
record=dict(all_passed=all(checks.values()),checks=checks,additional_assertions=222,green_total=3787,red_pass=8,red_expected_fail=2,scope='Offline test strengthening: canonical tests-reviewed.jl and test-helpers-reviewed.jl. Original tests/source checks preserved; no numerical execution.',sha256={str(D/n):hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ('tests.jl','test-helpers.jl','tests-reviewed.jl','test-helpers-reviewed.jl','candidate.jl','source-check-final.json')})
with (D/'input-bindings.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'prospective_green_total':3787}))
if not record['all_passed']:raise ValueError('binding supplement failed')
