
module MarkowitzInitialRowCountTests
using Test, SparseArrays, LinearAlgebra
import JSimplex

# Observe length queries while using real Dict storage and the real constructor.
mutable struct RowLengthDictionary{T} <: AbstractDict{Int,T}
    data::Dict{Int,T}
    reads::Int
end
RowLengthDictionary{T}() where T = RowLengthDictionary{T}(Dict{Int,T}(),0)
Base.length(d::RowLengthDictionary) = (d.reads += 1; length(d.data))
Base.iterate(d::RowLengthDictionary,args...) = iterate(d.data,args...)
Base.getindex(d::RowLengthDictionary,i) = d.data[i]
Base.setindex!(d::RowLengthDictionary,v,i) = (d.data[i] = v)
Base.haskey(d::RowLengthDictionary,i) = haskey(d.data,i)
Base.keys(d::RowLengthDictionary) = keys(d.data)
Base.values(d::RowLengthDictionary) = values(d.data)
Base.delete!(d::RowLengthDictionary,i) = (delete!(d.data,i); d)
Base.empty!(d::RowLengthDictionary) = (empty!(d.data); d.reads = 0; d)

@testset "Markowitz initial counts reuse active row length queries" begin
    # A singular empty input stops before elimination adds further length reads.
    # Reintroducing the separate sum would read active rows twice and tails once.
    for n in (3,8), capacity in (n,64)
        workspace = JSimplex.MarkowitzWorkspace(Float64,RowLengthDictionary{Float64})
        JSimplex._reset_markowitz_workspace!(workspace,capacity)
        row_owners = copy(workspace.rows)
        column_owners = copy(workspace.columns)
        workspace.rows[end].data[capacity] = 7.0
        workspace.columns[end].data[capacity] = 7.0
        failure = try
            JSimplex._construct_markowitz(spzeros(n,n),workspace,RowLengthDictionary{Float64})
            nothing
        catch err
            err
        end
        @test failure isa SingularException && failure.info == 1
        @test [row.reads for row in workspace.rows] == vcat(ones(Int,n),zeros(Int,capacity-n))
        @test length(workspace.rows) == capacity && all(workspace.rows[i] === row_owners[i] for i in 1:capacity)
        @test length(workspace.columns) == capacity && all(workspace.columns[i] === column_owners[i] for i in 1:capacity)
        @test all(isempty(row.data) for row in workspace.rows)
        @test all(isempty(column.data) for column in workspace.columns)
    end
end
end # module MarkowitzInitialRowCountTests
