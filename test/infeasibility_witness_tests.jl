module InfeasibilityWitnessTests
using JSimplex,Test,SparseArrays
const JS=JSimplex
q(x)=Rational{BigInt}(x)
function q(x::BigFloat)
    significand,power,sign=Base.decompose(x)
    integer=sign*significand
    power>=0 ? (integer<<power)//big(1) : integer//(big(1)<<(-power))
end
function exact_proof(w,rho,below)
    A=w.problem.A;m,n=size(A)
    coefficients=fill(big(0)//big(1),m+n);orientation=below ? 1 : -1
    for j in 1:n,k in nzrange(A,j)
        coefficients[j]+=orientation*q(rho[A.rowval[k]])*q(A.nzval[k])
    end
    for i in 1:m;coefficients[n+i]=-orientation*q(rho[i]);end
    result=big(0)//big(1)
    for i in eachindex(coefficients)
        c=coefficients[i];iszero(c) && continue
        b=c>0 ? w.lower[i] : w.upper[i];isfinite(b) || return false
        result+=c*q(bound_value(b))-abs(c)*q(JS._infeasibility_bound_allowance(w,i))
    end
    result>0
end
function fixture(T;max_refinements=3,gap=one(T))
    A=sparse(T[-1 0;10 -1;0 1])
    p=LinearProblem(A,T[0,0];row_upper=fill(-gap,3),column_lower=[nothing,nothing],column_upper=T[0,0])
    o=SolverOptions(T;verbose=false,presolve=false,scaling=:off,simplex_strategy=:legacy)
    policy=JS.NumericalPolicy(T;max_refinements)
    w=JS.initialize_workspace(p,o;progress=JS.SimplexProgressContext(p;numerical_policy=policy))
    b=nextfloat(one(T)/T(10));w,T[1,b,b]
end
@testset "Private bounded witnesses retain original tolerances and source values" begin
    for T in (Float32,Float64,BigFloat),bits in (64,128,240,512)
        setprecision(BigFloat,bits) do
            w,rho=fixture(T);old=deepcopy((rho,w.primal,w.costs,w.lower,w.upper,w.problem.A))
            accepted,witness,used=JS._certified_infeasibility_witness(w,rho,true)
            @test accepted && 0<used<=3 && witness!==rho
            @test exact_proof(w,witness,true)
            @test isequal(old,(rho,w.primal,w.costs,w.lower,w.upper,w.problem.A))
            @test w.options.primal_tolerance==T(1//10^7) && precision(BigFloat)==bits
            w0,r0=fixture(T;max_refinements=0)
            a0,v0,u0=JS._certified_infeasibility_witness(w0,r0,true)
            @test !a0 && v0===r0 && u0==0
            for gap in (zero(T),T(1e-8))
                weak,r=fixture(T;gap)
                @test !JS._infeasibility_certified(weak,r,true)
            end
        end
    end
end
@testset "Mixed BigFloat coefficients, orientation and exact enclosures" begin
    for (stored,working) in ((64,256),(256,64),(512,128)),below in (true,false)
        p,rho=setprecision(BigFloat,stored) do
            a=one(BigFloat)+BigFloat(2)^(-stored+8)
            p=LinearProblem(sparse(reshape(BigFloat[1,1],2,1)),BigFloat[0];
                row_upper=[BigFloat(0),nothing],row_lower=[nothing,BigFloat(0)],column_lower=[nothing],column_upper=[nothing])
            p,BigFloat[a,-1]
        end
        old=deepcopy((p.A,rho))
        setprecision(BigFloat,working) do
            negative=JS._witness_negate(rho[1])
            @test q(negative)==-q(rho[1]) && precision(negative)==stored
            w=JS.initialize_workspace(p,SolverOptions(BigFloat;verbose=false,presolve=false,scaling=:off))
            lower,upper=JS._witness_coefficient_bounds(w,rho,below,1,true)
            exact=(below ? 1 : -1)*(q(rho[1])+q(rho[2]))
            @test q(lower)<=exact<=q(upper)
            @test !JS._infeasibility_certified(w,rho,below)
            @test isequal(old,(p.A,rho)) && precision(BigFloat)==working
        end
    end
end
@testset "Tight rows and unsupported modes preserve certificate safeguards" begin
    for T in (Float32,Float64,BigFloat)
        A=sparse(reshape(T[1,-1],1,2));d=T[1,1]
        lower,upper=JS._recession_row_bounds(A,d,Val(false))
        @test lower==upper==T[0]
        p=LinearProblem(sparse(reshape(T[1,1],2,1)),T[0];row_upper=[zero(T),nothing],
            row_lower=[nothing,one(T)],column_lower=[nothing],column_upper=[nothing])
        w=JS.initialize_workspace(p,SolverOptions(T;verbose=false,presolve=false,scaling=:off))
        @test JS._infeasibility_certified(w,T[1,-1],true)
        for bad in (T(Inf),T(NaN))
            @test !JS._infeasibility_certified(w,T[bad,-1],true)
        end
    end
    for mode in (RoundDown,RoundUp)
        setrounding(BigFloat,mode) do
            w,r=fixture(BigFloat)
            accepted,v,used=JS._certified_infeasibility_witness(w,r,true)
            @test accepted==JS._floating_infeasibility_certified(w,r,true) && v===r && used==0
            @test !JS._tight_certificate_bounds(BigFloat)
        end
    end
    previous=get_zero_subnormals()
    try
        set_zero_subnormals(true)
        @test !JS._tight_certificate_bounds(Float64)
        @test isequal(JS._certificate_add_product_bounds(0.,0.,Inf,0.,true),JS._add_product_bounds(0.,0.,Inf,0.))
    finally;set_zero_subnormals(previous);end
end
end
