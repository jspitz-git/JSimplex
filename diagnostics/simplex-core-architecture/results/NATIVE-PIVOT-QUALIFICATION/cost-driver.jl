# UNEXECUTED managed-backend comparison; source entry counts, no native hooks.
using SparseArrays, LinearAlgebra, TOML, PrecompileTools
PrecompileTools.verbose[] && error("Unexpected precompile verbosity")
using JSimplex
const J=JSimplex
const CAPI=SparseArrays.LibSuiteSparse
const INFO_SLOTS=(CAPI.UMFPACK_STATUS+1,CAPI.UMFPACK_IR_TAKEN+1,CAPI.UMFPACK_IR_ATTEMPTED+1,CAPI.UMFPACK_SOLVE_FLOPS+1)
need(x,s)=x || error(s)
token(x::Float64)=string(reinterpret(UInt64,x);base=16,pad=16)
number(s)=reinterpret(Float64,parse(UInt64,s;base=16))
function save(out,name,value)
    p=joinpath(out,name);need(!ispath(p),"Output exists")
    open(p,"w") do io;TOML.print(io,value);flush(io);end
end
mutable struct Counts
    construction::Int;refactor::Int;forward::Int;transpose::Int
end
cdict(c)=Dict("construction"=>c.construction,"refactor"=>c.refactor,"forward"=>c.forward,"transpose"=>c.transpose)
metrics(t)=Dict("seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),"gctime"=>t.gctime,"compile_time"=>t.compile_time,"recompile_time"=>t.recompile_time)
function construct(B,p,c)
    c.construction+=1
    J._factorize_basis(B,Val(:native),p)
end
function refactor(f,B,c)
    c.refactor+=1
    J._refactorize_backend(f,B)
end
function solves!(xs,info,f,b,c)
    for r in 0:15
        for j in 1:3
            k=3r+j
            if j==3
                c.transpose+=1;J._backend_transpose_solve!(xs[k],f,b[j])
            else
                c.forward+=1;J._backend_forward_solve!(xs[k],f,b[j])
            end
            @inbounds for i in 1:4;info[i,k]=f.factorization.info[INFO_SLOTS[i]];end
        end
    end
    nothing
end
function regions(B,p,b,xs,info,c)
    build=@timed construct(B,p,c);f=build.value
    initial=f.factorization;firstid=objectid(initial);firstctrl=objectid(initial.control)
    no_spare=f.spare===nothing
    r1=@timed refactor(f,B,c)
    second=f.factorization;secondid=objectid(second)
    fresh=second!==initial && f.spare===initial
    r2=@timed refactor(f,B,c)
    reused=f.factorization===initial && f.spare===second && objectid(f.factorization.control)==firstctrl
    # These two owners are still the active/spare pair, not retired factor roots.
    solve=@timed solves!(xs,info,f,b,c)
    (f,build,r1,r2,solve,no_spare,fresh,reused,firstid,secondid,firstctrl)
end
function decoded(m)
    n=Int(m["n"]);need(n in (32,96),"Dimension")
    SparseMatrixCSC(n,n,Int.(m["colptr"]),Int.(m["rowval"]),number.(m["nzval"]))
end
function main()
    out,project,input=ARGS;c=Counts(0,0,0,0)
    raw=Dict{String,Any}("complete"=>false,"fatal"=>"")
    try
        need(realpath(pathof(JSimplex))==realpath(joinpath(project,"src/JSimplex.jl")),"Wrong loaded source")
        need(Threads.nthreads()==BLAS.get_num_threads()==1 && Int===Int64,"Runtime shape")
        raw["loaded"]=Dict("JSimplex"=>realpath(pathof(JSimplex)),"SparseArrays"=>realpath(pathof(SparseArrays)),"LinearAlgebra"=>realpath(pathof(LinearAlgebra)),"TOML"=>realpath(pathof(TOML)))
        raw["threads"]=Threads.nthreads();raw["blas_threads"]=BLAS.get_num_threads()
        fs=TOML.parsefile(input)["fixtures"];need(length(fs)==4,"Four fixtures")
        Bs=decoded.([f["matrix"] for f in fs]);bs=[Tuple(number.(f["rhs"][k]) for k in ("a","dse","unit")) for f in fs]
        owners=[(B.colptr,B.rowval,B.nzval,b...) for (B,b) in zip(Bs,bs)]
        xs=[[zeros(size(Bs[i],1)) for _ in 1:48] for i in 1:4 for _ in 1:22]
        infos=[zeros(4,48) for _ in 1:88]
        raw["output_payload_bytes"]=sum(sizeof(x) for window in xs for x in window)
        raw["info_payload_bytes"]=sum(sizeof(x) for x in infos)
        raw["diagnostic_graph_bytes"]=Base.summarysize((xs,infos))
        raw["default_control"]=token.(SparseArrays.UMFPACK.get_umfpack_control(Float64,Int))
        id=0
        for i in 1:4, round in 1:11
            for arm in (isodd(round) ? ("C","P") : ("P","C"))
                id+=1;p=arm=="C" ? J._NATIVE_PIVOT_DEFAULT : J._NATIVE_PIVOT_ONE
                total=@timed regions(Bs[i],p,bs[i],xs[id],infos[id],c)
                f,build,r1,r2,solve,no_spare,fresh,reused,firstid,secondid,firstctrl=total.value
                F=f.factorization
                record=Dict{String,Any}("schedule"=>Dict("id"=>id,"fixture"=>fs[i]["name"],"arm"=>arm,"round"=>round,"warm"=>round<=3),
                    "construction"=>metrics(build),"refactor_fresh"=>metrics(r1),"refactor_spare"=>metrics(r2),"solve"=>metrics(solve),"total"=>metrics(total),
                    "no_spare"=>no_spare,"fresh"=>fresh,"reused"=>reused,"policy"=>string(f.pivot_policy),
                    "owners"=>string.([firstid,secondid,firstctrl,objectid(F),objectid(f.spare),objectid(F.control)]),
                    "control"=>token.(F.control),"spare_control"=>token.(f.spare.control),"info"=>token.(F.info),
                    "Wi"=>length(F.workspace.Wi),"W"=>length(F.workspace.W),
                    "outputs"=>[token.(x) for x in xs[id]],"solve_info"=>[token.(infos[id][:,k]) for k in 1:48])
                if round==11
                    lnz,unz,m,n,nzd=SparseArrays.UMFPACK.umf_lunz(F)
                    record["factor"]=Dict("lnz"=>lnz,"unz"=>unz,"m"=>m,"n"=>n,"nzd"=>nzd,"graph_bytes"=>Base.summarysize(f),"spare_W"=>length(f.spare.workspace.W),"spare_Wi"=>length(f.spare.workspace.Wi))
                end
                save(out,"window-$(lpad(id,3,'0')).toml",record)
                need(no_spare && fresh && reused,"Lifecycle mismatch")
                if round>3
                    need(all(t.compile_time==t.recompile_time==0 for t in (build,r1,r2,solve,total)),"Measured compilation contamination")
                end
                # Drop the wrapper and timed return owners before the next window.
                f=nothing;F=nothing;total=nothing;build=nothing;r1=nothing;r2=nothing
            end
        end
        raw["inputs_unchanged"]=all(B.colptr===o[1] && B.rowval===o[2] && B.nzval===o[3] && B.colptr==f["matrix"]["colptr"] && B.rowval==f["matrix"]["rowval"] && token.(B.nzval)==f["matrix"]["nzval"] && all(b[j]===o[3+j] && token.(b[j])==f["rhs"][k] for (j,k) in enumerate(("a","dse","unit"))) for (B,b,o,f) in zip(Bs,bs,owners,fs))
        raw["windows"]=id;raw["complete"]=true
    catch e
        raw["fatal"]=sprint(showerror,e,catch_backtrace());println(stderr,raw["fatal"])
    finally
        raw["counts"]=cdict(c);save(out,"raw.toml",raw)
    end
    need(raw["complete"] && raw["inputs_unchanged"],"Incomplete cost run")
    need(cdict(c)==Dict("construction"=>88,"refactor"=>176,"forward"=>2816,"transpose"=>1408),"Work budget")
end
main()
