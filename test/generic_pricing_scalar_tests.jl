module GenericPricingScalarTests
using Test,JSimplex,SparseArrays,Logging
const MODES=(RoundNearest,RoundDown,RoundUp,RoundToZero,RoundFromZero)
same(a,b)=isequal(a,b)
same(a::BigFloat,b::BigFloat)=isequal(a,b)&&precision(a)==precision(b)&&signbit(a)==signbit(b)
same(a::Tuple,b::Tuple)=length(a)==length(b)&&all(same(x,y) for (x,y) in zip(a,b))
same(a::JSimplex.Bound,b::JSimplex.Bound)=a.bounded==b.bounded&&same(a.value,b.value)
reference_score(x::AbstractFloat)=JSimplex._primal_weighted_score(x,one(x isa BigFloat ? BigFloat : typeof(x)))
reference_score(x::Rational)=abs(big(x))
function outcome(f,x)
    try
        return (true,f(x))
    catch e
        return (false,(typeof(e),sprint(showerror,e)))
    end
end
function scalar_values(bits)
    setprecision(BigFloat,bits) do
        o=one(BigFloat);z=zero(BigFloat)
        v=BigFloat[z,-z,o,-o,prevfloat(o),nextfloat(o),BigFloat(3)/7,-BigFloat(3)/7,Inf,-Inf,NaN]
        for e in (-10000,-1,1,10000)
            x=ldexp(BigFloat(3)/4,e)
            append!(v,BigFloat[x,-x,prevfloat(x),nextfloat(x)])
        end
        append!(v,BigFloat[floatmin(BigFloat),-floatmin(BigFloat),floatmax(BigFloat),-floatmax(BigFloat)])
        v
    end
end
@testset "BigFloat Dantzig preserves ranking representation and scalar ownership" begin
    for stored in (64,128,256,512)
        values=scalar_values(stored)
        for bits in (64,128,256),mode in MODES
            setprecision(BigFloat,bits) do
                setrounding(BigFloat,mode) do
                    for x in values
                        before=deepcopy(x);owner=x
                        @test same(outcome(JSimplex._primal_dantzig_score,x),outcome(reference_score,x))
                        @test x===owner&&same(x,before)
                        @test precision(BigFloat)==bits&&rounding(BigFloat)==mode
                    end
                end
            end
        end
    end
    for T in (Float16,Float32,Float64,Rational{Int64},Rational{BigInt}),x in T[0,1,-2]
        @test same(JSimplex._primal_dantzig_score(x),reference_score(x))
    end
