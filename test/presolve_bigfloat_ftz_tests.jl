using JSimplex,SparseArrays,Test
const JS=JSimplex
@testset "BigFloat inequality eligibility is independent of hardware FTZ" begin
    old=get_zero_subnormals()
    try
        set_zero_subnormals(true)
        @test get_zero_subnormals()
        for bits in (64,240,512)
            setprecision(BigFloat,bits) do
                p=LinearProblem(sparse(BigFloat[1 1 1;1 -1 -1]),zeros(BigFloat,3);
                    row_lower=zeros(BigFloat,2),column_lower=fill(nothing,3),column_upper=fill(nothing,3))
                h=JS._PostsolveHistory(BigFloat)
                q=JS._augment_inequalities(JS.identity_presolve(p),p,BigFloat(1e-7),h,()->false,false;rounded_costs=false)
                @test size(q.problem.A)==(0,0)
                if size(q.problem.A)==(0,0)
                    @test JS._original_primal_feasible(p,JS.postsolve_primal(q,BigFloat[]),BigFloat(1e-7))
                end
                @test isnothing(JS._PresolveRepeat.current())
            end
        end
    finally
        set_zero_subnormals(old)
    end
    @test get_zero_subnormals()==old
end
