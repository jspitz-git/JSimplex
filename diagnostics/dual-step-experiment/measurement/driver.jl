using JSimplex,Test,LinearAlgebra,SparseArrays
const J=JSimplex
const W=normpath(joinpath(@__DIR__,"..","..",".."))
@assert realpath(pathof(J))==joinpath(W,"src","JSimplex.jl")
@assert Threads.nthreads()==1 && BLAS.get_num_threads()==1
include(joinpath(W,"experimental","dual_engine","ExperimentalDualEngine.jl"));const E=ExperimentalDualEngine
include(joinpath(W,"experimental","dual_engine","test","driver_fixtures.jl"))
include("inspection.jl")
emit(tag,fields...)=begin println(tag," ",join((string(k,"=",v) for (k,v) in fields)," "));flush(stdout);nothing end
function cases()
    out=[(id="n$(n)_$(dense ? "dense" : "sparse")",n=n,dense=dense,file="",presolve=false,designated=true) for n in (16,64) for dense in (false,true)]
    for name in ("afiro.mps","netlib/adlittle.mps","netlib/sc50a.mps","generated/degenerate-box.mps","generated/phase-one.mps","generated/scaled-diagonal.mps"),pre in (false,true)
        push!(out,(id="mps_"*replace(name,"/"=>"_","."=>"_")*"_p$(Int(pre))",n=0,dense=false,file=name,presolve=pre,designated=false))
    end
    out
end
function prepare(c)
    p=isempty(c.file) ? driver_problem(c.n;dense=c.dense) : J.read_mps(joinpath(W,"test","fixtures","solver",c.file))
    o=isempty(c.file) ? driver_options() : J.SolverOptions(Float64;pricing=:devex,basis_update=:pfi,simplex_strategy=:legacy,presolve=c.presolve,verbose=false)
    (p=p,o=o,before=deepcopy(p))
end
function evaluate(::Val{:reference},p,o)
    (solution=J.solve(p;options=o),record=nothing,diagnostics=nothing,probe=nothing)
end
function evaluate(::Val{:reference_counts},p,o)
    d=J.SimplexDiagnostics(kernel_timing=true)
    (solution=J._solve_diagnosed(p,d;options=o),record=nothing,diagnostics=d,probe=nothing)
end
function evaluate(::Val{:candidate},p,o)
    r=E.SolveRecord();s=E.solve_experimental(p;options=o,record=r)
    (solution=s,record=r,diagnostics=nothing,probe=nothing)
end
function evaluate(::Val{:inspection},p,o)
    r=E.SolveRecord();probe=Dict{String,Any}();d=J.SimplexDiagnostics();clock=J._SolveDeadline(time_ns(),o.time_limit);r.start_ns=clock.start_ns
    hook=E.Task6Adapter(r,clock,E.NoEvents(),false,probe)
    s=J._solve_diagnosed(p,d;options=o,clock,dual_engine=hook)
    (solution=s,record=r,diagnostics=d,probe=probe)
end
function same_input(p,before)
    all(k->isequal(getfield(p,k),getfield(before,k)),fieldnames(typeof(p)))
end
function valid_solution(p,o,before,s,target)
    s.status==J.OPTIMAL && !isnothing(s.primal) && !isnothing(s.objective_value) &&
        J._original_primal_feasible(p,s.primal,o.primal_tolerance) &&
        (isnan(target)||isapprox(s.objective_value,target;rtol=1e-6,atol=1e-6)) && same_input(p,before)
end
function work_fields(r)
    out=Pair{String,Any}[]
    for (prefix,counts) in (("EC",r.engine_counts),("KC",r.kernel_counts),("RC",r.repair_counts))
        for k in fieldnames(typeof(counts));push!(out,string(prefix,"_",k)=>getfield(counts,k));end
    end
    for k in (:entries,:imports,:import_attempts,:import_failures,:exports,:legacy_fallbacks,:original_retries,:original_cleanups,:original_recoveries,:export_entries)
        push!(out,string(k)=>getfield(r,k))
    end
    for k in sort!(collect(keys(r.legacy_counts)));push!(out,"LD_"*string(k)=>r.legacy_counts[k]);end
    out
end
function sample(c,p,o,before,arm,pair,phase,target)
    t=@timed evaluate(Val(arm),p,o)
    s=t.value.solution;r=t.value.record
    emit("SAMPLE",:case=>c.id,:phase=>phase,:pair=>pair,:arm=>arm,:seconds=>t.time,:bytes=>t.bytes,
        :allocs=>Base.gc_alloc_count(t.gcstats),:gctime=>t.gctime,:compile=>t.compile_time,:recompile=>t.recompile_time,
        :status=>s.status,:objective=>(isnothing(s.objective_value) ? NaN : s.objective_value),
        :iterations=>s.statistics.iterations,:refactors=>s.statistics.refactorizations,
        :record_bytes=>(isnothing(r) ? 0 : Base.summarysize(r)),
        (isnothing(r) ? Pair{String,Any}[] : work_fields(r))...)
    check=@timed valid_solution(p,o,before,s,target)
    emit("CHECK",:case=>c.id,:phase=>phase,:pair=>pair,:arm=>arm,:passed=>check.value,:seconds=>check.time,:bytes=>check.bytes,:allocs=>Base.gc_alloc_count(check.gcstats))
    @test check.value
    @test t.time>=0 && t.bytes>=0 && Base.gc_alloc_count(t.gcstats)>=0
    if phase=="measure";@test t.compile_time==t.recompile_time==0.;end
    if !isnothing(r)
        @test r.entries<=1 && r.legacy_fallbacks<=1 && r.import_failures==0
        if c.designated
            @test r.accepted_pivots>0 && r.legacy_fallbacks==r.original_retries==r.original_cleanups==r.original_recoveries==0
        end
    end
    s.objective_value
