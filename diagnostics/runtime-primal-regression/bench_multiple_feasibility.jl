# Cold recovery only. Setup and warmup are outside the measured repair call.
# Arguments: original solver.jl source, output.toml
using JSimplex, SparseArrays, LinearAlgebra, Statistics, TOML
const JS=JSimplex
const no_stop=()->false

function fixture(dense,k)
    m=dense ? 128 : 512
    B=dense ? sparse([i==j ? 2.0 : 1/1024 for i in 1:m,j in 1:m]) :
        spdiagm(0=>fill(2.0,m))
    A=[B B spzeros(m,1); spzeros(1,2m) sparse([1.0;;])]
    p=LinearProblem(A,vcat(zeros(2m),1.0);row_lower=zeros(m+1),
        row_upper=zeros(m+1),column_upper=vcat(fill(0.125,m),fill(0.125,k),zeros(m-k),nothing))
    o=SolverOptions(algorithm=:primal,basis_update=:huangfu_hall,verbose=false,
        presolve=false,scaling=:off,iteration_limit=1000)
    d=JS.SimplexDiagnostics(;kernel_timing=true)
    ws=JS.initialize_workspace(p,o;progress=JS.SimplexProgressContext(p;diagnostics=d))
    ws.basis=JS.Basis(collect(1:m+1),fill(JS.AT_LOWER,3m+2))
    ws.basis.basic_indices[end]=2m+1
    ws.basis.states[ws.basis.basic_indices].=JS.BASIC
    ws.basis.states[m+1:m+k].=JS.AT_UPPER
    JS.recompute!(ws;refactorize=true)
    @assert last(JS.primal_infeasibility_summary(ws))==k
    return ws,d
end

function sample(f,dense,k)
    ws,d=fixture(dense,k)
    before=copy(d.kernel_calls)
    t=@timed f(ws,no_stop)
    return Dict("accepted"=>t.value,"seconds"=>t.time,"compile_seconds"=>t.compile_time,
        "bytes"=>t.bytes,"allocations"=>Base.gc_alloc_count(t.gcstats),
        "pivots"=>ws.iterations,"remaining_violations"=>last(JS.primal_infeasibility_summary(ws)),
        "ftran"=>d.kernel_calls[:ftran]-before[:ftran],
        "btran"=>d.kernel_calls[:btran]-before[:btran],
        "refactorizations"=>d.kernel_calls[:refactorization]-before[:refactorization])
end

function main(original,output)
    ispath(output) && error("Use a fresh output file")
    BLAS.set_num_threads(1)
    source=read(original,String)
    start=findfirst("function _try_postsolve_feasibility_pivot!",source).start
    finish=findnext("function _project_postsolve_basis!",source,start).start-1
    method=replace(source[start:finish],"_try_postsolve_feasibility_pivot!"=>"_baseline_feasibility_repair!")
    baseline=Core.eval(JS,Meta.parse(strip(method)))
    records=Dict{String,Any}[]
    # Invoke the experiment in the new method world, outside timed sections.
    Base.invokelatest() do
        for dense in (false,true), k in (1,6), (name,f) in
            (("baseline",baseline),("fixed",JS._try_postsolve_feasibility_pivot!))
            warm=sample(f,dense,k)
            samples=[sample(f,dense,k) for _ in 1:5]
            @assert all(s["accepted"]==(name=="fixed" || k==1) for s in samples)
            push!(records,Dict("variant"=>name,"dense"=>dense,"initial_violations"=>k,
                "rows"=>dense ? 129 : 513,"warmup"=>warm,"samples"=>samples,
                "median_seconds"=>median(s["seconds"] for s in samples),
                "median_bytes"=>median(s["bytes"] for s in samples)))
        end
    end
    report=Dict("julia"=>string(VERSION),"architecture"=>string(Sys.ARCH),
        "blas_threads"=>BLAS.get_num_threads(),"records"=>records,
        "scope"=>"Recovery calls only, instrumented kernel counts. Setup and warmup excluded. Multi-violation baseline does no repair, so differing timings do not measure speedup. Five samples do not establish general performance.")
    open(output,"w") do io; TOML.print(io,report;sorted=true);end
end
length(ARGS)==2 || error("Expected: original-solver.jl output.toml")
main(ARGS...)
