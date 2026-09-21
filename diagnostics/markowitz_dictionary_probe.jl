# Process-local comparison only. Requires frozen src under the path below.
# No workspace production sources or project dependencies are modified.
using SparseArrays, LinearAlgebra, Logging, TOML, Statistics, Test
BLAS.set_num_threads(1)
include("/tmp/jsimplex-markowitz-dictionary-frozen/src/JSimplex.jl")
using .JSimplex
const mode = ARGS[1]
@assert mode in ("dict_fresh", "dict_recycled", "ordered_fresh", "ordered_recycled")
const recycled = endswith(mode, "recycled")
const ordered = startswith(mode, "ordered")
if ordered
    OC = Base.require(Base.PkgId(Base.UUID("bac558e1-5e72-5ebc-8fee-abe8a469f55d"), "OrderedCollections"))
    @eval JSimplex const ProbeDict = $OC.OrderedDict
else
    @eval JSimplex const ProbeDict = Dict
end

scratch_source = raw"""
mutable struct DictionaryProbeScratch{T}
    rows::Vector{ProbeDict{Int,T}}
    columns::Vector{ProbeDict{Int,T}}
    active_rows::BitVector
    active_columns::BitVector
    singleton_rows::Vector{Int}
    singleton_columns::Vector{Int}
    doubleton_columns::BitSet
    affected_rows::Vector{Int}
    row_positions::Vector{Int}
    column_positions::Vector{Int}
end
const dictionary_probe_cache = Dict{DataType,Any}()
function dictionary_probe_scratch(::Type{T}, n) where T
    s = get!(dictionary_probe_cache, T) do
        DictionaryProbeScratch{T}(ProbeDict{Int,T}[], ProbeDict{Int,T}[], falses(0),
            falses(0), Int[], Int[], BitSet(), Int[], Int[], Int[])
    end::DictionaryProbeScratch{T}
    for dictionaries in (s.rows,s.columns)
        while length(dictionaries) < n
            push!(dictionaries, ProbeDict{Int,T}())
        end
        resize!(dictionaries, n)
        foreach(empty!, dictionaries)
    end
    for flags in (s.active_rows, s.active_columns)
        resize!(flags,n); fill!(flags,true)
    end
    empty!(s.singleton_rows); empty!(s.singleton_columns)
    empty!(s.doubleton_columns); empty!(s.affected_rows)
    for positions in (s.row_positions,s.column_positions)
        resize!(positions,n); fill!(positions,0)
    end
    return s
end
"""
Base.include_string(JSimplex, scratch_source, "dictionary-probe-scratch.jl")
source = read("/tmp/jsimplex-markowitz-after-csc.jl", String)
start = findfirst("function _markowitz_set_entry!", source).start
stop = findfirst("function _backend_forward_solve!", source).start
body = replace(source[start:prevind(source,stop)], "Dict{Int,T}" => "ProbeDict{Int,T}")
if recycled
    body = replace(body,
        "rows = [ProbeDict{Int,T}() for _ in 1:n]\n    columns = [ProbeDict{Int,T}() for _ in 1:n]" =>
        "scratch = dictionary_probe_scratch(T,n)\n    rows = scratch.rows\n    columns = scratch.columns",
        "active_rows = trues(n)" => "active_rows = scratch.active_rows",
        "active_columns = trues(n)" => "active_columns = scratch.active_columns",
        "singleton_rows = Int[row for row in 1:n if length(rows[row]) == 1]" =>
        "singleton_rows = scratch.singleton_rows\n    for row in 1:n\n        length(rows[row]) == 1 && push!(singleton_rows,row)\n    end",
        "singleton_columns = Int[column for column in 1:n if length(columns[column]) == 1]" =>
        "singleton_columns = scratch.singleton_columns\n    for column in 1:n\n        length(columns[column]) == 1 && push!(singleton_columns,column)\n    end",
        "doubleton_columns = BitSet(column for column in 1:n if length(columns[column]) == 2)" =>
        "doubleton_columns = scratch.doubleton_columns\n    for column in 1:n\n        length(columns[column]) == 2 && push!(doubleton_columns,column)\n    end",
        "affected_rows = Int[]" => "affected_rows = scratch.affected_rows",
        "row_positions = zeros(Int, n)" => "row_positions = scratch.row_positions",
        "column_positions = zeros(Int, n)" => "column_positions = scratch.column_positions")
end
Base.include_string(JSimplex, body, "dictionary-probe-$mode.jl")

function matrix_case(::Type{T}, n, kind) where T
    B = spdiagm(0=>fill(T(4),n))
    if kind == "band"
        B += spdiagm(-1=>fill(-one(T),n-1),1=>fill(-one(T),n-1))
    elseif kind == "fill" || kind == "history"
        offsets = kind == "fill" ? (1,5,13) : 1:max(3,n÷4)
        for i in 1:n, offset in offsets
            B[i,mod1(i+offset,n)] = -one(T)
        end
        if kind == "history"
            for i in 1:n; B[i,i] = T(n+1); end
        end
    elseif kind == "hybrid"
        first_dense = n-n÷4+1
        for i in first_dense:n, j in first_dense:n
            B[i,j] = i==j ? T(n) : one(T)
        end
    end
    B
end

