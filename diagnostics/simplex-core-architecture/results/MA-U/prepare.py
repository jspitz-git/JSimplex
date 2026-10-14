from pathlib import Path
import hashlib,json
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-U';P=D.with_name('MA-R');T=D.with_name('MA-T')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,o):
 with (D/n).open('x') as f:json.dump(o,f,indent=2);f.write('\n')
old=(P/'candidate.jl').read_text()
needle='    return Base.MPFR.rounding_raw(BigFloat) == Base.MPFR.ROUNDING_MODE[]\n'
helper='''function _dense_ma_rounding_matches()::Bool
    scope = Core.current_scope()::Union{Base.ScopedValues.Scope,Nothing}
    scope === nothing && return true
    key = Base.MPFR.CURRENT_ROUNDING_MODE
    v = Base.@inline Base.KeyValue.get(scope.values, key)
    v === nothing && return true
    return (only(v)::Base.MPFR.MPFRRoundingMode) == Base.MPFR.ROUNDING_MODE[]
end

'''
if old.count(needle)!=1:raise SystemExit('Original expression count')
red=dict(helper_missing='function _dense_ma_rounding_matches()::Bool' not in old,helper_call_missing='    return _dense_ma_rounding_matches()\n' not in old)
save('source-red.json',dict(expected_missing_route=all(red.values()),checks=red,scope='Python textual missing optimization seam only; NOT Julia failure or allocation RED',sha256={str(P/'candidate.jl'):sha(P/'candidate.jl'),str(D/'guard-tests.jl'):sha(D/'guard-tests.jl'),str(D/'prepare.py'):sha(D/'prepare.py')}))
new=helper+old.replace(needle,'    return _dense_ma_rounding_matches()\n')
with (D/'candidate.jl').open('x') as f:f.write(new)
for n in ['reference.jl','tests.jl','fixtures.toml','instrumented.jl','JULIA-LICENSE.md']:
 with (D/n).open('xb') as f:f.write((P/n).read_bytes())
save('source-map.json',dict(original=str(P/'candidate.jl'),candidate=str(D/'candidate.jl'),helper=helper,old_expression=needle,new_expression='    return _dense_ma_rounding_matches()\n',copy_pairs=[dict(original=str(P/n),copy=str(D/n),sha256=sha(D/n)) for n in ['reference.jl','tests.jl','fixtures.toml','instrumented.jl','JULIA-LICENSE.md']],scope='Strip exact helper prefix and replace one call to recover original bytes; copied test helpers not automatic execution.'))
print(json.dumps(dict(candidate_sha256=sha(D/'candidate.jl'),guard_tests_sha256=sha(D/'guard-tests.jl'),red=red)))
