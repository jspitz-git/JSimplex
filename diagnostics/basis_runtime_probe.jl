# Compare complete snapshots while isolating basis replacement / pivot-search work.
# Usage: julia --project=dev diagnostics/basis_runtime_probe.jl BEFORE_SRC OUT [AFTER_SRC]
using SparseArrays, LinearAlgebra, Logging, Statistics, SHA, TOML, Test
# Share the snapshot loader; the main audit is deliberately not executed here.
include_string(Main, first(split(read(joinpath(@__DIR__, "runtime_probe.jl"), String),
    "const before_scope,"; limit=2)), "runtime_snapshot_loader.jl")
const old_scope, old_hashes = load_snapshot(:BasisBefore, abspath(ARGS[1]))
const Old = getfield(old_scope, :JSimplex)
const new_scope, new_hashes = load_snapshot(:BasisAfter, abspath(length(ARGS) >= 3 ? ARGS[3] : "src"))
const New = getfield(new_scope, :JSimplex)
const rows = Dict{String,Any}[]

function setup_upper(M, method, ::Type{T}, n, pattern) where T
    ctor = getfield(M, method)
    factor = ctor(spdiagm(0 => ones(T, n)))
    for j in 1:n
        entries = zeros(T, n)
        entries[j] = T(2)
        if pattern == "band"
            j > 1 && (entries[j-1] = T(1//4))
            j > 7 && (entries[j-7] = T(-1//8))
        elseif pattern == "dense"
            for i in 1:j-1
                entries[i] = T(isodd(i+j) ? 1//8 : -1//8)
            end
        end
        factor.upper[j] = M._packed_column(entries)
    end
    return factor
end

function factor_signature(M, f)
    T = eltype(f.work)
    rhs = T.(1:length(f.work))
    records = [Tuple(getfield(u, name) for name in fieldnames(typeof(u))) for u in f.updates]
    # BG step structs belong to different modules: normalize their scalar fields.
    records = [hasproperty(u, :steps) ?
        ([(s.row, s.last, s.swapped, s.multiplier) for s in u.steps],) : r
        for (u,r) in zip(f.updates,records)]
    return (copy(f.column_order), copy(f.positions),
        [(copy(c.indices),copy(c.values)) for c in f.upper], records,
        M.forward_solve(f,rhs), M.transpose_solve(f,rhs))
end

function replace_call(f, column, pivot, operation)
    operation(f, column, pivot)
    return nothing
end

function measure_replace(method,n,pattern; samples=15)
    old_op, new_op = Old.replace_column!, New.replace_column!
    column = fill(1.0/8,n); column[1] = 2.0
    old_setup = () -> setup_upper(Old,method,Float64,n,pattern)
    new_setup = () -> setup_upper(New,method,Float64,n,pattern)
    for _ in 1:3
        replace_call(old_setup(),column,1,old_op)
        replace_call(new_setup(),column,1,new_op)
    end
    old_times,new_times = Float64[],Float64[]
    old_bytes,new_bytes = Int[],Int[]
    for i in 1:samples
        old,new = old_setup(),new_setup()
        if isodd(i)
            a = @timed replace_call(old,column,1,old_op)
            b = @timed replace_call(new,column,1,new_op)
        else
            b = @timed replace_call(new,column,1,new_op)
            a = @timed replace_call(old,column,1,old_op)
        end
        @test isequal(factor_signature(Old,old),factor_signature(New,new))
        @test a.compile_time == b.compile_time == 0
        push!(old_times,a.time);push!(new_times,b.time)
        push!(old_bytes,a.bytes);push!(new_bytes,b.bytes)
    end
    result=Dict("case"=>"$method/$n/$pattern", "before_seconds"=>old_times,
        "after_seconds"=>new_times,"speedup"=>median(old_times./new_times),
        "before_bytes"=>minimum(old_bytes),"after_bytes"=>minimum(new_bytes))
    push!(rows,result)
    println(result["case"]," speedup=",round(result["speedup"],digits=3));flush(stdout)
end

with_logger(NullLogger()) do
    @testset "Exact packed factors and update histories" begin
        for T in (Float32,Float64,BigFloat,Rational{BigInt}), method in
            (:ForrestTomlinFactorization,:SuhlSuhlFactorization,:BartelsGolubFactorization),
            pattern in ("identity","band","dense"), reach in (24,32)
            old,new = setup_upper(Old,method,T,32,pattern),setup_upper(New,method,T,32,pattern)
            for pivot in (1,8,3,32,5,2)
                column=zeros(T,32);column[1:reach].=T(1//8);column[pivot]=T(2)
                Old.replace_column!(old,column,pivot)
                New.replace_column!(new,column,pivot)
                @test isequal(factor_signature(Old,old),factor_signature(New,new))
            end
        end
    end
    @testset "Paired replacement timings and exact factors" begin
        for method in (:ForrestTomlinFactorization,:SuhlSuhlFactorization,:BartelsGolubFactorization),
            n in (32,128,512), pattern in ("identity","band","dense")
            measure_replace(method,n,pattern)
        end
    end
end
open(ARGS[2],"w") do io
    TOML.print(io,Dict("julia"=>string(VERSION),"machine"=>Sys.MACHINE,
        "before_hashes"=>old_hashes,"after_hashes"=>new_hashes,"measurements"=>rows);sorted=true)
end
