using Test, JSimplex, SparseArrays, LinearAlgebra

function nonzero_coupled_chain(T; count=20)
    # Homogeneous differences leave a nonzero constant component undetermined.
    # Row sweeps propagate the small last-coordinate correction only one row
    # per sweep. Replacing the whole point by the minimum-norm solution (zero)
    # would exceed the permitted change; a residual solve must retain it.
    B=spzeros(T,count-1,count)
    for row in 1:count-1
        B[row,row]=one(T)
        B[row,row+1]=-one(T)
    end
    value=T===Float32 ? T(1e-8) : T(1e-16)
    delta=value*(T===Float32 ? T(1e-2) : T(1e-8))
    x=fill(value,count)
    x[end]-=delta
    return B,zeros(T,count-1),x,2delta
end

@testset "Nonzero block corrections retain limits and reject invalid proposals" begin
    for T in (Float32,Float64)
        B,rhs,initial,cutoff=nonzero_coupled_chain(T)
        policy=JSimplex.NumericalPolicy(T)
        for mode in (:cutoff,:inconsistent,:boundary,:columns,:rows)
            matrix=copy(B);right=copy(rhs);x=copy(initial);limit=cutoff
            if mode==:cutoff
                limit=cutoff/T(1000)
            elseif mode==:inconsistent
                matrix=vcat(matrix,matrix[1:1,:]);push!(right,cutoff)
            elseif mode==:boundary
                matrix=hcat(matrix,spzeros(T,size(matrix,1),1))
                last=spzeros(T,1,size(matrix,2));last[1,1]=T(1e20);last[1,end]=one(T)
                matrix=vcat(matrix,last);push!(x,one(T));push!(right,T(1e20)*x[1]+one(T))
            elseif mode==:columns
                matrix,right,x,limit=nonzero_coupled_chain(T;count=65)
            else
                matrix=repeat(matrix,7,1);right=repeat(right,7)
            end
            before=copy(x)
            # Direct coupled entry exercises bounds even when repeated rows
            # would let the scalar sweeps converge before the block is needed.
            scratch=JSimplex.SolveQualityScratch(T,length(right))
            JSimplex._compensated_solve_quality!(scratch,matrix,x,right,policy,false)
            @test !JSimplex._native_phase_coupled_rows!(x,matrix,copy(transpose(matrix)),right,
                policy,limit,scratch,()->false)
            @test isequal(x,before)
        end
    end
end

@testset "Nonzero reconstruction does not publish interrupted candidates" begin
    B,rhs,initial,cutoff=nonzero_coupled_chain(Float64)
    policy=JSimplex.NumericalPolicy(Float64)
    calls=Ref(0)
    @test JSimplex._native_phase_local_rows!(copy(initial),B,rhs,policy,cutoff,
        ()->begin calls[]+=1;false end)
    total=calls[]
    for boundary in unique([1,total÷3,total÷2,total-2,total]), throwing in (false,true)
        x=copy(initial);calls[]=0;failure=ErrorException("stop nonzero block correction")
        stop=()->begin
            calls[]+=1
            if calls[]==boundary
                throwing && throw(failure)
                return true
            end
            false
        end
        result=try JSimplex._native_phase_local_rows!(x,B,rhs,policy,cutoff,stop) catch e;e end
        @test result === (throwing ? failure : false)
        @test isequal(x,initial)
    end
end

@testset "Coupled residual reconstruction retains nonzero null-space values" begin
    for T in (Float32,Float64)
        B,rhs,x,cutoff=nonzero_coupled_chain(T)
        before=copy(x)
        policy=JSimplex.NumericalPolicy(T)
        @test !JSimplex.solve_quality!(JSimplex.SolveQualityScratch(T,length(rhs)),B,x,rhs,policy).reliable
        @test JSimplex._native_phase_local_rows!(x,B,rhs,policy,cutoff,()->false)
        @test JSimplex.solve_quality!(JSimplex.SolveQualityScratch(T,length(rhs)),B,x,rhs,policy).reliable
        @test maximum(abs,x-before)<=cutoff
        @test minimum(x)>minimum(before)/2
        @test maximum(x)-minimum(x)<=T(2)*policy.solve_tolerance*maximum(abs,x)
    end
end
