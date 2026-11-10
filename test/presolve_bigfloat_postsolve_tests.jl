using JSimplex, Test, SparseArrays, SHA, Serialization

module BigFloatPostsolveFixtures
using JSimplex, SparseArrays, SHA, Serialization
const JS=JSimplex
digest(x)=begin io=IOBuffer();serialize(io,x);bytes2hex(sha256(take!(io))) end
function propagation(p)
    builder=JS._PropagationHistory.Builder(BigFloat)
    q=JS._propagate_row_bounds(p,trues(size(p.A,1));history=builder)
    return q,JS._PropagationHistory.finish!(builder,p)
end
function model()
    LinearProblem(sparse(BigFloat[1 1 1;0 1 0]),BigFloat[-1,-2,0];
        row_upper=BigFloat[3,1],column_lower=BigFloat[0,0,0],column_upper=BigFloat[2,2,2])
end
end

@testset "BigFloat bound hints do not round away a tolerance violation" begin
    JS=JSimplex
    value,tol=setprecision(BigFloat,256) do
        t=BigFloat(1)/BigFloat(2)^24
        t+BigFloat(2)^(-180),t
    end
    for bits in (64,128), mode in (RoundNearest,RoundDown,RoundUp,RoundToZero)
        setprecision(BigFloat,bits) do
            setrounding(BigFloat,mode) do
                # Real predicate used when restoring a singleton/equality bound
                # side: rounding abs(value-bound) before comparing loses bits.
                @test !JS._PostsolveLift.at(value,Bound(BigFloat(0)),tol)
                @test JS._PostsolveLift.at(tol,Bound(BigFloat(0)),tol)
                @test precision(value)==256 && precision(tol)==256
                @test precision(BigFloat)==bits && rounding(BigFloat)==mode
            end
        end
    end
end

@testset "BigFloat singleton equality and propagation restore certified hints" begin
    JS=JSimplex;L=JS._PostsolveLift;H=JS._PropagationHistory;F=BigFloatPostsolveFixtures
    for inputbits in (64,256), bits in (64,128,256)
        singleton,equality,propagated=setprecision(BigFloat,inputbits) do
            s=LinearProblem(sparse(reshape(BigFloat[1,1],2,1)),BigFloat[-1];
                row_lower=[BigFloat(1),nothing],row_upper=[nothing,BigFloat(1)],
                column_lower=BigFloat[-10],column_upper=BigFloat[10])
            e=LinearProblem(sparse(reshape(BigFloat[1,1],1,2)),BigFloat[0,1];
                row_lower=BigFloat[3],row_upper=BigFloat[3],
                column_lower=BigFloat[1,0],column_upper=BigFloat[1,10])
            p=LinearProblem(sparse(BigFloat[1 1;0 1]),BigFloat[1,0];
                row_lower=[BigFloat(3),nothing],row_upper=[nothing,BigFloat(1)],
                column_lower=BigFloat[0,0],column_upper=BigFloat[3,2])
            s,e,p
        end
        before=F.digest((singleton,equality,propagated))
        setprecision(BigFloat,bits) do
            o=SolverOptions(BigFloat;verbose=false,scaling=:off,simplex_strategy=:legacy)
            for (p,pass,b,x,y) in (
                (singleton,JS.reduce_singleton_rows,JS.Basis(Int[],[JS.AT_LOWER]),BigFloat[1],BigFloat[]),
                (equality,JS.aggregate_singleton_equalities,JS.Basis([1],[JS.BASIC,JS.AT_UPPER]),BigFloat[1,2],BigFloat[1]))
                q=pass(p);meta=L.metadata(p,q,0)
                snapshot=F.digest((meta,b,x,y))
                rb,ry=L.one(meta,b,y,x,o)
                @test JS._original_witness_certified(p,o,rb,x,ry)
                @test rb.states[1]==(p===singleton ? JS.BASIC : JS.AT_UPPER)
                @test F.digest((meta,b,x,y))==snapshot
            end
            q,g1=F.propagation(propagated);z,g2=F.propagation(q.problem)
            metas=[L.metadata(propagated,q,8),L.metadata(q.problem,z,8)]
            b=JS.Basis([3],[JS.AT_LOWER,JS.AT_UPPER,JS.BASIC]);x=BigFloat[2,1];y=BigFloat[0]
            snapshot=F.digest((metas,g1,g2,b,x,y,o))
            rb,ry,rx=H.chain(metas,[g1,g2],b,y,x,o)
            @test rb.states[1:2]==[JS.BASIC,JS.BASIC]
            @test JS._original_witness_certified(propagated,o,rb,rx,ry)
            @test F.digest((metas,g1,g2,b,x,y,o))==snapshot
            @test precision(BigFloat)==bits
        end
        @test F.digest((singleton,equality,propagated))==before
    end
