using JSimplex, Test, LinearAlgebra, SparseArrays, Serialization, SHA, TOML, Logging
const J = JSimplex
const OLD = "/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl/diagnostics/klu-weight-btran/2026-10-29"
const OUT = abspath(ARGS[1])
function digestarrays(a...)
    io=IOBuffer()
    for v in a
        write(io,Int(length(v))); write(io,v)
    end
    bytes2hex(sha256(take!(io)))
end
matrixhash(B)=digestarrays(B.colptr,B.rowval,B.nzval)
function assemble(A,basis)
    m,n=size(A); ptr=Int[1]; rows=Int[]; values=Float64[]
    for column in basis
        if column<=n
            for k in nzrange(A,column)
                push!(rows,A.rowval[k]); push!(values,A.nzval[k])
            end
        else
            1<=column-n<=m || error("invalid artificial column")
            push!(rows,column-n); push!(values,-1.0)
        end
        push!(ptr,length(rows)+1)
    end
    SparseMatrixCSC(m,m,ptr,rows,values)
end
function workspace(p,basis,B)
    m,n=size(p.A)
    options=SolverOptions(Float64;algorithm=:dual,pricing=:steepest_edge,
        simplex_strategy=:legacy,basis_update=:pfi,basis_refactorization=:native,
        verbose=false,time_limit=Inf)
    diagnostics=J.SimplexDiagnostics()
    progress=J.SimplexProgressContext(p;diagnostics,
        numerical_policy=J.NumericalPolicy(Float64,options))
    states=fill(J.FREE_NONBASIC,m+n);states[basis].=J.BASIC
    factor=J._basis_factorization(B,options)
    J.SimplexWorkspace(p,options,progress,zeros(m+n),
        vcat(p.column_lower,p.row_lower),vcat(p.column_upper,p.row_upper),J.Basis(basis,states),
        zeros(m+n),zeros(m+n),ones(m+n),falses(m+n),factor,J.SimplexScratch(Float64,m,m+n),
        0,0,false,0,false,false,options.refactorization_interval,0,typemax(Int),0,0)
