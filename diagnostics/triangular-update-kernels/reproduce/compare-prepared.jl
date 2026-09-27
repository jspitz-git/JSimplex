using JSimplex, Serialization, SparseArrays, LinearAlgebra, TOML
include("reference-updates.jl")
function main(input,output)
    data=deserialize(input);m=size(data.A,1)
    A=hcat(data.A,spdiagm(0=>-ones(m)));records=Dict{String,Any}[]
    for Factor in (JSimplex.PFIFactorization,JSimplex.ForrestTomlinFactorization,
                   JSimplex.SuhlSuhlFactorization,JSimplex.BartelsGolubFactorization)
        for repeat in 1:3, enabled in (isodd(repeat) ? (false,true) : (true,false))
            Factor===JSimplex.PFIFactorization && enabled && continue
            reference=Factor!==JSimplex.PFIFactorization && !enabled
            basis=copy(data.basis);f=Factor(A[:,basis]);direction=zeros(m);other=zeros(m);rhs=ones(m)
            update_seconds=forward_seconds=0.0;hits=0
            for (k,(row,entering)) in enumerate(data.steps)
                column=Vector(A[:,entering])
                forward=reference ? JSimplex._reference_forward_solve! : JSimplex.forward_solve!
                forward_seconds+=@elapsed forward(direction,f,column)
                forward_seconds+=@elapsed forward(other,f,rhs)
                if enabled
                    # Inspect only buffer identities, without touching or warming
                    # either coefficient vector before the timed replacement.
                    cache=f.row_cache.prepared
                    hits+=!isnothing(cache) && any(e->e.destination===direction,cache.entries)
                end
                replacement=reference ? JSimplex._reference_replace! : JSimplex.replace_column!
                update_seconds+=@elapsed replacement(f,direction,row)
                k==1 && (update_seconds=forward_seconds=0.0)
                basis[row]=entering
                if k in (20,80,160,320)
                    B=A[:,basis];x=zeros(m);y=zeros(m)
                    forward(x,f,rhs);JSimplex.transpose_solve!(y,f,rhs)
                    fr=norm(B*x-rhs,Inf)/(opnorm(B,Inf)*norm(x,Inf)+1)
                    br=norm(B'*y-rhs,Inf)/(opnorm(B,1)*norm(y,Inf)+1)
                    @assert isfinite(fr)&&isfinite(br)&&fr<1e-10&&br<1e-10
                    rec=Dict{String,Any}("method"=>string(nameof(Factor)),"prepared"=>enabled,
                        "repeat"=>repeat,"updates"=>k,"update_seconds"=>update_seconds,
                        "two_forward_seconds"=>forward_seconds,"forward_residual"=>fr,
                        "transpose_residual"=>br,"eligible_outputs"=>hits,"source_iteration"=>data.iteration)
                    println(rec);flush(stdout);push!(records,rec)
                end
            end
        end
    end
    open(output,"w") do io
        TOML.print(io,Dict("samples"=>records,"history"=>basename(input),
            "input_sha256"=>data.input_sha256,"julia"=>string(VERSION)))
    end
end
mkpath(ARGS[1])
for input in ARGS[2:end]
    main(input,joinpath(ARGS[1],basename(input)*".toml"))
end
