using SHA
stream=SHA.SHA2_256_CTX()
const tally=Dict{String,Int}()
const transitions=Dict{String,Dict{String,Int}}()
const latest=Dict{Symbol,Any}()
const published=Ref{Any}(nothing)
const tracked=(:primal,:reduced_costs,:costs,:pricing_weights)
struct Mark
    ws::UInt
    iteration::Int
    site::String
    fields::Dict{String,Any}
end
sample(ws)=ws.iterations%4096 in (0,1)
counted(name)=(tally[name]=get(tally,name,0)+1)
record(parts...) = SHA.update!(stream, codeunits(join(parts,'|')*"\n"))
bits(x::Float64)=reinterpret(UInt64,x)
bits(x::Bool)=x
bits(x::Int)=x
function summary!(key, field, a, b)
    @assert length(a)==length(b)
    changed=count(i->!isequal(a[i],b[i]), eachindex(a,b))
    row=get!(transitions,key,Dict{String,Int}())
    row[field*"_pairs"]=get(row,field*"_pairs",0)+1
    row[field*"_different"]=get(row,field*"_different",0)+(changed>0)
    row[field*"_max_elements"]=max(changed,get(row,field*"_max_elements",0))
    return changed
end
function watch(kind,ws,site,fields)
    old=get(latest,kind,nothing)
    if !isnothing(old) && old.ws==objectid(ws) && 0<=ws.iterations-old.iteration<=1
        key=string(kind,": ",old.site," -> ",site)
        for (k,v) in fields
            summary!(key,k,old.fields[k],v)
        end
    end
    latest[kind]=Mark(objectid(ws),ws.iterations,site,Dict(k=>copy(v) for (k,v) in fields))
end
function audit_guard(kind,ws,answer,arg=nothing,extra=0.0)
    counted(string(kind))
    record(kind,ws.iterations,bits(answer))
    sample(ws) || return
    if kind==:finite
        callers=("_dual_iteration_entry!","update_dual_pricing_weights!","_dual_after_iteration!","_dual_optimize!",
                 "_dual_iteration_unchecked!","_make_dual_feasible!")
        site="other"
        for f in stacktrace()
            s=string(f.func)
            if any(c->occursin(c,s),callers)
                site=first(c for c in callers if occursin(c,s));break
            end
        end
        watch(kind,ws,site,Dict(string(k)=>getproperty(ws,k) for k in tracked))
    elseif kind==:row
        # Include all sparse matrix arrays, coefficient values, basis, rho and unit RHS index.
        p=ws.problem.A
        watch(kind,ws,"row",Dict("basis"=>ws.basis.basic_indices,"rho"=>arg,"row"=>[extra],
             "colptr"=>p.colptr,"rowval"=>p.rowval,"nzval"=>p.nzval))
    else
        # row_rhs already contains the scale after the direction check: pre-call
        # copies for sampled inputs are taken by the wrapper.
        watch(kind,ws,"direction",arg)
    end
end
function before_publish(ws,index)
    index!=0 && sample(ws) || return
    published[]=Mark(objectid(ws),ws.iterations,"weights",Dict(string(k)=>copy(getproperty(ws,k)) for k in tracked))
end
function shadow_finite(ws,index)
    full=JS._finite_workspace(ws)
    scalar=isfinite(ws.primal[index])
    @assert full==scalar
    counted("finite_reused")
    old=published[]
    if !isnothing(old) && old.ws==objectid(ws) && old.iteration+1==ws.iterations
        changed=0
        for k in tracked
            n=summary!("protected publish",string(k),old.fields[string(k)],getproperty(ws,k))
            if k==:primal
                @assert n==0 || (n==1 && !isequal(old.fields["primal"][index],ws.primal[index]))
                changed=n
            else
                @assert n==0
            end
        end
        counted(changed==0 ? "sample_primal_same" : "sample_primal_changed_at_leaving")
    end
    published[]=nothing
end
const last_ratio=Ref(NaN)
function shadow_row(ws,rho,l)
    accepted=last_ratio[]
    actual=JS._dual_row_residual_ratio(ws,rho,l)
    @assert isequal(accepted,actual) && actual<=1.0
    counted("row_reused")
end
function event!(ws,reason)
    counted("events")
    record(reason, ws.iterations,ws.refactorizations,ws.scratch.selected_row,ws.scratch.selected_entering)
    if sample(ws) && reason==:pivot_completed
        for a in (ws.basis.basic_indices,ws.primal,ws.costs,ws.reduced_costs,ws.pricing_weights)
            SHA.update!(stream,reinterpret(UInt8,a))
        end
    end
end
function install_audit()
    @eval JS function _simplex_event!(ws::SimplexWorkspace,reason::Symbol)
        Main.event!(ws,reason)
        _diagnostic_event!(ws.progress.diagnostics,reason,ws)
    end
    file=read(joinpath(dirname(pathof(JS)),"dual_simplex.jl"),String)
    for (name,kind) in (("_finite_workspace",:finite),("_dual_row_residual_ratio",:row),("_dual_direction_residual_ok!",:direction))
        pos=first(first(findall("function "*name*"(",file)))
        expr,_=Meta.parse(file,pos)
        body=expr.args[2]
        result=gensym(); inputs=gensym()
        observe=kind==:finite ? :(Main.audit_guard(:finite,workspace,$result)) :
            kind==:row ? :(begin Main.last_ratio[]=$result; Main.audit_guard(:row,workspace,$result,rho,leaving_row) end) :
            :(Main.audit_guard(:direction,workspace,$result,$inputs))
        capture=kind==:direction ? :(Main.sample(workspace) ? Dict("basis"=>copy(workspace.basis.basic_indices),
            "rhs"=>copy(workspace.scratch.row_rhs),"direction"=>copy(direction),"pivot"=>[pivot]) : nothing) : :(nothing)
        expr.args[2]=quote
            local $inputs=$capture
            local $result=(()->begin $body end)()
            $observe
            return $result
        end
        Core.eval(JS,expr)
    end
end
function reset_audit!()
    empty!(latest);empty!(tally);empty!(transitions);published[]=nothing
    # Start a distinct transcript after the warmup; contexts do not straddle solves.
    global stream = SHA.SHA2_256_CTX()
end
function audit_report()
    report=Dict("sha256"=>bytes2hex(SHA.digest!(stream)), "counts"=>tally, "sampled_transitions"=>transitions)
    if arm=="shadow"
        @assert get(tally,"row_reused",0)>0 && get(tally,"finite_reused",0)>0
    elseif arm=="original-audit"
        other=TOML.parsefile(joinpath(dirname(ARGS[end]),"shadow.toml.audit.toml"))
        if !(report["sha256"]==other["sha256"] && all(other["counts"][k]==v for (k,v) in tally))
            open(io->TOML.print(io,report),ARGS[end]*".audit-mismatch.toml","w")
            error("Full event and guard streams differ")
        end
    end
    return report
end
