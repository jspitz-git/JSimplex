from pathlib import Path
import json,re
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCK-DRIVER-PREPARATION';C=R/'diagnostics/direct-bg-block-upper/reproduce';O=D.parent/'DIRECT-BG-DYNAMIC-DRIVER-PREPARATION'
def put(n,s):
 with (D/n).open('x') as f:f.write(s)
names=sorted(set(re.findall(r'\b_bgu_[A-Za-z0-9_]+!?',(C/'block-upper.jl').read_text())))
put('block-suite.jl','''# Test-owned module; top-level inclusion only. Production methods unchanged.
module BlockStorageTests
using Test, SparseArrays
import JSimplex
import JSimplex: BGBlockUpper, '''+', '.join(names)+'''
include(joinpath(dirname(pathof(JSimplex)),"../test/block-oracles.jl"))
include(joinpath(dirname(pathof(JSimplex)),"../test/block-upper-tests.jl"))
end
''')
put('red.jl','''# Eight NEW contract checks; zero factor/solve/update entries.
function run_block_bg_red()
    @testset "Missing block BG U contracts (eight expected failures)" begin
        @test isdefined(JSimplex,:BGBlockUpper)
        @test isdefined(JSimplex,:_bgu_build)
        @test isdefined(JSimplex,:_bgu_insert_at!)
        @test isdefined(JSimplex,:_bgu_swap_rows!)
        @test isdefined(JSimplex,:_bgu_rotate_rows!)
        @test isdefined(JSimplex,:BlockBGFactor)
        @test isdefined(JSimplex,:_block_bg_factor)
        @test isdefined(JSimplex,:_block_bg_replace!)
    end
end
''')
s=(O/'driver.jl').read_text().replace('dynamic BG','block BG').replace('run_dynamic_bg_red','run_block_bg_red')
s=s.replace('const GREEN_FUNCTIONS=(:lifecycles,:rejection_and_aliases,:export_modes,:focused_updates)', '''length(ARGS)==3 || error("Exactly output/project/phase required")
ARGS[3] in ("red300","green300","red600","green600") || error("Invalid phase")
# All includes resolve BEFORE main is defined or invoked. No late module/global lookup.
if startswith(ARGS[3],"red")
    include(joinpath(@__DIR__,"red.jl"))
else
    include(joinpath(@__DIR__,"block-suite.jl"))
    include(joinpath(ARGS[2],"test/block-bg-tests.jl"))
end
const GREEN_FUNCTIONS=(:lifecycles,:rejection_and_aliases,:export_modes,:focused_updates,
    :block_boundaries,:storage_failure_boundaries,:new_scratch_aliases)''')
s=s.replace('            include(joinpath(@__DIR__,"red.jl"))\n','').replace('Base.invokelatest(run_block_bg_red)','run_block_bg_red()')
s=s.replace('            include(joinpath(@__DIR__,"slot-suite.jl"))\n            include(joinpath(project,"test/dynamic-bg-tests.jl"))\n','')
s=s.replace('BEGIN slots','BEGIN block storage').replace('END slots','END block storage').replace('Base.invokelatest(DynamicBGSlotTests.run_slots)','BlockStorageTests._bgu_structural_tests()').replace('Base.invokelatest(getfield(DynamicBGTests,name))','getfield(BlockBGTests,name)()')
put('driver.jl',s)
# Source derivation, independently checked before acceptance. Counts are prospective only.
struct=[('empty_and_import',6*3+3),('nonidentity_q',3+4*4+2),('handle_backrefs',6*2),('direct_cursor_and_malformed',6),('gap_move_grow',(11+4)*2),('split32_insert33',3*3),('boundary_swap_rotate',(5+4)*2),('deletion_merge_right',33*2+1+15+1+2),('reserve_failure',3*(2+14*3)+1+90*2),('checked_limits',17),('explicit_zero_order',4),('repeated_row_fills',160*2+29+2),('fragmented_high_water',40*40*2+1+40+1),('copy_independence',6+2+69*3)]
adapter=[('Seven fixed fixtures, two policies, direct reference',4*91+10*(91+8*55+5+55+2*12+7*14+14)),('Private scratch and supported routes',115),('Fallback, normalization fallback, q, transactional refactor',461),('Exact storage branches, failures, ordering',5*13+6+5+14+(55+2+2*14+55)+3+2*3),('Block boundaries, diagonals and contiguous solve order',12*29+10*65+3*2*3+2*11+2*2),('Setup copy refactor reserves and failed update boundary',2*(3*(1+29*7)+2)+4+2+2+2*6),('New block scratch aliases reject before dimension backend',10)]
expected={'red':{'assertions':8,'groups':[['Missing block BG U contracts (eight expected failures)',0,8,0,0]]},'green':{'assertions':sum(n for _,n in struct+adapter),'groups':[[name,n,0,0,0] for name,n in struct+adapter]}}
put('expected-tests.json',json.dumps(expected,indent=2)+'\n')
t=''
for mode in expected:
 t+='['+mode+']\nassertions = '+str(expected[mode]['assertions'])+'\n'
 for name,p,f,e,b in expected[mode]['groups']:t+='[[ '+mode+'.groups ]]\nname = '+json.dumps(name)+'\npass = '+str(p)+'\nfail = '+str(f)+'\nerror = '+str(e)+'\nbroken = '+str(b)+'\n'
put('expected-tests.toml',t)
put('assertion-derivation.json',json.dumps(dict(structural=struct,adapter=adapter,helpers=dict(pair_state=10,solve_pair=14,replace_pair=55,assert_owners=2),scope='Prospective source branch arithmetic; not executed Julia counts. Internal @assert oracles are not Test result entries.',row_growth_events=29,allocator_requests=dict(structural=7026,adapter=2787,total=9813,complete_before_throw=9436),failure_probe_operations=388,injected_failures=377),indent=2)+'\n')
print('New driver prepared; expected',expected['green']['assertions'],[n for _,n in struct+adapter])
