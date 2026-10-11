using JSimplex,LinearAlgebra,SparseArrays,Random,TOML
module Reference
    include(joinpath(ARGS[2],"JSimplex.jl"))
end
module BaselineBench
    const JS=Main.Reference.JSimplex
    include(joinpath(@__DIR__,"hh_scratch_cost_common.jl"))
end
module CandidateBench
    const JS=Main.JSimplex
    include(joinpath(@__DIR__,"hh_scratch_cost_common.jl"))
end
function main(output)
    @assert Threads.nthreads()==BLAS.get_num_threads()==1
    rng=MersenneTwister(74021)
    sparse_case=spdiagm(-1=>rand(rng,511),0=>fill(4.0,512),1=>rand(rng,511))
    dense_case=Matrix{Float64}(I,96,96)*96+randn(rng,96,96)
    samples=Dict[]
    data=Dict("scope"=>"HH same-size refactors and private scratch dimension transitions; no whole-solver timing claim",
              "pairs"=>3,"refactors_per_same_size_sample"=>8,"samples"=>samples)
    save()=open(io->TOML.print(io,data),output,"w")
    benches=(BaselineBench,CandidateBench)
    for backend in (:native,:markowitz), (kind,B) in ((:sparse,sparse_case),(:dense,dense_case))
        matrices=[scale*B for scale in (2.,3.,4.,2.,3.,4.,2.,3.)]
        for bench in benches;bench.same_size_sample(matrices,backend);end
        for pair in 1:3
            rows=Dict[]
            for side in (isodd(pair) ? (1,2) : (2,1))
                row=benches[side].same_size_sample(matrices,backend)
                @assert row["compile_seconds"]==0
                row["mode"]="same_size";row["backend"]=string(backend);row["model"]=string(kind)
                row["side"]=side==1 ? "baseline" : "candidate";row["pair"]=pair
                push!(rows,row);push!(samples,row)
            end
            for key in ("factor_hash","forward_hash","transpose_hash","scratch_capacity_elements")
                @assert rows[1][key]==rows[2][key] key
            end
            save()
        end
    end
    for backend in (:native,:markowitz)
        large=backend==:native ? 65536 : 2048
        matrices=[spdiagm(0=>fill(2.0,n)) for n in (large,4,0,7)]
        for bench in benches;bench.shape_sample(matrices,backend);end
        for pair in 1:3
            paired=Any[]
            for side in (isodd(pair) ? (1,2) : (2,1))
                rows=benches[side].shape_sample(matrices,backend)
                @assert all(r["compile_seconds"]==0 for r in rows)
                for row in rows
                    row["mode"]="changed_dimension";row["backend"]=string(backend)
                    row["model"]="diagonal";row["side"]=side==1 ? "baseline" : "candidate";row["pair"]=pair
                    side==2 && @assert row["scratch_capacity_elements"]==4*row["dimension"]
                    push!(samples,row)
                end
                push!(paired,rows)
            end
            for key in ("factor_hash","forward_hash","transpose_hash")
                @assert [r[key] for r in paired[1]]==[r[key] for r in paired[2]] key
            end
            save()
        end
    end
    println("HH cost/retention comparison passed: ",length(samples)," records");flush(stdout)
end
Base.invokelatest(main,ARGS[1])