end
stats(t)=Dict{String,Any}("seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),
    "compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time,"gc_seconds"=>t.gctime)
function save(name,value)
    path=joinpath(OUT,name)
    ispath(path) && error("output exists: $path")
    open(path,"w") do io
        TOML.print(io,value)
    end
end
function timed_trial(ws,c,algorithm)
    stop=J._guard_stop_callback(()->false)
    t=@timed J._recovery_trial_with_pricing(ws,c,stop;algorithm)
    t
end
function run_case(A,basis,id,expected)
    B=assemble(A,basis);ah=matrixhash(A);bh=matrixhash(B)
    @test bh==expected["matrix_hash"]
    # Exact old algebra holder: captured A, zero costs and unbounded unused bounds.
    prep=@timed begin
        p=J.LinearProblem(A,zeros(size(A,2));column_lower=fill(nothing,size(A,2)),name="captured-basis-weight-harness")
        a=workspace(p,basis,B);b=workspace(p,basis,B)
        (a,b,J.checkpoint_basis(a),J.checkpoint_basis(b))
    end
    strict,dual,c1,c2=prep.value; strictfactor=strict.factorization;dualfactor=dual.factorization
    original=Any[];pairs=Any[];pending=nothing
    for round in 1:7
        direct=@timed J._rebuild_recovery_weights!(strict,()->false)
        @test direct.value===false
        record=stats(direct);record["round"]=round;record["accepted"]=direct.value;push!(original,record)
        for algorithm in (iseven(round) ? (:dual,:unspecified) : (:unspecified,:dual))
            ws=algorithm===:dual ? dual : strict; checkpoint=algorithm===:dual ? c2 : c1
            t=timed_trial(ws,checkpoint,algorithm);r=t.value
            if algorithm===:dual
                @test r isa J._RecoveryTrialResult
                if r isa J._RecoveryTrialResult
                    @test r.devex_fallback && r.failed_weight_row>=1
                    @test J._weight_pricing(r.workspace,:dual)===:devex
                    @test r.workspace.basis.basic_indices==basis
                    @test J._finite_workspace(r.workspace) && J._recomputed_basis_reliable(r.workspace)
                    pending=r
                end
            else
                @test isnothing(r)
            end
            @test ws.factorization===(algorithm===:dual ? dualfactor : strictfactor)
            @test ws.iterations==0 && ws.basis.basic_indices==basis
            rec=stats(t);merge!(rec,Dict("round"=>round,"algorithm"=>string(algorithm),
                "returned_trial"=>!isnothing(r),"failed_weight_row"=>isnothing(r) ? 0 : r.failed_weight_row))
            push!(pairs,rec)
        end
        # Preparation/collection outside all timed whole-constructor windows.
        GC.gc()
    end
    @test strict.refactorizations==7 && dual.refactorizations==7
    @test all(iszero,strict.primal) && all(iszero,dual.primal)
    @test J._weight_pricing(strict,:dual)===:steepest_edge
    probe=J._rebuild_recovery_weights_result!(strict,()->false;algorithm=:dual)
    @test !probe.ok && probe.fallback_ready && probe.failed_row>=1
    @test probe.reason==J._weight_finite_inconclusive
    @test probe.refinement_cause in (J._refine_unchanged,J._refine_not_improved,J._refine_limit)
    published=false
    if pending isa J._RecoveryTrialResult
        pub=@timed J._publish_recovery!(dual,pending,:repair,J._guard_stop_callback(()->false))
        published=pub.value
        @test published
        @test dual.factorization===pending.workspace.factorization && dual.factorization!==dualfactor
        @test J._weight_pricing(dual,:dual)===:devex && dual.dual_devex_fallback
        @test all(isone,dual.pricing_weights)
        @test count(dual.devex_reference)==length(basis) && all(dual.devex_reference[basis])
        @test dual.basis.basic_indices==basis && dual.basis.states==c2.basis.states
        @test J._finite_workspace(dual) && J._recomputed_basis_reliable(dual)
        @test J.event_count(dual.progress.diagnostics,:pricing_devex)==1
        @test J.event_count(dual.progress.diagnostics,:pricing_weight_rejected)==1
        @test J.event_count(dual.progress.diagnostics,:repair)==1
        @test dual.iterations==strict.iterations==0
        publication=stats(pub)
    else
        publication=Dict{String,Any}()
    end
    @test matrixhash(A)==ah && matrixhash(B)==bh
    @test strict.costs==dual.costs==c1.costs==c2.costs
    @test strict.lower==dual.lower==c1.lower==c2.lower && strict.upper==dual.upper==c1.upper==c2.upper
    for rec in pairs
        if rec["round"]>2
            @test rec["compile_seconds"]==0 && rec["recompile_seconds"]==0
        end
    end
    result=Dict("id"=>id,"matrix_hash"=>bh,"A_hash"=>ah,"rows"=>size(A,1),"columns"=>size(A,2),
        "B_nnz"=>nnz(B),"preparation"=>stats(prep),"direct_strict"=>original,"trials"=>pairs,
        "publication"=>publication,"published"=>published,"pricing"=>string(J._weight_pricing(dual,:dual)),
        "iterations"=>dual.iterations,"failed_weight_row"=>probe.failed_row,
        "refinement_cause"=>string(probe.refinement_cause),"weight_reason"=>string(probe.reason),
        "events"=>Dict(string(k)=>v for (k,v) in dual.progress.diagnostics.counts if v!=0),
        "policy"=>Dict(string(k)=>getfield(dual.progress.numerical_policy,k) for k in fieldnames(typeof(dual.progress.numerical_policy))),
        "scope"=>"same captured algebra holder; native production PFI/UMFPACK; no LP solve or simplex iteration")
    save(id*".toml",result)
    println("CASE_COMPLETE ",id," published=",published," iterations=",dual.iterations);flush(stdout)
end
function main()
    @test pathof(JSimplex)=="/home/jspitz/JSimplex.jl/src/JSimplex.jl"
    @test Threads.nthreads()==1 && BLAS.get_num_threads()==1
    old=TOML.parsefile(joinpath(OLD,"results-2.toml"));cases=Dict(c["id"]=>c for c in old["cases"])
    @testset "Saved runtime basis Devex recovery" begin
        for entry in TOML.parsefile(joinpath(OLD,"inputs.toml"))["cases"]
            startswith(entry["id"],"runtime-") || continue
            @test bytes2hex(open(sha256,entry["path"]))==entry["sha256"]
            data=deserialize(entry["path"]);A=data.A;basis=copy(data.basis);initial=copy(basis);ah=matrixhash(A)
            @test data.input_sha256==entry["input_sha256"]
            for anchor in (0,80,160)
                if anchor>0
                    for state in anchor-79:anchor
                        row,enter=data.steps[state];basis[row]=enter
                    end
                end
                id=entry["id"]*"-B"*string(anchor)
                with_logger(NullLogger()) do
                    run_case(A,basis,id,cases[id])
                end
                GC.gc()
            end
            @test data.basis==initial && matrixhash(A)==ah
        end
        save("completion.toml",Dict("completed"=>true,"cases"=>6,"iterations"=>0,
            "julia"=>string(VERSION),"architecture"=>string(Sys.ARCH),"blas_threads"=>BLAS.get_num_threads(),
            "scope"=>"bounded component recovery only; old KLU experiment remains rejected"))
    end
end
main()
