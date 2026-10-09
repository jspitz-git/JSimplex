using JSimplex, Test, SparseArrays

function signed_zero_pricing_workspace(::Type{T},columns=2) where T
    A=columns==0 ? spzeros(T,2,0) : sparse(T[1 0;0 1])
    p=LinearProblem(A,zeros(T,columns);row_lower=zeros(T,2))
    options=SolverOptions(T;verbose=false)
    policy=JSimplex.NumericalPolicy(T;sparse_pricing=true)
    JSimplex.initialize_workspace(p,options;progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
end
signed_price_allocated(ws,out,rhs)=(@allocated JSimplex.price!(out,ws,rhs))

@testset "Dense sparse-pricing output preserves CSC slack zero signs" begin
    for T in (Float16,Float32,Float64)
        ws=signed_zero_pricing_workspace(T)
        out=zeros(T,4);reference=similar(out)
        for rhs in (T[0,-0.0],T[-0.0,2],T[1,-0.0])
            JSimplex._csc_price!(reference,ws.problem.A,rhs)
            JSimplex.price!(out,ws,rhs)
            @test isequal(out,reference)
        end
        rhs=T[0,-0.0]
        JSimplex.price!(out,ws,rhs)
        signed_price_allocated(ws,out,rhs)
        @test signed_price_allocated(ws,out,rhs)==0
        # With no structural columns, dense RHS and destination may be identical.
        empty_columns=signed_zero_pricing_workspace(T,0)
        alias_rhs=T[0,-0.0]
        expected=-alias_rhs
        JSimplex.price!(alias_rhs,empty_columns,alias_rhs)
        @test isequal(alias_rhs,expected)
    end
end

@testset "Dense pricing copy protects overlapping RHS storage" begin
    for T in (Float16,Float32,Float64)
        out=T[0,-0.0,7,8]
        rhs=@view out[1:2]
        values=T[3,4,0,0]
        expected=vcat(values[1:2],-copy(rhs))
        JSimplex._copy_sparse_prices!(out,values,rhs,2)
        @test isequal(out,expected)
    end
end
