module NativeBasicStationarityTests
# Ordinary Test regressions. No counters, method replacement or custom test recorder.
using Test, JSimplex, SparseArrays, TOML, LinearAlgebra
const NBST = JSimplex
const PERMANENT_DATA = TOML.parsefile(joinpath(@__DIR__,"fixtures","native_basic_stationarity.toml"))
const NBST_DATA = PERMANENT_DATA["component"]
nbst_float(s::String) = reinterpret(Float32, parse(UInt32, s; base=16))
nbst_bits(x::Float32) = reinterpret(UInt32,x)
nbst_bits(x::Float64) = reinterpret(UInt64,x)

# Independent exact IEEE decoder, not the production pair/error recurrence,
# Base floating decompose, or _native_dyadic_parts. No floating arithmetic here.
function nbst_exact_bits(bits::UInt64, fraction::Int, exponent_bits::Int, bias::Int)
    exponent_mask = (UInt64(1) << exponent_bits)-UInt64(1)
    exponent = Int((bits >> fraction) & exponent_mask)
    exponent == Int(exponent_mask) && throw(ArgumentError("nonfinite oracle input"))
    significand = BigInt(bits & ((UInt64(1) << fraction)-UInt64(1)))
    exponent != 0 && (significand += BigInt(1) << fraction)
    (bits >> (fraction+exponent_bits)) != 0 && (significand = -significand)
    power = (exponent == 0 ? 1-bias : exponent-bias)-fraction
    return power >= 0 ? (significand << power)//BigInt(1) :
                        significand//(BigInt(1) << (-power))
end
nbst_exact(x::Float32) = nbst_exact_bits(UInt64(reinterpret(UInt32,x)),23,8,127)
nbst_exact(x::Float64) = nbst_exact_bits(reinterpret(UInt64,x),52,11,1023)
function nbst_exact_residual(p, y, column)
    value = nbst_exact(p.objective[column])
    for k in nzrange(p.A,column)
        value -= nbst_exact(p.A.nzval[k])*nbst_exact(y[p.A.rowval[k]])
    end
    value
end
function nbst_rational(s::String)
    numerator,denominator=split(s,'/')
    parse(BigInt,numerator)//parse(BigInt,denominator)
end
function nbst_problem(a::Vector{T}, c::T) where T
    # Preserve explicitly stored zero coefficients and their signs. sparse(dense)
    # would erase exactly the zero/unit-shortcut probes required by this suite.
    A=SparseMatrixCSC{T,Int}(length(a),1,Int[1,length(a)+1],collect(1:length(a)),copy(a))
    NBST.LinearProblem(A,T[c])
end
function nbst_snapshot(p,y)
    owners=(p.A.colptr,p.A.rowval,p.A.nzval,p.objective,y)
    values=(copy(p.A.colptr),copy(p.A.rowval),[nbst_bits(x) for x in p.A.nzval],
            [nbst_bits(x) for x in p.objective],[nbst_bits(x) for x in y])
    owners,values
end
function nbst_unchanged(before,p,y)
    after=nbst_snapshot(p,y)
    all(before[1][i] === after[1][i] for i in 1:5) && isequal(before[2],after[2])
end
function nbst_checked(p::NBST.LinearProblem{T},y::Vector{T},j::Int) where T
    NBST._native_basic_certificate_mode(T) || return nothing
    NBST._native_basic_column_interval(p,y,j)
end
function nbst_coarse(p,y,j)
    lower,upper=NBST._original_reduced_cost_bounds(p,y)
    lower[j],upper[j]
end
# Test-only negative alternative: ordinary direct residual endpoints can still
# lose information at column64. This is not the candidate or exact oracle.
function nbst_plain_direct(p,y,j)
    lower=upper=p.objective[j]
    for k in nzrange(p.A,j)
        pl,pu=NBST._primal_product_bounds(p.A.nzval[k],y[p.A.rowval[k]])
        lower,_=NBST._primal_difference_bounds(lower,pu)
        _,upper=NBST._primal_difference_bounds(upper,pl)
    end
    lower,upper
end
function nbst_saved_problem()
    m=NBST_DATA["matrix"]
    A=SparseMatrixCSC{Float32,Int}(m["m"],m["n"],Int.(m["colptr"]),
        Int.(m["rowval"]),nbst_float.(m["nzval_bits"]))
    NBST.LinearProblem(A,nbst_float.(m["objective_bits"]))
