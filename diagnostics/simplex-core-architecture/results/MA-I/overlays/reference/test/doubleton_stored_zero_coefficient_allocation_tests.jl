using SparseArrays

@testset "Stored zero doubleton coefficients leave rows unchanged" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), pivot in (-2,2), rhs in (-4,0,4), stored_zero in (-0.0,0.0), bounds in ((0,0),(-10,10),(nothing,10),(-10,nothing),(nothing,nothing))
        lo,hi=bounds;cast(x)=isnothing(x) ? nothing : T(x)
        A=sparse([1,2,1,2],[1,1,2,2],T[pivot,stored_zero,1,2],2,2)
        problem=LinearProblem(A,T[2,3];objective_constant=T(7),row_lower=[T(rhs),cast(lo)],row_upper=[T(rhs),cast(hi)],
            column_lower=[nothing,T(-10)],column_upper=[nothing,T(10)])
        original=deepcopy(problem);result=JSimplex.substitute_free_doubleton(problem);alpha=T(rhs)/T(pivot);beta=-one(T)/T(pivot)
        @test nnz(problem.A)==4 && isequal(problem.A.nzval[2],T(stored_zero))
        @test result.problem.A==reshape(T[2],1,1)
        @test isequal(result.problem.row_lower,problem.row_lower[2:2]) && isequal(result.problem.row_upper,problem.row_upper[2:2])
        @test result.problem.objective==T[3+2beta] && result.problem.objective_constant==7+2alpha
        @test JSimplex.postsolve_primal(result,T[2])==T[alpha+2beta,2]
        basis=JSimplex.Basis([2],[JSimplex.FREE_NONBASIC,JSimplex.BASIC])
        @test JSimplex.restore_basis(result,basis).basic_indices==[1,4]
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
        @test isequal(problem.objective,original.objective) && isequal(problem.objective_constant,original.objective_constant)
    end
end

@testset "Stored zeros preserve untouched BigFloat values and signed bounds" begin
    for sign in (-1,1), ambient in (32,64,256)
        problem=setprecision(BigFloat,256) do
            high=BigFloat(1)+BigFloat(2)^(-200)
            A=sparse([1,2,1,2],[1,1,2,2],BigFloat[2,sign*zero(BigFloat),1,high],2,2)
            LinearProblem(A,BigFloat[0,3];objective_constant=BigFloat(7),row_lower=BigFloat[4,high],row_upper=BigFloat[4,high],
                column_lower=[nothing,BigFloat(-10)],column_upper=[nothing,BigFloat(10)])
        end
        original=deepcopy(problem)
        setprecision(BigFloat,ambient) do
            result=JSimplex.substitute_free_doubleton(problem)
            @test size(result.problem.A)==(1,1)
            @test isequal(result.problem.A[1,1],problem.A[2,2]) && precision(result.problem.A[1,1])==256
            @test isequal(result.problem.row_lower,problem.row_lower[2:2]) && isequal(result.problem.row_upper,problem.row_upper[2:2])
            @test precision(bound_value(result.problem.row_lower[1]))==256 && precision(bound_value(result.problem.row_upper[1]))==256
            @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.row_lower,original.row_lower)
        end
    end
    for T in (Float32,Float64)
        A=sparse([1,2,1,2],[1,1,2,2],T[2,-0.0,1,2],2,2)
        problem=LinearProblem(A,T[0,3];row_lower=T[4,-0.0],row_upper=T[4,0.0],column_lower=[nothing,T(-10)],column_upper=[nothing,T(10)])
        result=JSimplex.substitute_free_doubleton(problem)
        @test isequal(bound_value(result.problem.row_lower[1]),T(-0.0))
        @test isequal(bound_value(result.problem.row_upper[1]),T(0.0))
    end
end

