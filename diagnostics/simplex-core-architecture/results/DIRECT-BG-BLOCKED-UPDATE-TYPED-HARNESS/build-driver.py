from pathlib import Path
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');B=R/'diagnostics/simplex-core-architecture/results';D=B/'DIRECT-BG-BLOCKED-UPDATE-TYPED-HARNESS';F=B/'DIRECT-BG-BLOCKED-UPDATE-HARNESS'
s=(F/'driver.jl').read_text()
s=s.replace('# UNEXECUTED. All modules loaded at top level before main; no eval/invokelatest workaround.','# OFFLINE prepared. All includes remain at top level before main.\nconst LOAD_STATS=Base.gc_num()\nconst LOAD_START=time_ns()\nBase.cumulative_compile_timing(true)\nconst LOAD_COMPILE=Base.cumulative_compile_time_ns()')
s=s.replace('include(joinpath(C,"panel.jl"))\ninclude(joinpath(C,"factor.jl"))\ninclude(joinpath(C,"panel-fault.jl"))\ninclude(joinpath(C,"factor-fault.jl"))','const PANEL_LOAD=@timed begin\n    include("panel.jl")\n    include("factor.jl")\n    include("panel-fault.jl")\n    include("factor-fault.jl")\nend')
s=s.replace('include("panel-tests.jl")\ninclude("numerical-tests.jl")\ninclude("lifecycle-tests.jl")','const TESTS_LOAD=@timed begin\n    include("panel-tests.jl")\n    include("numerical-tests.jl")\n    include("lifecycle-tests.jl")\nend\nconst LOAD_DIFF=Base.GC_Diff(Base.gc_num(),LOAD_STATS)\nconst LOAD_SECONDS=(time_ns()-LOAD_START)/1e9\nconst LOAD_COMPILE_DIFF=Base.cumulative_compile_time_ns().-LOAD_COMPILE\nBase.cumulative_compile_timing(false)\nmetrics(t)=Dict("seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),\n    "gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time)')
s=s.replace('function main()','function measured_unit!(body,index,name)\n    t=@timed unit!(body,index,name)\n    save("cost-$index.toml",metrics(t))\n    t.value\nend\nfunction main()')
s=s.replace('raw=Dict{String,Any}', 'require(isdir(OUTPUT) && isempty(readdir(OUTPUT)),"Need empty reserved payload")\n    raw=Dict{String,Any}',1)
s=s.replace('println(stderr,"BEGIN BG blocked U driver ",PHASE);flush(stderr)', '''save("load.toml",Dict("seconds"=>LOAD_SECONDS,"bytes"=>LOAD_DIFF.allocd,
          "events"=>Base.gc_alloc_count(LOAD_DIFF),"gc_seconds"=>LOAD_DIFF.total_time/1e9,
          "compile_seconds"=>LOAD_COMPILE_DIFF[1]/1e9,"recompile_seconds"=>LOAD_COMPILE_DIFF[2]/1e9))
        save("panel-load.toml",metrics(PANEL_LOAD));save("tests-load.toml",metrics(TESTS_LOAD))
        println(stderr,"BEGIN BG blocked U driver ",PHASE);flush(stderr)''')
s=s.replace('total .+= unit!(', 'total .+= measured_unit!(')
with (D/'driver.jl').open('x') as f:f.write(s)
# Pure numerical oracle: preserve original formulas, strengthen fixed panel tree and failure/log validation.
s=(F/'oracle.py').read_text();s=s.replace(' return d\n\ndef unit',' d.update({f\'P{i:03d}\':1 for i in range(95,103)})\n return d\n\ndef unit',1)
s=s.replace('def unit(row,index,schedule,mode):\n','def unit(row,index,schedule,mode):\n need(mode in (\'red\',\'green\'),\'Mode\')\n need(type(row) is dict,\'Unit type\')\n',1)
s=s.replace("need(r['sites']==sparse(expected),'Exact event-conditioned assertion counts')","need(r['sites']==sparse(expected),'Exact event-conditioned assertion counts')\n if index==1:\n  need([tree(x) for x in row['tests']['children']]==[[31,0,0,0],[11619,0,0,0],[74,0,0,0],[44,0,0,0]],'Exact repaired panel group totals')")
s=s.replace("def test_results(raw,rows,schedule,loaded,phase):\n","def test_results(raw,rows,schedule,loaded,phase):\n need(phase in ('red300','green300'),'Phase')\n",1)
s+='''

PREPARATION=('load.toml','panel-load.toml','tests-load.toml')+tuple(f'cost-{i}.toml' for i in range(1,29))
PAYLOAD=set(PREPARATION)|{'raw.toml'}|{f'unit-{i}.toml' for i in range(1,29)}
METRICS={'seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds'}
def metrics(v):
 need(type(v) is dict and set(v)==METRICS,'Metric fields')
 need(all(type(v[k]) is int and 0<=v[k]<=2**63-1 for k in ('bytes','events')),'Integral allocation counters')
 need(all(type(v[k]) in (int,float) and math.isfinite(v[k]) and 0<=v[k]<=300 for k in METRICS-{'bytes','events'}),'Finite bounded cost times')
 return v

def validate(payload,schedule,loaded,phase):
 need(type(payload) is dict and set(payload)==PAYLOAD,'Exact 60 payload files')
 prep={n:metrics(payload[n]) for n in PREPARATION}
 rows={f'unit-{i}.toml':payload[f'unit-{i}.toml'] for i in range(1,29)}
 result=test_results(payload['raw.toml'],rows,schedule,loaded,phase)
 result['preparation']=prep
 result['scope']='Structural, lifecycle and stream qualification with typed P011; overlapping cold costs, no Task3 performance claim'
 return result

def warning_log(log,payload=None,phase=None):
 # Never exempt warning/error text merely because it occurs in a failure rendering.
 if re.search(r'warning|world.?age|method.*overwrit|LoadError|ERROR:|OutOfMemoryError|Test Error|FATAL|GROUP/COUNT MISMATCH',log,re.I):return True
 if payload is None:return bool(re.search(r'Test Failed|TEST FAILURE',log,re.I))
 if phase not in ('red300','green300'):return True
 failures=[]
 for i in range(1,29):
  u=payload[f'unit-{i}.toml']
  if log.count(f"UNIT BEGIN {i} {u['name']}\\n")!=1 or log.count(f"UNIT END {i} {u['name']}\\n")!=1:return True
  failures.extend(u['records']['failures'])
 if len(failures)!=(6 if phase=='red300' else 0):return True
 for f in failures:
  detail=f['detail']
  if f['site']!='N026' or f['kind']!='fail' or not detail or len(detail)>4096:return True
  if re.search(r'warning|world.?age|method.*overwrit|LoadError|ERROR:|OutOfMemoryError|Test Error|TEST FAILURE',detail,re.I):return True
  if detail.count('Test Failed')!=1 or 'minimum_panels' not in detail or 'observed' not in detail:return True
  token='TEST FAILURE: N026 '+detail
  # The same assertion rendering can occur in each of six stream units.
  if token not in log:return True
  log=log.replace(token,'',1)
 return bool(re.search(r'Test Failed|Test Error|TEST FAILURE',log,re.I))
'''
with (D/'oracle.py').open('x') as f:f.write(s)
print('Saved new driver and complete oracle')