end

# Saved residuals must be enclosed tightly; the coarse provider is a negative control.
function nbst_saved_columns(provider)
    @testset "NBST saved original and trial residuals" begin
        p=nbst_saved_problem()
        for role in ("original","trial")
            y=nbst_float.(NBST_DATA[role]["dual_bits"])
            for j in 1:64
                before=nbst_snapshot(p,y)
                exact=nbst_exact_residual(p,y,j)
                @test exact == nbst_rational(NBST_DATA[role]["exact_residual"][j])
                coarse=nbst_coarse(p,y,j)
                @test nbst_exact(coarse[1]) <= exact <= nbst_exact(coarse[2])
                result=provider(p,y,j)
                @test result !== nothing
                if result !== nothing
                    @test all(isfinite,result) && result[1] <= result[2]
                    @test nbst_exact(result[1]) == exact
                    @test nbst_exact(result[2]) == exact
                    @test NBST._native_basic_intersection(coarse,result) == result
                    @test isbitstype(typeof(result))
                end
                @test nbst_unchanged(before,p,y)
            end
        end
    end
end

@testset "NBST independent exact decoder identities" begin
    for T in (Float32,Float64)
        @test nbst_exact(T(1)) == 1//1
        @test nbst_exact(-zero(T)) == 0//1
        @test nbst_exact(nextfloat(zero(T))) == BigInt(1)//(BigInt(1) << (T===Float32 ? 149 : 1074))
        @test nbst_exact(nextfloat(one(T))) == 1//1+BigInt(1)//(BigInt(1) << (precision(T)-1))
        @test_throws ArgumentError nbst_exact(T(Inf))
        @test_throws ArgumentError nbst_exact(T(NaN))
    end
end

@testset "NBST eligibility modes and unsupported scalar types" begin
    for T in (Float32,Float64,Float16,BigFloat,Rational{BigInt}),
        mode in (RoundNearest,RoundDown,RoundUp,RoundToZero,RoundFromZero), ftz in (false,true)
        expected=(T===Float32 || T===Float64) && mode==RoundNearest && !ftz
        @test NBST._native_basic_certificate_mode(T,mode,ftz) === expected
    end
    for T in (Float32,Float64)
        @test NBST._native_basic_certificate_mode(T) # Admitted default mode required.
    end
    for T in (Float16,BigFloat,Rational{BigInt})
        @test !NBST._native_basic_certificate_mode(T)
        @test !hasmethod(NBST._native_basic_column_interval,Tuple{NBST.LinearProblem{T},Vector{T},Int})
    end
end

@testset "NBST original first and last column controls" begin
    p=nbst_saved_problem();tol=nbst_float(NBST_DATA["tolerance_bits"])
    for role in ("original","trial")
        y=nbst_float.(NBST_DATA[role]["dual_bits"])
        for j in (1,64)
            coarse=nbst_coarse(p,y,j)
            @test coarse == (reinterpret(Float32,UInt32(0xb4000000)),zero(Float32))
            @test coarse[1] < -tol
            @test nbst_exact_residual(p,y,j) == -BigInt(1)//(BigInt(1)<<25)
        end
        direct_first=nbst_plain_direct(p,y,1);direct_last=nbst_plain_direct(p,y,64)
        @test direct_first[1] == direct_first[2]
        @test direct_first[1] >= -tol && direct_first[2] <= tol
        @test direct_last == nbst_coarse(p,y,64)
        @test direct_last[1] < -tol
    end
end

nbst_saved_columns(nbst_checked)

