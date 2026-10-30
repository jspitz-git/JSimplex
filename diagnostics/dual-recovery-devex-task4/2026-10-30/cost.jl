using JSimplex,LinearAlgebra,SparseArrays,Test,TOML
include("tests/reference.jl")
module Task4Cost
using JSimplex,LinearAlgebra,SparseArrays,Test,TOML
const J=JSimplex
mutable struct Factor{T,F}
    base::F
    updates::Vector{J.PackedEta{T}}
    zero_correction::Bool
    calls::Int
end
function J.transpose_solve!(x::Vector{T},f::Factor{T},rhs::Vector{T}) where T
    f.calls+=1
    J.transpose_solve!(x,f.base,rhs)
    f.zero_correction && fill!(x,zero(T))
    x
end
mutable struct Stop
    calls::Int
end
(s::Stop)()=(s.calls+=1;false)
bits(x::Float32)=string(reinterpret(UInt32,x),base=16,pad=8)
bits(x::Float64)=string(reinterpret(UInt64,x),base=16,pad=16)
stats(t)=Dict("seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),
    "gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time)
function fixture(::Type{T},dense,bad) where T
    n=64;B=zeros(T,n,n)
    for j in 1:n,i in 1:n
        if i==j
            B[i,j]=T(64)
        elseif dense || abs(i-j)==1
            B[i,j]=T((iseven(i+j) ? -1 : 1)*(1+mod(i+2j,5)))/T(64)
        end
    end
    A=sparse(B);p=J.LinearProblem(A,zeros(T,n);column_lower=fill(nothing,n))
    options=J.SolverOptions(T;verbose=false,time_limit=Inf)
    policy=J.NumericalPolicy(T;solve_refinement=false,max_refinements=3,adaptive_refactor=true,refactor_timing=false,hypersparse=false)
    diag=J.SimplexDiagnostics();context=J.SimplexProgressContext(p;diagnostics=diag,numerical_policy=policy)
    base=J._basis_factorization(A,options)
    f=Factor{T,typeof(base)}(base,base.updates,bad,0)
    states=vcat(fill(J.BASIC,n),fill(J.FREE_NONBASIC,n))
    ws=J.SimplexWorkspace(p,options,context,zeros(T,2n),vcat(p.column_lower,p.row_lower),vcat(p.column_upper,p.row_upper),
        J.Basis(collect(1:n),states),zeros(T,2n),zeros(T,2n),ones(T,2n),falses(2n),f,J.SimplexScratch(T,n,2n),
        0,0,false,0,false,false,options.refactorization_interval,0,typemax(Int),0,0)
    J._basis_matrix!(ws);J._pivot_quality_buffers(ws)
    initial=zeros(T,n);initial[1]=bad ? T(0.5) : one(T)
    rhs=copy(B[1,:]) # B' * e1; independent of the declared correction output
    (;ws,f,policy,initial,rhs,x=copy(initial),stop=Stop(0),B)
end
function owners(f)
    b=J._pivot_quality_buffers(f.ws)
    map(objectid,(f.x,f.rhs,f.ws.problem.A.nzval,f.ws.basis.basic_indices,
                  f.ws.scratch.basis_matrix,b.rhs,b.unit,b.correction,b.trial,b.row.residual,b.column.residual))
end
function run_case(::Type{T},dense,bad,api::F) where {T,F}
    prepared=@timed fixture(T,dense,bad)
    f=prepared.value;identity=owners(f);savedB=copy(f.ws.problem.A);savedrhs=copy(f.rhs)
    warm=Dict{String,Any}[];samples=Dict{String,Any}[]
    # Three prescribed warm calls; all fixture preparation/GC is recorded apart.
    for k in 1:3
        copyto!(f.x,f.initial);before=(f.f.calls,f.stop.calls)
        timed=@timed api(f.x,f.ws,f.rhs,f.policy,f.stop;transposed=true)
        q=timed.value
        @test q.finite && q.reliable == !bad
        @test (f.f.calls-before[1],f.stop.calls-before[2])==(bad ? (1,1) : (0,0))
        push!(warm,stats(timed))
    end
    gc=@timed GC.gc() # exactly one explicit post-warm GC for this case
    for k in 1:7
        copyto!(f.x,f.initial);before=(f.f.calls,f.stop.calls)
        timed=@timed api(f.x,f.ws,f.rhs,f.policy,f.stop;transposed=true)
        q=timed.value
        @test q.finite && q.reliable == !bad
        @test f.x==f.initial && f.rhs==savedrhs && f.ws.problem.A==savedB
        @test owners(f)==identity
        solves,stops=f.f.calls-before[1],f.stop.calls-before[2]
        @test (solves,stops)==(bad ? (1,1) : (0,0))
        push!(samples,merge(stats(timed),Dict("index"=>k,"solve_entries"=>solves,"stop_entries"=>stops,
            "finite"=>q.finite,"reliable"=>q.reliable,"absolute_bits"=>bits(q.absolute_error),
            "relative_bits"=>bits(q.relative_error),"point_bits"=>bits.(f.x),"rhs_bits"=>bits.(f.rhs),"owners_preserved"=>true)))
    end
    # Capture input and retained Julia graph after windows; not hidden native memory.
    Dict("type"=>string(T),"layout"=>dense ? "dense" : "sparse","unreliable"=>bad,"dimension"=>64,
         "matrix_bits"=>bits.(vec(f.B)),"nnz"=>nnz(f.ws.problem.A),"warm"=>warm,"samples"=>samples,
         "preparation"=>stats(prepared),"post_warm_gc"=>stats(gc),"solve_entries_total"=>f.f.calls,
         "stop_entries_total"=>f.stop.calls,"retained_julia_bytes"=>Base.summarysize(f),
         "policy_solve_tolerance_bits"=>bits(f.policy.solve_tolerance))
end
function run(api::F,side,path) where F
    cases=Dict{String,Any}[]
    @testset "TASK4_COST" begin
        for T in (Float32,Float64),dense in (false,true),bad in (false,true)
            push!(cases,run_case(T,dense,bad,api))
        end
    end
    ispath(path) && error("output already exists")
    open(path,"w") do io
        TOML.print(io,Dict("side"=>side,"cases"=>cases);sorted=true)
    end
    println("TASK4_COST_COMPLETED ",side)
end
end
side=only(ARGS)
side in ("reference","candidate") || error("unknown cost side")
@assert realpath(pathof(JSimplex))==realpath(joinpath(@__DIR__,"overlays",side,"src","JSimplex.jl"))
api=side=="reference" ? RefinementReference.refine_basis_solve! : JSimplex.refine_basis_solve!
Base.invokelatest(Task4Cost.run,api,side,ENV["TASK4_OUTPUT"])
