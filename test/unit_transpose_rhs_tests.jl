using SparseArrays, LinearAlgebra, Random

@testset "Unit transpose RHS handoff" begin
    @test isdefined(JSimplex,:_unit_transpose_rhs)
    if isdefined(JSimplex,:_unit_transpose_rhs)
        rng=MersenneTwister(54931)
        for T in (Float32,Float64,BigFloat,Rational{BigInt}),
            backend in (:native,:markowitz),
            Factor in (JSimplex.PFIFactorization,JSimplex.ForrestTomlinFactorization,
                JSimplex.SuhlSuhlFactorization,JSimplex.BartelsGolubFactorization,
                JSimplex.HuangfuHallFactorization)
            n=9
            B=sparse(T.(Matrix{Int}(I,n,n)*16+rand(rng,-2:2,n,n)))
            f=Factor(B,Val(backend)); output=zeros(T,n); reference=similar(output)
            for k in 0:12
                if k>0
                    p=mod1(3k+1,n);a=Vector(B[:,p])+Vector(B[:,mod1(p+2,n)])/T(8)
                    JSimplex.replace_column!(f,JSimplex.forward_solve(f,a),p)
                    B[:,p]=a
                end
                for p in (1,4,n)
                    rhs=zeros(T,n);rhs[p]=one(T)
                    tagged=JSimplex._unit_transpose_rhs(f,rhs,p)
                    applicable_fastpath=T<:Union{Float32,Float64} && Factor!==JSimplex.PFIFactorization
                    @test (tagged!==rhs)==applicable_fastpath
                    @test collect(tagged)==rhs
                    JSimplex.transpose_solve!(reference,f,rhs)
                    JSimplex.transpose_solve!(output,f,tagged)
                    @test isequal(output,reference)
                    @test rhs[p]==one(T) && count(!iszero,rhs)==1
                    # Destination aliasing the dense RHS must still be supported.
                    aliased=copy(rhs);tagged_alias=JSimplex._unit_transpose_rhs(f,aliased,p)
                    JSimplex.transpose_solve!(aliased,f,tagged_alias)
                    @test isequal(aliased,reference)
                    @test_throws ArgumentError JSimplex.transpose_solve!(f.work,f,tagged)
                    @test_throws DimensionMismatch JSimplex.transpose_solve!(zeros(T,n-1),f,tagged)
                end
            end
            JSimplex.refactorize!(f,B)
            rhs=zeros(T,n);rhs[3]=one(T)
            JSimplex.transpose_solve!(reference,f,rhs)
            JSimplex.transpose_solve!(output,f,JSimplex._unit_transpose_rhs(f,rhs,3))
            @test isequal(output,reference)
            # An ordinary dense BTRAN still uses its full RHS after tagged calls.
            rhs.=T.(rand(rng,-3:3,n))
            @test transpose(B)*JSimplex.transpose_solve!(output,f,rhs)≈rhs
        end
    end
end

function unit_rhs_workspace(T, manager, backend; indexed=false)
    problem=LinearProblem(spdiagm(0=>ones(T,8)),zeros(T,8);row_lower=zeros(T,8))
    options=SolverOptions(T;basis_update=manager,basis_refactorization=backend,
        simplex_strategy=:legacy,verbose=false)
    policy=JSimplex.NumericalPolicy(T;hypersparse=indexed)
    JSimplex.initialize_workspace(problem,options;
        progress=JSimplex.SimplexProgressContext(problem;numerical_policy=policy))
end
@testset "Unit metadata preserves pipeline and refinement RHS" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}),
        manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub,:huangfu_hall),
        backend in (:native,:markowitz), indexed in (false,true)
        ws=unit_rhs_workspace(T,manager,backend;indexed)
        rhs=JSimplex._pipeline_unit_rhs!(ws,3)
        expected=copy(rhs)
        for mode in (:dense,:sparse)
            JSimplex._pipeline_basis_solve!(ws.scratch.rho,ws,rhs;transposed=true,
                unit_row=3,kernel_mode=mode)
            @test ws.scratch.rho == -expected
            @test isequal(rhs,expected)
        end
        JSimplex._checked_basis_solve!(ws.scratch.rho,ws,rhs;transposed=true,unit_row=3)
        @test ws.scratch.rho == -expected
        @test isequal(rhs,expected)
        # Sequential reuse must not retain the previous unit index.
        JSimplex._pipeline_column_rhs!(ws,6)
        JSimplex._pipeline_basis_solve!(ws.scratch.rho,ws,rhs;transposed=true)
        @test ws.scratch.rho == -T[i==6 for i in 1:8]
    end
end

@testset "Unit BTRAN invalidates same-rounded prepared output" begin
    for Factor in (JSimplex.ForrestTomlinFactorization,JSimplex.SuhlSuhlFactorization,
                   JSimplex.BartelsGolubFactorization)
        f=Factor(Matrix{Float64}(I,2,2))
        JSimplex.replace_column!(f,[2.0,0.0],1)
        d=JSimplex.forward_solve(f,[nextfloat(0.0),1.0])
        @test d==[0.0,1.0]
        @test JSimplex._copy_prepared_spike!(f,d)
        rhs=[0.0,1.0]
        JSimplex.transpose_solve!(d,f,JSimplex._unit_transpose_rhs(f,rhs,2))
        @test d==[0.0,1.0]
        @test !JSimplex._copy_prepared_spike!(f,d)
    end
end
@testset "HH unit BTRAN uses a nonidentity inverse column permutation" begin
    n=32;rng=MersenneTwister(734)
    B=spdiagm(-1=>fill(-0.1,n-1),0=>fill(2.0,n),1=>fill(0.125,n-1))[:,randperm(rng,n)]
    f=JSimplex.HuangfuHallFactorization(B)
    @test f.base.columns != collect(1:n)
    for p in 1:n
        rhs=zeros(n);rhs[p]=1
        expected=JSimplex.transpose_solve(f,rhs)
        @test isequal(JSimplex.transpose_solve(f,JSimplex._unit_transpose_rhs(f,rhs,p)),expected)
    end
end
