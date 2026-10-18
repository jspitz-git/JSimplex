from pathlib import Path
import json,hashlib
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-SPLIT-ADAPTER-PREPARATION';N=R/'diagnostics/direct-bg-split-upper/reproduce';O=R/'diagnostics/direct-bg-block-upper/reproduce'
renames=[('BlockBGFactor','SplitBGFactor'),('BGBlockUpper','BGSplitUpper'),('_block_bg_','_split_bg_'),('_bbg_','_sbg_'),('_bgu_','_sbu_'),('BlockBGTests','SplitBGTests'),('run_block_bg_tests','run_split_bg_tests'),('block_tokens','split_tokens'),('_check_block_upper','_check_split_upper'),('block-oracles.jl','split-oracles.jl')]
t=(O/'block-bg-tests.jl').read_text()
for a,b in renames:t=t.replace(a,b)
extra='''# NEW demand-sized allocator integration oracles. Deliberately storage-only
# mutations of controlled exports: never solve an arbitrarily edited factor.
function split_assign_pair!(r,d,row,col,value)
    cid=r.column_order[col];slot,old=J._upper_entry(r.upper[col],row)
    J._set_upper_value_at!(r.upper,r.row_columns,col,row,value,slot,cid)
    J._sbu_set!(d.upper,Int(d.upper.row_order[row]),Int(d.upper.column_order[col]),value)
    @test isequal(packed_tokens(r),split_tokens(d.upper))
    @test _check_split_upper(d.upper)
end
function split_allocator_differentials()
    @testset "Demand-sized growth, split33, suffix reuse and refill" begin
        r,d=controlled_pair(spzeros(40,40),collect(40:-1:1))
        J._ensure_bartels_golub_incidence!(r)
        for row in 1:32
            split_assign_pair!(r,d,row,1,Float64(row))
            b=Int(d.upper.column_head[d.upper.column_order[1]])
            @test Int(d.upper.capacity[b])==J._sbu_target(row)
            @test d.upper.next[b]==0
        end
        # New empty-column demand must use existing free reserve, no new slab.
        slabs=d.upper.slabs
        split_assign_pair!(r,d,1,2,2.0)
        @test d.upper.slabs==slabs
        @test d.upper.capacity[d.upper.column_head[d.upper.column_order[2]]]==1
        split_assign_pair!(r,d,33,1,33.0)
        @test d.upper.next[d.upper.column_head[d.upper.column_order[1]]]!=0
        # Deletion can merge blocks; re-growth is not covered by monotone31.
        for row in 2:2:32;split_assign_pair!(r,d,row,1,0.0);end
        for row in 2:2:32;split_assign_pair!(r,d,row,1,-Float64(row));end
        for row in 1:33;split_assign_pair!(r,d,row,1,0.0);end
        @test d.upper.column_head[d.upper.column_order[1]]==0
        for row in 1:9;split_assign_pair!(r,d,row,1,Float64(row));end
    end
    @testset "Imported short exact tails and rotations across split extents" begin
        # Lengths0/1/3/5/31/32/33 include non-power imported tails.
        lens=(0,1,3,5,31,32,33);M=spzeros(40,40)
        for (col,len) in enumerate(lens), row in 1:len;M[row,col]=Float64(row+col);end
        r,d=controlled_pair(M,collect(40:-1:1));J._ensure_bartels_golub_incidence!(r)
        @test isequal(packed_tokens(r),split_tokens(d.upper))
        for col in 1:7
            split_assign_pair!(r,d,lens[col]+1,col,-Float64(col))
        end
        # Use packed incidence rotation, not a dense reference that loses zeros.
        for (first,last) in ((1,34),(3,18),(1,40))
            J._rotate_upper_rows!(r.upper,r.row_columns,Int[],zeros(40),first,last,r.positions)
            J._sbu_rotate_rows!(d.upper,first,last)
            @test isequal(packed_tokens(r),split_tokens(d.upper))
            @test _check_split_upper(d.upper)
        end
        for col in 1:7
            split_assign_pair!(r,d,2,col,0.0)
            split_assign_pair!(r,d,2,col,Float64(col))
        end
        # Source/target incidence merge after the physical extents diverge.
        trace=Int[]
        for cid in r.row_columns[1]
            col=r.positions[cid];col<=1 && continue
            push!(trace,cid);u=r.upper[col];slot,old=J._upper_entry(u,2)
            J._set_upper_value_at!(r.upper,r.row_columns,col,2,old-J._upper_value(u,1),slot,cid)
        end
        observed=Int[];J._sbg_eliminate_row!(d,1,1.0,cid->push!(observed,cid))
        @test trace==observed
        @test isequal(packed_tokens(r),split_tokens(d.upper)) && _check_split_upper(d.upper)
    end
end

'''
anchor='function run_split_bg_tests()\n'
assert t.count(anchor)==1
t=t.replace(anchor,extra+anchor).replace('block_boundaries();storage_failure_boundaries();new_scratch_aliases()','block_boundaries();storage_failure_boundaries();new_scratch_aliases()\n    split_allocator_differentials()')
for name,data in [('split-bg-tests.jl',t.encode()),('fixtures.jl',(O/'fixtures.jl').read_bytes())]:
 with (N/name).open('xb') as f:f.write(data)
r=dict(scope='Tests authored before adapter. Julia UNEXECUTED.',renames=renames,extra=extra,call='    split_allocator_differentials()\n',sha256={str(N/x):hashlib.sha256((N/x).read_bytes()).hexdigest() for x in ['split-bg-tests.jl','fixtures.jl']},adapter_absent=not (N/'split-bg.jl').exists())
with (E/'tests-first.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print('Tests written first; adapter absent:',r['adapter_absent'])
