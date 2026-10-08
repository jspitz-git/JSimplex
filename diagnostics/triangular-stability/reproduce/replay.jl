# Reuse preserved histories and independent fresh-LU probes. Refactorizations
# occur only at the requested schedule; no numerical correction is applied.
const EXPERIMENT = "/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl"
include(joinpath(EXPERIMENT,"diagnostics/basis-interval-sweep/reproduce/common.jl"))
function main(history,arm_name,interval_text,output)
    ispath(output) && error("Choose a fresh output path")
    interval=parse(Int,interval_text)
    data=load_history(history); A=augmented_history(data); basis=copy(data.basis)
    arm=ARMS[arm_name]; f=build(arm,A[:,basis]); m=length(basis)
    rhs=zeros(m); d=zeros(m); aux=zeros(m); dense=ones(m); unit=zeros(m)
    records=[]; swaps=0; max_multiplier=0.0; refactors=0
    started=time()
    for (k,(row,entering)) in enumerate(data.steps)
        fill_column!(rhs,A,entering)
        JSimplex.forward_solve!(d,f,rhs)
        JSimplex.replace_column!(f,d,row;zero_tolerance=ZERO_TOL)
        advance_basis!(basis,row,entering)
        u=f.updates[end]
        if hasproperty(u,:swapped_rows) && u.swapped_rows !== nothing
            swaps+=length(u.swapped_rows)
        end
        max_multiplier=max(max_multiplier,maximum(abs,u.multipliers;init=0.0))
        JSimplex._ordinary_forward_solve!(aux,f,dense)
        fill!(unit,0.0);unit[row]=1;JSimplex.transpose_solve!(aux,f,unit)
        if k%80==0 || k==length(data.steps)
            checks=validate(f,A[:,basis],rhs,row)
            push!(records,Dict("step"=>k,"checks"=>checks,"valid"=>valid(checks),
                "counts"=>Dict(string(p)=>v for (p,v) in pairs(counts(f)))))
            println("step=",k," valid=",valid(checks)," residual=",maximum(c["residual"] for c in checks));flush(stdout)
        end
        if k%interval==0 && k<length(data.steps)
            reset!(f,arm,A[:,basis]);refactors+=1
        end
    end
    save_report(output,Dict("source_sha256"=>source_digest(),
        "history_sha256"=>bytes2hex(open(sha256,history)),"arm"=>arm_name,
        "interval"=>interval,"steps"=>length(data.steps),"scheduled_refactors"=>refactors,
        "swaps"=>swaps,"maximum_multiplier"=>max_multiplier,"elapsed"=>time()-started,
        "memory"=>memory(),"records"=>records,"valid"=>all(r["valid"] for r in records)))
end
Base.invokelatest(main,ARGS...)
