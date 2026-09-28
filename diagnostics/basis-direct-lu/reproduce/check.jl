using JSimplex, LinearAlgebra, SparseArrays, Test, Random
Base.include(JSimplex,joinpath(@__DIR__,"direct.jl"))
const NORMALIZE=get(ENV,"JSIMPLEX_DIRECT_NORMALIZE","false")=="true"
trial_factor(Factor,B)=JSimplex._trial_direct_factor(Factor,B;normalize=NORMALIZE)
@testset "Direct native LU identity, updates and ownership" begin
    rng=MersenneTwister(579)
    for Factor in (JSimplex.ForrestTomlinFactorization,JSimplex.SuhlSuhlFactorization,JSimplex.BartelsGolubFactorization)
        n=16;C=Matrix(sprand(rng,n,n,0.15));C+=Diagonal(2 .+ vec(sum(abs,C;dims=2)))
        B=sparse(Diagonal(10.0 .^ range(-3,3;length=n))*C[randperm(rng,n),randperm(rng,n)])
        f=trial_factor(Factor,B)
        @test isnothing(f.base.fallback)
        rhs=randn(rng,n)
        for k in 1:40
            for transposed in (false,true)
                M=transposed ? B' : B
                operation=transposed ? JSimplex.transpose_solve! : JSimplex.forward_solve!
                reference=Matrix(M)\rhs
                for alias in (false,true)
                    source=copy(rhs);dest=alias ? source : zeros(n)
                    operation(dest,f,source)
                    @test dest≈reference rtol=1e-9
                    @test norm(M*dest-rhs,Inf)/(opnorm(M,Inf)*norm(dest,Inf)+1)<1e-12
                end
            end
            pivot=mod1(k,n);a=Vector(B[:,pivot]);a[mod1(k+3,n)]+=1e-4
            direction=JSimplex.forward_solve(f,a)
            JSimplex.replace_column!(f,direction,pivot);B[:,pivot]=a
        end
        g=JSimplex.copy_basis_factorization(f)
        @test g.base.work !== f.base.work
        @test JSimplex.forward_solve(g,rhs)≈B\rhs rtol=1e-9
        @test_throws ZeroPivotException JSimplex.replace_column!(f,zeros(n),1)
        @test_throws SingularException JSimplex.refactorize!(f,spzeros(n,n))
        @test JSimplex.transpose_solve(f,rhs)≈B'\rhs rtol=1e-9
        JSimplex.refactorize!(f,spdiagm(0=>[2.0,3.0,4.0]))
        @test JSimplex.forward_solve(f,[2.,3.,4.])≈ones(3)
        @test JSimplex.transpose_solve(g,rhs)≈B'\rhs rtol=1e-9
    end
end
@testset "Direct LU scale conventions and unsupported paths" begin
    for Factor in (JSimplex.ForrestTomlinFactorization,JSimplex.SuhlSuhlFactorization,JSimplex.BartelsGolubFactorization), diagonal in ([1e-300,1e300],[2.,4.],[nextfloat(1.0),1.0],Float64[])
        B=spdiagm(0=>diagonal);f=trial_factor(Factor,B)
        @test JSimplex.forward_solve(f,diagonal)≈ones(length(diagonal))
        @test JSimplex.transpose_solve(f,diagonal)≈ones(length(diagonal))
        diagonal==[nextfloat(1.0),1.0] && @test !isnothing(f.base.fallback)
    end
    @test trial_factor(JSimplex.ForrestTomlinFactorization,Matrix{Float32}(I,2,2)).base isa JSimplex.Float32LUBackend
    JSimplex._install_trial_direct!(normalize=NORMALIZE)
    for strategy in (:legacy,:adaptive)
        options=SolverOptions(simplex_strategy=strategy,basis_update=:forrest_tomlin)
        f=Base.invokelatest(JSimplex._basis_factorization,spdiagm(0=>ones(4)),options)
        @test (f.base isa JSimplex.TrialLowerBackend)==(strategy==:legacy)
    end
