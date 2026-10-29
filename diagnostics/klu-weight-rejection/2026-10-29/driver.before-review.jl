using Test, LinearAlgebra, SparseArrays, Serialization, SHA, TOML, Libdl
using JSimplex
include(joinpath(@__DIR__, "vendor/KLU/src/KLU.jl"))
include(joinpath(@__DIR__, "export.jl"))
include(joinpath(@__DIR__, "ftran.jl"))
include(joinpath(@__DIR__, "candidate.jl"))
const JS = JSimplex
const D = @__DIR__
function digestarrays(arrays...)
    io = IOBuffer()
    for v in arrays
        write(io, Int(length(v)))
        write(io, v)
    end
    bytes2hex(sha256(take!(io)))
end
matrixhash(B) = digestarrays(B.colptr, B.rowval, B.nzval)
function assemble(A, basis)
    n, N = size(A)
    ptr = Int[1]; rows = Int[]; vals = Float64[]
    for e in basis
        if e <= N
            for k in nzrange(A, e)
                push!(rows, A.rowval[k]); push!(vals, A.nzval[k])
            end
        else
            1 <= e-N <= n || error("invalid artificial column")
            push!(rows, e-N); push!(vals, -1.0)
        end
        push!(ptr, length(rows)+1)
    end
    SparseMatrixCSC(n, n, ptr, rows, vals)
end
bits(v::Float64) = string(reinterpret(UInt64, v); base=16, pad=16)
bitsequal(a, b) = reinterpret(UInt64, a) == reinterpret(UInt64, b)
qualitydict(q) = Dict("absolute_error"=>q.absolute_error, "relative_error"=>q.relative_error,
                      "finite"=>q.finite, "reliable"=>q.reliable)
qualityequal(a,b) = isequal(a.absolute_error,b.absolute_error) &&
    isequal(a.relative_error,b.relative_error) && a.finite==b.finite && a.reliable==b.reliable
statistics(t) = Dict("seconds"=>t.time, "bytes"=>t.bytes, "events"=>Base.gc_alloc_count(t.gcstats),
    "gc_seconds"=>t.gctime, "compile_seconds"=>t.compile_time, "recompile_seconds"=>t.recompile_time)
struct KluDelegate{C}
    ctx::C
end
struct UmfDelegate{F}
    factor::F
end
delegate!(dest, f::KluDelegate, rhs) = generic_btran!(dest, f.ctx, rhs)
delegate!(dest, f::UmfDelegate, rhs) = ldiv!(dest, transpose(f.factor), rhs)
mutable struct TraceFactor{F}
    delegate::F
    updates::Vector{JS.PackedEta{Float64}}
    point::Vector{Float64}
    calls::Int
    before::NTuple{3,Vector{Float64}}
    rhs::NTuple{3,Vector{Float64}}
    delta::NTuple{3,Vector{Float64}}
end
function tracefactor(f, x)
    n = length(x)
    TraceFactor(f, JS.PackedEta{Float64}[], x, 0,
        ntuple(_->zeros(n),3), ntuple(_->zeros(n),3), ntuple(_->zeros(n),3))
end
function JS.transpose_solve!(dest::Vector{Float64}, f::TraceFactor, rhs::Vector{Float64})
    f.calls += 1
    1 <= f.calls <= 3 || error("correction budget exceeded")
    k = f.calls
    copyto!(f.before[k], f.point)
    copyto!(f.rhs[k], rhs)
    delegate!(dest, f.delegate, rhs)
    copyto!(f.delta[k], dest)
    dest
end
mutable struct NoStop
    calls::Int
end
(s::NoStop)() = (s.calls += 1; false)
function workspace(problem, basis, factor)
    n, N = size(problem.A)
    options = JS.SolverOptions(Float64; algorithm=:dual, pricing=:steepest_edge,
        simplex_strategy=:legacy, verbose=false, time_limit=Inf)
    progress = JS.SimplexProgressContext(problem; numerical_policy=JS.NumericalPolicy(Float64,options))
    states = fill(JS.FREE_NONBASIC,n+N); states[basis] .= JS.BASIC
    JS.SimplexWorkspace(problem,options,progress,zeros(n+N),
        vcat(problem.column_lower,problem.row_lower),vcat(problem.column_upper,problem.row_upper),
        JS.Basis(copy(basis),states),zeros(n+N),zeros(n+N),ones(n+N),falses(n+N),factor,
        JS.SimplexScratch(Float64,n,n+N),0,0,false,0,false,false,options.refactorization_interval,
        0,typemax(Int),0,0)
