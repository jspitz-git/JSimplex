"""Exclusive offline source preparation. No historical code is executed."""
from pathlib import Path
import hashlib,json,re
R=Path.cwd();H=Path(__file__).resolve().parent;Z=H.parent/'S5-Z';X=H.parent/'S5-X';Y=H.parent/'S5-Y';U=H.parent/'S5-U'
def save(n,s):
 with (H/n).open('x') as f:f.write(s)
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(n,x):save(n,json.dumps(x,indent=2)+'\n')
old=(R/'test/simplex_start_state_tests.jl').read_bytes();suffix=(Z/'append-reviewed.jl').read_text();cand=(Z/'candidate-reviewed.jl').read_bytes()
assert len(old)==4774 and cand==old+suffix.encode() and sha(cand)=='ce256932a4bbda14bb9c55678525d6506a8e63732683442def57b22873b0415f'
save('original-test.jl',old.decode());save('guard.py',(Y/'guard.py').read_text());dump('guard-source.json',{'source':str(Y/'guard.py'),'sha256':sha((Y/'guard.py').read_bytes()),'byte_identical':True})
x=(X/'candidate.jl').read_text();record=x[x.index('    observations = Dict('):x.index('    open(out,"w")')].replace('s5x_record_dict','aa_record_dict')+'    AA_RECORD[]=output\n    aa_save_case(output)\n'
ins=[dict(anchor='function crash_fallback_observer_checks()\n',before='',after='    AA_COUNTS[1]+=1\n'),dict(anchor='    initial = JSimplex.initialize_workspace(p,SolverOptions(verbose=false);progress)\n',before='    AA_COUNTS[2]+=1\n',after=''),dict(anchor='        ws,expired = JSimplex._crash_workspace(initial,()->done[])\n',before='        AA_COUNTS[3]+=1\n',after=''),dict(anchor='@testset "Crash fallback observer preserves initial ownership after work merge" begin\n',before='',after='    AA_COUNTS[4]+=1\n'),dict(anchor='    return checks\n',before=record,after='')]
e=suffix
for p in ins:
 assert e.count(p['anchor'])==1;e=e.replace(p['anchor'],p['before']+p['anchor']+p['after'])
i=e
for p in reversed(ins):i=i.replace(p['before']+p['anchor']+p['after'],p['anchor'])
assert i==suffix
save('insertions.toml','\n'.join('[[insertions]]\n'+''.join(k+' = '+json.dumps(v)+'\n' for k,v in p.items()) for p in ins));save('expected-suffix.jl',e)
schema=json.loads((Y/'schema.json').read_text());dump('schema.json',schema)
expected=dict(candidate=sha(cand),prefix=sha(old),suffix=sha(suffix.encode()),executed=sha(e.encode()),checks=schema['checks'])
save('expected.toml',''.join(k+' = '+json.dumps(v)+'\n' for k,v in expected.items()))
driver=(U/'driver.jl').read_text().replace('U_','AA_').replace('u_instrument','aa_instrument').replace('u_run','aa_run').replace('7647','4774').replace('7648','4775').replace('simplex_precision_tests.jl','simplex_start_state_tests.jl').replace('zeros(Int,3) # case entry, initializer entry, testset entry','zeros(Int,4) # case, INITIAL setup, crash, testset entries')
a=driver.index('function u_work_record');b=driver.index('function aa_run')
driver=driver[:a]+'''function aa_record_dict(x)
    names=("iterations","refactorizations","crash_pivot","refactor_other","crash_fallback","crash_accepted","callbacks")
    return Dict(names[i]=>x[i] for i in 1:7)
end
function aa_save_case(x)
    path=joinpath(AA_OUT,"case.toml")
    ispath(path) && error("case already exists")
    open(path,"w") do io
        TOML.print(io,x)
    end
end
'''+driver[b:]
driver=driver.replace('S5-U focused actual supplied-basis stop test','S5-AA focused actual crash fallback observer test').replace('[1,1,1]','[1,1,1,1]').replace('collect(string.(keys(AA_RECORD[].checks)))==AA_EXPECTED["checks"]','Set(keys(AA_RECORD[]["checks"]))==Set(AA_EXPECTED["checks"])')
a=driver.index('        if !isnothing(AA_RECORD[])');b=driver.index('        tc=isnothing(result)',a);driver=driver[:a]+driver[b:]
save('driver.jl',driver)
checks=dict(prefix_exact=cand[:4774]==old,inverse_exact=i==suffix,explicit_import='using LinearAlgebra: SingularException\n' in suffix,one_case=suffix.count('checks = crash_fallback_observer_checks()')==1,one_setup=suffix.count('JSimplex.initialize_workspace(')==1,one_crash=suffix.count('JSimplex._crash_workspace(')==1,one_testset=suffix.count('@testset')==1,fifty_assertions=suffix.count('@test checks.')==50,all_names=re.findall(r'@test checks\.(\w+)',suffix)==schema['checks'],five_insertions=len(ins)==5,raw_before_tests=e.index('aa_save_case(output)')<e.index('@testset'),guard_identical=(H/'guard.py').read_bytes()==(Y/'guard.py').read_bytes(),actual_unchanged=(R/'test/simplex_start_state_tests.jl').read_bytes()==old)
dump('source-preparation.json',dict(checks=checks,all_passed=all(checks.values()),sha256={str(H/n):sha((H/n).read_bytes()) for n in ['prepare.py','original-test.jl','guard.py','guard-source.json','driver.jl','insertions.toml','expected.toml','expected-suffix.jl','schema.json']}));assert all(checks.values());print('13 source checks PASS; five inverse-bound insertions; no Julia or actual test edit')
