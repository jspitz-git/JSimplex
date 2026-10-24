module PositiveWeightValidationTests
using Test,JSimplex,SparseArrays
reference(values,flag::Val)=invoke(JSimplex._finite_values,Tuple{Any,typeof(flag)},values,flag)
function reference_workspace(ws)
    reference(ws.primal,Val(false)) && reference(ws.reduced_costs,Val(false)) &&
    reference(ws.costs,Val(false)) &&
    (JSimplex._weight_pricing(ws,:dual)==:dantzig || reference(ws.pricing_weights,Val(true)))
end
same(a,b)=isequal(a,b)
same(a::BigFloat,b::BigFloat)=isequal(a,b)&&precision(a)==precision(b)
arrays(x::AbstractVector)=(x,)
arrays(ws::JSimplex.SimplexWorkspace)=(ws.primal,ws.reduced_costs,ws.costs,ws.pricing_weights)
function snapshot(x)
    a=arrays(x);(a,deepcopy(a),map(copy,a))
end
function unchanged(x,s)
    a,b,o=s;c=arrays(x)
    all(c[k]===a[k] && length(c[k])==length(b[k]) &&
        all(same(c[k][i],b[k][i])&&c[k][i]===o[k][i] for i in eachindex(c[k])) for k in eachindex(c))
end
function values_to_check(::Type{T}) where T
    result=T[T(3),zero(T),-one(T)]
    if T<:AbstractFloat
        append!(result,T[-zero(T),Inf,-Inf,NaN])
        T===BigFloat && append!(result,BigFloat[BigFloat(2)^(-10000),-BigFloat(2)^(-10000)])
    elseif T<:Rational
        append!(result,T[T(1,0),T(-1,0)])
        T===Rational{BigInt} && push!(result,BigInt(1)//(BigInt(1)<<1024))
    end
    result
end
function fixture(::Type{T},n=17) where T
    p=LinearProblem(spzeros(T,1,n-1),ones(T,n-1))
    policy=JSimplex.NumericalPolicy(T;refactor_timing=false)
    JSimplex._initialize_workspace_state(p,SolverOptions(T;verbose=false);
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
end

@testset "Finite positive values preserve generic and hardware behavior" begin
    for T in (Float16,Float32,Float64,BigFloat,Rational{Int64},Rational{BigInt}),n in (0,1,17),positive in (false,true)
        x=[T(2) for _ in 1:n]
        @test JSimplex._finite_values(x,Val(positive))===reference(x,Val(positive))===true
        for i in unique([1,max(1,n÷2),n])
            n==0 && continue
            for v in values_to_check(T)
                old=x[i];x[i]=v;s=snapshot(x)
                expected=isfinite(v)&&(!positive||v>0)
                @test JSimplex._finite_values(x,Val(positive))===expected
                @test reference(x,Val(positive))===expected
                @test unchanged(x,s)
                x[i]=old
            end
        end
        # Views retain their original generic method and are only read.
        view_x=@view x[:];s=snapshot(view_x)
        @test JSimplex._finite_values(view_x,Val(positive))===reference(view_x,Val(positive))
        @test unchanged(view_x,s)
    end
end

@testset "Positive validation preserves stored precision and rounding" begin
    x=setprecision(BigFloat,192) do
        BigFloat[BigFloat(2)^(-10000),-zero(BigFloat),BigFloat(3),BigFloat(Inf),BigFloat(NaN)]
    end
    for bits in (64,256),mode in (RoundNearest,RoundDown,RoundUp)
        setprecision(BigFloat,bits) do
            setrounding(BigFloat,mode) do
                for value in x,positive in (false,true)
                    a=[value];s=snapshot(a)
                    @test JSimplex._finite_values(a,Val(positive))===reference(a,Val(positive))
                    @test unchanged(a,s)
                    @test precision(BigFloat)==bits&&rounding(BigFloat)==mode
                end
            end
        end
    end
end

@testset "Full workspace validation retains every array and live pricing mode" begin
    for T in (BigFloat,Rational{BigInt})
        ws=fixture(T)
        for pricing in (:steepest_edge,:devex,:dantzig,:auto)
            ws.options=SolverOptions(T;pricing,verbose=false)
            for field in (:primal,:reduced_costs,:costs,:pricing_weights),i in (1,17),value in values_to_check(T)
                a=getfield(ws,field);old=a[i];a[i]=value;s=snapshot(ws)
                expected=field===:pricing_weights ? (pricing===:dantzig || (isfinite(value)&&value>0)) : isfinite(value)
                @test JSimplex._finite_workspace(ws)===reference_workspace(ws)===expected
                @test unchanged(ws,s)
                a[i]=old
            end
        end
        ws.options=SolverOptions(T;pricing=:auto,verbose=false)
        ws.pricing_weights[end]=zero(T)
        @test !JSimplex._finite_workspace(ws)
        ws.dual_pricing_fallback=true
        @test !JSimplex._finite_workspace(ws) # Auto chooses its rule before this fallback.
        ws.dual_pricing_fallback=false
        state=JSimplex.PricingState(T);ws.scratch.pricing=state;state.algorithm=:dual
        state.active=:dantzig
        @test JSimplex._finite_workspace(ws)
        state.temporary=true;state.return_mode=:steepest_edge
        @test !JSimplex._finite_workspace(ws)
        state.return_mode=:dantzig
        @test JSimplex._finite_workspace(ws)
        state.temporary=false;state.active=:steepest_edge
        ws.pricing_weights[end]=one(T)
        @test JSimplex._finite_workspace(ws)
        # Subsequent calls must see mutations through aliases, without cached validity.
        shared=copy(ws.pricing_weights)
        ws.primal=ws.reduced_costs=ws.costs=ws.pricing_weights=shared
        @test JSimplex._finite_workspace(ws)
        shared[end]=zero(T)
        @test !JSimplex._finite_workspace(ws)
        ws.options=SolverOptions(T;pricing=:dantzig,verbose=false);ws.scratch.pricing=nothing
        @test JSimplex._finite_workspace(ws)
        shared[end]=T(2)
        @test JSimplex._finite_workspace(ws)
    end
end

@noinline check(::Val{:normal},::Val{:vector},x)=JSimplex._finite_values(x,Val(true))
@noinline check(::Val{:reference},::Val{:vector},x)=reference(x,Val(true))
@noinline check(::Val{:normal},::Val{:workspace},x)=JSimplex._finite_workspace(x)
@noinline check(::Val{:reference},::Val{:workspace},x)=reference_workspace(x)
@noinline function batch(method::M,scope::S,x::X) where {M,S,X}
    result=0
    for _ in 1:4
        result+=Int(check(method,scope,x))
    end
    result
end
function allocated(method::M,scope::S,x::X) where {M,S,X}
    @allocated batch(method,scope,x)
end
@testset "Positive validation removes temporary numerical zero allocations" begin
    for T in (BigFloat,Rational{BigInt}),scope in (:vector,:workspace)
        x=scope===:vector ? [T(i%17+1) for i in 1:64] : fixture(T,65)
        for _ in 1:2,method in (:normal,:reference)
            @test batch(Val(method),Val(scope),x)==4
            allocated(Val(method),Val(scope),x)
        end
        actual=allocated(Val(:normal),Val(scope),x)
        baseline=allocated(Val(:reference),Val(scope),x)
        @test baseline>0
        @test actual==0
    end
end
end
