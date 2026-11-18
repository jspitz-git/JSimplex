module PrimalInfeasibilitySweepTests
using JSimplex,Test,SparseArrays
const JS=JSimplex
q(x)=Rational{BigInt}(x)
function q(x::BigFloat)
    significand,power,sign=Base.decompose(x);integer=sign*significand
    power>=0 ? (integer<<power)//big(1) : integer//(big(1)<<(-power))
end
function exact_proof(w,rho)
    A=w.problem.A;m,n=size(A);coefficients=fill(big(0)//big(1),m+n)
    for j in 1:n,k in nzrange(A,j);coefficients[j]-=q(rho[A.rowval[k]])*q(A.nzval[k]);end
    for i in 1:m;coefficients[n+i]=q(rho[i]);end
    result=big(0)//big(1)
    for i in eachindex(coefficients)
        c=coefficients[i];iszero(c) && continue
        b=c>0 ? w.lower[i] : w.upper[i];isfinite(b) || return false
        result+=c*q(bound_value(b))-abs(c)*q(JS._infeasibility_bound_allowance(w,i))
    end
    result>0
end
function fixture(T;chains=8,max_refinements=3,gap=one(T),strategy=:legacy,limit=Inf)
    A=blockdiag((sparse(T[-1 0;10 -1;0 1]) for _ in 1:chains)...)
    p=LinearProblem(A,zeros(T,2chains);row_upper=fill(-gap,3chains),column_lower=fill(nothing,2chains),column_upper=zeros(T,2chains))
    o=SolverOptions(T;algorithm=:primal,presolve=false,scaling=:off,verbose=false,simplex_strategy=strategy,time_limit=limit)
    policy=JS.NumericalPolicy(T;max_refinements)
    w=JS.initialize_workspace(p,o;progress=JS.SimplexProgressContext(p;numerical_policy=policy))
    b=nextfloat(one(T)/T(10));w,repeat(-T[1,b,b],chains)
end
@testset "Primal terminal witness repairs independent cancellation constraints" begin
    for T in (Float32,Float64,BigFloat)
        setprecision(BigFloat,128) do
            w,rho=fixture(T)
            @test !first(JS._certified_infeasibility_witness(w,rho,false))
            before=deepcopy((rho,w.problem.A,w.primal,w.costs,w.lower,w.upper,w.basis.basic_indices,w.basis.states))
            @test JS._primal_infeasibility_certified(w,rho)
            @test isequal(before,(rho,w.problem.A,w.primal,w.costs,w.lower,w.upper,w.basis.basic_indices,w.basis.states))
        end
    end
end
@testset "Sweep proposals retain original sign and tolerance authority" begin
    for T in (Float32,Float64,BigFloat),bits in (64,128,240,512)
        setprecision(BigFloat,bits) do
            w,rho=fixture(T);saved=deepcopy((rho,w.problem.A,w.primal,w.costs,w.lower,w.upper,w.basis.basic_indices,w.basis.states))
            accepted,v,used=JS._certified_infeasibility_witness(w,rho,false;sweep=true)
            @test accepted && v!==rho && 0<used<=w.progress.numerical_policy.max_refinements
            @test exact_proof(w,v)
            @test all(abs.(v).<=abs.(rho)) && all((sign.(v).==sign.(rho)).|iszero.(v))
            @test isequal(saved,(rho,w.problem.A,w.primal,w.costs,w.lower,w.upper,w.basis.basic_indices,w.basis.states))
            @test precision(BigFloat)==bits
            # Orientation is a proposal choice, never permission to change signs.
            a1,v1,u1=JS._certified_infeasibility_witness(w,-rho,true;sweep=true)
            @test a1 && exact_proof(w,-v1) && 0<u1<=3
            for gap in (zero(T),T(1e-8))
                weak,r=fixture(T;gap)
                a2,v2,u2=JS._certified_infeasibility_witness(weak,r,false;sweep=true)
                @test !a2 && v2===r && 0<=u2<=3
            end
            limited,r=fixture(T;max_refinements=1)
            a3,v3,u3=JS._certified_infeasibility_witness(limited,r,false;sweep=true)
            @test 0<=u3<=1 && (a3 ? exact_proof(limited,v3) : v3===r)
        end
    end
end
@testset "Disabled authority and nonfinite inputs do not certify" begin
    for T in (Float32,Float64,BigFloat)
        for kw in ((max_refinements=0,),(strategy=:adaptive,),(limit=1.,))
            w,rho=fixture(T;kw...);a,v,u=JS._certified_infeasibility_witness(w,rho,false;sweep=true)
            @test !a && v===rho && u==0 && !JS._primal_infeasibility_certified(w,rho)
        end
        for bad in (T(Inf),T(NaN))
            w,rho=fixture(T);rho[2]=bad;before=deepcopy(rho)
            a,v,u=JS._certified_infeasibility_witness(w,rho,false;sweep=true)
            @test !a && v===rho && isequal(before,rho)
        end
    end
    original=get_zero_subnormals()
    try
        w,rho=fixture(Float64);set_zero_subnormals(true)
        a,v,u=JS._certified_infeasibility_witness(w,rho,false;sweep=true)
        @test !a && v===rho && u==0
    finally
        set_zero_subnormals(original)
    end
    w,rho=fixture(BigFloat)
    setrounding(BigFloat,RoundDown) do
        a,v,u=JS._certified_infeasibility_witness(w,rho,false;sweep=true)
        @test !a && v===rho && u==0
    end
end
@testset "Mixed BigFloat precisions keep exact proof and source ownership" begin
    for (stored,working) in ((64,256),(256,64),(512,128),(128,512))
        w,rho=setprecision(BigFloat,stored) do;fixture(BigFloat);end
        before=deepcopy((rho,w.problem.A,w.lower,w.upper))
        setprecision(BigFloat,working) do
            a,v,u=JS._certified_infeasibility_witness(w,rho,false;sweep=true)
            @test a ? exact_proof(w,v) : v===rho
            @test 0<=u<=3 && precision(BigFloat)==working
            @test isequal(before,(rho,w.problem.A,w.lower,w.upper))
        end
    end
end

@testset "Finite columns do not steer the sign-repair proposal" begin
    for T in (Float32,Float64,BigFloat)
        w,rho=fixture(T);a,v,used=JS._certified_infeasibility_witness(w,rho,false;sweep=true)
        m,n=size(w.problem.A)
        p=LinearProblem(hcat(w.problem.A,sparse(ones(T,m,1))),zeros(T,n+1);
            row_upper=fill(-one(T),m),column_lower=vcat(fill(nothing,n),zero(T)),column_upper=zeros(T,n+1))
        bounded=JS.initialize_workspace(p,w.options)
        b,vb,usedb=JS._certified_infeasibility_witness(bounded,rho,false;sweep=true)
        @test a && b && used==usedb && v==vb
        @test exact_proof(bounded,vb)
    end
end

end