@testset "NBST finite product cancellation and input lifetime" begin
    for T in (Float32,Float64)
        large=ldexp(one(T),precision(T))
        cases=[
            (T[],T[],T(0.25)),
            (T[1],T[0.5],T(1)),
            (T[large,1,-large],ones(T,3),T(1)),
            (T[nextfloat(one(T)),-nextfloat(one(T)),1],T[prevfloat(one(T)),prevfloat(one(T)),1],T(1)),
            (T[-1,3],T[0.5,0.25],T(-0.5)),
            (T[0,-0.0,1],T[-1,1,-0.0],-zero(T)),
            (T[floatmax(T)],T[0],T(0.25)),
            (T[1],T[nextfloat(zero(T))],zero(T)),
        ]
        a=repeat(T[1,-1,nextfloat(one(T)),-nextfloat(one(T))],32)
        y=repeat(T[1,1,prevfloat(one(T)),prevfloat(one(T))],32)
        push!(cases,(a,y,T(0.25)))
        for (a,y,c) in cases
            p=nbst_problem(a,c);before=nbst_snapshot(p,y)
            result=nbst_checked(p,y,1)
            @test result !== nothing
            if result !== nothing
                exact=nbst_exact_residual(p,y,1)
                @test all(isfinite,result) && result[1] <= result[2]
                @test nbst_exact(result[1]) <= exact <= nbst_exact(result[2])
                @test isbitstype(typeof(result))
            end
            @test nbst_unchanged(before,p,y)
            again=nbst_checked(p,y,1)
            @test isequal(again,result)
        end
        p=nbst_problem(T[1],one(T));y=p.objective # Legal input alias, both read-only.
        before=nbst_snapshot(p,y)
        @test nbst_checked(p,y,1) == (zero(T),zero(T))
        @test p.objective === y && nbst_unchanged(before,p,y)
    end
end

@testset "NBST absolute tolerance and non-exact product rejection" begin
    for T in (Float32,Float64)
        for tol in (zero(T),T(1e-7))
            outside=nextfloat(tol)
            for residual in (zero(T),tol,-tol,outside,-outside)
                p=nbst_problem(T[0],residual);y=T[0]
                got=nbst_checked(p,y,1)
                @test got !== nothing
                if got !== nothing
                    exact=nbst_exact_residual(p,y,1)
                    @test nbst_exact(got[1]) == exact == nbst_exact(got[2])
                    certified=got[1]>=-tol && got[2]<=tol
                    @test certified == (abs(exact)<=nbst_exact(tol))
                end
            end
        end
        p=nbst_problem(T[nextfloat(one(T))],one(T));y=T[prevfloat(one(T))]
        got=nbst_checked(p,y,1);exact=nbst_exact_residual(p,y,1)
        @test !iszero(exact)
        @test got !== nothing
        if got !== nothing
            @test nbst_exact(got[1]) <= exact <= nbst_exact(got[2])
            @test !(got[1]>=zero(T) && got[2]<=zero(T))
        end
    end
end

@testset "NBST finite checks precede zero and unit shortcuts" begin
    for T in (Float32,Float64), bad in (T(Inf),T(-Inf),T(NaN))
        p=nbst_problem(T[1],zero(T));y=T[0];p.A.nzval[1]=bad
        before=nbst_snapshot(p,y)
        @test nbst_checked(p,y,1) === nothing
        @test nbst_unchanged(before,p,y)
        p=nbst_problem(T[0],zero(T));y=T[bad]
        @test nnz(p.A)==1 && iszero(p.A.nzval[1])
        before=nbst_snapshot(p,y)
        @test nbst_checked(p,y,1) === nothing
        @test nbst_unchanged(before,p,y)
        p=nbst_problem(T[1],zero(T));y=T[1];p.objective[1]=bad
        before=nbst_snapshot(p,y)
        @test nbst_checked(p,y,1) === nothing
        @test nbst_unchanged(before,p,y)
    end
end

@testset "NBST range refusal and ordinary indexing exceptions" begin
    for T in (Float32,Float64)
        tiny=nextfloat(zero(T))
        cases=[(T[floatmax(T)],T[2],zero(T)),
               (T[floatmax(T),floatmax(T)],ones(T,2),zero(T)),
               (T[tiny],T[0.5],zero(T)),
               (T[tiny,tiny],ones(T,2),zero(T)),
               (T[1],T[tiny],T(2)*tiny)]
        for (a,y,c) in cases
            p=nbst_problem(a,c);before=nbst_snapshot(p,y)
            @test nbst_checked(p,y,1) === nothing
            @test nbst_unchanged(before,p,y)
        end
        p=nbst_problem(T[1],one(T));y=T[1];before=nbst_snapshot(p,y)
        @test_throws BoundsError nbst_checked(p,y,0)
        @test_throws BoundsError nbst_checked(p,y,2)
        @test_throws DimensionMismatch nbst_checked(p,T[],1)
        @test nbst_unchanged(before,p,y)
    end
end