end
function selected_equation(B,x,rhs,basis,j,r,scale,ratio)
    positions = nzrange(B,j)
    Dict("column"=>j,"original_basis_variable"=>basis[j],"rhs_bits"=>bits(rhs[j]),
        "rows"=>B.rowval[positions], "coefficients_bits"=>bits.(B.nzval[positions]),
        "solution_bits"=>bits.(x[B.rowval[positions]]),
        "wide_residual"=>string(r[j]), "wide_scale"=>string(scale[j]),
        "wide_ratio"=>string(ratio[j]))
end
function snapshot(B,x,rhs,basis,policy,label)
    n = length(rhs)
    scratch = JS.SolveQualityScratch(Float64,n)
    q = JS.solve_quality!(scratch,B,x,rhs,policy; transposed=true)
    actual_residual = copy(scratch.residual)
    raw = JS.SolveQualityScratch(Float64,n)
    unsafe = JS._quality_components!(raw.work_residual,raw.work_scale,raw.terms,B,x,rhs,true)
    gamma = JS._quality_roundoff(Float64,raw.terms)
    triggered = unsafe || !all(isfinite,raw.work_residual) || !all(isfinite,raw.work_scale) ||
        gamma > policy.solve_tolerance/4
    branch = "plain"
    if triggered
        native = unsafe ? nothing : JS._compensated_solve_quality!(raw,B,x,rhs,policy,true)
        if isnothing(native)
            branch = "wide"
            reconstructed = JS._wide_solve_quality!(raw,B,x,rhs,policy,true)
        else
            branch = "compensated"
            reconstructed = native
        end
    else
        reconstructed = JS._floating_quality!(raw,raw.work_residual,raw.work_scale,raw.terms,policy)
    end
    @test qualityequal(q,reconstructed)
    @test bitsequal(actual_residual,raw.residual)
    input_bits = JS._stored_quality_bits(Float64,B,x,rhs,policy)
    oracle_bits = max(128,2*input_bits+ndigits(max(size(B)...,1); base=2)+16)
    selected, maximum_ratio, absolute, firstbad, maxindex = setprecision(BigFloat,oracle_bits) do
        r = zeros(BigFloat,n); scale = zeros(BigFloat,n); terms = zeros(Int,n)
        wide_unsafe = JS._quality_components!(r,scale,terms,B,x,rhs,true)
        @test !wide_unsafe
        ratio = [iszero(scale[i]) ? (iszero(r[i]) ? BigFloat(0) : BigFloat(Inf)) : abs(r[i])/scale[i] for i in 1:n]
        maxindex = argmax(ratio)
        bad = findfirst(v->v>policy.solve_tolerance,ratio)
        indices = unique([maxindex, isnothing(bad) ? maxindex : bad, argmax(abs.(r))])
        equations = [selected_equation(B,x,rhs,basis,j,r,scale,ratio) for j in indices]
        equations, string(ratio[maxindex]), string(maximum(abs,r)), isnothing(bad) ? 0 : bad, maxindex
    end
    record = Dict("label"=>label,"quality"=>qualitydict(q),"branch"=>branch,
        "raw_unsafe_range"=>unsafe,"raw_roundoff"=>gamma,"raw_max_terms"=>maximum(raw.terms),
        "diagnostic_oracle_bits"=>oracle_bits,"oracle_max_ratio"=>maximum_ratio,
        "oracle_max_absolute"=>absolute,"first_oracle_bad_column"=>firstbad,
        "max_oracle_ratio_column"=>maxindex,"selected_equations"=>selected,
        "point_hash"=>digestarrays(x),"residual_hash"=>digestarrays(actual_residual))
    record,q,actual_residual
