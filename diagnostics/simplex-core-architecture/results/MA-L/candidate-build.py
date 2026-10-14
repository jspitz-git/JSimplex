"""One-shot offline text preparation; never invokes/parses Julia."""
from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent;R=D.parents[3]
def put(name,text):
 with (D/name).open('x') as f:f.write(text)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=(R/'src/presolve_aggregation.jl').read_text()
original=source[source.index('function _equality_implies_column_bounds('):source.index('\nfunction aggregate_sparse_equalities(')]
red={'scope':'Offline missing-source markers only, NOT an executed Julia RED','missing_candidate_before':not (D/'candidate.jl').exists(),'tests_written_first':True,'test_hashes':{n:sha(D/n) for n in ('tests.jl','test-helpers.jl','fixtures.json','fixtures.jl')},'runtime_red':'UNEXECUTED; original_route_red expects exactly two scratch-route failures, numerical/preservation assertions pass'}
put('structural-red.json',json.dumps(red,indent=2)+'\n')
reference=original.replace('function _equality_implies_column_bounds(','function reference_bounds(',1)
put('reference.jl',reference)
private=(D.parent/'MA-J/candidate.jl').read_text();private=private[private.index('function private_add('):private.index('\nfunction candidate_bounds(')].replace('private_add','_mal_private_add')
edits=[];special=original
def change(old,new,count=1):
 global special
 if special.count(old)!=count:raise ValueError(('replacement count',old,special.count(old),count))
 special=special.replace(old,new);edits.append(dict(old=old,new=new,count=count))
change('function _equality_implies_column_bounds(','function _ma_equality_bounds8(')
change('    for (column, stored) in row_terms\n','    scratch = nothing\n    eligible_count = 0\n    decided = isnothing(other_min) || isnothing(other_max)\n    for (position, (column, stored)) in enumerate(row_terms)\n        position == 4 && (decided = true)\n')
change('        min_product::ExactEndpoint = nothing\n','''        min_product::ExactEndpoint = nothing
        check_pair = !decided && !isnothing(other_min) && !isnothing(other_max) &&
                     isfinite(min_bound) && isfinite(max_bound)
        equal_bounds = check_pair ? min_bound == max_bound : false
        eligible_term = check_pair && !equal_bounds
''')
change('if !isnothing(other_max) && min_bound == max_bound','if !isnothing(other_max) && (check_pair ? equal_bounds : min_bound == max_bound)')
for endpoint in ('other_min','other_max'):
 shared='                shared_activity && !isnothing(min_product) ? other_min :\n' if endpoint=='other_max' else ''
 old=f'''            iszero({endpoint}) ? product :
{shared}                denominator({endpoint}) == denominator(product) ?
                Rational{{BigInt}}(numerator({endpoint}) + numerator(product), denominator({endpoint})) :
                {endpoint} + product'''
 sharedif='''            elseif shared_activity && !isnothing(min_product)
                other_min
''' if endpoint=='other_max' else ''
 new=f'''            if iszero({endpoint})
                product
{sharedif}            elseif !isnothing(scratch)
                _mal_private_add(scratch, {endpoint}, product, other_min, other_max)
            elseif denominator({endpoint}) == denominator(product)
                Rational{{BigInt}}(numerator({endpoint}) + numerator(product), denominator({endpoint}))
            else
                if eligible_term && !decided && !iszero(product)
                    eligible_count += 1
                    if eligible_count == 2
                        decided = true
                        if (numerator({endpoint}) > 0) == (numerator(product) > 0) &&
                           ndigits(numerator({endpoint}); base=2) >= 129 &&
                           ndigits(numerator(product); base=2) >= 129
                            scratch = ((zero(ExactValue), zero(ExactValue), zero(ExactValue)),
                                       MA.buffer_for(+, ExactValue, ExactValue))
                        end
                    end
                end
                isnothing(scratch) ? {endpoint} + product :
                    _mal_private_add(scratch, {endpoint}, product, other_min, other_max)
            end'''
 change(old,new)
generic=original.replace('function _equality_implies_column_bounds(','function candidate_bounds(',1)
dispatch='''function candidate_bounds(problem::LinearProblem{Rational{BigInt}},
                          row_terms::Vector{Tuple{Int,Rational{BigInt}}},
                          pivot_column::Int, pivot::ExactValue, rhs::ExactValue)
    length(row_terms) == 8 || return invoke(candidate_bounds,
        Tuple{LinearProblem,Any,Int,ExactValue,ExactValue},
        problem,row_terms,pivot_column,pivot,rhs)
    return _ma_equality_bounds8(problem,row_terms,pivot_column,pivot,rhs)
end

'''
header='# MA-L UNEXECUTED isolated candidate. No production method overwrite.\n'
candidate=header+private+'\n'+generic+'\n'+dispatch+special
put('candidate.jl',candidate)
trace=candidate;tedits=[]
def tchange(old,new,count=None):
 global trace
 actual=trace.count(old)
 if count is not None and actual!=count:raise ValueError(('trace count',old,actual,count))
 if not actual:raise ValueError('trace missing '+old)
 trace=trace.replace(old,new);tedits.append(dict(old=old,new=new,count=actual))
tchange('candidate_bounds','traced_bounds')
tchange('_ma_equality_bounds8','_mal_traced_bounds8')
tchange('_mal_private_add','_mal_traced_add')
tchange('    pool, buffer = scratch\n','    _mal_note_add!(scratch, x, y, lo, hi)\n    pool, buffer = scratch\n',1)
tchange('        return out\n','        return _mal_note_result!(out)\n',1)
tchange('    return MA.buffered_operate_to!(buffer, out, +, x, y)\n','    return _mal_note_result!(MA.buffered_operate_to!(buffer, out, +, x, y))\n',1)
tchange('                    eligible_count += 1\n','                    eligible_count += 1\n                    _mal_note_eligible!(position, eligible_count)\n',2)
tchange('                                       MA.buffer_for(+, ExactValue, ExactValue))\n','                                       MA.buffer_for(+, ExactValue, ExactValue))\n                            _mal_note_scratch!(scratch, position)\n',2)
put('candidate-trace.jl',trace)
put('inverse.json',json.dumps(dict(source=str(R/'src/presolve_aggregation.jl'),source_sha256=sha(R/'src/presolve_aggregation.jl'),original_sha256=hashlib.sha256(original.encode()).hexdigest(),generic_rename={'old':'_equality_implies_column_bounds','new':'candidate_bounds'},special_edits=edits,trace_edits=tedits,parts=dict(header=header,private=private,generic=generic,dispatch=dispatch,special=special)),indent=2)+'\n')
print(json.dumps(dict(candidate_lines=len(candidate.splitlines()),trace_lines=len(trace.splitlines()),special_edits=len(edits),trace_edits=len(tedits),runtime='UNEXECUTED')))
