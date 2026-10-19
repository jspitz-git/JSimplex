"""Prepare a separate, unexecuted GC-warm driver amendment. No Julia."""
from pathlib import Path
import json,hashlib,shutil
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');D=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-SPECIALIZATION-DRIVER';N=D.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-GC-PREPARATION')
def put(n,s):
 with (N/n).open('x') as f:f.write(s)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
# Text expectations are defined and evaluated before new driver creation.
old=(D/'driver.jl').read_text()
markers=['include("preparation.jl")','prepare_gc!(cell,f.name)','raw["preparation_calls"]']
put('structural-red.json',json.dumps(dict(scope='Source-only missing preparation markers, not Julia RED or allocation gate execution',expected_missing=3,actual_missing=sum(m not in old for m in markers),candidate_absent=not (N/'driver.jl').exists(),old_sha256=sha(D/'driver.jl')),indent=2)+'\n')
validator='''"""Pure offline preparation-record validation; not a full run auditor."""
import math
CELLS=('sparse32','dense32','sparse96')
PHASES=('redgc300','greengc300')
KEYS=set('phase fixture cell after_pair before_pair requested_full_gc calls cumulative_calls returned seconds bytes events gc_seconds compile_seconds recompile_seconds gc_pauses full_collections'.split())
def require(v,m):
 if not v:raise ValueError(m)
def validate_record(r,cell,phase):
 require(type(r) is dict and set(r)==KEYS,'record schema')
 require(type(cell) is int and 1<=cell<=3 and phase in PHASES,'expected identity')
 require(r['phase']==phase and r['fixture']==CELLS[cell-1],'identity')
 for key,expected in [('cell',cell),('after_pair',3),('before_pair',4),('calls',1),('cumulative_calls',cell)]:
  require(type(r[key]) is int and r[key]==expected,'schedule '+key)
 require(r['requested_full_gc'] is True and r['returned'] is True,'completed full request')
 for key in ('bytes','events','gc_pauses','full_collections'):
  require(type(r[key]) is int and r[key]>=0,'counter '+key)
 for key in ('seconds','gc_seconds','compile_seconds','recompile_seconds'):
  require(type(r[key]) is float and math.isfinite(r[key]) and r[key]>=0,'time '+key)
 # Compilation and GC may overlap; no sum or timing-subtraction oracle.
 return True
def validate_records(rows,phase,complete):
 require(type(rows) is dict and phase in PHASES and type(complete) is bool,'collection schema')
 require(0<=len(rows)<=3 and (not complete or len(rows)==3),'preparation count')
 require(set(rows)=={f'preparation-{i}.toml' for i in range(1,len(rows)+1)},'exact prefix')
 for cell in range(1,len(rows)+1):validate_record(rows[f'preparation-{cell}.toml'],cell,phase)
 return True
'''
put('preparation_schema.py',validator)
for n in ['red-kernel.jl','green-kernel.jl','recorder.jl','inputs.toml','expected-tests.toml']:
 with (N/n).open('xb') as f:f.write((D/n).read_bytes())
helper='''# UNEXECUTED preparation amendment. No factor object is accepted or retained here.
const PREPARATION_CALLS = Ref(0)
const PREPARATION_COMPLETED = Ref(0)
function prepare_gc!(cell::Int,fixture)
    require(PREPARATION_CALLS[] == PREPARATION_COMPLETED[] == cell-1,
            "Preparation order or repeated call")
    PREPARATION_CALLS[] += 1 # Attempt count survives a thrown GC/recording failure.
    measured = @timed GC.gc(true) # Exactly one fixed full request per completed warm cell.
    row = Dict{String,Any}(
        "phase"=>PHASE,"fixture"=>fixture,"cell"=>cell,
        "after_pair"=>3,"before_pair"=>4,"requested_full_gc"=>true,
        "calls"=>1,"cumulative_calls"=>PREPARATION_CALLS[],"returned"=>true,
        "seconds"=>measured.time,"bytes"=>measured.bytes,
        "events"=>Base.gc_alloc_count(measured.gcstats),"gc_seconds"=>measured.gctime,
        "compile_seconds"=>measured.compile_time,"recompile_seconds"=>measured.recompile_time,
        "gc_pauses"=>measured.gcstats.pause,"full_collections"=>measured.gcstats.full_sweep)
    save_window("preparation-$cell.toml",row)
    PREPARATION_COMPLETED[] += 1 # Completed means cost record successfully saved.
    nothing
end
'''
put('preparation.jl',helper)
new=old.replace('# UNEXECUTED Task2; ordinary stage, all definitions before main; no runtime include.','# UNEXECUTED GC preparation amendment; same lifecycle and gates, separate run admission required.',1)
new=new.replace('PHASE in ("red300","green300","red600","green600")','PHASE in ("redgc300","greengc300")',1)
anchor='end\nfunction exact_tree(root,expected)'
assert new.count(anchor)==1
new=new.replace(anchor,'end\ninclude("preparation.jl")\nfunction exact_tree(root,expected)',1)
anchor='            require(paired["reference"]["outputs"]==paired["candidate"]["outputs"] && paired["reference"]["modes"]==paired["candidate"]["modes"],"Paired output/mode mismatch")\n'
assert new.count(anchor)==1
new=new.replace(anchor,anchor+'            pair == 3 && prepare_gc!(cell,f.name)\n',1)
anchor='        raw["complete"]=true'
new=new.replace(anchor,'        require(PREPARATION_CALLS[] == PREPARATION_COMPLETED[] == 3,"Preparation count")\n'+anchor,1)
anchor='        raw["tests"]=RecordedTests.dictionary(root)'
new=new.replace(anchor,'        raw["preparation_calls"]=PREPARATION_CALLS[]\n        raw["preparations_completed"]=PREPARATION_COMPLETED[]\n'+anchor,1)
put('driver.jl',new)
put('source-map.json',json.dumps(dict(original_driver=str(D/'driver.jl'),original_sha256=sha(D/'driver.jl'),new_sha256=sha(N/'driver.jl'),copies={n:sha(N/n) for n in ['red-kernel.jl','green-kernel.jl','recorder.jl','inputs.toml','expected-tests.toml']},changes=['header','new redgc300/greengc300 phase identity','top-level preparation helper include','one pair==3 call after both warm sides and paired check','final preparation count gate','two raw finally counters'],scope='Only stated text substitutions; full inverse checked separately'),indent=2)+'\n')
print('Prepared separate driver, helper, pure schema; no Julia')
