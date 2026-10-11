# Before/after whole pipeline calls; fixed modes, no solver-policy promotion.
using JSimplex,SparseArrays,LinearAlgebra,TOML,SHA,Logging
const JS=JSimplex
@assert Threads.nthreads()==BLAS.get_num_threads()==1
const OUTPUT=ARGS[1]
const REMAINING=length(ARGS)==2 && ARGS[2]=="remaining"
@assert length(ARGS)==1 || REMAINING
const REPEATS=256
const BASELINE=joinpath(@__DIR__,"pipeline_support_baseline.jl")
Base.include(JS,BASELINE)
const SOURCE=read(joinpath(dirname(pathof(JS)),"hypersparse_pipeline.jl"),String)
function control_function(name,newname)
    positions=findall("function $name(",SOURCE);@assert length(positions)==1
    expression,_=Meta.parse(SOURCE,first(only(positions)))
    signature=expression.args[1]
    while signature.head in (:(::),:where)
        signature=signature.args[1]
    end
    @assert signature.head==:call
    signature.args[1]=newname
    hits=Ref(0)
    function rewrite(x)
        x isa Expr || return x
        y=Expr(x.head,map(rewrite,x.args)...)
        if y.head==:call && y.args[1]==:_pipeline_output_support!
            @assert length(y.args)==6
            y.args[1]=:_pipeline_original_output_support!
            pop!(y.args);hits[]+=1
        end
        return y
    end
    expression.args[2]=rewrite(expression.args[2]);@assert hits[]==1
    Core.eval(JS,expression)