end
@testset "Direct reconstruction, divergent copies and fallback transitions" begin
    for Factor in (JSimplex.ForrestTomlinFactorization,JSimplex.SuhlSuhlFactorization,JSimplex.BartelsGolubFactorization)
        B=spdiagm(0=>fill(2.0,8),-1=>fill(0.2,7),3=>fill(-0.1,5));f=trial_factor(Factor,B)
        for pivot in (3,1,4)
            a=Vector(B[:,pivot]);a[8]+=0.1
            direction=JSimplex.forward_solve(f,a)
            JSimplex.replace_column!(f,copy(direction),pivot);B[:,pivot]=a
        end
        g=JSimplex.copy_basis_factorization(f);C=copy(B)
        a=Vector(C[:,2]);a[7]-=0.1
        JSimplex.replace_column!(g,copy(JSimplex.forward_solve(g,a)),2);C[:,2]=a
        a=Vector(B[:,5]);a[6]+=0.1
        JSimplex.replace_column!(f,JSimplex.forward_solve(f,a),5);B[:,5]=a
        for (factor,matrix) in ((f,B),(g,C))
            @test JSimplex.forward_solve(factor,ones(8))≈Matrix(matrix)\ones(8)
            @test JSimplex.transpose_solve(factor,ones(8))≈Matrix(matrix')\ones(8)
            rhs=JSimplex.IndexedVector{Float64}(8);dest=JSimplex.IndexedVector{Float64}(8)
            JSimplex.set_entry!(rhs,2,1.0)
            JSimplex.forward_solve!(dest,factor,rhs)
            @test matrix*dest.values≈rhs.values atol=1e-12
            JSimplex.transpose_solve!(dest,factor,rhs)
            @test matrix'*dest.values≈rhs.values atol=1e-12
        end
        near=spdiagm(0=>[nextfloat(1.0),1.0]);JSimplex.refactorize!(f,near)
        @test !isnothing(f.base.fallback)
        @test_throws SingularException JSimplex.refactorize!(f,spzeros(2,2))
        @test JSimplex.forward_solve(f,ones(2))≈Matrix(near)\ones(2)
        JSimplex.refactorize!(f,spdiagm(0=>[2.,4.]))
        @test isnothing(f.base.fallback)
        @test JSimplex.forward_solve(f,[2.,4.])≈ones(2)
    end
end
@testset "Direct LU componentwise residual under row scaling and cancellation" begin
    n=6;C=[1.0/(i+j-1) for i in 1:n,j in 1:n]
    B=sparse(Diagonal(10.0 .^ range(-80,80;length=n))*C)
    for Factor in (JSimplex.ForrestTomlinFactorization,JSimplex.SuhlSuhlFactorization,JSimplex.BartelsGolubFactorization)
        f=trial_factor(Factor,B)
        @test isnothing(f.base.fallback)
        for transposed in (false,true)
            M=transposed ? B' : B
            rhs=M*[(-1.0)^i for i in 1:n]
            x=transposed ? JSimplex.transpose_solve(f,rhs) : JSimplex.forward_solve(f,rhs)
            wide=Matrix{BigFloat}(M);wx=BigFloat.(x);wrhs=BigFloat.(rhs)
            errors=abs.(wide*wx-wrhs);bounds=abs.(wide)*abs.(wx)+abs.(wrhs)
            @test all(errors .<= 128eps(Float64).*bounds)
        end
    end
end
@testset "All direct installation modes retain adaptive and Markowitz paths" begin
    B=spdiagm(0=>ones(4))
    for mode in (:forrest_tomlin,:suhl_suhl,:bartels_golub),strategy in (:legacy,:adaptive),backend in (:native,:markowitz)
        options=SolverOptions(basis_update=mode,simplex_strategy=strategy,basis_refactorization=backend)
        f=Base.invokelatest(JSimplex._basis_factorization,B,options)
        @test (f.base isa JSimplex.TrialLowerBackend)==(strategy==:legacy && backend==:native)
    end
end
