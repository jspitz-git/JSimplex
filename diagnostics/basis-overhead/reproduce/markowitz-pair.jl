using JSimplex, SparseArrays, LinearAlgebra, Statistics, TOML, Test, SHA
module Reference
include(joinpath(ENV["JSIMPLEX_BASELINE_SOURCE"], "JSimplex.jl"))
end
const Old = Reference.JSimplex

function signature(f)
    return (f.row_order, f.column_order, f.diagonal,
        [(v.indices,v.values) for v in f.lower],
        [(v.indices,v.values) for v in f.upper], f.core.factors, f.core.ipiv)
end

function measure(B, label)
    a, b = Base.invokelatest(Old.MarkowitzBackend,B), Base.invokelatest(JSimplex.MarkowitzBackend,B)
    @test isequal(signature(a), signature(b))
    rhs = ones(eltype(B), size(B,1))
    for (M,f) in ((Old,a),(JSimplex,b))
        result = similar(rhs)
        Base.invokelatest(M._backend_forward_solve!,result,f,rhs)
        @test B * result ≈ rhs
        Base.invokelatest(M._backend_transpose_solve!,result,f,rhs)
        @test B' * result ≈ rhs
    end
    # Alternate timed construction order after warming both implementations.
    times = zeros(7,2)
    for sample in 1:9
        for side in (isodd(sample) ? (1,2) : (2,1))
            M = side == 1 ? Old : JSimplex
            elapsed = @timed Base.invokelatest(M.MarkowitzBackend,B)
            sample <= 2 && continue
            @test elapsed.compile_time == 0
            @test isequal(signature(a),signature(elapsed.value))
            times[sample-2,side] = elapsed.time
        end
    end
    result = Dict("case"=>label,"before_seconds"=>times[:,1],
        "after_seconds"=>times[:,2],"speedup"=>median(times[:,1])/median(times[:,2]))
    println(label," speedup=",result["speedup"]); flush(stdout)
    return result
end

function main(output)
    isfile(output) && error("Use a fresh output path")
    n = parse(Int,get(ENV,"JSIMPLEX_PROBE_DIMENSION","64"))
    32 <= n <= 1024 && n % 32 == 0 || error("Dimension must be a multiple of 32 between 32 and 1024")
    results = Dict{String,Any}[]
    @testset "Persistent Markowitz maxima and exact factor equivalence" begin
        for pattern in (:band,:fill,:blocks)
            B = spdiagm(0=>fill(8.0,n))
            for i in 1:n, offset in (pattern == :band ? (1,) : (1,5,13))
                j = pattern == :blocks ? (i-1)÷32*32 + mod1(i+offset,32) : mod1(i+offset,n)
                B[i,j] = -1.0
                B[j,i] = -1.0
            end
            push!(results,measure(B,"$pattern/$n"))
            save_results(output,results)
        end
        for T in (get(ENV,"JSIMPLEX_PROBE_GENERIC","0") == "1" ? (Float32,BigFloat,Rational{BigInt}) : ())
            B = spdiagm(-1=>fill(-one(T),31),0=>fill(T(4),32),1=>fill(-one(T),31))
            push!(results,measure(B,"band/$T/32"))
            save_results(output,results)
        end
    end
end
function save_results(output,results)
    open(output,"w") do io
        TOML.print(io,Dict("julia"=>string(VERSION),"machine"=>Sys.MACHINE,
            "julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),
            "baseline_source_sha256"=>bytes2hex(sha256(read(joinpath(ENV["JSIMPLEX_BASELINE_SOURCE"],"markowitz_factorization.jl")))),
            "current_source_sha256"=>bytes2hex(sha256(read(joinpath(dirname(pathof(JSimplex)),"markowitz_factorization.jl")))),
            "measurements"=>results))
    end
end
Base.invokelatest(main,ARGS[1])
