from pathlib import Path
import json,hashlib
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
E=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-ZERO-COUNTS-HARNESS'
P=E.with_name('DIRECT-BG-P011-HARNESS');C=E.with_name('DIRECT-BG-ZERO-COUNTS-CANDIDATE');F=E.with_name('DIRECT-BG-BLOCKED-UPDATE-RED2-HARNESS')
def put(n,s):
 with (E/n).open('x') as f:f.write(s)
def js(n,v):put(n,json.dumps(v,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
copied={}
for n in ['guard.py','supervisor.py','post-return.py','baseline.json','runtime-inputs-complete.json','stages.json','environment.json','loaded-paths.json']:
 put(n,(P/n).read_text());copied[n]=dict(source=str(P/n),sha256=sha(P/n))
js('copied-files.json',copied)
h=json.loads((P/'runs/p011-300/outer-closure.json').read_text())['host']
js('historical-groups.json',dict(groups=h['groups'],source=str(P/'runs/p011-300/outer-closure.json'),sha256=sha(P/'runs/p011-300/outer-closure.json')))
for n in ['control.py','outer.py','seal.py','launch.py','audit.py']:
 s=(P/n).read_text().replace('p011-300','zero-counts-300').replace('P011 diagnostic harness preparation','BG zero-count harness preparation').replace('P011 diagnostic exact-run admission','BG zero-count exact-run admission').replace('ab931f468070b0cb5f3324c65fc58547d79faffb','716b7ecfd6df6172edaf19cb21e6446c08bf29b0')
 s=s.replace("str(PROBE/'driver.jl')","str(D/'driver.jl')").replace("PROBE=D.with_name('DIRECT-BG-P011-DIAGNOSTIC')","PROBE=D.with_name('DIRECT-BG-ZERO-COUNTS-CANDIDATE')")
 s=s.replace('Only separately prepared P011300 is allowed','Only separately prepared zero-counts-300 is allowed').replace('P011 diagnostic phase','zero-count diagnostic phase').replace('Saved P011 diagnostic integrity/results','Saved zero-count diagnostic integrity/results')
 if n=='control.py':
  s=s[:s.index('def validate_probe():')]+'''def validate_probe():
 v=rd(PROBE/'review.json')
 require(v.get('accepted') is True and v.get('findings')==[] and bindings(v),'Candidate independent review')
 require(sha(PROBE/'panel.jl')=='19dccf0d5259d730b19333b2b1c685a50ee76f93d2cc3b242cb54a762cae9295','Frozen candidate')
 require(sha(PROBE/'zero-counts-tests.jl')=='927789cf6260b52694bdc258529696a62af3ab338744a32b4564dd6aad0dae6f','Frozen candidate tests')
'''
 put(n,s)
old=(E.with_name('DIRECT-BG-P011-DIAGNOSTIC')/'driver.jl').read_text()
state=old[old.index('function state('):old.index('function metrics(')]
operations='''# Included once into each distinct side module. All Julia text UNEXECUTED.
const K = BGBlockedPanel
const T = BGBlockedPanelTests
const Carrier = T.Carrier
const Decision = K.BGPanelDecision
const Z = (0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)
require(ok,text) = ok || error(text)
zero_value(f::Carrier) = K.counts(K.BGNoCounts())
dimension_value(f::Carrier)::Decision = K._bgb_dimensions(length(f.upper),1)
eligibility_value(f::Carrier)::Decision = K._bgb_eligibility(f,1)
valuefun(::Val{:zeros}) = zero_value
valuefun(::Val{:dimensions}) = dimension_value
valuefun(::Val{:eligibility}) = eligibility_value
valuefun(::Val{:original}) = eligibility_value
function inner_bytes(kind, input::Carrier, replacement::Carrier)
    (Base.allocated(valuefun(kind),input), true)
end
function inner_events(kind, input::Carrier, replacement::Carrier)
    (Base.allocations(valuefun(kind),input), true)
end
# Reduced original-shaped capture; NOT the frozen P011 compiled caller.
function inner_bytes(::Val{:original},input::Carrier,replacement::Carrier)
    f=input
    K._bgb_eligibility(f,1)
    b=@allocated K._bgb_eligibility(f,1)
    f=replacement
    (b,f===replacement)
end
function inner_events(::Val{:original},input::Carrier,replacement::Carrier)
    f=input
    K._bgb_eligibility(f,1)
    e=@allocations K._bgb_eligibility(f,1)
    f=replacement
    (e,f===replacement)
end
function consume!(kind,sink,f::Carrier)
    sink[]=valuefun(kind)(f)
    nothing
end
function observed(::Val{:zeros},v)
    Dict("counters"=>collect(v))
end
function observed(kind,v::Decision)
    Dict("start"=>v.start,"count"=>v.count,"accepted"=>v.accepted,
         "reason"=>string(v.reason),"finite"=>v.finite,"counters"=>collect(v.counters))
end
function correct(::Val{:zeros},v)
    v===Z
end
function correct(kind,d::Decision)
    d.start==1 && d.count==0 && !d.accepted && d.reason===:dimensions && d.finite && d.counters==Z
end
'''+state+'''
function setup()
    input=T.carrier(zeros(32,32))
    replacement=T.carrier(T.denseband(64))
    (input=input,replacement=replacement,zero_sink=Ref(Z),decision_sink=Ref(Decision(0,0,false,:uninitialized,false,Z)))
end
sinkfor(::Val{:zeros},s)=s.zero_sink
sinkfor(kind,s)=s.decision_sink
function metrics(t)
    Dict("seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),
      "gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time)
end
function sample(kind,s)
    sink=sinkfor(kind,s)
    b=@timed inner_bytes(kind,s.input,s.replacement)
    e=@timed inner_events(kind,s.input,s.replacement)
    c=@timed consume!(kind,sink,s.input)
    Dict("inner_bytes"=>b.value[1],"inner_events"=>e.value[1],
      "assignment_ok"=>(b.value[2] && e.value[2]),"decision_ok"=>correct(kind,sink[]),
      "observed"=>observed(kind,sink[]),"bytes_wrapper"=>metrics(b),
      "events_wrapper"=>metrics(e),"consumed_result"=>metrics(c))
end
'''
put('operations.jl',operations)
for side in ['Reference','Candidate']:
 panel=R/'diagnostics/direct-bg-blocked-update/reproduce/panel.jl' if side=='Reference' else C/'panel.jl'
 s=f'''module BGZero{side}
import ..JSimplex
import ..HarnessRecords
include({json.dumps(str(panel))})
include({json.dumps(str(F/'panel-tests.jl'))}) # definitions only
'''
 if side=='Candidate':s+=f'include({json.dumps(str(C/"zero-counts-tests.jl"))})\n'
 s+='include(joinpath(@__DIR__,"operations.jl"))\nend\n';put(side.lower()+'-side.jl',s)
put('driver.jl','''# Offline prepared driver; top-level includes prevent runtime world-age crossings.
const LOAD_STATS=Base.gc_num()
const LOAD_START=time_ns()
Base.cumulative_compile_timing(true)
const LOAD_COMPILE=Base.cumulative_compile_time_ns()
using Test,LinearAlgebra,TOML,JSimplex
'''+f'include({json.dumps(str(F/"recorder.jl"))}) # ONE custom Test API owner\n'+'''const REFERENCE_LOAD=@timed include(joinpath(@__DIR__,"reference-side.jl"))
const CANDIDATE_LOAD=@timed include(joinpath(@__DIR__,"candidate-side.jl"))
const LOAD_DIFF=Base.GC_Diff(Base.gc_num(),LOAD_STATS)
const LOAD_SECONDS=(time_ns()-LOAD_START)/1e9
const LOAD_COMPILE_DIFF=Base.cumulative_compile_time_ns().-LOAD_COMPILE
Base.cumulative_compile_timing(false)
module ZeroDriver
using ..Test,..TOML
import ..JSimplex,..BGZeroReference,..BGZeroCandidate,..HarnessRecords
const A=BGZeroReference
const B=BGZeroCandidate
require(ok,text)=ok || error(text)
metrics(t)=A.metrics(t)
function save(output,name,v)
    p=joinpath(output,name)
    ispath(p) && error("Existing output: "*p)
    open(p,"w") do io
        TOML.print(io,v;sorted=true);flush(io)
    end
end
function tests()
    HarnessRecords.reset!()
    t=@testset HarnessRecords.Capture "zero-count candidate" begin
        B.BGZeroCountsTests.run_zero_counts_tests()
    end
    Dict("tree"=>HarnessRecords.dictionary(t),"failure_count"=>HarnessRecords.failure_count[],
         "failures"=>copy(HarnessRecords.failures))
end
function tests_ok(t)
    tree=t["tree"]
    expected=(7,300,10,26,7)
    t["failure_count"]==0 && isempty(t["failures"]) &&
      all(tree[k]==0 for k in ("pass","fail","error","broken")) &&
      length(tree["children"])==5 && all(
        c["pass"]==p && all(c[k]==0 for k in ("fail","error","broken")) && isempty(c["children"])
        for (c,p) in zip(tree["children"],expected))
end
function main(output,project,load_record)
    require(isdir(output) && isempty(readdir(output)),"Need reserved empty output")
    raw=Dict{String,Any}("schema"=>1,"complete"=>false,"fatal"=>"",
      "qualification"=>"zero_counts_diagnostic","records"=>Any[])
    try
        require(realpath(pathof(JSimplex))==realpath(joinpath(project,"src/JSimplex.jl")),"Wrong stage")
        require(Threads.nthreads()==1 && Main.LinearAlgebra.BLAS.get_num_threads()==1,"Threads")
        raw["loaded"]=Dict(string(nameof(m))=>realpath(pathof(m)) for m in
          (JSimplex,Main.Test,Main.LinearAlgebra,TOML))
        save(output,"load.toml",load_record)
        save(output,"reference-load.toml",metrics(Main.REFERENCE_LOAD))
        save(output,"candidate-load.toml",metrics(Main.CANDIDATE_LOAD))
        setup=@timed (A.setup(),B.setup())
        a,b=setup.value;save(output,"setup.toml",metrics(setup))
        pre=@timed (A.state(a.input),A.state(a.replacement),B.state(b.input),B.state(b.replacement))
        save(output,"snapshot-before.toml",metrics(pre))
        schedule=[("first",0,1),("first",0,2),("warm",0,2),("warm",0,1)]
        for pair in 1:4, side in (isodd(pair) ? (1,2) : (2,1))
            push!(schedule,("sample",pair,side))
        end
        index=0
        for kind in (Val(:zeros),Val(:dimensions),Val(:eligibility),Val(:original))
            name=string(typeof(kind).parameters[1])
            for (phase,pair,side) in schedule
                index+=1
                row=side==1 ? A.sample(kind,a) : B.sample(kind,b)
                merge!(row,Dict("index"=>index,"case"=>name,"phase"=>phase,"pair"=>pair,
                  "arm"=>(side==1 ? "reference" : "candidate")))
                push!(raw["records"],row);save(output,"record-$index.toml",row)
                require(row["assignment_ok"] && row["decision_ok"],"Incorrect observed result")
            end
        end
        post=@timed (A.state(a.input),A.state(a.replacement),B.state(b.input),B.state(b.replacement))
        save(output,"snapshot-after.toml",metrics(post))
        raw["input_unchanged"]=A.unchanged(pre.value[1],post.value[1]) && B.unchanged(pre.value[3],post.value[3])
        raw["replacement_unchanged"]=A.unchanged(pre.value[2],post.value[2]) && B.unchanged(pre.value[4],post.value[4])
        require(raw["input_unchanged"] && raw["replacement_unchanged"],"Input mutation")
        tc=@timed tests()
        save(output,"tests-cost.toml",metrics(tc));save(output,"tests.toml",tc.value)
        raw["tests"]=tc.value
        require(tests_ok(tc.value),"Structural tests failed")
        raw["complete"]=true
    catch e
        raw["fatal"]=sprint(showerror,e,catch_backtrace())
    finally
        save(output,"raw.toml",raw)
    end
    raw["complete"] || exit(2)
end
end
length(ARGS)==2 || error("Expected payload and stage")
ZeroDriver.main(ARGS[1],ARGS[2],Dict("seconds"=>LOAD_SECONDS,"bytes"=>LOAD_DIFF.allocd,
  "events"=>Base.gc_alloc_count(LOAD_DIFF),"gc_seconds"=>LOAD_DIFF.total_time/1e9,
  "compile_seconds"=>LOAD_COMPILE_DIFF[1]/1e9,"recompile_seconds"=>LOAD_COMPILE_DIFF[2]/1e9))
''')
put('oracle.py','''"""Pure strict zero-count payload oracle; no process or Julia work."""
import math,re,statistics
METRICS={'seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds'}
PREPARATION=('load.toml','reference-load.toml','candidate-load.toml','setup.toml','snapshot-before.toml','snapshot-after.toml','tests-cost.toml')
CASES=('zeros','dimensions','eligibility','original')
BASE=[('first',0,'reference'),('first',0,'candidate'),('warm',0,'candidate'),('warm',0,'reference')]
for pair in range(1,5):
 for arm in (('reference','candidate') if pair%2 else ('candidate','reference')):BASE.append(('sample',pair,arm))
SCHEDULE=[(case,*v) for case in CASES for v in BASE]
PAYLOAD=set(PREPARATION)|{'raw.toml','tests.toml'}|{f'record-{i}.toml' for i in range(1,49)}
NAMES=('zero statistics retain their complete immutable contract','independent mutable counters and checked overflow at every slot','peak replaces only its owning counter tuple','dimension decisions preserve all fields and boundaries','cheap eligibility returns zero decision without touching counters')
COUNTS=(7,300,10,26,7)
def require(v,m):
 if not v:raise ValueError(m)
def integer(v):return type(v) is int and 0<=v<=2**63-1
def number(v):return type(v) in (int,float) and math.isfinite(v) and 0<=v<=300
def metrics(v):
 require(type(v) is dict and set(v)==METRICS,'Metric fields')
 require(all(integer(v[k]) for k in ('bytes','events')),'Integral counters')
 require(all(number(v[k]) for k in METRICS-{'bytes','events'}),'Finite bounded times')
 return dict(v)
def suite(v):
 require(type(v) is dict and set(v)=={'tree','failure_count','failures'},'Suite fields')
 require(type(v['failure_count']) is int and v['failure_count']==0 and v['failures']==[],'Test failures')
 def node(x,name,count):
  require(type(x) is dict and set(x)=={'name','pass','fail','error','broken','children'},'Test node fields')
  require(x['name']==name and type(x['children']) is list,'Test name/children')
  require(all(type(x[k]) is int and x[k]==(count if k=='pass' else 0) for k in ('pass','fail','error','broken')),'Exact test counts')
 t=v['tree'];node(t,'zero-count candidate',0);require(len(t['children'])==5,'Five suites')
 for x,name,count in zip(t['children'],NAMES,COUNTS):node(x,name,count);require(x['children']==[],'Leaf suite')
 return v
def row(v,index):
 keys={'index','case','phase','pair','arm','inner_bytes','inner_events','assignment_ok','decision_ok','observed','bytes_wrapper','events_wrapper','consumed_result'}
 require(type(v) is dict and set(v)==keys,'Record fields')
 case,phase,pair,arm=SCHEDULE[index-1]
 require(type(v['index']) is int and v['index']==index and type(v['pair']) is int and v['pair']==pair and (v['case'],v['phase'],v['arm'])==(case,phase,arm),'Record schedule')
 require(v['assignment_ok'] is True and v['decision_ok'] is True,'Decision/assignment')
 require(integer(v['inner_bytes']) and integer(v['inner_events']),'Inner counters')
 for k in ('bytes_wrapper','events_wrapper','consumed_result'):metrics(v[k])
 obs=v['observed'];expected={'counters':[0]*20}
 if case!='zeros':expected.update(start=1,count=0,accepted=False,reason='dimensions',finite=True)
 require(type(obs) is dict and set(obs)==set(expected) and obs==expected,'Observed complete result')
 require(type(obs['counters']) is list and all(type(x) is int for x in obs['counters']),'Counter integer type')
 if case!='zeros':require(type(obs['start']) is int and type(obs['count']) is int and obs['accepted'] is False and obs['finite'] is True,'Decision field types')
 return v
def warning_log(log):return bool(re.search(r'warning|world[ -]?age|method.*overwrit|LoadError|ERROR:|OutOfMemoryError|Test Failed|Test Error|TEST FAILURE',log,re.I))
def validate(payload,loaded):
 require(type(payload) is dict and set(payload)==PAYLOAD,'Exact57 payload')
 prep={n:metrics(payload[n]) for n in PREPARATION};test=suite(payload['tests.toml'])
 raw=payload['raw.toml'];keys={'schema','complete','fatal','qualification','records','loaded','input_unchanged','replacement_unchanged','tests'}
 require(type(raw) is dict and set(raw)==keys,'Raw fields')
 require(type(raw['schema']) is int and raw['schema']==1 and raw['complete'] is True and raw['fatal']=='','Incomplete/fatal')
 require(raw['qualification']=='zero_counts_diagnostic' and type(raw['loaded']) is dict and raw['loaded']==loaded,'Qualification/path')
 require(raw['input_unchanged'] is True and raw['replacement_unchanged'] is True,'Input/owner mutation')
 require(suite(raw['tests'])==test,'Raw suite mismatch')
 require(type(raw['records']) is list and len(raw['records'])==48,'48 records')
 rows=[]
 for i in range(1,49):
  v=row(payload[f'record-{i}.toml'],i);row(raw['records'][i-1],i)
  require(v==raw['records'][i-1],'Raw/file mismatch');rows.append(v)
 summaries={}
 for case in CASES:
  sides={}
  for arm in ('reference','candidate'):
   selected=[v for v in rows if v['case']==case and v['arm']==arm and v['phase']=='sample']
   clean=[v['index'] for v in selected if all(v[k][f]==0 for k in ('bytes_wrapper','events_wrapper','consumed_result') for f in ('compile_seconds','recompile_seconds','gc_seconds'))]
   sides[arm]=dict(inner_bytes=[v['inner_bytes'] for v in selected],inner_events=[v['inner_events'] for v in selected],consumed_seconds=[v['consumed_result']['seconds'] for v in selected],clean_wrapper_indices=clean)
  summaries[case]=sides
 return dict(records=rows,preparation=prep,tests=test,descriptive_sample_counters=summaries,source_schedule_invocations=168,
  qualification='zero_counts_diagnostic',structural_assertions=350,p011_accepted=False,red_accepted=False,
  scope='Four samples per side/case, distinct byte/event/consumed executions. No automatic speedup or allocation threshold; nonzero compile and GC retained. Structural tests required. Loading records overlap total load.')
''')
# Adapt the saved pure synthetic tests into a NEW script, never rerun old evidence.
s=(P/'tests_reviewed.py').read_text().replace('p011-300','zero-counts-300').replace('P011 diagnostic exact-run admission','BG zero-count exact-run admission').replace("str(c.PROBE/'driver.jl')","str(c.D/'driver.jl')").replace('tests_reviewed.py','tests.py').replace('tests-reviewed.json','tests.json').replace('range(1,13)','range(1,49)')
start=s.index('def fixture():');end=s.index('p=fixture();',start)
s=s[:start]+'''def fixture():
 rows=[]
 for i,(case,phase,pair,arm) in enumerate(o.SCHEDULE,1):
  obs=dict(counters=[0]*20)
  if case!='zeros':obs.update(start=1,count=0,accepted=False,reason='dimensions',finite=True)
  rows.append(dict(index=i,case=case,phase=phase,pair=pair,arm=arm,observed=obs,inner_bytes=16 if arm=='reference' else 0,inner_events=1 if arm=='reference' else 0,assignment_ok=True,decision_ok=True,bytes_wrapper=metric(),events_wrapper=metric(),consumed_result=metric()))
 def node(name,count):return dict(name=name,**{'pass':count,'fail':0,'error':0,'broken':0,'children':[]})
 tree=node('zero-count candidate',0);tree['children']=[node(n,c) for n,c in zip(o.NAMES,o.COUNTS)]
 suite=dict(tree=tree,failure_count=0,failures=[])
 p={name:metric() for name in o.PREPARATION};p['tests.toml']=suite
 p.update({f'record-{i}.toml':deepcopy(v) for i,v in enumerate(rows,1)})
 p['raw.toml']=dict(schema=1,complete=True,fatal='',qualification='zero_counts_diagnostic',records=rows,loaded=LOADED.copy(),input_unchanged=True,replacement_unchanged=True,tests=deepcopy(suite))
 return p
'''+s[end:]
s=s.replace("v['descriptive_sample_counters']['original']['clean_wrapper_indices']","v['descriptive_sample_counters']['zeros']['reference']['clean_wrapper_indices']")
pos=s.index('# Fresh one-shot check output')
s=s[:pos]+'''# Strict test-tree and observed-result mutations, both duplicated raw views changed.
for field in ('pass','fail','error','broken'):
 for index in range(5):
  q=deepcopy(p);q['tests.toml']['tree']['children'][index][field]+=1;q['raw.toml']['tests']=deepcopy(q['tests.toml'])
  refuse('suite_'+field+str(index),lambda q=q:o.validate(q,LOADED))
for i in range(1,49):
 q=deepcopy(p);q[f'record-{i}.toml']['observed']['counters'][0]=False;q['raw.toml']['records'][i-1]=deepcopy(q[f'record-{i}.toml'])
 refuse('observed_bool_'+str(i),lambda q=q:o.validate(q,LOADED))
q=deepcopy(p);q['tests.toml']['tree']['pass']=False;q['raw.toml']['tests']=deepcopy(q['tests.toml']);refuse('suite_bool',lambda:o.validate(q,LOADED))
'''+s[pos:]
put('tests.py',s)
put('prepare.py',Path(__file__).read_text())
print('prepared',len(list(E.iterdir())),'files; no Julia')
