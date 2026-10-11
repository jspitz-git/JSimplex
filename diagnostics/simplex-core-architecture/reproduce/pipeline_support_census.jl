# Count exact parsed method bodies in this isolated diagnostic process only.
using Test,JSimplex,SparseArrays,LinearAlgebra,TOML,SHA
const JS=JSimplex
@assert Threads.nthreads()==BLAS.get_num_threads()==1
length(ARGS)==2 || error("usage: census|red|green OUTPUT")
const MODE,OUTPUT=ARGS
@assert MODE in ("census","red","green")
const SOURCE=dirname(pathof(JS))
const HASHES=Dict(f=>bytes2hex(sha256(read(joinpath(SOURCE,f)))) for f in
    ("indexed_vector.jl","hypersparse_pipeline.jl","hypersparse_updates.jl","hypersparse_factorization.jl","sparse_pricing.jl"))
function source_function(file,name)
    source=read(joinpath(SOURCE,file),String)
    positions=findall("function $name(",source)
    length(positions)==1 || error("Unexpected source definition: $name")
    expression,_=Meta.parse(source,first(only(positions)))
    @assert expression.head==:function
    return expression
end
Core.eval(JS,:(const _sc_counts=zeros(Int,6)))
for (file,name,kind) in (("indexed_vector.jl","compact_support!",:compact),
    ("hypersparse_pipeline.jl","_pipeline_output_support!",:output),
    ("hypersparse_pipeline.jl","_rebuild_pipeline_support!",:rebuild))
    expr=source_function(file,name);body=expr.args[2]
    expr.args[2]=if kind==:compact
        quote
            _sc_counts[1]+=1;_sc_counts[2]+=length(v.indices)
            $body
        end
    elseif kind==:rebuild
        quote
            _sc_counts[5]+=1;_sc_counts[6]+=length(cache.buffers[index].values)
            $body
        end
    else
        before_calls,before_elements=gensym(:before_calls),gensym(:before_elements)
        quote
            $before_calls=_sc_counts[1];$before_elements=_sc_counts[2]
            try
                $body
            finally
                _sc_counts[3]+=_sc_counts[1]-$before_calls
                _sc_counts[4]+=_sc_counts[2]-$before_elements
            end
        end
    end
    Core.eval(JS,expr)