@testset "NBST intersection preserves enclosures and refuses invalid intervals" begin
    for T in (Float32,Float64)
        intersect=NBST._native_basic_intersection
        @test intersect((T(-2),T(2)),(T(-1),T(1))) == (T(-1),T(1))
        @test intersect((T(-2),T(1)),(T(0),T(2))) == (T(0),T(1))
        @test intersect((T(1),T(1)),(T(1),T(1))) == (T(1),T(1))
        @test intersect((-zero(T),zero(T)),(zero(T),zero(T))) == (zero(T),zero(T))
        for (coarse,refined) in [((T(0),T(1)),(T(2),T(3))),
                                 ((T(2),T(1)),(T(1),T(2))),
                                 ((T(0),T(2)),(T(2),T(1))),
                                 ((T(-Inf),T(1)),(T(0),T(1))),
                                 ((T(0),T(1)),(T(0),T(Inf))),
                                 ((T(NaN),T(1)),(T(0),T(1))),
                                 ((T(0),T(1)),(T(0),T(NaN)))]
            @test intersect(coarse,refined) === nothing
        end
    end
end

@testset "NBST actual FTZ guard and restoration" begin
    old=get_zero_subnormals()
    try
        set_zero_subnormals(true)
        supported=get_zero_subnormals()
        println("NBST_FTZ_ACTUAL_SUPPORTED ",supported)
        if supported
            for T in (Float32,Float64)
                p=nbst_problem(T[1],one(T));y=T[1]
                @test !NBST._native_basic_certificate_mode(T)
                @test nbst_checked(p,y,1) === nothing
            end
        else
            @test_skip supported
        end
    finally
        set_zero_subnormals(old)
    end
    @test get_zero_subnormals() == old
end

# Test-local baseline for differential checks; never installed in JSimplex.
using JSimplex: Basis, BASIC, _original_reduced_cost_bounds, _primal_row_bounds, _is_exact, _primal_difference_bounds, _is_fixed, _primal_interval_at_bound, _refined_primal_rows_feasible
function nbst2_reference(problem::LinearProblem{T}, options::SolverOptions{T},
                                     basis::Basis, primal::Vector{T}, dual::Vector{T}) where T
    row_count, column_count = size(problem.A)
    length(primal) == column_count && length(dual) == row_count &&
        length(basis.states) == column_count + row_count || return false
    all(isfinite, primal) && all(isfinite, dual) || return false
    reduced_lower, reduced_upper = _original_reduced_cost_bounds(problem, dual)
    all(isfinite, reduced_lower) && all(isfinite, reduced_upper) || return false
    row_lower, row_upper = _primal_row_bounds(problem.A, primal, _is_exact(T))
    _, negative_tolerance = _primal_difference_bounds(zero(T), options.dual_tolerance)
    uncertain_rows = nothing
    active_bounds = nothing
    for index in eachindex(reduced_lower)
        stationary = reduced_lower[index] >= negative_tolerance &&
                     reduced_upper[index] <= options.dual_tolerance
        basis.states[index] == BASIC && !stationary && return false
        stationary && continue
        lower = index <= column_count ? problem.column_lower[index] : problem.row_lower[index - column_count]
        upper = index <= column_count ? problem.column_upper[index] : problem.row_upper[index - column_count]
        _is_fixed(lower, upper) && continue
        # Use actual structural values and certified original row activities,
        # not stored slack values or a possibly stale nonbasic bound label.
        value_lower = index <= column_count ? primal[index] : row_lower[index - column_count]
        value_upper = index <= column_count ? primal[index] : row_upper[index - column_count]
        at_lower = reduced_lower[index] >= negative_tolerance &&
                   _primal_interval_at_bound(value_lower, value_upper, lower,
                                             options.primal_tolerance)
        at_upper = reduced_upper[index] <= options.dual_tolerance &&
                   _primal_interval_at_bound(value_lower, value_upper, upper,
                                             options.primal_tolerance)
        at_lower || at_upper || begin
            # Cancellation can make the coarse activity interval inconclusive
            # even when native compensated feasibility has already succeeded.
            # Recheck distance to the priced bound, not just row feasibility.
            index > column_count && T <: Union{Float32,Float64} || return false
            active_bound = reduced_lower[index] >= negative_tolerance ? lower :
                           reduced_upper[index] <= options.dual_tolerance ? upper : nothing
            isnothing(active_bound) && return false
            isfinite(active_bound) || return false
            if isnothing(uncertain_rows)
                uncertain_rows = Int[]
                active_bounds = copy(problem.row_lower)
            end
            row = index - column_count
            push!(uncertain_rows, row)
            active_bounds[row] = active_bound
        end
    end
    isnothing(uncertain_rows) && return true
    return _refined_primal_rows_feasible(problem, primal, options.primal_tolerance,
                                         uncertain_rows, active_bounds, active_bounds)