end
function gate(beforeq, trialq, before, delta, trial)
    !all(isfinite,delta) && return "nonfinite_correction"
    !all(isfinite,trial) && return "nonfinite_trial"
    !any(trial .!= before) && return "unchanged_trial"
    !trialq.finite && return "nonfinite_trial_quality"
    !(trialq.reliable || JS._refinement_error(trialq)<JS._refinement_error(beforeq)) && return "quality_not_improved"
    "accepted"
end
function diagnose(B,problem,basis,name,result,witness)
    n = size(B,1); rhs = zeros(n); rhs[1] = 1.0; x = zeros(n)
    if name == "UMFPACK"
        preparation = @timed lu(B)
        factor = preparation.value
        delegate = UmfDelegate(factor)
        ldiv!(x,transpose(factor),rhs)
        controls = Dict("control"=>copy(factor.control),"IRSTEP"=>factor.control[SparseArrays.UMFPACK.JL_UMFPACK_IRSTEP])
    else
        minimum = name == "native-KLU" ? typemax(Int) : 4096
        preparation = @timed prepare_staged(B; minimum_dimension=minimum)
        ctx,_ = preparation.value
        @test (ctx.forward isa GraphContext) == (name=="local-KLU")
        unit_btran!(x,ctx,rhs,1,name=="native-KLU" ? Val(:native) : Val(:local))
        delegate = KluDelegate(ctx)
        controls = Dict("tol"=>ctx.forward.native.common.tol,"btf"=>Int(ctx.forward.native.common.btf),
            "ordering"=>Int(ctx.forward.native.common.ordering),"scale"=>Int(ctx.forward.native.common.scale),
            "maxwork"=>ctx.forward.native.common.maxwork,"initial_path"=>ctx.forward.last_path)
    end
    push!(result["preparation"],merge(statistics(preparation),Dict("arm"=>name,"stage"=>"private-factor-and-context")))
    initial = copy(x); f = tracefactor(delegate,x); ws = workspace(problem,basis,f)
    policy = ws.progress.numerical_policy
    @test policy.solve_tolerance == 256eps(Float64) && policy.max_refinements==3
    @test !policy.solve_refinement && !policy.adaptive_refactor && !policy.hypersparse
    @test matrixhash(JS._basis_matrix!(ws))==matrixhash(B)
    initial_record,initialq,_ = snapshot(B,x,rhs,basis,policy,"initial")
    stop = NoStop(0)
    finalq = JS.refine_basis_solve!(x,ws,rhs,policy,stop; transposed=true)
    final = copy(x)
    final_record,checkq,_ = snapshot(B,x,rhs,basis,policy,"final")
    @test qualityequal(finalq,checkq)
    name != "UMFPACK" && (@test !initialq.reliable && !finalq.reliable)
    corrections = Any[]
    for k in 1:f.calls
        before,delta = f.before[k],f.delta[k]
        before_record,beforeq,residual = snapshot(B,before,rhs,basis,policy,"before-correction-$k")
        @test bitsequal(residual,f.rhs[k])
        trial = [before[i]+delta[i] for i in eachindex(before)]
        trial_record,trialq,_ = snapshot(B,trial,rhs,basis,policy,"trial-correction-$k")
        reason = gate(beforeq,trialq,before,delta,trial)
        adopted = k<f.calls ? f.before[k+1] : final
        accepted = reason=="accepted"
        @test bitsequal(adopted,accepted ? trial : before)
        push!(corrections,Dict("index"=>k,"gate"=>reason,"accepted"=>accepted,
            "changed_components"=>count(trial .!= before),"correction_rhs_hash"=>digestarrays(f.rhs[k]),
            "correction_hash"=>digestarrays(delta),"before"=>before_record,"trial"=>trial_record))
    end
    @test all(isfinite,initial) && all(isfinite,final)
    @test bitsequal(rhs,[i==1 ? 1.0 : 0.0 for i in 1:n])
    @test ws.basis.basic_indices==basis && all(iszero,ws.primal) && all(iszero,ws.reduced_costs)
    record = Dict("name"=>name,"controls"=>controls,"initial"=>initial_record,"final"=>final_record,
        "correction_calls"=>f.calls,"stop_calls"=>stop.calls,"corrections"=>corrections,
        "policy"=>Dict(string(k)=>getfield(policy,k) for k in fieldnames(typeof(policy))))
    push!(result["arms"],record)
    push!(witness,(name=name,initial=initial,final=final,
        before=[copy(f.before[k]) for k in 1:f.calls],
        correction_rhs=[copy(f.rhs[k]) for k in 1:f.calls],delta=[copy(f.delta[k]) for k in 1:f.calls]))
    println(name," initial=",qualitydict(initialq)," final=",qualitydict(finalq)," corrections=",f.calls);flush(stdout)