function measured(f; samples=7)
    f(); f()
    times = Float64[]; bytes = Int[]; counts = Int[]; compiles = Float64[]
    for _ in 1:samples
        GC.gc()
        t = @timed f()
        push!(times,t.time); push!(bytes,t.bytes)
        push!(counts,Base.gc_alloc_count(t.gcstats)); push!(compiles,t.compile_time)
    end
    Dict{String,Any}("seconds_min"=>minimum(times),"seconds_median"=>median(times),
         "bytes"=>minimum(bytes),"allocations"=>minimum(counts),
         "compile_seconds"=>maximum(compiles),"samples"=>samples)
end
function metadata(f,B)
    backend=f.base; T=eltype(B); n=size(B,1)
    rhs=B*ones(T,n); rhs_t=transpose(B)*ones(T,n)
    x=JSimplex.forward_solve(f,rhs); xt=JSimplex.transpose_solve(f,rhs_t)
    @test x ≈ ones(T,n)
    @test xt ≈ ones(T,n)
    Dict("row_order"=>copy(backend.row_order),"column_order"=>copy(backend.column_order),
         "sparse_pivots"=>backend.sparse_pivots,"core_dimension"=>size(backend.core,1),
         "lower_nnz"=>sum(v->length(v.indices),backend.lower;init=0),
         "upper_nnz"=>sum(v->length(v.indices),backend.upper;init=0),
         "forward_error"=>Float64(maximum(abs,x.-one(T))),
         "transpose_error"=>Float64(maximum(abs,xt.-one(T))))
end
function capacity(::Type{T}) where T
    recycled || return 0
    s=JSimplex.dictionary_probe_cache[T]
    sum(d->length(d.slots),s.rows)+sum(d->length(d.slots),s.columns)
end

rows=Dict{String,Any}[]; histories=Dict{String,Any}[]; solves=Dict{String,Any}[]
@testset "Dictionary prototype numerical and ownership checks" begin
    for T in (Float64,Float32,BigFloat,Rational{BigInt})
        ns = T==Float64 ? (64,256) : T==Float32 ? (64,) : (16,)
        for n in ns, kind in ("diagonal","band","fill","hybrid")
            empty!(JSimplex.dictionary_probe_cache)
            B=matrix_case(T,n,kind)
            factor=JSimplex.PFIFactorization(B,Val(:markowitz))
            cold=metadata(factor,B)
            saved=JSimplex.copy_basis_factorization(factor)
            run=()->(JSimplex.refactorize!(factor,B); nothing)
            result=measured(run;samples=T==Float64 ? 7 : 3)
            warm=metadata(factor,B)
            slots=capacity(T)
            merge!(result,warm,Dict("value_type"=>string(T),"dimension"=>n,"pattern"=>kind,
                "cold_matches_warm"=>cold["row_order"]==warm["row_order"] && cold["column_order"]==warm["column_order"],
                "retained_hash_slots"=>slots))
            @test metadata(saved,B)==cold
            push!(rows,result)
            if T==Float64
                # Actual denser matrix history grows retained tables before returning to B.
                H=matrix_case(T,n,"history")
                JSimplex.refactorize!(factor,H)
                before_slots=capacity(T)
                JSimplex.refactorize!(factor,B)
                first_after=metadata(factor,B)
                history_result=measured(run;samples=7)
                after=metadata(factor,B)
                merge!(history_result,after,Dict("dimension"=>n,"pattern"=>kind,
                    "history_hash_slots"=>before_slots,"returned_hash_slots"=>capacity(T),
                    "first_return_matches_stable"=>first_after["row_order"]==after["row_order"] && first_after["column_order"]==after["column_order"],
                    "warm_matches_history"=>warm["row_order"]==after["row_order"] && warm["column_order"]==after["column_order"]))
                push!(histories,history_result)
            end
            println(mode," ",T," ",n," ",kind," ",result["bytes"]," B"); flush(stdout)
        end
    end
end
with_logger(NullLogger()) do
    for (name,path) in (("afiro","test/fixtures/solver/afiro.mps"),("adlittle","test/fixtures/solver/netlib/adlittle.mps"))
        problem=read_mps(path)
        for algorithm in (:dual,:primal)
            options=SolverOptions(;basis_refactorization=:markowitz,basis_update=:pfi,algorithm,
                presolve=false,scaling=:off,verbose=false,iteration_limit=10_000)
            # Each full solve starts with empty scratch cache. Reuse occurs only within it.
            run=()->(empty!(JSimplex.dictionary_probe_cache); solve(problem;options))
            result=measured(run;samples=5)
            sol=run()
            @test sol.status==OPTIMAL
            merge!(result,Dict("dataset"=>name,"algorithm"=>string(algorithm),
                "status"=>string(sol.status),"objective"=>sol.objective_value,
                "iterations"=>sol.statistics.iterations,"refactorizations"=>sol.statistics.refactorizations))
            push!(solves,result)
            println(mode," ",name," ",algorithm," ",sol.status);flush(stdout)
        end
    end
end
open(io->TOML.print(io,Dict("mode"=>mode,"julia_version"=>string(VERSION),
    "machine"=>Sys.MACHINE,"blas_threads"=>BLAS.get_num_threads(),"rows"=>rows,
    "histories"=>histories,"solves"=>solves);sorted=true),ARGS[2],"w")
