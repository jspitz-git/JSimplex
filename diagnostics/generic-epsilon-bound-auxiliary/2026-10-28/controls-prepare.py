from pathlib import Path
import sys,json,shutil,itertools
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-epsilon-bound-auxiliary/2026-10-28');O=D.parents[1]/'generic-unit-perturb-residual/2026-10-28';sys.path.insert(0,str(D));import common as c
s=(D/'fixtures.jl').read_text()
needle='  if T===BigFloat\n'
insert='''  for scope in (:errors,:direction)
   scope===:direction&&!(T<:AbstractFloat)&&continue
   a=fixture(T,0,:sparse,:positive,scope;mode=scope===:errors ? :free : :good);b=fixture(T,0,:sparse,:positive,scope;mode=scope===:errors ? :free : :good)
   r=checkpair(a,b,scope===:direction ? :A : :B);@test r[1]===:value
   @test scope===:direction ? r[2]===true : all(iszero,r[2])
  end
  if T===Float64||T===BigFloat
   for tag in (Val(:original),Val(:C))
    sentinel=ErrorException("EBA observer sentinel");held=Ref{Any}(nothing)
    observer=(reason,ws)->begin
     if reason===:refactor_other;held[]=ws;throw(sentinel);end
     nothing
    end
    a=fixture(T,8,:sparse,:positive,:auxiliary;observer);before=deepcopy(inputvalues(a));reset!(a)
    caught=try;whole(tag,a);nothing;catch e;e;end
    @test caught isa J.DiagnosticObserverFailure&&caught.cause===sentinel
    @test a.budget[].refactorizations>=1
    @test !isnothing(held[])&&held[].basis.basic_indices!==a.w.basis.basic_indices&&held[].basis.states!==a.w.basis.states
    @test same(before,inputvalues(a))
   end
  end
'''
c.need(s.count(needle)==1,'insertion');s=s.replace(needle,insert+needle);(D/'fixtures.jl').write_text(s)
contexts=[f'BF{bits}_{mode}' for bits in [64,128,256] for mode in ['Nearest','Down','Up','ToZero','FromZero']]+['Float32','Float64','Rational{BigInt}','Rational{Int64}']
grid=[]
for context in contexts:
 if not context.startswith('Rational'):
  for n,density,shape,mode in itertools.product([16,64],['sparse','dense'],['positive','negative','mixed'],['good','bad']):grid.append(dict(context=context,variant='A',scope='direction',n=n,density=density,shape=shape,mode=mode))
 modes=['free','lower','box','fixed','mixed']+(['native_free','native_mixed'] if context.startswith('BF') else [])
 for n,mode,shape in itertools.product([16,64],modes,['positive','negative','mixed']):grid.append(dict(context=context,variant='B',scope='errors',n=n,density='sparse',shape=shape,mode=mode))
 for n,density in itertools.product([8,16],['sparse','dense']):grid.append(dict(context=context,variant='C',scope='auxiliary',n=n,density=density,shape='positive',mode='good'))
for i,g in enumerate(grid):g['id']=f'EBA{i+1:04}'
c.put('expected-cases.json',grid)
with (D/'grid.toml').open('x') as f:
 for g in grid:
  f.write('[[cells]]\n');f.writelines(f'{k} = {json.dumps(v)}\n' for k,v in g.items())
driver=(O/'driver-qualified.jl').read_text().replace('fixtures-qualified.jl','fixtures.jl').replace('Unit perturb residual whole-function comparison','Epsilon bound auxiliary whole-function comparison').replace('UNIT_PERTURB_RESIDUAL_COMPLETE','EPSILON_BOUND_AUXILIARY_COMPLETE')
old='  if spec["scope"] in ("dual","primal");@test T<:Rational ? z["result"]==0 : z["result"]>0;end'
new='  if spec["scope"]=="direction";@test z["result"]===(spec["mode"]=="good");end\n  if spec["scope"]=="auxiliary";@test z["result"]==Int(J.OPTIMAL);end'
c.need(old in driver,'driver checksum');driver=driver.replace(old,new);(D/'driver.jl').write_text(driver)
audit=(O/'audit-qualified.py').read_text().replace('common_qualified','common').replace('contract-qualified.json','contract.json').replace('pins-qualified.json','pins.json').replace('audit-qualified.py','audit.py').replace('Unit perturb residual whole-function comparison','Epsilon bound auxiliary whole-function comparison').replace('UNIT_PERTURB_RESIDUAL_COMPLETE','EPSILON_BOUND_AUXILIARY_COMPLETE')
old="    if spec['scope'] in ['dual','primal']:need(type(w['result']) is int and (w['result']==0 if spec['context'].startswith('Rational') else w['result']>0),'row index checksum')\n    else:need(type(w['result']) is float and math.isfinite(w['result']),'float result checksum')"
new="    if spec['scope']=='direction':need(type(w['result']) is bool and w['result']==(spec['mode']=='good'),'direction Boolean result')\n    elif spec['scope']=='auxiliary':need(type(w['result']) is int and w['result']==con['optimal_status'],'whole auxiliary optimal status')\n    else:need(type(w['result']) is float and math.isfinite(w['result']),'finite metric checksum')"
c.need(old in audit,'audit checksums');audit=audit.replace(old,new).replace("elapsed_shared_seconds=sup['elapsed_seconds']","elapsed_shared_seconds=read('completed.json')['elapsed_shared_seconds']")
(D/'audit.py').write_text(audit)
shutil.copyfile(__file__,D/'controls-prepare.py')
cmd=c.read(str(O/'contract-qualified.json'))['command'];cmd[-2:]=[str(D/'driver.jl'),str(D/'output/results.toml')]
c.put('contract.json',dict(command=cmd,attempts=1,contexts=19,cases=len(grid),measured_windows=len(grid)*18,optimal_status=0,expected_exit=0,shared_limit_seconds=900,guard_limit_seconds=892,baseline=c.TARGET,ordinary_Test=True))
counts={a:sum(v['variant']==a for v in grid) for a in ['A','B','C']}
with (D/'CALL-BUDGET.md').open('x') as f:
 f.write(f'''# Fixed comparison call ledger\n\n{len(grid)} cells, {counts}, {len(grid)*18} measured windows. Each cell has two initial calls, six warm calls, two precheck calls, eighteen measured calls and two postcheck calls: thirty whole calls, or {counts['C']*30} actual auxiliary invocations for C benchmark cells. Context correctness is separate and all its costs are recorded. No hidden constructor-only substitute. All time, GC, compile, bytes/events are recorded per window and fixture/reset/validation/consumption preparation remains separate.\n\nC uses valid transferred bases and zero objectives. Each successful invocation retains the real factor setup, recompute/reliability, auxiliary solve, original witness, finally budget sync and diagnostics merge. Counted budget outputs are compared; factory/native internal solve counts are not a complete PREforward/native/import budget. The observer throw tests exercise actual factor setup and event wrapping before auxiliary assignment; early stop tests exercise all-nothing return and unchanged parent inputs.\n\nFor A only AbstractFloat has a method. Rational controls are covered by B/C without inventing an A dispatch. B includes native Float64 bounds with BigFloat residual metrics.\n''')
print(json.dumps(dict(cells=len(grid),counts=counts,windows=len(grid)*18)))