end

@testset "BigFloat outward propagation history owns stored proof values" begin
    JS=JSimplex;H=JS._PropagationHistory;F=BigFloatPostsolveFixtures
    for bits in (64,128,256), sign in (-1,1)
        p=setprecision(BigFloat,192) do
            LinearProblem(sparse(reshape(BigFloat[3,1],1,2)),BigFloat[sign,0];
                row_lower=sign>0 ? BigFloat[1] : [nothing],
                row_upper=sign<0 ? BigFloat[1] : [nothing],
                column_lower=BigFloat[0,0],column_upper=BigFloat[2,0])
        end
        setprecision(BigFloat,bits) do
            q,g=F.propagation(p)
            @test length(g.events)==1
            if length(g.events)==1
                e=only(g.events)
                @test precision(e.new)==bits && precision(e.old.value)==192
                @test precision(only(g.proofs).bound.value)==192
                @test all(==(192),precision.(g.values))
                x=BigFloat[e.new,0];y=BigFloat[0]
                b=JS.Basis([3],[e.upper ? JS.AT_UPPER : JS.AT_LOWER,JS.AT_LOWER,JS.BASIC])
                o=SolverOptions(BigFloat;verbose=false)
                rb,ry=H.apply(g,b,y,x,o)
                @test rb.basic_indices==[1]
                @test JS._original_witness_certified(p,o,rb,x,ry)
                # Inactive proof and an already nonzero row dual cannot claim
                # this exchange; the original gate must still reject both.
                for (xx,yy) in ((BigFloat[0,0],BigFloat[0]),(x,BigFloat[1]))
                    b=JS.Basis([3],[e.upper ? JS.AT_UPPER : JS.AT_LOWER,JS.AT_LOWER,JS.BASIC])
                    rb,_=H.apply(g,b,copy(yy),xx,o)
                    @test rb.basic_indices==[3]
                end
                @test precision(BigFloat)==bits
            end
        end
    end
end

@testset "BigFloat mixed-cost restoration remains a certified hint" begin
    JS=JSimplex;L=JS._PostsolveLift;F=BigFloatPostsolveFixtures
    p=setprecision(BigFloat,256) do
        LinearProblem(sparse(reshape(BigFloat[1],1,1)),BigFloat[-(1+BigFloat(2)^(-180))];
            row_upper=BigFloat[1],column_lower=BigFloat[0],column_upper=BigFloat[2])
    end
    before=F.digest(p)
    for bits in (64,128,256)
        setprecision(BigFloat,bits) do
            q=JS.reduce_singleton_rows(p);meta=L.metadata(p,q,0)
            @test precision(only(meta.singleton).col.cost)==256
            rb,ry=L.one(meta,JS.Basis(Int[],[JS.AT_UPPER]),BigFloat[],BigFloat[1],
                SolverOptions(BigFloat;verbose=false))
            @test JS._original_witness_certified(p,SolverOptions(BigFloat),rb,BigFloat[1],ry)
            @test F.digest(p)==before
            # A much tighter caller-supplied tolerance must reject loss of the
            # low cost bit. This test does not loosen any solver tolerance.
            strict=setprecision(BigFloat,256) do
                SolverOptions(BigFloat;dual_tolerance=BigFloat(2)^(-200),verbose=false)
            end
            certified=JS._original_witness_certified(p,strict,rb,BigFloat[1],ry)
            @test certified == (bits==256)
        end
    end
end

