using JSimplex, LinearAlgebra, SparseArrays, Test
Base.include(JSimplex,joinpath(@__DIR__,"hybrid.jl"))
@testset "Experimental immutable-base hypersparse solves" begin
    n=64; B=spdiagm(0=>fill(2.0,n),-1=>fill(-0.1,n-1),3=>fill(0.05,n-3))
    for Factor in (JSimplex.ForrestTomlinFactorization,JSimplex.SuhlSuhlFactorization,JSimplex.BartelsGolubFactorization), forward in (false,true)
        f=JSimplex._trial_hybrid_factor(Factor,B;forward,cutoff=1.0); current=copy(B)
        for k in 1:20
            rhs=zeros(n);rhs[mod1(7k,n)]=1
            @test current*JSimplex.forward_solve(f,rhs)≈rhs
            @test current'*JSimplex.transpose_solve(f,rhs)≈rhs
            a=Vector(current[:,k]); a[mod1(k+5,n)]+=0.02
            direction=JSimplex.forward_solve(f,a)
            JSimplex.replace_column!(f,direction,k);current[:,k]=a
        end
        @test f.base.builds==1
        g=JSimplex.copy_basis_factorization(f)
        @test g.base.input !== f.base.input
        @test g.base.view.work !== f.base.view.work
        @test current'*JSimplex.transpose_solve(g,ones(n))≈ones(n)
        @test_throws SingularException JSimplex.refactorize!(f,spzeros(n,n))
        @test current'*JSimplex.transpose_solve(f,ones(n))≈ones(n)
        JSimplex.refactorize!(f,B)
        @test isnothing(f.base.view)
        @test B'*JSimplex.transpose_solve(f,ones(n))≈ones(n)
        @test f.base.builds==1
        rhs=fill(Inf,n)
        reference=JSimplex.transpose_solve(Factor(B),rhs)
        @test isequal(JSimplex.transpose_solve(f,rhs),reference)
    end
end
@testset "Hybrid selection and dense fallback" begin
    B=spdiagm(0=>ones(32))
    f=JSimplex._trial_hybrid_factor(JSimplex.ForrestTomlinFactorization,B)
    @test JSimplex.transpose_solve(f,ones(32))==ones(32)
    @test f.base.builds==0
    e=zeros(32); e[1]=1
    @test JSimplex.transpose_solve(f,e)==e
    @test f.base.builds==1
    JSimplex._install_trial_hybrid!()
    for strategy in (:legacy,:adaptive)
        options=SolverOptions(simplex_strategy=strategy,basis_update=:forrest_tomlin)
        result=Base.invokelatest(JSimplex._basis_factorization,B,options)
        @test (result.base isa JSimplex.TrialHybridBackend)==(strategy==:legacy)
    end
    @test JSimplex._trial_hybrid_factor(JSimplex.ForrestTomlinFactorization,Matrix{Float32}(I,2,2)).base isa JSimplex.Float32LUBackend
end
@testset "Sparse overflow fallback and unavailable views" begin
    for transposed in (false,true)
        B=spdiagm(0=>[1e-300,1.0]);base=JSimplex._factorize_basis(B)
        b=JSimplex.TrialHybridBackend(base;forward=true,cutoff=1.0)
        operation=transposed ? JSimplex._backend_transpose_solve! : JSimplex._backend_forward_solve!
        rhs=[1e300,0.0];actual=zeros(2);expected=zeros(2)
        operation(expected,base,rhs);operation(actual,b,rhs)
        @test isequal(actual,expected)
        @test b.dense_calls==1 && b.sparse_calls==0
        operation(actual,b,[0.0,1.0])
        @test actual==[0.0,1.0]
        @test b.sparse_calls==1
    end
    B=spdiagm(0=>[nextfloat(1.0),1.0])
    b=JSimplex.TrialHybridBackend(JSimplex._factorize_basis(B);forward=true,cutoff=1.0)
    rhs=[1.0,0.0];actual=zeros(2);expected=zeros(2)
    for operation in (JSimplex._backend_forward_solve!,JSimplex._backend_transpose_solve!)
        operation(expected,b.base,rhs);operation(actual,b,rhs)
        @test actual==expected
        @test isnothing(b.view)
        @test b.builds==1
    end
end
