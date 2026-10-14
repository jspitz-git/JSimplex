from pathlib import Path
import json
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-V';U=D.with_name('MA-U');S=D.with_name('MA-S-2')
def write(n,s):
 with (D/n).open('x') as f:f.write(s)
def save(n,o):write(n,json.dumps(o,indent=2)+'\n')
# A separate diagnostic-only copy adds raw route counts already asserted in U.
s=(U/'tests.jl').read_text();a='exception=ra.failure,output=ra.output)';b='exception=ra.failure,output=ra.output,route_counts=P.route_counts())';assert s.count(a)==1
s=s.replace(a,b).replace('joinpath(@__DIR__, "fixtures.toml")','joinpath(@__DIR__, "../MA-U/fixtures.toml")')
write('tests-recorded.jl',s)
cases=[]
for n,layout,scopes in [(32,'dense',['absent','equal','up','nested']),(32,'zeroheavy',['up']),(15,'dense',['up'])]:
 for scope in scopes:
  for dr in ['forward','transpose']:cases.append(dict(id=f'{n}/{layout}/{scope}/{dr}',n=n,layout=layout,scope=scope,direction=dr,eligible=n==32 and scope in ['absent','equal']))
red=[dict(id='old/'+dr,n=32,layout='dense',scope='up',direction=dr,eligible=False) for dr in ['forward','transpose']]
micro=[dict(id=x,expected=x in ['absent','keys8','equal']) for x in ['absent','keys8','equal','up','nested','upkeys64']]
save('schedule.json',dict(costs=cases,red=red,micro=micro,processes=2,warm_pairs=3,measured_pairs=7,backend_calls_per_window=4,predicate_calls_per_window=256,timer_baselines_per_process=10))
commands=json.loads((S/'commands.json').read_text())
commands={i:[*commands[i][:-3],str(D/'driver.jl'),i,str(D/f'run-{i}')] for i in ['1','2']};save('commands.json',commands)
write('guard.py',(S/'guard.py').read_text())
# Explicit static calls, no loop in measured predicate batch.
write('micro-batch.jl','''# Generated once offline; 256 explicit monomorphic noinline calls per arm.
@noinline probe(::Val{:old}) = G.old_guard()
@noinline probe(::Val{:new}) = P._dense_ma_rounding_matches()
@noinline function microbatch(tag::Val)
    total = 0
'''+''.join('    total += Int(probe(tag))\n' for _ in range(256))+'''    return total
end
''')
