"""Exclusive text-only permanent candidate preparation; no Julia parser."""
from pathlib import Path
import json,re,hashlib
R=Path.cwd();H=Path(__file__).resolve().parent;X=H.parent/'S5-X';Y=H.parent/'S5-Y';test=R/'test/simplex_start_state_tests.jl';s=(X/'candidate.jl').read_text();prefix=test.read_bytes()
def put(n,b):
 with (H/n).open('xb') as f:f.write(b if isinstance(b,bytes) else b.encode())
# Structural absent-coverage evidence only, before constructing the new suffix.
missing={k:k not in prefix.decode() for k in ['Crash fallback observer preserves initial ownership after work merge','CrashFallbackObserverProbe','trial_owned_containers','no_later_selected_work_events']}
put('structural-red.json',json.dumps(dict(missing=missing,all_missing=all(missing.values()),scope='Text-only missing coverage, not a failing Julia test or CI reproduction'),indent=2)+'\n');assert all(missing.values())
helpers=s[s.index('mutable struct S5XProbe'):s.index('function s5x_record_dict')]
core=s[s.index('    failure = SingularException(42)'):s.index('    observations = Dict(')]
names=re.findall(r'^        (\w+) = ',core);assert len(names)==50
renames={'S5XProbe':'CrashFallbackObserverProbe','s5x_owners':'crash_fallback_observer_owners','s5x_record':'crash_fallback_observer_record'}
def rename(t):
 for a,b in renames.items():t=t.replace(a,b)
 return t
append='\n# One native fallback observer boundary; retained trial values are endpoint observations.\n'+rename(helpers)+'function crash_fallback_observer_checks()\n'+rename(core)+'    return checks\nend\n\n@testset "Crash fallback observer preserves initial ownership after work merge" begin\n    checks = crash_fallback_observer_checks()\n'+''.join('    @test checks.'+n+'\n' for n in names)+'end\n'
put('original-test.jl',prefix);put('append.jl',append);put('candidate.jl',prefix+append.encode());put('renames.json',json.dumps(renames,indent=2)+'\n');put('predicates.json',json.dumps(names,indent=2)+'\n')
put('inverse-core.txt',helpers+core)
checks=dict(prefix_exact=(H/'candidate.jl').read_bytes()[:len(prefix)]==prefix,actual_test_unchanged=test.read_bytes()==prefix,helpers_inverse=all(append.count(b)>0 for b in renames.values()),predicates50=len(names)==50,assertions50=append.count('@test checks.')==50,one_testset=append.count('@testset ')==1,one_initial=append.count('JSimplex.initialize_workspace(')==1,one_crash=append.count('JSimplex._crash_workspace(')==1,seven_copies=append.count('copy(')==7,no_matrix_factor_copy='copy_basis_factorization' not in append,no_serialization=all(k not in append for k in ['TOML','ARGS','Dict(','s5x_record_dict','observations =','open(out']),storage_before_setup=append.index('probe = ' )<append.index('initial = '),arm_after_captures=append.index('probe.armed = true')>append.index('entry_work = '),unchanged_sentinel='failure = SingularException(42)' in append,unchanged_stop='JSimplex._crash_workspace(initial,()->done[])' in append,no_new_import='using ' not in append,structural_red=all(missing.values()))
back=append
for a,b in renames.items():back=back.replace(b,a)
checks['helpers_exact_inverse']=helpers in back;checks['core_exact_inverse']=core in back
put('source-check.json',json.dumps(dict(checks=checks,all_passed=all(checks.values()),prefix_bytes=len(prefix),append_lines=len(append.splitlines()),candidate_sha256=hashlib.sha256(prefix+append.encode()).hexdigest()),indent=2)+'\n');assert all(checks.values())
print(json.dumps(dict(checks=len(checks),prefix_bytes=len(prefix),append_lines=len(append.splitlines()),candidate_sha256=hashlib.sha256(prefix+append.encode()).hexdigest())))
