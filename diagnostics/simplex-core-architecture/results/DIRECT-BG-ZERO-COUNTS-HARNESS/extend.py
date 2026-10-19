from pathlib import Path
import json,hashlib
E=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/results/DIRECT-BG-ZERO-COUNTS-HARNESS')
for n in ('operations.jl','driver.jl','oracle.py','tests.py','outer.py'):
 p=E/n
 with (E/(n+'.initial')).open('x') as f:f.write(p.read_text())
s=(E/'operations.jl').read_text().replace('zero_value(f::Carrier) =','constructor_value(f::Carrier) = K.BGPanelCounts()\nvaluefun(::Val{:constructor}) = constructor_value\nzero_value(f::Carrier) =')
s=s.replace('function observed(::Val{:zeros},v)','function observed(::Val{:constructor},v)\n    Dict("counters"=>collect(K.counts(v)))\nend\nfunction observed(::Val{:zeros},v)')
s=s.replace('function correct(::Val{:zeros},v)','correct(::Val{:constructor},v) = K.counts(v)==Z\nfunction correct(::Val{:zeros},v)')
s=s.replace('zero_sink=Ref(Z),decision_sink=', 'zero_sink=Ref(Z),counter_sink=Ref(K.BGPanelCounts()),decision_sink=')
s=s.replace('sinkfor(::Val{:zeros},s)=','sinkfor(::Val{:constructor},s)=s.counter_sink\nsinkfor(::Val{:zeros},s)=')
s=s.replace('    c=@timed consume!(kind,sink,s.input)','    previous=sink[]\n    c=@timed consume!(kind,sink,s.input)\n    obs=observed(kind,sink[])\n    if kind isa Val{:constructor}\n        obs["fresh_owner"]=sink[] !== previous\n    end')
s=s.replace('"observed"=>observed(kind,sink[])','"observed"=>obs').replace('"decision_ok"=>correct(kind,sink[])','"decision_ok"=>(correct(kind,sink[]) && (!(kind isa Val{:constructor}) || sink[] !== previous))')
(E/'operations.jl').write_text(s)
s=(E/'driver.jl').read_text().replace('(Val(:zeros),Val(:dimensions)','(Val(:zeros),Val(:constructor),Val(:dimensions)');(E/'driver.jl').write_text(s)
s=(E/'oracle.py').read_text().replace("('zeros','dimensions'","('zeros','constructor','dimensions'").replace('range(1,49)','range(1,61)').replace('Exact57','Exact69').replace('==48','==60').replace('48 records','60 records').replace("case!='zeros'","case not in ('zeros','constructor')").replace("obs=v['observed'];expected={'counters':[0]*20}","obs=v['observed'];expected={'counters':[0]*20}\n if case=='constructor':expected['fresh_owner']=True").replace("require(type(obs['counters'])", "if case=='constructor':require(obs['fresh_owner'] is True,'Distinct mutable constructor result')\n require(type(obs['counters'])").replace('source_schedule_invocations=168','source_schedule_invocations=204');(E/'oracle.py').write_text(s)
s=(E/'tests.py').read_text().replace('range(1,49)','range(1,61)').replace("case!='zeros'","case not in ('zeros','constructor')").replace('obs=dict(counters=[0]*20)','obs=dict(counters=[0]*20)\n  if case==\'constructor\':obs[\'fresh_owner\']=True').replace("'tests.py','oracle.py'","'tests-extended.py','oracle.py'").replace("D/'tests.json'","D/'tests-extended.json'")
s=s.replace('# Fresh one-shot check output',"""for value in (False,1):
 q=deepcopy(p);q['record-13.toml']['observed']['fresh_owner']=value;q['raw.toml']['records'][12]=deepcopy(q['record-13.toml'])
 refuse('constructor_fresh_'+str(value),lambda q=q:o.validate(q,LOADED))
# Fresh one-shot check output""")
with (E/'tests-extended.py').open('x') as f:f.write(s)
# Initial tested script remains unchanged. Canonical new test script is extended.
s=(E/'outer.py').read_text().replace('One explicit P011 diagnostic invocation','One explicit zero-count diagnostic invocation');(E/'outer.py').write_text(s)
with (E/'extend.py').open('x') as f:f.write(Path(__file__).read_text())
print('five cases;60records;69payload;204source calls')