end
control_function("_pipeline_basis_solve!",:_pipeline_control_basis!)
control_function("_pipeline_price!",:_pipeline_control_price!)
function fixture(T,manager,backend,kind,history)
    m=kind==:sparse ? 256 : 64
    A=kind==:sparse ? spdiagm(0=>ones(T,m),-1=>fill(T(1//8),m-1)) :
        sparse(Matrix{T}(I,m,m).+T(1//1024))
    costs=zeros(T,m);costs[1:max(history,1)].=-one(T)
    p=JS.LinearProblem(A,costs;row_upper=fill(T(10),m))
    o=JS.SolverOptions(T;algorithm=:primal,simplex_strategy=:legacy,pricing=:dantzig,
        basis_update=manager,basis_refactorization=backend,partial_pricing=false,
        refactorization_interval=160,iteration_limit=100,verbose=false)
    policy=JS.NumericalPolicy(T;simplex_strategy=:legacy,hypersparse=true,refactor_timing=false)
    ws=JS.initialize_workspace(p,o;progress=JS.SimplexProgressContext(p;numerical_policy=policy))
    for i in 1:history
        @assert isnothing(JS._primal_iteration!(ws,()->false,o.dual_tolerance))
    end
    @assert ws.iterations==history && length(ws.factorization.updates)==history
    return ws,Matrix(JS.basis_matrix(ws))
end
function inputs!(ws,operation,kind)
    m=size(ws.problem.A,1)
    input=operation==:pricing ? ws.scratch.rho : ws.scratch.row_rhs
    fill!(input,zero(eltype(input)))
    if kind==:sparse
        input[1]=one(eltype(input));input[m]=one(eltype(input))
    else
        fill!(input,one(eltype(input)))
    end
    JS._pipeline_changed!(ws,input)
    output=operation==:pricing ? ws.scratch.tableau_row : operation==:btran ? ws.scratch.rho : ws.scratch.row_solution
    return input,output
end
function batch!(f::F,ws,input,output,operation,mode,n) where F
    for i in 1:n
        if operation==:pricing
            f(output,ws,input;kernel_mode=mode)
        else
            f(output,ws,input;transposed=operation==:btran,kernel_mode=mode)
        end
    end
    nothing
end
metric(m)=Dict{String,Any}("seconds"=>m.time,"bytes"=>m.bytes,
    "allocations"=>Base.gc_alloc_count(m.gcstats),"gc_seconds"=>m.gctime,"compile_seconds"=>m.compile_time)
function fingerprint(ws,input,output,operation,B)
    @assert all(isfinite,output)
    if operation==:pricing
        reference=vcat(transpose(ws.problem.A)*input,-input)
        @assert output==reference
    else
        matrix=operation==:btran ? transpose(B) : B
        residual=matrix*output-input
        allowance=128size(B,1)*eps(eltype(input))*max(norm(matrix,Inf)*norm(output,Inf),norm(input,Inf))
        @assert norm(residual,Inf)<=allowance
    end
    cache=JS._hypersparse_workspace!(ws);v=cache.buffers[JS._pipeline_buffer_index(cache,output)]
    @assert Set(v.indices)==Set(findall(!iszero,output))
    @assert length(v.indices)==length(unique(v.indices))
    return bytes2hex(sha256(reinterpret(UInt8,output)))
end
function main()
    samples=Dict[];warmups=Dict[];setups=Dict[]
    configs=vcat([(Float64,m,:native) for m in (:pfi,:huangfu_hall,:forrest_tomlin,:suhl_suhl,:bartels_golub)],
        [(Float32,m,:markowitz) for m in (:pfi,:huangfu_hall)])
    try
        with_logger(NullLogger()) do
            for (T,manager,backend) in configs,kind in (:sparse,:dense),history in (0,8)
                # Preserve the 23 completed fixtures from cost-2. The two dense
                # Float32/history8 fixtures fail identically before timing in
                # old/new code (fixture-probe-1), so report their missing coverage.
                REMAINING && !(T===Float32 && manager==:huangfu_hall &&
                    !(kind==:dense && history==8)) && continue
                setup=@timed fixture(T,manager,backend,kind,history)
                ws,B=setup.value
                labels=Dict{String,Any}("type"=>string(T),"manager"=>string(manager),"backend"=>string(backend),
                    "matrix"=>string(kind),"history"=>history,"rows"=>size(B,1),"nnz"=>nnz(ws.problem.A))
                push!(setups,merge(copy(labels),metric(setup)))
                for operation in (:ftran,:btran,:pricing),mode in (:sparse,:dense)
                    input,output=inputs!(ws,operation,kind)
                    variants=operation==:pricing ? (("control",JS._pipeline_control_price!),("candidate",JS._pipeline_price!)) :
                        (("control",JS._pipeline_control_basis!),("candidate",JS._pipeline_basis_solve!))
                    reference_hash=nothing
                    for (variant,f) in variants
                        warm=@timed batch!(f,ws,input,output,operation,mode,REPEATS)
                        h=fingerprint(ws,input,output,operation,B)
                        isnothing(reference_hash) ? (reference_hash=h) : (@assert h==reference_hash)
                        push!(warmups,merge(copy(labels),metric(warm),Dict("operation"=>string(operation),"mode"=>string(mode),"variant"=>variant)))
                    end
                    for pair in 1:3
                        for (variant,f) in (isodd(pair) ? variants : reverse(variants))
                            GC.gc(true)
                            measured=@timed batch!(f,ws,input,output,operation,mode,REPEATS)
                            h=fingerprint(ws,input,output,operation,B);@assert h==reference_hash
                            @assert length(ws.factorization.updates)==history
                            actual=JS._pipeline_state(JS._hypersparse_workspace!(ws),operation).last_mode
                            push!(samples,merge(copy(labels),metric(measured),Dict("operation"=>string(operation),
                                "mode"=>string(mode),"actual_mode"=>string(actual),"pair"=>pair,"variant"=>variant,
                                "calls"=>REPEATS,"output_hash"=>h)))
                        end
                    end
                end
                println("Measured ",T,"/",manager,"/",kind,"/history",history);flush(stdout)
            end
        end
    finally
        open(io->TOML.print(io,Dict("samples"=>samples,"warmups"=>warmups,"setups"=>setups,
            "pipeline_source_hash"=>bytes2hex(sha256(SOURCE)),"baseline_helper_hash"=>bytes2hex(sha256(read(BASELINE))),
            "semantics"=>"whole pipeline calls; 3 interleaved pairs; fixed outer modes; compilation/setup separate; post-timing values/support/residual checks; no whole-solver claim")),OUTPUT,"w")
    end
end
main()
