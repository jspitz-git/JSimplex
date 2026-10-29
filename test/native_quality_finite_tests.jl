using Test,SparseArrays,Random
using .JSimplex

@testset "Native quality finite validation" begin
    for T in (Float32,Float64)
        values=T[0,-0.0,nextfloat(zero(T)),floatmin(T),1,-1,floatmax(T)]
        @test JSimplex._quality_finite_values(values)
        @test JSimplex._quality_finite_values(T[])
        @test JSimplex._quality_finite_values(view(values,:))
        for bad in (T(Inf),T(-Inf),T(NaN)),position in eachindex(values)
            trial=copy(values);trial[position]=bad;snapshot=copy(trial)
            @test !JSimplex._quality_finite_values(trial)
            @test !JSimplex._quality_finite_values(view(trial,:))
            @test isequal(trial,snapshot)
        end
        for dense in (false,true),t in (false,true)
            mat=sparse(T[4 1 0; -1 4 1; 0 -1 4]);dense && (mat=Matrix(mat))
            x=T[1,2,-1];rhs=(t ? transpose(mat) : mat)*x
            s=JSimplex.SolveQualityScratch(T,3);p=JSimplex.NumericalPolicy(T)
            snapshot=deepcopy((mat,x,rhs))
            @test JSimplex.solve_quality!(s,mat,x,rhs,p;transposed=t).reliable
            @test all(iszero,s.residual)
            @test isequal((mat,x,rhs),snapshot)
            @test_throws ArgumentError JSimplex.solve_quality!(s,mat,s.work_residual,rhs,p;transposed=t)
            @test_throws DimensionMismatch JSimplex.solve_quality!(s,mat,T[1],rhs,p;transposed=t)
            wrong=copy(x);wrong[1]+=one(T)
            @test !JSimplex.solve_quality!(s,mat,wrong,rhs,p;transposed=t).reliable
            for source in (:matrix,:solution,:rhs),value in (T(Inf),T(NaN))
                a,b,c=deepcopy((mat,x,rhs))
                source===:matrix ? (a[1,1]=value) : source===:solution ? (b[1]=value) : (c[1]=value)
                before=deepcopy((a,b,c))
                q=JSimplex.solve_quality!(s,a,b,c,p;transposed=t)
                @test !q.finite && !q.reliable
                @test all(isinf,s.residual)
                @test isequal((a,b,c),before)
            end
        end
    end
    # Generic/multiprecision fallback semantics remain unchanged.
    for T in (BigFloat,Rational{BigInt})
        x=T[0,1,-1];before=deepcopy(x)
        @test JSimplex._quality_finite_values(x)
        @test isequal(x,before)
    end
end