@testset "BigFloat successful history restores a certified original basis" begin
    JS=JSimplex;F=BigFloatPostsolveFixtures
    for bits in (64,128,256)
        setprecision(BigFloat,bits) do
            p=F.model();o=SolverOptions(BigFloat;verbose=false,scaling=:off)
            h=JS._PostsolveHistory(BigFloat)
            q=JS._presolve_for_solve(p,o.primal_tolerance;history=h)
            r=JS._solve_continuous_dual(q.problem,o;
                progress=JS.SimplexProgressContext(q.problem;witness_problem=q.problem))
            @test r.status==OPTIMAL && !isnothing(r.dual)
            if r.status==OPTIMAL
                before=F.digest((p,q,r,o))
                b,x=JS._postsolve_with_dual(h,q,JS.identity_scaling(q.problem),r,o)
                @test b.states[2]==JS.BASIC # undo the implied y<=1 bound
                # x is at its own upper bound and the first logical variable
                # remains basic: its multiplier is zero, so y2=-2.
                @test JS._original_witness_certified(p,o,b,x,BigFloat[0,-2])
                @test isempty(h.metadata) && isempty(h.propagation)
                @test F.digest((p,q,r,o))==before
            end
        end
    end
end

@testset "BigFloat restoration preserves cancellation in stored costs" begin
    JS=JSimplex;L=JS._PostsolveLift;F=BigFloatPostsolveFixtures
    p=setprecision(BigFloat,256) do
        huge=BigFloat(2)^100
        LinearProblem(sparse(BigFloat[1 0;1 1]),BigFloat[huge+1,huge];
            row_lower=BigFloat[1,3],column_lower=BigFloat[0,0])
    end
    before=F.digest(p)
    for bits in (64,128,256)
        setprecision(BigFloat,bits) do
            q=JS.reduce_singleton_rows(p);meta=L.metadata(p,q,0)
            b=JS.Basis([2],[JS.AT_LOWER,JS.BASIC,JS.AT_LOWER])
            x=BigFloat[1,2];y=BigFloat[BigFloat(2)^100]
            rb,ry=L.one(meta,b,y,x,SolverOptions(BigFloat;verbose=false))
            @test ry==BigFloat[1,BigFloat(2)^100]
            @test rb.states[1:2]==[JS.BASIC,JS.BASIC]
            # At 64 bits the original interval certificate cannot resolve the
            # huge-plus-one reduced cost. The hint must not bypass that guard.
            @test JS._original_witness_certified(p,SolverOptions(BigFloat),rb,x,ry)==(bits>=128)
            @test F.digest(p)==before && precision(BigFloat)==bits
        end
    end
end

@testset "BigFloat propagation prices preserve cancellation and nonfinite guards" begin
    JS=JSimplex;L=JS._PostsolveLift;H=JS._PropagationHistory;F=BigFloatPostsolveFixtures
    p=setprecision(BigFloat,256) do
        LinearProblem(sparse(BigFloat[1 1;1 1]),BigFloat[BigFloat(2)^100+1,0];
            row_upper=BigFloat[1,3],column_lower=BigFloat[0,0])
    end
    for bits in (64,128,256)
        setprecision(BigFloat,bits) do
            _,g=F.propagation(p)
            @test H.price(g,1,BigFloat[0,BigFloat(2)^100])==1
            value=p.objective[1]
            @test L.price_step(value,BigFloat(3),BigFloat(0))===value
            @test !isfinite(L.price_step(value,BigFloat(Inf),BigFloat(0)))
            @test !isfinite(L.price_step(value,BigFloat(NaN),BigFloat(0)))
            @test precision(value)==256 && precision(BigFloat)==bits
        end
    end
end

@testset "BigFloat propagation certifies a cancellation-heavy original row" begin
    JS=JSimplex;H=JS._PropagationHistory;F=BigFloatPostsolveFixtures
    p=setprecision(BigFloat,256) do
        huge=BigFloat(2)^100
        LinearProblem(sparse(reshape(BigFloat[huge+1,-huge,3],1,3)),BigFloat[0,0,3];
            row_lower=BigFloat[1],column_lower=BigFloat[1,1,-1],column_upper=[BigFloat(1),BigFloat(1),nothing])
    end
    before=F.digest(p)
    for bits in (64,128,256)
        setprecision(BigFloat,bits) do
            q,g=F.propagation(p)
            @test bound_value(q.problem.column_lower[3])==0
            @test length(g.events)==1
            b=JS.Basis([4],[JS.AT_LOWER,JS.AT_LOWER,JS.AT_LOWER,JS.BASIC])
            x=BigFloat[1,1,0];o=SolverOptions(BigFloat;verbose=false)
            rb,y=H.apply(g,b,BigFloat[0],x,o)
            @test rb.basic_indices==[3] && y==BigFloat[1]
            @test JS._original_witness_certified(p,o,rb,x,y)
            @test F.digest(p)==before
        end
    end
