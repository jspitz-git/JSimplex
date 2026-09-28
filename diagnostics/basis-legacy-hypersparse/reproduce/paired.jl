using JSimplex, Serialization, SparseArrays, LinearAlgebra, TOML, SHA
Base.include(JSimplex,joinpath(@__DIR__,"hybrid.jl"))
function step!(f,direction,other,backward,column,rhs,unit,row)
    ft=@elapsed JSimplex.forward_solve!(direction,f,column)
    ft+=@elapsed JSimplex._ordinary_forward_solve!(other,f,rhs)
    ut=@elapsed JSimplex.replace_column!(f,direction,row)
    bt=@elapsed JSimplex.transpose_solve!(backward,f,unit)
    return (ft,ut,bt)
end
function warmup(Factor)
    B=spdiagm(0=>ones(32));rhs=ones(32);unit=zeros(32);unit[1]=1
    for f in (Factor(B),JSimplex._trial_hybrid_factor(Factor,B),JSimplex._trial_hybrid_factor(Factor,B;forward=true),JSimplex.PFIFactorization(B))
        step!(f,zeros(32),zeros(32),zeros(32),unit,rhs,unit,1)
        f.base isa JSimplex.TrialHybridBackend && @assert f.base.sparse_calls>0
    end
end
function paired(Factor,A,data,repeat)
    warmup(Factor)
    n=size(A,1);basis=copy(data.basis);B=A[:,basis]
    factors=(Factor(B),JSimplex._trial_hybrid_factor(Factor,B),
             JSimplex._trial_hybrid_factor(Factor,B;forward=true),JSimplex.PFIFactorization(B))
    directions=ntuple(_->zeros(n),4);others=ntuple(_->zeros(n),4);backs=ntuple(_->zeros(n),4)
    rhs=ones(n);unit=zeros(n);times=zeros(3,4);records=Dict{String,Any}[]
    for (k,(row,entering)) in enumerate(data.steps)
        column=Vector(A[:,entering]);fill!(unit,0);unit[row]=1
        for side in (isodd(k+repeat) ? (1,2,3,4) : (4,3,2,1))
            elapsed=step!(factors[side],directions[side],others[side],backs[side],column,rhs,unit,row)
            for stage in 1:3;times[stage,side]+=elapsed[stage];end
        end
        @assert isequal(directions[1],directions[2]) && isequal(others[1],others[2])
        basis[row]=entering
        if k in (20,80,160,320)
            B=A[:,basis]
            for side in 1:4
                f=factors[side];x=JSimplex.forward_solve(f,rhs)
                fr=norm(B*x-rhs,Inf)/(opnorm(B,Inf)*norm(x,Inf)+1)
                br=norm(B'*backs[side]-unit,Inf)/(opnorm(B,1)*norm(backs[side],Inf)+1)
                @assert isfinite(fr) && isfinite(br) && max(fr,br)<1e-8
                base=f.base
                push!(records,Dict("method"=>string(nameof(Factor)),"variant"=>("dense","btran","both","pfi")[side],
                    "repeat"=>repeat,"updates"=>k,"two_forward_seconds"=>times[1,side],
                    "update_seconds"=>times[2,side],"transpose_seconds"=>times[3,side],
                    "forward_residual"=>fr,"transpose_residual"=>br,
                    "view_build_seconds"=>(side in (2,3) ? base.build_seconds : 0.0),
                    "sparse_calls"=>(side in (2,3) ? base.sparse_calls : 0),
                    "dense_calls"=>(side in (2,3) ? base.dense_calls : 0)))
            end
        end
    end
    for r in records[end-3:end];println(r);end;flush(stdout)
    return records
end
function main(input,output)
    ispath(output) && error("Choose a fresh output path")
    data=deserialize(input);n=size(data.A,1);A=hcat(data.A,spdiagm(0=>-ones(n)))
    records=Dict{String,Any}[]
    for Factor in (JSimplex.ForrestTomlinFactorization,JSimplex.SuhlSuhlFactorization,JSimplex.BartelsGolubFactorization),repeat in 1:parse(Int,get(ENV,"JSIMPLEX_PROBE_REPEATS","2"))
        append!(records,paired(Factor,A,data,repeat))
        open(output,"w") do io
            TOML.print(io,Dict("samples"=>records,"history"=>basename(input),"history_sha256"=>bytes2hex(open(sha256,input)),
                "input_sha256"=>data.input_sha256,"baseline_revision"=>"a1adfb4","julia"=>string(VERSION),
                "architecture"=>string(Sys.ARCH),"julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads()))
        end
    end
end
mkpath(ARGS[1])
for input in ARGS[2:end]
    Base.invokelatest(main,input,joinpath(ARGS[1],basename(input)*".toml"))
end