end
function fixture(::Type{T},n=5;pricing=:auto,algorithm=:dual) where T
    p=LinearProblem(spzeros(T,1,n-1),zeros(T,n-1);column_lower=zeros(T,n-1))
    policy=JSimplex.NumericalPolicy(T;refactor_timing=false)
    ws=JSimplex._initialize_workspace_state(p,SolverOptions(T;pricing,algorithm,verbose=false,log_level=Logging.Debug);
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
    state=JSimplex.PricingState(T);state.algorithm=algorithm;state.active=state.return_mode=:steepest_edge
    ws.scratch.pricing=state
    for i in eachindex(ws.pricing_weights);ws.pricing_weights[i]=T(i%7+1);end
    ws
end
arrays(ws)=(ws.primal,ws.costs,ws.reduced_costs,ws.pricing_weights,ws.lower,ws.upper,
    ws.basis.basic_indices,ws.basis.states,ws.devex_reference,ws.problem.A.colptr,ws.problem.A.rowval,ws.problem.A.nzval)
function snapshot(ws)
    a=arrays(ws);(a,deepcopy(a),map(copy,a))
end
function intact(ws,s)
    a,b,o=s;c=arrays(ws)
    all(c[k]===a[k]&&axes(c[k])==axes(b[k])&&all(same(c[k][i],b[k][i])&&c[k][i]===o[k][i] for i in eachindex(c[k])) for k in eachindex(c))
end
@testset "Dantzig selection preserves ties, exclusions and direction" begin
    for bits in (64,128,256),mode in MODES
        setprecision(BigFloat,bits) do
            setrounding(BigFloat,mode) do
                ws=fixture(BigFloat;pricing=:dantzig,algorithm=:primal)
                ws.scratch.pricing=nothing
                ws.reduced_costs[1:4]=BigFloat[-1,-8,-8,-2]
                s=snapshot(ws)
                @test JSimplex._primal_entering(ws,ws.options.dual_tolerance)==(2,one(BigFloat))
                @test intact(ws,s)
                push!(ws.scratch.rejected_entering,2)
                @test JSimplex._primal_entering(ws,ws.options.dual_tolerance)==(3,one(BigFloat))
                empty!(ws.scratch.rejected_entering)
                ws.upper[2]=JSimplex.Bound(BigFloat(1));ws.basis.states[2]=JSimplex.AT_UPPER;ws.reduced_costs[2]=BigFloat(8)
                @test JSimplex._primal_entering(ws,ws.options.dual_tolerance)==(2,-one(BigFloat))
                # Three infeasible slack activities, first tie wins under the scaled auto path.
                p=LinearProblem(spzeros(BigFloat,3,1),BigFloat[0];row_lower=zeros(BigFloat,3),row_upper=zeros(BigFloat,3))
                policy=JSimplex.NumericalPolicy(BigFloat;refactor_timing=false)
                dual=JSimplex._initialize_workspace_state(p,SolverOptions(BigFloat;pricing=:auto,verbose=false);
                    progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
                state=JSimplex.PricingState(BigFloat);state.algorithm=:dual;state.active=state.return_mode=:dantzig;dual.scratch.pricing=state
                dual.primal[2:4]=BigFloat[-1,-8,-8]
                @test JSimplex.dual_edge_selection(dual)==2
                push!(dual.scratch.rejected_rows,2)
                @test JSimplex.dual_edge_selection(dual)==3
                @test precision(BigFloat)==bits&&rounding(BigFloat)==mode
            end
        end
    end
end
function bad_values(::Type{T}) where T
    values=T[zero(T),-one(T)]
    if T<:AbstractFloat
        append!(values,T[-zero(T),Inf,-Inf,NaN])
    else
        append!(values,T[T(1,0),T(-1,0)])
    end
    values
end
@testset "Weight consumers retain invalid-value recovery and callback checks" begin
    for T in (Float32,Float64,BigFloat,Rational{Int64},Rational{BigInt})
        for v in bad_values(T),position in (1,3,5)
            ws=fixture(T);ws.pricing_weights[position]=v
            @test JSimplex._prepare_auto_pricing!(ws,:dual)
            @test ws.scratch.pricing.active==:devex
            @test all(isone,ws.pricing_weights)
            @test ws.scratch.pricing.rejected_weights==1
            ws=fixture(T);ws.pricing_weights[position]=v
            @test JSimplex._recover_invalid_dse_weights!(ws,()->false)
            @test ws.scratch.pricing.active==:devex
            @test all(isone,ws.pricing_weights)
            @test ws.scratch.pricing.rejected_weights==1
        end
        for scope in (:prepare,:recover)
            ws=fixture(T);s=snapshot(ws)
            @test (scope===:prepare ? JSimplex._prepare_auto_pricing!(ws,:dual) : !JSimplex._recover_invalid_dse_weights!(ws,()->false))
            @test intact(ws,s)
        end
        for when in (1,2)
            ws=fixture(T);calls=Ref(0)
            callback=()->begin calls[]+=1;calls[]==when&&(ws.pricing_weights[end]=zero(T));false end
            @test JSimplex._prepare_auto_pricing!(ws,:dual;stop=callback)
            @test calls[]==2
            @test ws.scratch.pricing.rejected_weights==(when==1 ? 1 : 0)
            @test JSimplex._prepare_auto_pricing!(ws,:dual)
            @test ws.scratch.pricing.rejected_weights==1
            @test all(isone,ws.pricing_weights)
        end
        ws=fixture(T)
        @test !JSimplex._prepare_auto_pricing!(ws,:dual;stop=()->true)
        @test_throws ErrorException JSimplex._prepare_auto_pricing!(ws,:dual;stop=()->error("weight-stop sentinel"))
        @test ws.scratch.pricing.rejected_weights==0
        # Explicit exact steepest-edge mode retains its historical recovery bypass.
        ws=fixture(T;pricing=:steepest_edge);ws.pricing_weights[end]=zero(T)
        @test JSimplex._recover_invalid_dse_weights!(ws,()->false)==(T<:AbstractFloat)
    end
    stored=setprecision(BigFloat,512) do
        BigFloat[BigFloat(2)^(-10000),BigFloat(3),-zero(BigFloat),Inf,NaN]
    end
    for bits in (64,128,256),mode in MODES
        setprecision(BigFloat,bits) do
            setrounding(BigFloat,mode) do
                for v in stored,scope in (:prepare,:recover)
                    ws=fixture(BigFloat);ws.pricing_weights[end]=v;before=deepcopy(v);owner=v
                    invalid=!isfinite(v)||iszero(v)||signbit(v)
                    @test (scope===:prepare ? JSimplex._prepare_auto_pricing!(ws,:dual) : JSimplex._recover_invalid_dse_weights!(ws,()->false))==(scope===:prepare||invalid)
                    @test ws.scratch.pricing.rejected_weights==Int(invalid)
                    @test same(v,before)&&v===owner
                    @test precision(BigFloat)==bits&&rounding(BigFloat)==mode
                end
            end
        end
    end
end
@noinline function score_batch(method::Val{M},values::Vector{BigFloat},sink::Base.RefValue{Int}) where M
    result=0
    for x in values
        e,m=M===:reference ? reference_score(x) : JSimplex._primal_dantzig_score(x)
        result=xor(result,e)+Int(isfinite(m))
    end
    sink[]=result
    nothing
end
function score_bytes(method::M,values::V,sink::S) where {M,V,S}
    @allocated score_batch(method,values,sink)
end
never_stop()=false
@noinline function weight_batch(scope::Val{S},ws::W) where {S,W}
    result=false
    for _ in 1:4
        result ⊻=S===:prepare ? JSimplex._prepare_auto_pricing!(ws,:dual) : JSimplex._recover_invalid_dse_weights!(ws,never_stop)
    end
    result
end
function weight_bytes(scope::S,ws::W) where {S,W}
    @allocated weight_batch(scope,ws)
end
@testset "Pricing scalar paths remove measured allocation work" begin
    setprecision(BigFloat,128) do
        setrounding(BigFloat,RoundNearest) do
            values=BigFloat[BigFloat(i)/8 for i in 1:64];sink=Ref(0)
            for _ in 1:3,m in (:reference,:production)
                score_batch(Val(m),values,sink);score_bytes(Val(m),values,sink)
            end
            baseline=score_bytes(Val(:reference),values,sink)
            actual=score_bytes(Val(:production),values,sink)
            @test baseline>0
            @test 2actual<=baseline
            for T in (BigFloat,Rational{BigInt}),scope in (:prepare,:recover)
                ws=fixture(T,65)
                for _ in 1:3
                    weight_batch(Val(scope),ws);weight_bytes(Val(scope),ws)
                end
                actual=weight_bytes(Val(scope),ws)
                @test actual==0
            end
        end
    end
end
end
