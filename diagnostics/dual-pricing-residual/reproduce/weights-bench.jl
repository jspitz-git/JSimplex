using JSimplex,SparseArrays,Statistics,TOML,Random,LinearAlgebra
Base.include(JSimplex,joinpath(@__DIR__,"weights-reference.jl"))
function sample(f,ws,rho,row,column,reps)
    f(ws,rho,row,column,1,1.0,1.0,()->false)
    fill!(ws.pricing_weights,1.0);GC.gc()
    @timed for _ in 1:reps;@assert f(ws,rho,row,column,1,1.0,1.0,()->false);end
end
function main(out)
    @assert !ispath(out)
    records=[]
    for (name,m,n,dense) in (("dense",512,768,true),("sparse",32768,49152,false),("large-sparse",360982,186497,false))
        rng=MersenneTwister(184)
        A=dense ? sparse(randn(rng,m,n)) : sparse(rand(rng,1:m,3n),repeat(1:n;inner=3),randn(rng,3n),m,n)
        ws=JSimplex.initialize_workspace(LinearProblem(A,zeros(n)),SolverOptions(verbose=false,basis_update=:huangfu_hall))
        rho=randn(rng,m);row=randn(rng,n+m);column=randn(rng,m);column[1]=1.0
        old=[];new=[];ob=[];nb=[];reps=10
        for round in 1:15
            oldweights=nothing;newweights=nothing
            for flag in (isodd(round) ? (false,true) : (true,false))
                t=sample(flag ? JSimplex.update_dual_pricing_weights! : JSimplex._guard_reference_weights!,ws,rho,row,column,reps)
                @assert t.compile_time==0
                @assert !ws.dual_devex_fallback
                push!(flag ? new : old,t.time/reps);push!(flag ? nb : ob,t.bytes/reps)
                if flag;newweights=copy(ws.pricing_weights);else;oldweights=copy(ws.pricing_weights);end
            end
            @assert isequal(oldweights,newweights)
        end
        r=Dict("case"=>name,"rows"=>m,"columns"=>n,"nonzeros"=>nnz(A),"old_seconds"=>old,"new_seconds"=>new,"old_bytes"=>ob,"new_bytes"=>nb,"ratio"=>median(new)/median(old),"repetitions"=>reps)
        push!(records,r);println(name," ratio=",r["ratio"]," bytes=",median(ob),"/",median(nb));flush(stdout)
    end
    open(out,"w") do io;TOML.print(io,Dict("cases"=>records));end
end
Base.invokelatest(main,only(ARGS))
