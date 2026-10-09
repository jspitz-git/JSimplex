using JSimplex, SparseArrays, LinearAlgebra, Statistics, TOML, Test
const JS=JSimplex
function primal_probe(ws)
    tolerance=ws.options.primal_tolerance
    for i in ws.basis.basic_indices
        value=ws.primal[i]
        (JS._lower_violation(ws.lower[i],value)>tolerance ||
         JS._upper_violation(ws.upper[i],value)>tolerance) && return false
    end
    return true
end
function dual_probe(ws)
    tolerance=ws.options.dual_tolerance
    for i in eachindex(ws.basis.states)
        state=ws.basis.states[i]
        (state==JS.BASIC || JS._is_fixed(ws.lower[i],ws.upper[i])) && continue
        price=ws.reduced_costs[i]
        if state==JS.AT_LOWER && price < -tolerance ||
           state==JS.AT_UPPER && price > tolerance ||
           state==JS.FREE_NONBASIC && abs(price)>tolerance
            return false
        end
    end
    return true
end
primal_reference(ws)=JS.primal_infeasibility(ws)<=ws.options.primal_tolerance
dual_reference(ws)=JS.dual_infeasibility(ws)<=ws.options.dual_tolerance
function measure(f,ws,repeats)
    f(ws);GC.gc()
    elapsed=@elapsed for _ in 1:repeats;f(ws);end
    allocated=@allocated f(ws)
    return elapsed/repeats,allocated
end
function main(out,mode="probe")
    @assert !ispath(out)
    reports=[]
    for T in (Float32,Float64), n in (4132,360982)
        p=LinearProblem(spzeros(T,n,n),zeros(T,n);row_lower=zeros(T,n),row_upper=ones(T,n))
        # Scan-only fixture: no large matrix is factorized. The factor/scratch are
        # intentionally unused by these read-only vector kernels.
        empty_problem=LinearProblem(spzeros(T,0,0),T[])
        ws=JS._initialize_workspace_state(empty_problem,SolverOptions(T;verbose=false))
        ws.problem=p
        ws.primal=zeros(T,2n);ws.reduced_costs=zeros(T,2n)
        ws.lower=vcat(p.column_lower,p.row_lower);ws.upper=vcat(p.column_upper,p.row_upper)
        ws.basis=JS.Basis(collect(n+1:2n),vcat(fill(JS.AT_LOWER,n),fill(JS.BASIC,n)))
        for kind in (:primal,:dual), location in (:none,:first,:middle,:last)
            fill!(ws.primal,zero(T));fill!(ws.reduced_costs,zero(T))
            at=location==:first ? 1 : location==:middle ? n÷2 : n
            if location!=:none
                if kind==:primal;ws.primal[n+at]=-one(T)
                else;ws.reduced_costs[at]=-one(T);end
            end
            reference=kind==:primal ? primal_reference : dual_reference
            candidate=kind==:primal ? (mode=="production" ? JS._primal_feasible : primal_probe) : dual_probe
            @test reference(ws)==candidate(ws)==(location==:none)
            old=[];new=[];oldbytes=[];newbytes=[]
            for sample in 1:9
                for (f,t,b) in (isodd(sample) ? ((reference,old,oldbytes),(candidate,new,newbytes)) : ((candidate,new,newbytes),(reference,old,oldbytes)))
                    elapsed,bytes=measure(f,ws,40);push!(t,elapsed);push!(b,bytes)
                end
            end
            push!(reports,Dict("type"=>string(T),"rows"=>n,"kind"=>string(kind),"violation"=>string(location),
                "candidate_kind"=>(kind==:primal ? mode : "probe"),"reference_seconds"=>old,"candidate_seconds"=>new,"reference_bytes"=>oldbytes,"candidate_bytes"=>newbytes,
                "reference_visited"=>kind==:primal ? n : 2n,"candidate_visited"=>location==:none ? (kind==:primal ? n : 2n) : at))
        end
    end
    open(out,"w") do io;TOML.print(io,Dict("measurements"=>reports));end
end
main(ARGS...)
