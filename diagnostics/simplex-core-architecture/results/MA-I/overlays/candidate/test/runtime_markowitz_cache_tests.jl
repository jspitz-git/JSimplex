# Count complete maximum scans while delegating dictionary order to real storage.
mutable struct RuntimeMaximumDict{T,D<:AbstractDict{Int,T}} <: AbstractDict{Int,T}
    data::D
    scans::Int
end
RuntimeMaximumDict(d::D) where {T,D<:AbstractDict{Int,T}} = RuntimeMaximumDict{T,D}(d,0)
Base.length(d::RuntimeMaximumDict) = length(d.data)
Base.iterate(d::RuntimeMaximumDict,args...) = iterate(d.data,args...)
Base.getindex(d::RuntimeMaximumDict,i) = d.data[i]
Base.keys(d::RuntimeMaximumDict) = keys(d.data)
Base.values(d::RuntimeMaximumDict) = (d.scans += 1; values(d.data))

function runtime_maximum_problem(::Type{T},D) where T
    rows = [D(1=>T(1)),D(1=>T(1)),D(1=>T(100),2=>T(1),3=>T(1)),
            D(1=>T(100),2=>T(1),3=>T(1))]
    columns = [D(1=>T(1),2=>T(1),3=>T(100),4=>T(100)),
               D(3=>T(1),4=>T(1)),D(3=>T(1),4=>T(1))]
    return RuntimeMaximumDict.(rows), RuntimeMaximumDict.(columns)
end

@testset "Markowitz caches raw maxima once per pivot search" begin
    for T in (Float32,Float64,BigFloat,Rational{Int64},Rational{BigInt}),
        D in (Dict{Int,T},JSimplex.OrderedCollections.OrderedDict{Int,T})
        rows,columns = runtime_maximum_problem(T,D)
        cache = (zeros(T,3),falses(3))
        search(args...) = JSimplex._markowitz_pivot(rows,columns,trues(4),trues(3),[1,2],Int[],BitSet([2,3]),args...)
        expected = search()
        @test [c.scans for c in columns] == [3,2,2]
        foreach(c->c.scans=0,columns)
        @test search(cache) == expected
        @test [c.scans for c in columns] == [1,1,1]
        # The rejected row singleton becomes admissible in the next search.
        for row in (3,4)
            rows[row].data[1] = columns[1].data[row] = T(2)
        end
        @test search(cache) == search() == (2,1)
        @test cache[1][1] == T(2)
    end
end

@testset "Markowitz maximum cache retains stored BigFloat precision" begin
    D = JSimplex.OrderedCollections.OrderedDict{Int,BigFloat}
    rows,columns = runtime_maximum_problem(BigFloat,D)
    stored = setprecision(BigFloat,512) do
        -BigFloat(10)-ldexp(BigFloat(1),-300)
    end
    rows[3].data[1] = columns[1].data[3] = stored
    rows[4].data[1] = columns[1].data[4] = BigFloat(2)
    cache = (zeros(BigFloat,3),falses(3))
    for bits in (24,128,512), mode in (RoundNearest,RoundUp,RoundDown,RoundToZero)
        setprecision(BigFloat,bits) do
            setrounding(BigFloat,mode) do
                search(args...) = JSimplex._markowitz_pivot(rows,columns,trues(4),trues(3),[1,2],Int[],BitSet([2,3]),args...)
                @test search(cache) == search()
                @test precision(cache[1][1]) == 512
                @test isequal(cache[1][1],JSimplex._markowitz_column_maximum(columns[1]))
            end
        end
    end
end

@testset "Markowitz maximum storage survives workspace shrink" begin
    ws = JSimplex.MarkowitzWorkspace(Float64,JSimplex.OrderedCollections.OrderedDict{Int,Float64})
    JSimplex._reset_markowitz_workspace!(ws,64)
    maxima,valid = ws.column_maxima,ws.column_maxima_valid
    fill!(maxima,42.0); fill!(valid,true)
    JSimplex._reset_markowitz_workspace!(ws,3)
    @test ws.column_maxima === maxima
    @test ws.column_maxima_valid === valid
    @test length(maxima) >= 64
    @test !any(valid)
end
