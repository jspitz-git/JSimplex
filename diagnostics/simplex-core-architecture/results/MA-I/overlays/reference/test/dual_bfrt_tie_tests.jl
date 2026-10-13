using Test, JSimplex, SparseArrays

function bfrt_tie_fixture(T)
    tiny=T(1)/T(1_000_000)
    problem=LinearProblem(sparse(reshape(T[tiny,1,1],1,3)),T[0,0,1];
        row_lower=T[1],column_upper=[Bound{T}(nothing),Bound{T}(nothing),Bound(one(T))])
    options=SolverOptions(T;algorithm=:dual,verbose=false)
    ws=JSimplex.initialize_workspace(problem,options)
    ws.reduced_costs[1:3].=T[0,0,1]
    row=T[-tiny,-1,-1,1]
    return ws,row
end

@testset "Equal BFRT breakpoints preserve a strong available pivot" begin
    for T in (Float32,Float64,BigFloat,Rational{Int64},Rational{BigInt}), orientation in (-1,1)
        ws,row=bfrt_tie_fixture(T)
        orientation==1 && (row .*= -one(T))
        entering,flips,exhausted=JSimplex._bound_flipping_ratio_test(ws,row,T(orientation),one(T))
        @test entering==2
        @test isempty(flips) && !exhausted
        # The unrelated boxed column must not remove Harris's existing safe tie.
        ws.upper[3]=Bound{T}(nothing)
        @test JSimplex.dual_ratio_test(ws,row,T(orientation))==2
        # A nonzero equal breakpoint has the same numerical ambiguity.
        ws.upper[3]=Bound(one(T))
        ws.reduced_costs[1:3].=T[abs(row[1]),1,2]
        @test JSimplex._bound_flipping_ratio_test(ws,row,T(orientation),one(T))[1]==2
        # A genuinely earlier breakpoint retains priority, without a Harris window.
        ws.reduced_costs[1:3].=T[0,T <: AbstractFloat ? eps(T) : T(1)/T(10^6),1]
        @test JSimplex._bound_flipping_ratio_test(ws,row,T(orientation),one(T))[1]==1
    end
end

@testset "Equal strengths keep index order and do not mutate ratio inputs" begin
    ws, row = bfrt_tie_fixture(Float64)
    row[1] = row[2]
    before = deepcopy((row, ws.primal, ws.reduced_costs, ws.basis.states))
    @test JSimplex._bound_flipping_ratio_test(ws, row, -1.0, 1.0)[1] == 1
    @test isequal(before, (row, ws.primal, ws.reduced_costs, ws.basis.states))
    push!(ws.scratch.rejected_entering, 1)
    @test JSimplex._bound_flipping_ratio_test(ws, row, -1.0, 1.0)[1] == -1
end

@testset "Signed zero breakpoints represent the same dual step" begin
    for T in (Float32, Float64, BigFloat)
        ws, row = bfrt_tie_fixture(T)
        ws.lower[1] = Bound{T}(nothing)
        ws.upper[1] = Bound(zero(T))
        ws.basis.states[1] = JSimplex.AT_UPPER
        row[1:3] .= T[-T(1)/T(1_000_000),1,1]
        @test iszero(ws.reduced_costs[1] / row[1])
        @test signbit(ws.reduced_costs[1] / row[1])
        # An unbounded weak upper-state candidate has -0, while the strong lower
        # candidate has +0. Their mathematical dual steps are identical.
        @test JSimplex._bound_flipping_ratio_test(ws,row,one(T),one(T))[1] == 2
    end
end