end

const NBST2_INPUT = Dict("input"=>PERMANENT_DATA["input"])
const NBST2_WITNESS = PERMANENT_DATA["witness"]
const nbst2_candidate = NBST._original_witness_certified
nbst2_bound(s) = s=="unbounded" ? nothing : nbst_float(s)
function nbst2_saved()
    d=NBST2_INPUT["input"];m=d["m"];n=d["n"]
    A=SparseMatrixCSC{Float32,Int}(m,n,Int.(d["colptr"]),Int.(d["rowval"]),nbst_float.(d["nzval"]))
    p=LinearProblem(A,nbst_float.(d["objective"]);
        row_lower=nbst2_bound.(d["row_lower"]),row_upper=nbst2_bound.(d["row_upper"]),
        column_lower=nbst2_bound.(d["column_lower"]),column_upper=nbst2_bound.(d["column_upper"]))
    o=SolverOptions(Float32;verbose=false,primal_tolerance=nbst_float(NBST_DATA["tolerance_bits"]),
        dual_tolerance=nbst_float(NBST_DATA["tolerance_bits"]))
    b=NBST.Basis(Int.(NBST2_WITNESS["basic_indices"]),NBST.VariableState.(UInt8.(NBST2_WITNESS["state_codes"])))
    x=nbst_float.(NBST2_WITNESS["primal_bits"])
    return p,o,b,x
end
function nbst2_snapshot(p,o,b,x,y)
    owners=(p.A.colptr,p.A.rowval,p.A.nzval,p.objective,p.row_lower,p.row_upper,
            p.column_lower,p.column_upper,b.basic_indices,b.states,x,y)
    values=deepcopy(owners)
    return owners,values,o
end
function nbst2_unchanged(s,p,o,b,x,y)
    after=nbst2_snapshot(p,o,b,x,y)
    all(s[1][j]===after[1][j] for j in eachindex(s[1])) && isequal(s[2],after[2]) && s[3]===o
end
nbst2_at(v,b,t)=isfinite(b) && abs(v-nbst_exact(bound_value(b)))<=t
function nbst2_within(v,lo,hi,t)
    (!isfinite(lo) || v>=nbst_exact(bound_value(lo))-t) &&
    (!isfinite(hi) || v<=nbst_exact(bound_value(hi))+t)
