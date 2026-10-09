include("paired.jl")
using Test
function differential()
    rng=MersenneTwister(820)
    accepted=0;rejected=0
    @testset "Frozen point certificate accepted/rejected differential" begin
        for T in (Float32,Float64), trial in 1:120
            m=16;n=9
            D=T.(rand(rng,-8:8,m,n))./T(8);D[rand(rng,m,n).<0.6].=zero(T)
            D[1,1]=T(1)/T(2)
            x=T.(rand(rng,-4:4,n))./T(2);x[1]=one(T);A=sparse(D);activity=A*x
            p=LinearProblem(A,zeros(T,n);row_lower=activity .- T(1),row_upper=activity .+ T(1),column_lower=fill(T(-Inf),n))
            w=JS._initialize_workspace_state(p,SolverOptions(T;algorithm=:primal,primal_tolerance=eps(T)^2))
            w.primal[1:n]=x;w.primal[n+1:end]=activity
            @test BASELINE(w)==JS._legacy_primal_point_certified(w)==true;accepted+=1
            p=w.problem
            row=rand(rng,1:m);oldbound=p.row_upper[row]
            p.row_upper[row]=Bound(activity[row]-T(1)/T(8))
            @test BASELINE(w)==JS._legacy_primal_point_certified(w)==false;rejected+=1
            p.row_upper[row]=oldbound
            w.primal[n+row]+=T(1)/T(8)
            @test BASELINE(w)==JS._legacy_primal_point_certified(w)==false;rejected+=1
            w.primal[n+row]=activity[row]
            @test BASELINE(w)==JS._legacy_primal_point_certified(w)==true;accepted+=1
            # LinearProblem owns a copied matrix; mutate that actual matrix.
            matrix=w.problem.A;@assert !isempty(matrix.nzval)
            column=findfirst(j->!iszero(x[j]) && matrix.colptr[j+1]>matrix.colptr[j],1:n)
            k=rand(rng,collect(nzrange(matrix,column)));oldvalue=matrix.nzval[k];matrix.nzval[k]=T(NaN)
            @test BASELINE(w)==JS._legacy_primal_point_certified(w)==false;rejected+=1
            matrix.nzval[k]=oldvalue
            @test BASELINE(w)==JS._legacy_primal_point_certified(w)==true;accepted+=1
            column=findfirst(j->matrix.colptr[j+1]>matrix.colptr[j],1:n)
            w.primal[column]+=T(1)/T(8)
            @test BASELINE(w)==JS._legacy_primal_point_certified(w)==false;rejected+=1
        end
    end
    println("Explicit accepted checks=",accepted," rejected checks=",rejected)
end
Base.invokelatest(differential)
