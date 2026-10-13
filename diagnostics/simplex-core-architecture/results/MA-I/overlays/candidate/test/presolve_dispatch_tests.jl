using SparseArrays

@testset "Exact interval dispatch includes finite and unbounded endpoints" begin
    endpoints = JSimplex.ExactEndpoint[nothing, -1, 0, 1]
    intervals = [(lower, upper) for lower in endpoints for upper in endpoints
                 if isnothing(lower) || isnothing(upper) || lower <= upper]
    # Every possible endpoint and every region between/outside endpoints has a
    # witness, making set comparisons an independent oracle for these intervals.
    witnesses = Rational{BigInt}[-2, -1, -1//2, 0, 1//2, 1, 2]
    members(interval) = Set(x for x in witnesses
        if (isnothing(interval[1]) || x >= interval[1]) &&
           (isnothing(interval[2]) || x <= interval[2]))
    for a in intervals, b in intervals
        @test JSimplex._interval_subset(a, b) == issubset(members(a), members(b))
        @test JSimplex._interval_disjoint(a, b) == isdisjoint(members(a), members(b))
    end
end

@testset "Aggregate presolve history preserves inferred restoration and ownership" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt})
        chain=LinearProblem(sparse(T[1 1 0;0 1 1]),T[1,0,0];
            row_lower=[nothing,T(5)],row_upper=[T(10),nothing],
            column_upper=[nothing,nothing,T(2)])
        reduced=JSimplex.presolve_problem(chain)
        @test length(reduced.postsolve_stack)>1
        @test size(reduced.problem.A)==(0,0)
        input=T[]
        restored=@inferred JSimplex.postsolve_primal(reduced,input)
        @test restored==T[0,3,2]
        basis=JSimplex.Basis(Int[],JSimplex.VariableState[])
        restored_basis=@inferred JSimplex.restore_basis(reduced,basis)
        # The existing tuple replay is an independent reference for storage order.
        tuple_result=JSimplex.PresolveResult(reduced.problem,
            Tuple(reduced.postsolve_stack),reduced.original_column_count)
        reference_basis=JSimplex.restore_basis(tuple_result,basis)
        @test restored_basis.basic_indices==reference_basis.basic_indices
        @test restored_basis.states==reference_basis.states
        @test restored==JSimplex.postsolve_primal(tuple_result,input)
        restored[1]=T(9)
        @test JSimplex.postsolve_primal(reduced,input)==T[0,3,2]
        @test isempty(basis.states) && isempty(basis.basic_indices)

        unchanged=LinearProblem(sparse(T[1 2;2 1]),zeros(T,2);
            row_upper=T[3,4],column_lower=[nothing,nothing])
        identity=JSimplex.presolve_problem(unchanged)
        @test isempty(identity.postsolve_stack)
        @test identity.problem===unchanged
        original=T[0,0]
        copied=@inferred JSimplex.postsolve_primal(identity,original)
        @test copied==original && copied !== original
        copied[1]=one(T)
        @test original==zeros(T,2)
        original_basis=JSimplex.Basis([3,4],JSimplex.VariableState[
            JSimplex.FREE_NONBASIC,JSimplex.FREE_NONBASIC,JSimplex.BASIC,JSimplex.BASIC])
        copied_basis=@inferred JSimplex.restore_basis(identity,original_basis)
        @test copied_basis.basic_indices==original_basis.basic_indices
        @test copied_basis.states==original_basis.states
        @test copied_basis.basic_indices !== original_basis.basic_indices
        @test copied_basis.states !== original_basis.states
        copied_basis.basic_indices[1]=1
        copied_basis.states[1]=JSimplex.BASIC
        @test original_basis.basic_indices==[3,4]
        @test original_basis.states[1]==JSimplex.FREE_NONBASIC
    end
end
