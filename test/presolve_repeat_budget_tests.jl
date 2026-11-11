using JSimplex, SparseArrays, Test, Serialization, SHA

_repeat_digest(x) = begin
    io=IOBuffer(); serialize(io,x); bytes2hex(sha256(take!(io)))
end
function _repeat_chain(T)
    LinearProblem(sparse(T[1 1 1;1 -1 -1]),zeros(T,3);
        row_lower=zeros(T,2),column_lower=fill(nothing,3),column_upper=fill(nothing,3))
end
function _repeat_checks(T)
    R=JSimplex._PresolveRepeat
    p=_repeat_chain(T); base=JSimplex.identity_presolve(p)
    history=JSimplex._PostsolveHistory(T); before=_repeat_digest(p)
    q=JSimplex._augment_inequalities(base,p,T(1e-7),history,()->false,false;rounded_costs=T!==BigFloat)
    @test size(q.problem.A)==(0,0)
    @test count(s->s isa JSimplex.InequalityActivationStep,q.postsolve_stack)>=2
    @test length(history.metadata)==length(history.propagation)==length(q.postsolve_stack)
    @test all(m.step===step for (m,step) in zip(history.metadata,q.postsolve_stack))
    @test JSimplex._original_primal_feasible(p,JSimplex.postsolve_primal(q,T[]),T(1e-7))
    @test _repeat_digest(p)==before && isnothing(R.current())
    # Cancellation after the first committed activation retains a usable prefix.
    history=JSimplex._PostsolveHistory(T)
    prefix=JSimplex._augment_inequalities(base,p,T(1e-7),history,()->!isempty(history.metadata),false;rounded_costs=false)
    @test size(prefix.problem.A)==(1,2)
    @test length(history.metadata)==length(history.propagation)==length(prefix.postsolve_stack)
    @test JSimplex._original_primal_feasible(p,JSimplex.postsolve_primal(prefix,zeros(T,2)),T(1e-7))
    saved=_repeat_digest(history)
    @test JSimplex._augment_inequalities(prefix,p,T(1e-7),history,()->true,false;rounded_costs=false)===prefix
    @test _repeat_digest(history)==saved
    @test_throws ErrorException JSimplex._augment_inequalities(prefix,p,T(1e-7),history,()->error("injected stop"),false;rounded_costs=false)
    @test isnothing(R.current()) && _repeat_digest(history)==saved
    b=R.Ledger(limit=60)
    wide=LinearProblem(sparse(ones(T,30,1)),zeros(T,1);row_upper=zeros(T,30),column_lower=[nothing],column_upper=[nothing])
    R.infer_shared(wide,b);R.infer_shared(wide,b)
    @test all(getfield(b,k)<=60 for k in (:term_visits,:proof_edges,:expansion_edges,:singleton_term_visits))
    @test b.rounds<=8
    b=R.Ledger(limit=1);b.term_visits=1
    cs,stats=R.infer_shared(p,b)
    @test isempty(cs) && isempty(stats) && b.term_visits==1
    R.with_budget(b) do
        h=JSimplex._PostsolveHistory(T)
        @test JSimplex._augment_inequalities(base,p,T(1e-7),h,()->false,false;rounded_costs=false)===base
        @test b.term_visits==1 && R.current()===b && isempty(h.metadata)
    end
    b=R.Ledger();b.sparse_updates=199999
    eq=LinearProblem(sparse(T[1 1;1 -1]),T[1,0];row_lower=T[3,1],row_upper=T[3,1],column_lower=fill(nothing,2),column_upper=fill(nothing,2))
    R.with_budget(b) do
        @test !isempty(JSimplex.aggregate_sparse_equalities(eq).postsolve_stack)
        @test b.sparse_updates==200000 && b.sparse_records==1
        @test isempty(JSimplex.aggregate_sparse_equalities(eq).postsolve_stack)
        @test b.sparse_updates==200000 && b.sparse_records==1
        b.sparse_records=50000;b.dependent_work=200000
        dep=LinearProblem(sparse(T[1 1;2 2]),zeros(T,2);row_upper=T[3,6],column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        @test size(JSimplex.reduce_dependent_rows(dep).problem.A,1)==2
        @test b.dependent_work==200000
    end
    @test isnothing(R.current())
    # A nested binding restores its caller, including exceptional exit.
    R.with_budget(b) do
        child=R.Ledger()
        @test_throws ErrorException R.with_budget(()->error("nested"),child)
        @test R.current()===b
    end
    @test isnothing(R.current())
end

@testset "Cumulative certified inequality reduction budget" begin
    for T in (Float32,Float64)
        _repeat_checks(T)
    end
    for bits in (32,64,128,240,256,512)
        setprecision(BigFloat,bits) do
            _repeat_checks(BigFloat)
            p=setprecision(BigFloat,320) do;_repeat_chain(BigFloat);end
            before=_repeat_digest(p);env=(precision(BigFloat),rounding(BigFloat))
            base=JSimplex.identity_presolve(p);h=JSimplex._PostsolveHistory(BigFloat)
            result=JSimplex._augment_inequalities(base,p,BigFloat(1e-7),h,()->false,false;rounded_costs=false)
            @test size(result.problem.A)==(0,0)
            @test _repeat_digest(p)==before && env==(precision(BigFloat),rounding(BigFloat))
            @test !JSimplex._allow_rounded_presolve_costs(BigFloat,true)
            for mode in (RoundDown,RoundUp,RoundToZero,RoundFromZero)
                setrounding(BigFloat,mode) do
                    h=JSimplex._PostsolveHistory(BigFloat);saved=_repeat_digest(h)
                    @test JSimplex._augment_inequalities(base,p,BigFloat(1e-7),h,()->false,false;rounded_costs=false)===base
                    @test _repeat_digest(h)==saved && isnothing(JSimplex._PresolveRepeat.current())
                end
            end
        end
    end
end