end
function qualify_case(c,p,o,before)
    baseline=evaluate(Val(:reference),p,o);instrumented=evaluate(Val(:reference_counts),p,o)
    target=baseline.solution.objective_value
    candidate=evaluate(Val(:candidate),p,o);inspection=evaluate(Val(:inspection),p,o)
    for x in (baseline,instrumented,candidate,inspection);@test valid_solution(p,o,before,x.solution,target);end
    @test baseline.solution.primal==instrumented.solution.primal
    @test baseline.solution.statistics.iterations==instrumented.solution.statistics.iterations
    @test baseline.solution.statistics.refactorizations==instrumented.solution.statistics.refactorizations
    @test candidate.solution.primal==inspection.solution.primal
    @test candidate.solution.statistics.iterations==inspection.solution.statistics.iterations
    @test candidate.solution.statistics.refactorizations==inspection.solution.statistics.refactorizations
    for k in (:engine_counts,:kernel_counts,:repair_counts)
        a=getfield(candidate.record,k);b=getfield(inspection.record,k)
        @test all(i->getfield(a,i)==getfield(b,i),1:fieldcount(typeof(a)))
    end
    r=candidate.record
    emit("QUAL",:case=>c.id,:status=>candidate.solution.status,:reference=>baseline.solution.status,:objective=>target,:designated=>c.designated,work_fields(r)...)
    @test r.entries<=1 && r.legacy_fallbacks<=1 && r.import_failures==0
    if c.designated
        @test r.accepted_pivots>0 && r.legacy_fallbacks==r.original_retries==r.original_cleanups==r.original_recoveries==0
        @test c.dense ? r.dense_prices>0 : r.sparse_prices>0
    end
    d=instrumented.diagnostics
    emit("REFERENCE_WORK",:case=>c.id,([string("event_",k)=>v for (k,v) in sort!(collect(d.counts);by=first)])...,([string("kernel_",k)=>v for(k,v) in sort!(collect(d.kernel_calls);by=first)])...)
    for label in sort!(collect(keys(inspection.probe)))
        data=inspection.probe[label]
        emit("INSPECT",:case=>c.id,:stage=>label,(sort!(collect(data);by=first))...)
    end
end
function run_task6(mode)
    mode in ("qualify","compare")||throw(ArgumentError("mode"))
    @testset "Task6 $(mode) whole verified solves" begin
        @test mode in ("qualify","compare")
        for c in cases()
            @testset "$(c.id)" begin
                emit("CASE_BEGIN",:case=>c.id,:mode=>mode)
                prep=@timed prepare(c);p=prep.value.p;o=prep.value.o;before=prep.value.before
                emit("PREP",:case=>c.id,:seconds=>prep.time,:bytes=>prep.bytes,:allocs=>Base.gc_alloc_count(prep.gcstats),:compile=>prep.compile_time,:recompile=>prep.recompile_time,:m=>size(p.A,1),:n=>size(p.A,2),:nnz=>nnz(p.A))
                if mode=="qualify"
                    qualify_case(c,p,o,before)
                else
                    target=NaN
                    for pair in 1:2
                        arms=isodd(pair) ? (:reference,:candidate) : (:candidate,:reference)
                        for arm in arms
                            obj=sample(c,p,o,before,arm,pair,"warm",target)
                            isnan(target)&&(target=obj)
                        end
                    end
                    release=@timed GC.gc()
                    emit("PREP_GC",:case=>c.id,:seconds=>release.time,:bytes=>release.bytes,:allocs=>Base.gc_alloc_count(release.gcstats))
                    for pair in 1:5
                        arms=isodd(pair) ? (:reference,:candidate) : (:candidate,:reference)
                        for arm in arms;sample(c,p,o,before,arm,pair,"measure",target);end
                    end
                end
                emit("CASE_DONE",:case=>c.id,:mode=>mode)
            end
        end
        if mode=="qualify"
            @testset "honest verified legacy boundary" begin
                p=J.LinearProblem(sparse(reshape([-1.],1,1)),[1.];row_lower=[1.]);o=driver_options();r=E.SolveRecord()
                baseline=J.solve(p;options=o);s=E.solve_experimental(p;options=o,record=r)
                emit("FALLBACK",:status=>s.status,:reference=>baseline.status,work_fields(r)...)
                @test s.status==baseline.status==J.INFEASIBLE
                @test isnothing(s.primal) && isnothing(s.objective_value)
                @test r.accepted_pivots==0 && r.legacy_fallbacks==1 && r.exports==1
            end
        end
    end
    println("TASK6_COMPLETED ",mode);flush(stdout)
end
run_task6(only(ARGS))
