from pathlib import Path
import json,hashlib,tomllib
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');E=R/'diagnostics/simplex-core-architecture/results';D=E/'DIRECT-BG-EXPORT-SPECIALIZATION-DRIVER';H=E/'DIRECT-BG-EXPORT-WORKSPACE-DRIVER-PREPARATION';G=E/'DIRECT-BG-EXPORT-WORKSPACE-GREEN2-PREPARATION';O=E/'DIRECT-BG-EXPORT-WORKSPACE-COST-PREPARATION';C=R/'diagnostics/direct-bg-export-specialized/reproduce'
def put(n,t):
 with (D/n).open('x') as f:f.write(t)
def js(n,j):put(n,json.dumps(j,indent=2)+'\n')
def cp(n,src):
 with (D/n).open('xb') as f:f.write(src.read_bytes())
cp('prepare.py',Path(__file__))
for n in ['guard.py','supervisor.py','baseline.json','environment.json','runtime-inputs-complete.json','loaded-paths.json','recorder.jl','oracle.py'] :cp(n,H/n)
cp('analysis.py',O/'analysis.py');cp('inputs.json',O/'inputs.json');cp('inputs.toml',O/'inputs.toml')
m=json.loads((C/'overlay-manifest.json').read_text());js('stages.json',{s:{'path':m['stage'],'sha256':m['stage_sha256']} for s in ['red','green']})
# Exact existing six-clock lifecycle plus window. Different namespace only.
s=(O/'cost.jl').read_text();body=s[s.index('token(x::Float64)'):s.index('# Untimed bounded controls')]
body=body.replace('function save(name,data)','function save_window(name,data)')
for mode,ns in [('red','_bgx_'),('green','_bgxs_')]:put(mode+'-kernel.jl','# UNEXECUTED. Exact old lifecycle/window body except save name and candidate namespace.\n'+body.replace('_bgx_',ns))
old=tomllib.loads((G/'expected-tests.toml').read_text())['green'];new=[('boundary_request_equivalence',370),('boundary_hook_order',112),('boundary_hot_and_hook_agree',220)]
groups=[[g['name'],g['pass'],g['fail'],g['error'],g['broken']] for g in old['groups']]
cells=['sparse32','dense32','sparse96'];allocation=[[f'allocation_nonincrease_{n}',1,0,0,0] for n in cells]
js('expected-tests.json',{'red':{'assertions':3,'groups':[[g[0],0,1,0,0] for g in allocation]},'green':{'assertions':7935+sum(n for _,n in new)+3,'groups':groups+[[n,v,0,0,0] for n,v in new]+allocation}})
put('expected-tests.toml','[red]\nassertions = 3\n'+''.join(f'[[red.groups]]\nname = "allocation_nonincrease_{n}"\npass = 0\nfail = 1\nerror = 0\nbroken = 0\n' for n in cells)+'[green]\nassertions = 8640\n'+''.join(f'[[green.groups]]\nname = "{n}"\npass = {p}\nfail = {f}\nerror = {e}\nbroken = {b}\n' for n,p,f,e,b in groups+[[n,v,0,0,0] for n,v in new]+allocation))
put('assertion-inventory.md','''# Prospective assertion derivation — no Julia executed

Inherited eleven groups: exact namespace inverse to accepted GREEN2 test sources,
including the separate corrected import test. Per-group 42,6,35,56,108,53,303,
6236,378,108,610 = 7935. The initial uncorrected import file is not loaded.

New boundary_request_equivalence = 370: orientation2*(8+5*3)+6 =52;
10 import combinations *5 fixed predicates +4*67 allocation-prefix predicates=318.
The five n values0,1,3,2,2 give requests3+2n without normalization and4+2n
with normalization, sum67; both division rejections still finish their request list.

boundary_hook_order =112:2 policies*(2 sides*(5 success+5*4 failures)+6 paired)=112.
Hook5 throws before checker, which therefore asserts only on k0.

boundary_hot_and_hook_agree =220:24 build_pair calls*8 +12 paired +4 rejection
cases*4=220. The optional three retention checks are not reached: dimensions0/1/2
have P0/16 below512, hence no workspace. If runtime contradicts this source premise,
preserve the mismatch and stop; never adjust counts after a run.

GREEN structural total8637, plus3 allocation predicates =8640;14 structural groups
plus3 allocation groups. RED has only3 allocation predicates and no structural suite.
Correctness/input/compile and exact offline residual gates are mandatory in both.
Counts are prospective source derivations, not observed assertions.
''')
# Top-level includes and shared main; test imports precede function definitions.
incs='\n'.join('    include('+json.dumps(p)+')' for p in m['test_order'])
entries='\n'.join('                '+e for e in m['test_entries'])
put('driver.jl','''# UNEXECUTED Task2; ordinary stage, all definitions before main; no runtime include.
using Test, LinearAlgebra, SparseArrays, TOML, PrecompileTools, Statistics
using JSimplex
const J=JSimplex
length(ARGS)==3 || error("Exactly output/project/phase required")
const OUTPUT, PROJECT, PHASE=ARGS
PHASE in ("red300","green300","red600","green600") || error("Invalid phase")
const MODE=startswith(PHASE,"red") ? "red" : "green"
require(v,s)=v || error(s)
include("recorder.jl")
if MODE=="red"
    include("red-kernel.jl")
else
    include("green-kernel.jl")
'''+incs+'''
end
function exact_tree(root,expected)
    length(root.children)==length(expected["groups"]) || return false
    root.passed==root.failed==root.errored==root.broken==0 || return false
    isempty(root.failures) || return false
    for (t,e) in zip(root.children,expected["groups"])
        isempty(t.children) || return false
        (t.description,t.passed,t.failed,t.errored,t.broken)==
            (e["name"],e["pass"],e["fail"],e["error"],e["broken"]) || return false
        length(t.failures)==t.failed+t.errored || return false
    end
    true
end
function allocation_tests()
    source=TOML.parsefile(joinpath(@__DIR__,"inputs.toml"))["fixtures"]
    selected=[s for s in source if s["name"] in ("sparse32","dense32","sparse96")]
    require([s["name"] for s in selected]==["sparse32","dense32","sparse96"],"Fixture selection/order")
    for (cell,input) in enumerate(selected)
        f=decode_fixture(input);outputs=[zeros(f.n) for _ in 1:24]
        refs_bytes=Int[];cands_bytes=Int[];refs_events=Int[];cands_events=Int[]
        for pair in 1:10
            sides=isodd(pair) ? (Val(:reference),Val(:candidate)) : (Val(:candidate),Val(:reference))
            paired=Dict{String,Any}()
            for (order,side) in enumerate(sides)
                row=window(J.BartelsGolubFactorization,Val(:native),side,f,input,pair,order,outputs)
                save_window("window-$cell-$(2*(pair-1)+order).toml",row)
                require(row["correct"],"Correctness/mode/input failure")
                require(!row["measured"] || (row["compile_seconds"]==0 && row["recompile_seconds"]==0),"Measured compilation")
                paired[row["side"]]=row
                if pair>3
                    push!(side===Val(:reference) ? refs_bytes : cands_bytes,row["bytes"])
                    push!(side===Val(:reference) ? refs_events : cands_events,row["events"])
                end
            end
            require(paired["reference"]["outputs"]==paired["candidate"]["outputs"] && paired["reference"]["modes"]==paired["candidate"]["modes"],"Paired output/mode mismatch")
        end
        @testset "allocation_nonincrease_$(f.name)" begin
            @test median(cands_events)<=median(refs_events) && median(cands_bytes)<=median(refs_bytes)
        end
    end
end
function main()
    raw=Dict{String,Any}("phase"=>PHASE,"complete"=>false,"fatal"=>"")
    root=RecordedTests.Capture("root")
    try
        require(realpath(pathof(J))==realpath(joinpath(PROJECT,"src/JSimplex.jl")),"Wrong package source")
        require(Threads.nthreads()==BLAS.get_num_threads()==1 && !PrecompileTools.verbose[],"Thread/precompile configuration")
        raw["loaded"]=Dict(string(nameof(m))=>realpath(pathof(m)) for m in
            (J,SparseArrays,LinearAlgebra,TOML,Test,PrecompileTools,Statistics))
        raw["threads"]=Threads.nthreads();raw["blas_threads"]=BLAS.get_num_threads()
        println(stderr,"BEGIN BG specialization driver ",PHASE);flush(stderr)
        Test.@with_testset root begin
            if MODE=="green"
'''+entries+'''
            end
            allocation_tests()
        end
        raw["complete"]=true
    catch e
        raw["fatal"]=sprint(showerror,e,catch_backtrace());println(stderr,"FATAL DRIVER: ",raw["fatal"]);flush(stderr)
    finally
        raw["tests"]=RecordedTests.dictionary(root)
        save_window("raw.toml",raw)
    end
    expected=TOML.parsefile(joinpath(@__DIR__,"expected-tests.toml"))[MODE]
    valid=raw["complete"] && isempty(raw["fatal"]) && exact_tree(root,expected)
    valid || (println(stderr,"GROUP/COUNT MISMATCH OR FATAL");flush(stderr))
    exit(valid ? (MODE=="red" ? 1 : 0) : 2)
end
main()
''')
# Self-contained copied protocols: no execution/import of old mains.
text=(H/'control.py').read_text().replace("C=R/'diagnostics/direct-bg-export-workspace/reproduce'","C=R/'diagnostics/direct-bg-export-specialized/reproduce'")
text=text.replace("ENTRY='8bd2e14cdf0210363747f86b716e70569cf7b9b2'","ENTRY='b504ea4fbf3bc40a9fa87cfc0b9a7dd69cc821cd'")
text=text.replace('BG export workspace driver preparation','BG specialization driver preparation').replace('BG export workspace RED result','BG specialization RED result')
put('control.py',text)
for n in ['seal.py','launch.py']:
 text=(G/n).read_text().replace('BG export workspace exact-stage admission','BG specialization exact-stage admission').replace('BG export workspace phase','BG specialization phase')
 put(n,text)
