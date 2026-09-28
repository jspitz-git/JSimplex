using JSimplex, Serialization, SparseArrays, LinearAlgebra, TOML
module Reference
include(joinpath(ENV["JSIMPLEX_BASELINE_SOURCE"],"JSimplex.jl"))
end
const Baseline = Reference.JSimplex

function step!(forward!,replace!,transpose!,factor,direction,other,backward,column,rhs,row)
    ft=@elapsed forward!(direction,factor,column)
    ft+=@elapsed forward!(other,factor,rhs)
    ut=@elapsed replace!(factor,direction,row)
    bt=@elapsed transpose!(backward,factor,rhs)
    return (ft,ut,bt)
end

function same_update(a,b)
    if hasproperty(a,:steps)
        return isequal([(s.row,s.last,s.swapped,s.multiplier) for s in a.steps],
                       [(s.row,s.last,s.swapped,s.multiplier) for s in b.steps])
    end
    return a.pivot==b.pivot && isequal(a.indices,b.indices) &&
        isequal(a.multipliers,b.multipliers) &&
        (!hasproperty(a,:last) || a.last==b.last)
end

function paired(name,A,data,repeat)
    m=size(A,1); basis=copy(data.basis)
    factors=(getproperty(Baseline,name)(A[:,basis]),getproperty(JSimplex,name)(A[:,basis]))
    directions=(zeros(m),zeros(m)); others=(zeros(m),zeros(m)); backs=(zeros(m),zeros(m))
    rhs=ones(m); times=zeros(3,2); records=Dict{String,Any}[]
    for (k,(row,entering)) in enumerate(data.steps)
        column=Vector(A[:,entering])
        # Alternate within each exchange to reduce drift from unrelated host load.
        for side in (isodd(k+repeat) ? (1,2) : (2,1))
            mod=side==1 ? Baseline : JSimplex
            elapsed=step!(mod.forward_solve!,mod.replace_column!,mod.transpose_solve!,
                factors[side],directions[side],others[side],backs[side],column,rhs,row)
            for stage in 1:3; times[stage,side]+=elapsed[stage]; end
        end
        @assert isequal(directions[1],directions[2])
        @assert isequal(others[1],others[2])
        @assert isequal(backs[1],backs[2])
        f,g=factors
        if repeat==1 && name != :PFIFactorization
            @assert f.column_order==g.column_order && f.positions==g.positions
            @assert all(isequal(a.indices,b.indices) && isequal(a.values,b.values)
                for (a,b) in zip(f.upper,g.upper))
            @assert same_update(f.updates[end],g.updates[end])
        end
        k==1 && fill!(times,0) # Exclude compilation warm-up in both implementations.
        basis[row]=entering
        if k in (20,80,160,320)
            B=A[:,basis]
            for side in 1:2
                mod=side==1 ? Baseline : JSimplex
                x=mod.forward_solve(factors[side],rhs)
                fr=norm(B*x-rhs,Inf)/(opnorm(B,Inf)*norm(x,Inf)+1)
                br=norm(B'*backs[side]-rhs,Inf)/(opnorm(B,1)*norm(backs[side],Inf)+1)
                @assert isfinite(fr) && isfinite(br) && max(fr,br)<1e-10
                push!(records,Dict("method"=>string(name),"stable"=>side==2,
                    "repeat"=>repeat,"updates"=>k,"timed_updates"=>k-1,
                    "two_forward_seconds"=>times[1,side],"update_seconds"=>times[2,side],
                    "transpose_seconds"=>times[3,side],"forward_residual"=>fr,
                    "transpose_residual"=>br))
            end
        end
    end
    println(records[end-1]);println(records[end]);flush(stdout)
    return records
end

function main(input,output)
    data=deserialize(input);m=size(data.A,1);A=hcat(data.A,spdiagm(0=>-ones(m)))
    records=Dict{String,Any}[]
    for name in (:ForrestTomlinFactorization,:SuhlSuhlFactorization,
                 :BartelsGolubFactorization,:PFIFactorization),repeat in 1:3
        append!(records,paired(name,A,data,repeat))
        open(output,"w") do io
            TOML.print(io,Dict("samples"=>records,"history"=>basename(input),
                "input_sha256"=>data.input_sha256,"source_iteration"=>data.iteration,
                "baseline_revision"=>"e1b1567","julia"=>string(VERSION),
                "exact_outputs_storage_and_history"=>true))
        end
    end
end
mkpath(ARGS[1])
for input in ARGS[2:end]
    main(input,joinpath(ARGS[1],basename(input)*".toml"))
end