@testset "Tiny nonzero doubleton coefficients still update the matrix" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), sign in (-1,1), ambient in (32,64,256)
        problem=setprecision(BigFloat,256) do
            tiny=T in (Float32,Float64) ? sign*nextfloat(zero(T)) : T(sign*(big(1)//(BigInt(1)<<200)))
            LinearProblem(sparse(T[1 1;tiny 2tiny]),T[0,3];objective_constant=T(7),row_lower=[T(0),nothing],row_upper=[T(0),nothing],
                column_lower=[nothing,T(-10)],column_upper=[nothing,T(10)])
        end
        original=deepcopy(problem)
        setprecision(BigFloat,ambient) do
            result=JSimplex.substitute_free_doubleton(problem)
            @test result.problem.A==reshape(T[problem.A[2,1]],1,1)
            @test !iszero(result.problem.A[1,1])
            @test JSimplex.postsolve_primal(result,T[2])==T[-2,2]
            @test isequal(problem.A.nzval,original.A.nzval)
        end
    end
    for T in (Float32,Float64), sign in (-1,1)
        tiny=sign*nextfloat(zero(T));A=sparse([1,2,1,2],[1,1,2,2],T[2,tiny,1,0],2,2)
        problem=LinearProblem(A,T[0,3];row_lower=[T(0),nothing],row_upper=[T(0),nothing],column_lower=[nothing,T(-10)],column_upper=[nothing,T(10)])
        original=deepcopy(problem);result=JSimplex.substitute_free_doubleton(problem)
        @test result.problem===problem && isempty(result.postsolve_stack)
        @test isequal(problem.A.nzval,original.A.nzval)
    end
end

@testset "Doubleton substitution skips conversion of stored zero coefficients" begin
function doubleton_stored_zero_coefficient_probe(kind; count=128, T=Float64)
    coefficient=kind==:negative ? -zero(T) : kind==:nonzero ? T(3) : zero(T)
    first_rows=kind==:absent ? [1] : collect(1:count+1)
    rows=vcat(first_rows,collect(1:count+1))
    columns=vcat(fill(1,length(first_rows)),fill(2,count+1))
    values=vcat(kind==:absent ? T[2] : T[2;fill(coefficient,count)],T[1;fill(T(2),count)])
    A=sparse(rows,columns,values,count+1,2)
    lower=kind==:unbounded ? nothing : kind==:equal_bounds ? T(20) : T(-100)
    upper=kind==:unbounded ? nothing : kind==:equal_bounds ? T(20) : T(100)
    problem=LinearProblem(A,T[2,3];objective_constant=T(7),
        row_lower=[T(4);fill(lower,count)],row_upper=[T(4);fill(upper,count)],
        column_lower=[nothing,T(-10)],column_upper=[nothing,T(10)])
    return problem,JSimplex.substitute_free_doubleton
end
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:positive,:negative,:equal_bounds,:unbounded,:nonzero,:absent)
        count=4;problem,pass=doubleton_stored_zero_coefficient_probe(kind;count,T);original=deepcopy(problem);result=pass(problem)
        coefficient=problem.A[2,1];shift=2coefficient
        @test nnz(problem.A)==(kind==:absent ? count+2 : 2count+2)
        @test result.problem.A==fill(T(2)-coefficient/2,count,1)
        translated(bound)=isfinite(bound) ? Bound(bound_value(bound)-shift) : bound
        @test result.problem.row_lower==translated.(problem.row_lower[2:end]) && result.problem.row_upper==translated.(problem.row_upper[2:end])
        @test result.problem.objective==T[2] && result.problem.objective_constant==11
        @test only(result.postsolve_stack).eliminated==1 && only(result.postsolve_stack).equality_row==1
        primal=T[2];restored=JSimplex.postsolve_primal(result,primal)
        @test restored==T[1,2]
        @test problem.objective_constant+sum(problem.objective.*restored)==result.problem.objective_constant+sum(result.problem.objective.*primal)
        for state in (JSimplex.AT_LOWER,JSimplex.AT_UPPER)
            basis=JSimplex.Basis(collect(2:count+1),[state;fill(JSimplex.BASIC,count)]);restored_basis=JSimplex.restore_basis(result,basis)
            @test restored_basis.basic_indices==[1;collect(4:count+3)]
            @test restored_basis.states[1:2]==[JSimplex.BASIC,state]
        end
        result.problem.objective[1]+=one(T);result.problem.A.nzval[1]+=one(T);result.problem.row_upper[1]=Bound(T(20))
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.objective,original.objective)
        @test isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper)
        @test isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
    for (kind,limit) in ((:positive,906),(:negative,906),(:equal_bounds,906),(:unbounded,906),(:nonzero,17470),(:absent,316))
        problem,pass=doubleton_stored_zero_coefficient_probe(kind)
        pass(problem)
        measured=@timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats)<=limit
    end
end
