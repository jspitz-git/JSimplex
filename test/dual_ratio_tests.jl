using SparseArrays

function ratio_workspace(row::Vector{T}, costs; lower=zeros(T,length(row)),
                         upper=fill(nothing,length(row))) where {T}
    p = LinearProblem(sparse(reshape(row,1,:)), T.(costs);
                      column_lower=lower, column_upper=upper)
    return JSimplex.initialize_workspace(p, SolverOptions(T; verbose=false))
end

@testset "Dual ratio types, orientation and optional flips" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        policy = JSimplex.NumericalPolicy(T; stable_ratio=true)
        for orientation in (one(T),-one(T))
            w = ratio_workspace(T[1,2],T[1,2]; upper=T[1,1])
            q = @inferred JSimplex.propose_dual_step!(w,orientation*T[1,2,0],
                                                      orientation,T(5//2),policy)
            @test q.outcome == :pivot
            @test q.entering == 2
            @test q.flips == [1]
            @test q.dual_step == one(T)
        end
    end
    # A coefficient rejected by the safety threshold cannot support exhaustion.
    w = ratio_workspace([1.0,1e-10],[1.0,2e-10]; upper=[1.0,1e20])
    policy = JSimplex.NumericalPolicy(Float64; stable_ratio=true)
    @test JSimplex.propose_dual_step!(w,[1.0,1e-10,0.0],1.0,2.0,policy).outcome == :uncertain
    w = ratio_workspace([0.1],[1.0]; upper=[nextfloat(0.0)])
    @test JSimplex.propose_dual_step!(w,[0.1,0.0],1.0,1.0,policy).outcome == :uncertain
    # Equal breakpoints use the index to break equal-pivot ties.
    w = ratio_workspace([1.0,1.0],[1.0,1.0]; upper=[2.0,2.0])
    @test JSimplex.propose_dual_step!(w,[1.0,1.0,0.0],1.0,1.0,policy).entering == 1
end

@testset "Stable dual bound flipping proposals" begin
    policy = JSimplex.NumericalPolicy(Float64; stable_ratio=true)
    @test JSimplex.NumericalPolicy(Float64; simplex_strategy=:adaptive).stable_ratio
    w = ratio_workspace([1e-6,1.0], [1e-6,1.0+5e-8]; upper=[1e6,2.0])
    saved = (copy(w.costs),copy(w.reduced_costs),copy(w.primal),
             copy(w.basis.states),copy(w.basis.basic_indices))
    q = JSimplex.propose_dual_step!(w,[1e-6,1.0,0.0],1.0,0.5,policy)
    @test q.outcome == :pivot
    @test q.entering == 2
    @test isempty(q.flips)
    @test q.dual_step == 1.0+5e-8
    @test saved == (w.costs,w.reduced_costs,w.primal,w.basis.states,w.basis.basic_indices)

    for (row,costs,lower,upper,violation,entering,flips,outcome) in (
        ([1.0,2.0],[1.0,4.0],[0.0,0.0],[1.0,2.0],2.0,2,[1],:pivot),
        ([1.0,2.0],[1.0,4.0],[0.0,0.0],[0.0,2.0],2.0,2,Int[],:pivot),
        ([1.0],[0.0],[nothing],[nothing],2.0,1,Int[],:pivot),
        ([-1.0],[-1.0],[nothing],[0.0],2.0,1,Int[],:pivot),
        ([1.0],[-5e-8],[0.0],[2.0],0.5,1,Int[],:pivot),
        ([1.0],[1.0],[0.0],[1.0],2.0,-1,Int[],:exhausted),
        ([1e-10],[1.0],[0.0],[1e20],2.0,-1,Int[],:uncertain),
        ([1.0],[1.0],[-1e308],[1e308],1.0,-1,Int[],:uncertain),
        # An unbounded variable's earlier breakpoint limits later boxed pivots.
        ([1e-6,1.0],[1e-6,2.0],[0.0,0.0],[nothing,2.0],0.5,1,Int[],:pivot),
    )
        w = ratio_workspace(row,costs; lower,upper)
        # Exercise a tolerated negative breakpoint independently of initialization.
        w.reduced_costs[1:length(costs)] .= costs
        q = JSimplex.propose_dual_step!(w,[row;0.0],1.0,violation,policy)
        @test (q.entering,q.outcome) == (entering,outcome)
        @test q.flips == flips
    end
end

# Independent finite enumeration of all possible pivots and bound-flip subsets.
function enumerated_ratio_choices(a,c,u,v)
    valid = Set{Tuple{Int,Tuple}}()
    for j in eachindex(a), mask in 0:(2^length(a)-1)
        (mask >> (j-1)) & 1 == 0 || continue
        flips = [i for i in eachindex(a) if (mask >> (i-1)) & 1 == 1]
        step = c[j]/a[j]
        remaining = v-sum((a[i]*u[i] for i in flips); init=zero(v))
        0 <= remaining <= a[j]*u[j] || continue
        all(i == j || (i in flips ? c[i]-step*a[i] <= 0 :
                                    c[i]-step*a[i] >= 0) for i in eachindex(a)) || continue
        push!(valid,(j,Tuple(flips)))
    end
    return valid
end

@testset "Exact dual ratio enumeration" begin
    T = Rational{BigInt}
    policy = JSimplex.NumericalPolicy(T; stable_ratio=true)
    for a in (T[1,1,1],T[1,2,3]), c in (T[0,0,0],T[1,1,1],T[1,2,3]),
        u in (T[1,1,1],T[1,2,3]), v in T.((1//2,1,2,3,4,7,20))
        choices = enumerated_ratio_choices(a,c,u,v)
        w = ratio_workspace(a,c; upper=u)
        q = JSimplex.propose_dual_step!(w,[a;zero(T)],one(T),v,policy)
        @test q.outcome == (isempty(choices) ? :exhausted : :pivot)
        if q.outcome == :pivot
            @test (q.entering,Tuple(sort(q.flips))) in choices
            @test q.dual_step == c[q.entering]/a[q.entering]
        end
    end
end