end
function main(out,witness_path)
    isfile(out) && error("result path already exists")
    ispath(witness_path) && error("witness path already exists")
    @test sizeof(Int)==8 && Threads.nthreads()==1 && BLAS.get_num_threads()==1
    result = Dict{String,Any}("completed"=>false,"arms"=>Any[],"preparation"=>Any[],
        "scope"=>"one captured runtime-30000 B0, unit RHS row 1; diagnostic, not benchmark or LP solve")
    witness = Any[]
    @testset "First rejected KLU weight RHS" begin
        entries = TOML.parsefile(joinpath(D,"inputs.toml"))["cases"]
        @test length(entries)==1
        entry = only(entries)
        @test bytes2hex(open(sha256,entry["path"]))==entry["sha256"]
        loaded = @timed deserialize(entry["path"])
        data = loaded.value; A = data.A; basis = copy(data.basis); initial_basis = copy(basis)
        @test data.input_sha256==entry["input_sha256"]
        push!(result["preparation"],merge(statistics(loaded),Dict("stage"=>"deserialize")))
        A_hash = matrixhash(A)
        assembled = @timed assemble(A,basis); B = assembled.value
        push!(result["preparation"],merge(statistics(assembled),Dict("stage"=>"assemble-B0")))
        B_hash = matrixhash(B)
        @test B_hash=="7b6ab789d7f49d73ec163eee3e2c5c5e9207dadd5f66a3b31972755b367c6d5c"
        holder = @timed JS.LinearProblem(A,zeros(size(A,2));column_lower=fill(nothing,size(A,2)),name="first-rejected-weight-rhs")
        problem = holder.value
        push!(result["preparation"],merge(statistics(holder),Dict("stage"=>"algebraic-holder")))
        for name in ("native-KLU","local-KLU","UMFPACK")
            diagnose(B,problem,basis,name,result,witness)
            @test matrixhash(B)==B_hash && matrixhash(A)==A_hash && matrixhash(problem.A)==A_hash
            GC.gc()
        end
        @test data.basis==initial_basis
        result["n"]=size(B,1);result["nnz"]=nnz(B);result["matrix_hash"]=B_hash;result["A_hash"]=A_hash
        result["loaded_libraries"]=[realpath(p) for p in Libdl.dllist() if any(s->occursin(s,basename(p)),("libklu.","libbtf.","libumfpack.","libamd.","libcolamd.","libsuitesparseconfig."))]
        expected = TOML.parsefile(joinpath(D,"library-pins.toml"))["libraries"]
        @test all(p->haskey(expected,p) && bytes2hex(open(sha256,p))==expected[p],result["loaded_libraries"])
        mkpath(dirname(witness_path))
        serialize(witness_path,(basis=basis,rhs=[i==1 ? 1.0 : 0.0 for i in eachindex(basis)],arms=witness))
        result["witness"]=Dict("path"=>witness_path,"bytes"=>filesize(witness_path),"sha256"=>bytes2hex(open(sha256,witness_path)))
        result["completed"]=true
        open(out,"w") do io
            TOML.print(io,result)
        end
    end
end
# Entry is compiled after all new diagnostic methods have been defined.
Base.invokelatest(main,abspath(ARGS[1]),abspath(ARGS[2]))
