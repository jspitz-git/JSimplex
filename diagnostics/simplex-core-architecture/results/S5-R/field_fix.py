"""One offline correction; original unexecuted candidate/pins remain unchanged."""
from pathlib import Path
import re,json,hashlib
R=Path.cwd();O=R/'diagnostics/simplex-core-architecture/results/S5-R'
s=(O/'candidate.jl').read_text();n=(R/'src/simplex_numerics.jl').read_text();body=n.split('struct NumericalPolicy',1)[1].split('\nend',1)[0];fields=set(re.findall(r'^    (\w+)::',body,re.M))
missing=sorted(set(re.findall(r'policy\.(\w+)',s))-fields)
assert missing==['numerical_profile']
bad='policy.numerical_profile === :native && policy.recovery && !policy.solve_refinement'
good='policy.recovery && !policy.solve_refinement && !policy.stable_ratio && !policy.pivot_validation'
assert s.count(bad)==1
fixed=s.replace(bad,good)
with (O/'candidate-reviewed.jl').open('x') as f:f.write(fixed)
checks={'RED_one_missing_policy_field':missing==['numerical_profile'],'GREEN_all_policy_fields_exist':set(re.findall(r'policy\.(\w+)',fixed))<=fields,'inverse_one_replacement':fixed.replace(good,bad)==s,'source_native_defaults':all(x in n for x in ['numerical_profile::Symbol=:native','stable_ratio::Bool=(numerical_profile == :checked)','pivot_validation::Bool=(numerical_profile == :checked)','solve_refinement::Bool=(numerical_profile == :checked)'])}
paths=[O/'candidate.jl',O/'candidate-reviewed.jl',O/'field_fix.py',R/'src/simplex_numerics.jl']
out=dict(checks=checks,all_passed=all(checks.values()),original_missing_fields=missing,sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},scope='Offline text RED/GREEN, not Julia execution')
with (O/'field-fix.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps(checks));assert out['all_passed']