end

@testset "BigFloat original cleanup works with all production managers" begin
    F=BigFloatPostsolveFixtures
    setprecision(BigFloat,128) do
        p=F.model()
        for manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub,:huangfu_hall)
            o=SolverOptions(BigFloat;presolve=true,scaling=:off,algorithm=:dual,
                simplex_strategy=:legacy,basis_update=manager,verbose=false)
            r=solve(p;options=o)
            @test r.status==OPTIMAL
            @test r.objective_value==BigFloat(-4)
            @test !isnothing(r.primal) && JSimplex._original_primal_feasible(p,r.primal,o.primal_tolerance)
        end
    end
end

@testset "BigFloat public solves opt in to reduced witnesses only" begin
    JS=JSimplex;F=BigFloatPostsolveFixtures
    for bits in (64,128,256), algorithm in (:dual,:primal), scaling in (:off,:auto)
        p=setprecision(BigFloat,bits) do; F.model(); end
        # Mixed matrix precisions without demanding that the unchanged final
        # objective guard accept higher-precision objective/primal values.
        p.A.nzval[1]=setprecision(BigFloat,192) do; BigFloat(1); end
        before=F.digest(p)
        setprecision(BigFloat,bits) do
            options=SolverOptions(BigFloat;presolve=true,scaling,algorithm,
                simplex_strategy=:legacy,basis_update=:pfi,verbose=false)
            opts=F.digest(options)
            reduced_witnesses=Ref(0);cleanup_witnesses=Ref(0)
            diag=JS.SimplexDiagnostics(observer=(reason,ws)->begin
                if reason==:certification && ws.progress.witness_problem===ws.problem
                    reduced_witnesses[]+=1
                    size(ws.problem.A,1)==size(p.A,1) && (cleanup_witnesses[]+=1)
                end
            end)
            r=JS._solve_diagnosed(p,diag;options)
            @test r.status==OPTIMAL
            if r.status==OPTIMAL
                @test r.objective_value==BigFloat(-4)
                @test JS._original_primal_feasible(p,r.primal,options.primal_tolerance)
            end
            @test reduced_witnesses[]>0
            @test cleanup_witnesses[]==0
            @test F.digest(options)==opts && F.digest(p)==before
            @test precision(BigFloat)==bits
        end
    end
end

@testset "BigFloat lower working precision retains inconclusive objective guard" begin
    JS=JSimplex;F=BigFloatPostsolveFixtures
    p=setprecision(BigFloat,192) do; F.model(); end
    for bits in (64,128), presolve in (false,true)
        setprecision(BigFloat,bits) do
            o=SolverOptions(BigFloat;presolve,scaling=:off,algorithm=:dual,
                simplex_strategy=:legacy,basis_update=:pfi,verbose=false)
            r=solve(p;options=o)
            @test r.status==NUMERICAL_ERROR
            @test occursin("original-objective evaluation is inconclusive",r.message)
            @test isnothing(r.primal) && isnothing(r.objective_value)
            @test precision(BigFloat)==bits
        end
    end
end

@testset "BigFloat missing witness uses ordinary restoration and clears history" begin
    JS=JSimplex;F=BigFloatPostsolveFixtures
    setprecision(BigFloat,128) do
        p=F.model();h=JS._PostsolveHistory(BigFloat);o=SolverOptions(BigFloat;verbose=false)
        q=JS._presolve_for_solve(p,o.primal_tolerance;history=h)
        @test !isempty(h.metadata)
        progress=JS.SimplexProgressContext(q.problem;witness_problem=q.problem)
        run=JS._solve_continuous_dual(q.problem,o;progress)
        @test run.status==OPTIMAL && !isnothing(run.dual)
        if run.status==OPTIMAL
            @test JS._original_witness_certified(q.problem,o,run.basis,run.primal,run.dual)
            without=JS.DualRunResult{BigFloat}(run.status,run.objective_value,run.primal,
                run.iterations,run.refactorizations,run.message,run.basis)
            b,x=JS._postsolve_with_dual(h,q,JS.identity_scaling(q.problem),without,o)
            ordinary=JS.restore_basis(q,run.basis)
            @test b.basic_indices==ordinary.basic_indices && b.states==ordinary.states
            @test x==JS.postsolve_primal(q,run.primal)
            @test isempty(h.metadata) && isempty(h.propagation)
        end
    end
end