end
function fixture(T,manager,backend,history)
    m=16
    A=spdiagm(0=>ones(T,m));A[2,1]=T(1//8)
    # First structural column pivots once; all other costs are zero.
    p=JS.LinearProblem(A,vcat(-one(T),zeros(T,m-1));row_upper=vcat(one(T),fill(T(100),m-1)))
    o=JS.SolverOptions(T;algorithm=:primal,simplex_strategy=:legacy,pricing=:dantzig,
        basis_update=manager,basis_refactorization=backend,partial_pricing=false,verbose=false)
    policy=JS.NumericalPolicy(T;simplex_strategy=:legacy,hypersparse=true,refactor_timing=false)
    ws=JS.initialize_workspace(p,o;progress=JS.SimplexProgressContext(p;numerical_policy=policy))
    if history
        @assert isnothing(JS._primal_iteration!(ws,()->false,o.dual_tolerance))
        @assert ws.iterations==1 && length(ws.factorization.updates)==1
    end
    return ws,Matrix(JS.basis_matrix(ws))
end
function one_case(ws,B,pattern,forced,operation;external=false)
    T=eltype(ws.primal);m=size(B,1);cache=JS._hypersparse_workspace!(ws)
    values=operation==:pricing ? ws.scratch.rho : ws.scratch.row_rhs
    input=cache.buffers[JS._pipeline_buffer_index(cache,values)]
    JS.clear!(input)
    if pattern==:sparse
        JS.set_entry!(input,2,one(T))
        # Deliberately leave a cancellation index: input compaction is required.
        JS.set_entry!(input,3,one(T));JS.add_entry!(input,3,-one(T))
        @assert 3 in input.indices && iszero(input.values[3])
    elseif pattern==:dense
        for i in 1:m;JS.set_entry!(input,i,one(T));end
    end
    cache.valid[JS._pipeline_buffer_index(cache,values)]=true
    saved=copy(values)
    destination=external ? zeros(T,m) : operation==:pricing ? ws.scratch.tableau_row :
        operation==:btran ? ws.scratch.rho : ws.scratch.row_solution
    index=JS._pipeline_buffer_index(cache,destination)
    before_rebuild=cache.support_rebuilds
    fill!(JS._sc_counts,0)
    if operation==:pricing
        JS._pipeline_price!(destination,ws,values;kernel_mode=forced)
    else
        JS._pipeline_basis_solve!(destination,ws,values;transposed=operation==:btran,kernel_mode=forced)
    end
    counts=copy(JS._sc_counts)
    actual=JS._pipeline_state(cache,operation).last_mode
    if operation==:pricing
        @test destination==vcat(transpose(ws.problem.A)*saved,-saved)
    else
        @test (operation==:btran ? transpose(B) : B)*destination==saved
    end
    @test values==saved
    canonical=actual in (:sparse,:empty) && index>0
    if index>0
        vector=cache.buffers[index]
        @test cache.valid[index]
        @test length(vector.indices)==length(unique(vector.indices))
        @test Set(vector.indices)==Set(findall(!iszero,destination))
        @test all(vector.membership[i]==vector.generation for i in vector.indices)
    end
    @test counts[5]==cache.support_rebuilds-before_rebuild
    @test actual==(pattern==:empty ? :empty : external || (operation!=:pricing && forced==:sparse && !JS._pipeline_sparse_available!(ws)) ? :dense : forced)
    if MODE=="census"
        @test counts[3]==Int(canonical)
        @test counts[4]==(canonical ? count(!iszero,destination) : 0)
    else
        # Intended RED on unchanged producer-consumer pipeline.
        @test counts[3]==0
        @test counts[4]==0
    end
    if pattern==:sparse
        @test !(3 in input.indices)
        @test counts[1]>=1 # Ordinary input compaction must not disappear.
    end
    return Dict("pattern"=>string(pattern),"forced"=>string(forced),"operation"=>string(operation),
        "actual_mode"=>string(actual),"external"=>external,"support"=>count(!iszero,destination),
        "compact_calls"=>counts[1],"compact_elements"=>counts[2],
        "output_compact_calls"=>counts[3],"output_compact_elements"=>counts[4],
        "rebuilds"=>counts[5],"rebuild_scan_size"=>counts[6])
end
rows=Dict[]
try
@testset "Canonical pipeline output work $MODE" begin
    types=MODE=="red" ? (Float64,) : (Float32,Float64,BigFloat,Rational{Int64},Rational{BigInt})
    managers=MODE=="red" ? (:pfi,) : (:pfi,:huangfu_hall,:forrest_tomlin,:suhl_suhl,:bartels_golub)
    backends=MODE=="red" ? (:native,) : (:native,:markowitz)
    histories=MODE=="red" ? (false,) : (false,true)
    patterns=MODE=="red" ? (:sparse,) : (:empty,:sparse,:dense)
    for T in types,manager in managers,backend in backends,history in histories
        ws,B=fixture(T,manager,backend,history)
        for pattern in patterns,forced in (:sparse,:dense),operation in (:ftran,:btran,:pricing)
            row=one_case(ws,B,pattern,forced,operation)
            merge!(row,Dict("type"=>string(T),"manager"=>string(manager),"backend"=>string(backend),"history"=>Int(history)))
            push!(rows,row)
        end
        row=one_case(ws,B,:sparse,:sparse,:ftran;external=true)
        merge!(row,Dict("type"=>string(T),"manager"=>string(manager),"backend"=>string(backend),"history"=>Int(history)))
        push!(rows,row)
    end
end
finally
    open(io->TOML.print(io,Dict("mode"=>MODE,"source_hashes"=>HASHES,"cases"=>rows,
        "semantics"=>"isolated exact-body instrumentation; no timing claim; rebuild scan size counts scheduled successful-scan entries")),OUTPUT,"w")
end