end
# Independent original-model point/KKT predicates. No interval or pair helper.
function nbst2_exact_certificate(p,o,b,x,y)
    m,n=size(p.A);pt=nbst_exact(o.primal_tolerance);dt=nbst_exact(o.dual_tolerance)
    length(x)==n && length(y)==m && length(b.states)==m+n || return false
    rows=fill(BigInt(0)//BigInt(1),m)
    for j in 1:n,k in nzrange(p.A,j)
        rows[p.A.rowval[k]]+=nbst_exact(p.A.nzval[k])*nbst_exact(x[j])
    end
    all(nbst2_within(nbst_exact(x[j]),p.column_lower[j],p.column_upper[j],pt) for j in 1:n) || return false
    all(nbst2_within(rows[i],p.row_lower[i],p.row_upper[i],pt) for i in 1:m) || return false
    for j in 1:n+m
        r=j<=n ? nbst_exact_residual(p,y,j) : nbst_exact(y[j-n])
        b.states[j]==NBST.BASIC && (abs(r)<=dt || return false)
        abs(r)<=dt && continue
        lo=j<=n ? p.column_lower[j] : p.row_lower[j-n]
        hi=j<=n ? p.column_upper[j] : p.row_upper[j-n]
        isfinite(lo) && isfinite(hi) && bound_value(lo)==bound_value(hi) && continue
        v=j<=n ? nbst_exact(x[j]) : rows[j-n]
        ((r>=-dt && nbst2_at(v,lo,pt)) || (r<=dt && nbst2_at(v,hi,pt))) || return false
    end
    return true
end
function nbst2_one(T,c; a=one(T),y=one(T),tol=T(1e-7))
    A=SparseMatrixCSC{T,Int}(1,1,[1,2],[1],T[a])
    p=LinearProblem(A,T[c];row_lower=T[0],row_upper=T[0])
    o=SolverOptions(T;verbose=false,dual_tolerance=tol,primal_tolerance=tol)
    b=NBST.Basis([1],[NBST.BASIC,NBST.AT_LOWER])
    p,o,b,T[0],T[y]
end

@testset "NBST2 saved original and repaired witnesses full predicates" begin
    p,o,b,x=nbst2_saved()
    for role in ("original_bits","trial_bits")
        y=nbst_float.(NBST2_WITNESS[role]);before=nbst2_snapshot(p,o,b,x,y)
        @test nbst2_exact_certificate(p,o,b,x,y)
        @test NBST._original_primal_feasible(p,x,o.primal_tolerance)
        @test !nbst2_reference(p,o,b,x,y) # Numerical baseline rejection, never missing methods.
        result=nbst2_candidate(p,o,b,x,y)
        @test result

        @test nbst2_unchanged(before,p,o,b,x,y)
    end
end

@testset "NBST2 conclusive pass fail ambiguity refusal and smallest positive tolerance" begin
    for T in (Float32,Float64)
        p,o,b,x,y=nbst2_one(T,one(T))
        @test nbst2_reference(p,o,b,x,y)
        result=nbst2_candidate(p,o,b,x,y);@test result
        p,o,b,x,y=nbst2_one(T,T(2))
        @test !nbst2_reference(p,o,b,x,y)
        result=nbst2_candidate(p,o,b,x,y);@test !result
        # Genuine nonzero product residual: refinement must not accept zero.
        p,o,b,x,y=nbst2_one(T,one(T);a=nextfloat(one(T)),y=prevfloat(one(T)),tol=nextfloat(zero(T)))
        @test !iszero(nbst_exact_residual(p,y,1))
        result=nbst2_candidate(p,o,b,x,y);@test !result

        # Positive configured tolerance; coarse cancellation remains ambiguous.
        # The compensated kernel refuses term2's unsafe tiny*.5 product.
        scale=T===Float32 ? one(T) : ldexp(one(T),30)
        A=SparseMatrixCSC{T,Int}(3,1,[1,4],[1,2,3],T[scale,nextfloat(zero(T)),-scale])
        p=LinearProblem(A,T[0];row_lower=zeros(T,3),row_upper=zeros(T,3))
        o=SolverOptions(T;verbose=false,primal_tolerance=T(1e-7),dual_tolerance=T(1e-7))
        b=NBST.Basis([1],vcat(NBST.BASIC,fill(NBST.AT_LOWER,3)));x=T[0];y=T[1,0.5,1]
        result=nbst2_candidate(p,o,b,x,y);@test !result

        # Row-activity BASIC cannot enter the structural-only helper.
        p,o,b,x,y=nbst2_one(T,one(T));b=NBST.Basis([2],[NBST.AT_LOWER,NBST.BASIC])
        result=nbst2_candidate(p,o,b,x,y);@test !result
    end
end

@testset "NBST2 repaired basics cannot bypass genuine later rejections" begin
    p,o,b,x=nbst2_saved();y=nbst_float.(NBST2_WITNESS["original_bits"]);n=length(x)
    A=hcat(p.A,spzeros(Float32,64,1))
    q=LinearProblem(A,vcat(p.objective,-1f0);row_lower=p.row_lower,row_upper=p.row_upper)
    qb=NBST.Basis(b.basic_indices,vcat(fill(NBST.BASIC,64),fill(NBST.AT_LOWER,65)));qx=vcat(x,0f0)
    @test !nbst2_exact_certificate(q,o,qb,qx,y)
    result=nbst2_candidate(q,o,qb,qx,y);@test !result

    fixed=LinearProblem(A,vcat(p.objective,-1f0);row_lower=p.row_lower,row_upper=p.row_upper,
        column_lower=zeros(Float32,65),column_upper=vcat(fill(nothing,64),0f0))
    @test nbst2_exact_certificate(fixed,o,qb,qx,y)
    @test nbst2_candidate(fixed,o,qb,qx,y) # Fixed nonbasic predicate remains legal.
    badx=copy(x);badx[1]=-1f0
    @test !nbst2_exact_certificate(p,o,b,badx,y)
    @test !NBST._original_primal_feasible(p,badx,o.primal_tolerance)
    @test !(NBST._original_primal_feasible(p,badx,o.primal_tolerance) && nbst2_candidate(p,o,b,badx,y))
    rowbad=LinearProblem(p.A,p.objective;row_lower=fill(2f0,64))
    @test !nbst2_exact_certificate(rowbad,o,b,x,y)
    @test !nbst2_candidate(rowbad,o,b,x,y)
end

@testset "NBST2 invocation-local proof lifetime and changed inputs" begin
    p,o,b,x=nbst2_saved();y=nbst_float.(NBST2_WITNESS["original_bits"])
    for repeat in 1:2
        result=nbst2_candidate(p,o,b,x,y);@test result

    end
    old=y[1];y[1]+=1f0
    result=nbst2_candidate(p,o,b,x,y);@test !result;y[1]=old
    old=p.objective[1];p.objective[1]+=1f0
    result=nbst2_candidate(p,o,b,x,y);@test !result;p.objective[1]=old
    old=p.A.nzval[1];p.A.nzval[1]+=1f0
    result=nbst2_candidate(p,o,b,x,y);@test !result;p.A.nzval[1]=old
    old=b.states[1];b.states[1]=NBST.AT_LOWER
    result=nbst2_candidate(p,o,b,x,y);@test !result;b.states[1]=old
    result=nbst2_candidate(p,o,b,x,y);@test result

    for args in ((p,o,b,x,Float32[]),(p,o,b,Float32[],y),
                 (p,o,NBST.Basis([1],[NBST.BASIC]),x,y))
        result=nbst2_candidate(args...);@test !result
    end
    old=p.objective[1];p.objective[1]=Float32(NaN)
    result=nbst2_candidate(p,o,b,x,y);@test !result;p.objective[1]=old
    old=y[1];y[1]=Float32(Inf)
    result=nbst2_candidate(p,o,b,x,y);@test !result;y[1]=old
end

@testset "NBST2 actual FTZ transitions never reuse a local mode decision" begin
    previous=get_zero_subnormals()
    try
        set_zero_subnormals(false)
        p,o,b,x=nbst2_saved();y=nbst_float.(NBST2_WITNESS["original_bits"])
        result=nbst2_candidate(p,o,b,x,y);@test result

        set_zero_subnormals(true);supported=get_zero_subnormals()
        println("NBST2_FTZ_ACTUAL_SUPPORTED ",supported)
        if supported
            result=nbst2_candidate(p,o,b,x,y);@test !result

            @test result==nbst2_reference(p,o,b,x,y)
        else
            @test_skip supported
        end
        set_zero_subnormals(false)
        result=nbst2_candidate(p,o,b,x,y);@test result

    finally
        set_zero_subnormals(previous)
    end
    @test get_zero_subnormals()==previous
end

@testset "NBST2 unsupported types reference route and private slack arrays" begin
    for T in (Float16,BigFloat,Rational{BigInt})
        p,o,b,x,y=nbst2_one(T,one(T))
        result=nbst2_candidate(p,o,b,x,y)
        @test result==nbst2_reference(p,o,b,x,y);@test result
        p.objective[1]=T(2)
        result=nbst2_candidate(p,o,b,x,y)
        @test result==nbst2_reference(p,o,b,x,y);@test !result
        lo,hi=NBST._original_reduced_cost_bounds(p,y)
        @test lo !== hi && lo !== y && hi !== y
        lo[2]=T(99);hi[2]=T(-99);@test y==T[1]
    end
    p,y=setprecision(BigFloat,512) do
        LinearProblem(spzeros(BigFloat,1,0),BigFloat[]),[BigFloat(1)+BigFloat(2)^(-300)]
    end
    setprecision(BigFloat,64) do
        lo,hi=NBST._original_reduced_cost_bounds(p,y)
        @test isequal(lo,y) && isequal(hi,y)
        @test precision(only(lo))==precision(only(hi))==512
        @test lo !== hi && lo !== y && hi !== y
    end
end

@testset "NBST2 full workspace read-only certificate ownership" begin
    p,o,b,x,y=nbst2_one(Float64,1.0)
    ws=NBST.initialize_from_basis(p,b,o)
    before=deepcopy((ws.primal,ws.costs,ws.reduced_costs,ws.scratch.rho,ws.lower,ws.upper,
        ws.basis.basic_indices,ws.basis.states,ws.iterations,ws.refactorizations))
    factor=ws.factorization;progress=ws.progress;basis=ws.basis
    @test nbst2_candidate(ws.problem,ws.options,ws.basis,x,y)
    @test isequal(before,(ws.primal,ws.costs,ws.reduced_costs,ws.scratch.rho,ws.lower,ws.upper,
        ws.basis.basic_indices,ws.basis.states,ws.iterations,ws.refactorizations))
    @test ws.factorization===factor && ws.progress===progress && ws.basis===basis
    saved=nbst2_snapshot(p,o,b,x,y)
    @test_throws BoundsError begin
        ws.basis.basic_indices[1]=3
        NBST._original_dual_witness(ws)
    end
    @test nbst2_unchanged(saved,p,o,b,x,y) # ws owns its basis; caller b remains unchanged.
end

@testset "NBST2 rounded precision consumer and stop exception identity" begin
    T=Float64;p,o,b,x,y=nbst2_one(T,one(T));ws=NBST.initialize_from_basis(p,b,o)
    hp=LinearProblem(sparse(BigFloat[1;;]),BigFloat[1];row_lower=BigFloat[0],row_upper=BigFloat[0])
    ho=SolverOptions(BigFloat;verbose=false);hb=NBST.Basis([1],[NBST.BASIC,NBST.AT_LOWER])
    working=NBST.initialize_from_basis(hp,hb,ho);budget=NBST.SimplexRunBudget(ws)
    run=NBST.DualRunResult{BigFloat}(NBST.OPTIMAL,BigFloat(0),BigFloat[0],0,0,"component",hb)
    converted=NBST._convert_precision_run(ws,working,run,budget,()->false)
    @test converted.status==NBST.OPTIMAL && converted.primal==T[0]
    p.objective[1]=2.0
    rejected=NBST._convert_precision_run(ws,working,run,budget,()->false)
    @test rejected.status==NBST.NUMERICAL_ERROR
    failure=ErrorException("NBST2 precision stop identity")
    caught=try NBST._convert_precision_run(ws,working,run,budget,()->throw(failure)) catch e;e end
    @test caught===failure
    stopped=NBST._convert_precision_run(ws,working,run,budget,()->true)
    @test stopped.status==NBST.TIME_LIMIT
end

@testset "NBST2 LP projection keeps original-model active-bound rejection" begin
    p=LinearProblem(sparse([1.0;;]),[1.0];column_lower=[1.0],row_lower=[1.0],row_upper=[2.0])
    o=SolverOptions(;verbose=false,presolve=false,scaling=:off)
    b=NBST.Basis([1],[NBST.BASIC,NBST.AT_LOWER]);ws=NBST.initialize_from_basis(p,b,o)
    r=NBST._lp_residuals(ws,[1.25,1.5],[1.0]);correction,map=NBST.build_correction_problem(ws,r,4,8)
    ab=NBST.Basis([3],[NBST.AT_LOWER,NBST.AT_LOWER,NBST.BASIC])
    auxiliary=NBST.initialize_from_basis(correction,ab,o);budget=NBST.SimplexRunBudget(ws)
    before=copy(ws.primal);indices=copy(ws.basis.basic_indices)
    probe=NBST._lp_project_certificate(ws,auxiliary,map,[1.0,1.0],[1.0],budget,NBST._guard_stop_callback(()->false))
    @test probe !== nothing
    if probe !== nothing
        @test probe.basis.basic_indices==[1] && probe.primal==[1.0,1.0]
        @test probe.scratch.lp_dual_witness==[1.0]
    end
    @test isnothing(NBST._lp_project_certificate(ws,auxiliary,map,[1.5,1.5],[1.0],budget,NBST._guard_stop_callback(()->false)))
    @test ws.primal==before && ws.basis.basic_indices==indices
    failure=SingularException(42)
    caught=try NBST._lp_project_certificate(ws,auxiliary,map,[1.0,1.0],[1.0],budget,()->throw(failure)) catch e;e end
    @test caught===failure
end

end # NativeBasicStationarityTests