text=(H/'oracle.py').read_text().replace('Expected missing-contract RED','Expected allocation-regression RED').replace('BG export workspace driver ','BG specialization driver ').replace('BG export workspace correctness only; no cost/public-solver acceptance','BG specialization structural/allocation gates only; no full-cost/public-solver acceptance')
(D/'oracle.py').write_text(text)
text=(G/'audit.py').read_text().replace('BG export workspace exact-stage admission','BG specialization exact-stage admission').replace('BG export workspace phase','BG specialization phase')
text=text.replace("require(names in [base,base|{'raw.toml'}]", "windows={f'window-{c}-{w}.toml' for c in range(1,4) for w in range(1,21)}\n require(base<=names<=base|{'raw.toml'}|windows")
text=text.replace("names==base|{'raw.toml'}","names==base|{'raw.toml'}|windows").replace("(6 if cfg['mode']=='red' else 0)","(3 if cfg['mode']=='red' else 0)")
text=text.replace("return dict(all_passed=True,pure_timeout=False,result=result,error='')", "from allocation_oracle import allocation_results\n rows={n:tomllib.loads((out/n).read_text()) for n in windows}\n allocation=allocation_results(rows,rd(D/'inputs.json')['fixtures'],cfg['mode'])\n return dict(all_passed=True,pure_timeout=False,result=result,allocation=allocation,error='')")
put('audit.py',text)
put('allocation_oracle.py','''"""Pure exact offline Task2 gates. All raw windows retained; no filesystem side effects."""
from analysis import require, matrix, window_ok, summarize
CELLS=('sparse32','dense32','sparse96')
def allocation_results(rows,fixtures,mode):
 require(mode in ('red','green'),'Mode')
 require(set(rows)=={f'window-{c}-{w}.toml' for c in range(1,4) for w in range(1,21)},'Window membership')
 selected=[f for f in fixtures if f['name'] in CELLS]
 require(tuple(f['name'] for f in selected)==CELLS,'Fixture order')
 result=[]
 for cell,f in enumerate(selected,1):
  matrices=[(matrix(m),matrix(m,True)) for m in f['matrices']];allrows=[]
  for pair in range(1,11):
   a=[]
   for order in (1,2):
    r=rows[f'window-{cell}-{2*(pair-1)+order}.toml']
    window_ok(r,f,1,pair,order,matrices)
    require(r['policy']=='threshold_one','Native policy');a.append(r);allrows.append(r)
   require(a[0]['outputs']==a[1]['outputs'] and a[0]['modes']==a[1]['modes'],'Paired bits/modes')
  s=summarize(allrows)
  require(s['allocation_gate'] is (mode=='green'),'Unexpected allocation predicate')
  result.append(dict(fixture=f['name'],statistics=s))
 return result
''')
# No attempts, output directories, reservations or seals are created.
js('copied-files.json',{n:{'source':str(src),'sha256':hashlib.sha256(src.read_bytes()).hexdigest()} for n,src in [(n,H/n) for n in ['guard.py','supervisor.py','baseline.json','environment.json','runtime-inputs-complete.json','loaded-paths.json','recorder.jl']]+[(n,O/n) for n in ['analysis.py','inputs.json','inputs.toml']]})
print('Prepared new source text and control definitions only; no Julia.')
