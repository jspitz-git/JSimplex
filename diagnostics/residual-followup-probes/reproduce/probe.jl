using JSimplex, SparseArrays, LinearAlgebra, Random, Serialization, TOML, Statistics
const JS = JSimplex
# Process-local probe: the only changed operation skips a zero numerator division
# with a positive denominator, after the original finite checks.
let source = read(joinpath(dirname(pathof(JS)), "dual_simplex.jl"), String)
    start = first(findfirst("function _dual_row_residual_ratio(", source))
    ex, _ = Meta.parse(source, start)
    body = string(ex)
    body = replace(body, "_dual_row_residual_ratio" => "_probe_zero_row_ratio")
    body = replace(body, "worst_ratio = max(worst_ratio, abs(residual) / tolerance)" =>
        "if !(iszero(residual) && tolerance > zero(T)); worst_ratio = max(worst_ratio, abs(residual) / tolerance); end")
    @assert occursin("iszero(residual)", body)
    Core.eval(JS, Meta.parse(body))
end
Base.@noinline function batch(f, args, n)
    for _ in 1:n
        Base.donotdelete(f(args...))
    end
end
function timed_pair(funs, args; n=30)
    times = [Float64[] for _ in funs]; bytes = [Int[] for _ in funs]; allocs = [Int[] for _ in funs]
    for f in funs; batch(f, args, n); end
    for round in 1:9
        for k in (isodd(round) ? eachindex(funs) : reverse(eachindex(funs)))
            GC.gc(); t = @timed batch(funs[k], args, n)
            @assert t.compile_time == 0
            push!(times[k], t.time/n); push!(bytes[k], t.bytes); push!(allocs[k], Base.gc_alloc_count(t.gcstats))
        end
    end
    Dict("seconds"=>times, "median_seconds"=>median.(times), "batch_bytes"=>bytes, "batch_allocations"=>allocs, "calls_per_batch"=>n)
end
function workspace(A::SparseMatrixCSC{T}, basics) where T
    w = JS._initialize_workspace_state(LinearProblem(A, zeros(T, size(A,2))), SolverOptions(T))
    copyto!(w.basis.basic_indices, basics)
    fill!(w.basis.states, JS.AT_LOWER)
    w.basis.states[basics] .= JS.BASIC
    w
end
function measure(name, w, rho, row)
    a = JS._dual_row_residual_ratio(w, rho, row); b = JS._probe_zero_row_ratio(w, rho, row)
    @assert isequal(a,b)
    m,n=size(w.problem.A); A=w.problem.A; zeros_count=0; terms=0
    for (i,j) in enumerate(w.basis.basic_indices)
        residual = i==row ? -one(eltype(A)) : -zero(eltype(A))
        if j<=n
            for p in nzrange(A,j); residual += A.nzval[p]*rho[A.rowval[p]]; terms+=1; end
        else
            residual += -rho[j-n]; terms+=1
        end
        zeros_count += iszero(residual)
    end
    result=timed_pair((JS._dual_row_residual_ratio,JS._probe_zero_row_ratio),(w,rho,row))
    merge!(result,Dict("name"=>name,"type"=>string(eltype(A)),"rows"=>m,"basis_terms"=>terms,"zero_residual_columns"=>zeros_count,"ratio"=>a,"speedup"=>result["median_seconds"][1]/result["median_seconds"][2]))
    B=JS._basis_matrix!(w)
    result["validate"]=timed_pair((JS._validate_basis,), (w,))
    result["assemble"]=timed_pair((JS._assemble_basis_matrix,), (w,B))
    result["basis_matrix"]=timed_pair((JS._basis_matrix!,), (w,))
    println(name," ",result["type"]," zero=",zeros_count/m," speedup=",result["speedup"]," assembly=",result["assemble"]["median_seconds"]);flush(stdout)
    result
end
function main(out)
    @assert Threads.nthreads()==BLAS.get_num_threads()==1
    rows=[];rng=MersenneTwister(749)
    for T in (Float32,Float64), kind in (:sparse,:dense,:mostly_zero,:zero)
        m=kind==:dense ? 512 : 8000
        A=sprand(rng,T,m,m,kind==:dense ? 1.0 : 0.001)
        rho=randn(rng,T,m)
        kind==:mostly_zero && fill!(view(rho,2:m),zero(T))
        kind==:zero && fill!(rho,zero(T))
        push!(rows,measure(string(kind),workspace(A,collect(1:m)),rho,1))
    end
    for iteration in (1000,10000,30000,50000)
        d=deserialize(".superpowers/simplex-data-movement/runtime-final-v2/solve/row-0-$(iteration).bin")
        push!(rows,measure("runtime_$(iteration)",workspace(d.A,d.basics),d.rho,d.row))
    end
    d=deserialize(".superpowers/dual-allocation-cost/census/cost-medium.toml-state-0-1000.bin")
    w=JS._initialize_workspace_state(d.problem,d.options)
    copyto!(w.basis.basic_indices,d.basics);copyto!(w.basis.states,d.states)
    # The census stored the tableau row, not the BTRAN vector. Explicitly label
    # this control as a random vector on a captured medium basis.
    push!(rows,measure("medium_basis_random_rho",w,randn(rng,length(d.basics)),1))
    open(out,"w") do io; TOML.print(io,Dict("cases"=>rows)); end
end
Base.invokelatest(main,only(ARGS))
