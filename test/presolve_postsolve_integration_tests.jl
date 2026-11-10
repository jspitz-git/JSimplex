using JSimplex, SparseArrays, Test, SHA, Serialization
@testset "Owned presolve history and dual/basis restoration" begin
    JS=JSimplex; L=JS._PostsolveLift; H=JS._PropagationHistory
    digest(x)=begin io=IOBuffer();serialize(io,x);bytes2hex(sha256(take!(io))) end
    function propagation(p)
        b=H.Builder(eltype(p.A))
        q=JS._propagate_row_bounds(p,trues(size(p.A,1));history=b)
        q,H.finish!(b,p)
    end
    for T in (Float32,Float64)
        o=SolverOptions(T;verbose=false)
        for sign in (one(T),-one(T))
            p=LinearProblem(sparse(reshape(T[1,1],2,1)),T[-sign];row_lower=[T(1),nothing],row_upper=[nothing,T(1)],column_lower=T[-10],column_upper=T[10])
            q=JS.reduce_singleton_rows(p); b=JS.Basis(Int[],[JS.AT_LOWER]); x=T[1]
            before=digest((p,q,b,x))
            rb,y=L.one(L.metadata(p,q,2),b,T[],x,o)
            @test rb.basic_indices==(sign>0 ? [2,1] : [1,3])
            @test JS._original_witness_certified(p,o,rb,x,y)
            @test digest((p,q,b,x))==before
        end
        for a in (T(1),T(-2)), price in (T(1),T(-1))
            p=LinearProblem(sparse(reshape(T[a,1],1,2)),T[0,price];row_lower=T[a+2],row_upper=T[a+2],column_lower=T[1,0],column_upper=T[1,10])
            q=JS.aggregate_singleton_equalities(p)
            b=JS.Basis([1],[JS.BASIC,price>0 ? JS.AT_UPPER : JS.AT_LOWER]);x=T[1,2];y=T[price]
            before=digest((p,q,b,x,y))
            rb,ry=L.one(L.metadata(p,q,3),b,y,x,o)
            desired=price>0 ? JS.AT_LOWER : JS.AT_UPPER
            @test rb.states[1]==((a>0)==(desired==JS.AT_LOWER) ? JS.AT_UPPER : JS.AT_LOWER)
            @test JS._original_witness_certified(p,o,rb,x,ry)
            @test digest((p,q,b,x,y))==before
        end
        p=LinearProblem(sparse(T[1 1;0 1]),T[1,0];row_lower=[T(3),nothing],row_upper=[nothing,T(1)],column_lower=T[0,0],column_upper=T[3,2])
        q,g1=propagation(p);z,g2=propagation(q.problem)
        metas=[L.metadata(p,q,8),L.metadata(q.problem,z,8)]
        b=JS.Basis([3],[JS.AT_LOWER,JS.AT_UPPER,JS.BASIC]);x=T[2,1];y=T[0]
        before=digest((metas,[g1,g2],b,x,y))
        rb,ry,rx=H.chain(metas,[g1,g2],b,y,x,o)
        @test rb.states[1:2]==[JS.BASIC,JS.BASIC]
        @test JS._original_witness_certified(p,o,rb,rx,ry)
        @test digest((metas,[g1,g2],b,x,y))==before
        pp=LinearProblem(sparse(T[1 1;0 1]),T[1,0];row_lower=[T(3),nothing],column_lower=T[0,0],column_upper=T[3,2])
        qq,g=propagation(pp)
        bb=JS.Basis([4,3],[JS.AT_LOWER,JS.AT_UPPER,JS.BASIC,JS.BASIC])
        rb,ry=H.apply(g,bb,zeros(T,2),T[1,2],o)
        @test rb.basic_indices==[4,1]
        @test JS._original_witness_certified(pp,o,rb,T[1,2],ry)
        for (xx,yy) in ((T[0,2],T[0,0]),(T[1,2],T[1,0]),(T[1,1],T[0,0]),(T[1,2],T[NaN,0]))
            bb=JS.Basis([3,4],[JS.AT_LOWER,JS.AT_UPPER,JS.BASIC,JS.BASIC]);snap=digest(bb)
            rb,_=H.apply(g,bb,copy(yy),xx,o)
            @test digest(rb)==snap
        end
        pp=LinearProblem(sparse(reshape(T[3,1],1,2)),T[1,0];row_lower=T[1],column_lower=T[0,0],column_upper=T[2,0])
        qq,g=propagation(pp);xx=T[JS.bound_value(qq.problem.column_lower[1]),0]
        bb=JS.Basis([3],[JS.AT_LOWER,JS.AT_LOWER,JS.BASIC]);rb,ry=H.apply(g,bb,T[0],xx,o)
        @test !isempty(g.events) && JS._exact_rational(xx[1]) <= BigInt(1)//BigInt(3)
        @test rb.states[1]==JS.BASIC
        @test JS._original_witness_certified(pp,o,rb,xx,ry)
        # A failed presolve proof must not leave history, including with a valid prefix.
        gap=T(1//4096);tol=T(1//1024)
        p=LinearProblem(sparse(reshape(T[1],1,1)),T[2];row_lower=T[1+gap],column_lower=T[1],column_upper=T[1])
        h=JS._PostsolveHistory(T);q=JS._presolve_for_solve(p,tol;history=h)
        @test q isa JS.PresolveResult && isempty(q.postsolve_stack)
        @test isempty(h.metadata) && isempty(h.propagation)
        # Exception rollback clears both parts, preserving the input.
        @test_throws ErrorException JS._history_transaction(h) do
            push!(h.metadata,metas[1]);push!(h.propagation,g1);error("injected")
        end
        @test isempty(h.metadata) && isempty(h.propagation)
    end
    for T in (Float32,Float64,BigFloat,Rational{BigInt})
        p=LinearProblem(sparse(reshape(T[1],1,1)),T[0];row_upper=T[2],column_lower=T[0],column_upper=T[1])
        q,g=propagation(p)
        @test length(q.postsolve_stack)==1 && size(q.problem.A)==(0,1)
        @test isempty(g.events) && isempty(g.column_ids)
        meta=L.metadata(p,q,8);b=JS.Basis(Int[],[JS.AT_LOWER]);o=SolverOptions(T;verbose=false)
        rb,ry,rx=H.chain([meta],[g],b,T[],T[0],o)
        @test JS._original_witness_certified(p,o,rb,rx,ry)
        # No model-sized bitmap/copy for empty history; builder identity retained.
        huge=LinearProblem(spzeros(T,0,10000),zeros(T,10000));builder=H.Builder(T)
        @test H.finish!(builder,huge)===builder.group
    end
end

@testset "Activation fallback restores the original bound side" begin
    JS=JSimplex
    for T in (Float32,Float64), upper in (false,true)
        p=LinearProblem(sparse(reshape(T[1],1,1)),T[upper ? -1 : 1];
            row_lower=upper ? [nothing] : T[1],row_upper=upper ? T[1] : [nothing],
            column_lower=[nothing],column_upper=[nothing])
        map=JS.PresolveMap{T}([1],[1],Union{Nothing,T}[nothing],[JS.FREE_NONBASIC],1)
        step=JS.InequalityActivationStep{T}(1,1,[(1,upper)])
        presolved=JS.PresolveResult(p,JS.PostsolveStep{T}[step],1)
        b=JS.Basis([1],[JS.BASIC,upper ? JS.AT_LOWER : JS.AT_UPPER])
        run=JS.DualRunResult{T}(JS.OPTIMAL,T(-1),T[1],1,0,"fixture",b)
        h=JS._PostsolveHistory(T)
        # Missing metadata/witness deliberately exercises certified fallback.
        rb,x=JS._postsolve_with_dual(h,presolved,JS.identity_scaling(p),run,SolverOptions(T;verbose=false))
        @test rb.states[2]==(upper ? JS.AT_UPPER : JS.AT_LOWER)
        @test JS.bound_value(upper ? p.row_upper[1] : p.row_lower[1])==1
        @test x==T[1] && isempty(h.metadata)
        @test b.states[2]!=(upper ? JS.AT_UPPER : JS.AT_LOWER)
    end
end

@testset "Existing certified witness is opt-in and model scoped" begin
    JS=JSimplex
    p=LinearProblem(sparse([1.0 1.0]),[-1.0,-2.0];row_upper=[3.0],column_lower=[0.0,0.0],column_upper=[2.0,2.0])
    o=SolverOptions(Float64;presolve=false,scaling=:off,verbose=false)
    progress=JS.SimplexProgressContext(p;witness_problem=p)
    r=JS._solve_continuous_dual(p,o;progress)
    @test r.status==JS.OPTIMAL && !isnothing(r.dual)
    @test JS._original_witness_certified(p,o,r.basis,r.primal,r.dual)
    plain=JS._solve_continuous_dual(p,o)
    @test plain.status==JS.OPTIMAL && isnothing(plain.dual)
    @test plain.primal==r.primal && plain.iterations==r.iterations
    other=LinearProblem(copy(p.A),copy(p.objective);row_upper=[3.0],column_lower=[0.0,0.0],column_upper=[2.0,2.0])
    mismatch=JS._solve_continuous_dual(p,o;progress=JS.SimplexProgressContext(p;witness_problem=other))
    @test mismatch.status==JS.OPTIMAL && isnothing(mismatch.dual)
end
