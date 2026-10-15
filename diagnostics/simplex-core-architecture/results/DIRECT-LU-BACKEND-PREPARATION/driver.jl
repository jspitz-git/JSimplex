# UNEXECUTED diagnostic driver. Fixed two contexts; no production method overwrite.
using JSimplex, LinearAlgebra, SparseArrays, TOML
const J=JSimplex
const API=SparseArrays.UMFPACK
const OUTPUT,PROJECT,INPUTS=ARGS
need(x,s)=x || error(s)
token(x::Float64)=string(reinterpret(UInt64,x);base=16,pad=16)
number(s)=reinterpret(Float64,parse(UInt64,s;base=16))
function save(name,value)
    p=joinpath(OUTPUT,name);need(!ispath(p),"Output exists")
    open(p,"w") do io;TOML.print(io,value);flush(io);end
end
function decode(f)
    mats=[SparseMatrixCSC(m["n"],m["n"],Int.(m["colptr"]),Int.(m["rowval"]),number.(m["nzval"])) for m in f["matrices"][1:5]]
    steps=[(j=Int(s["j"]),a=number.(s["a"]),dse=number.(s["dse"]),unit=number.(s["unit"])) for s in f["steps"][1:5]]
    mats,steps
end
function unchanged(mats,steps,f)
    all(m.colptr==s["colptr"] && m.rowval==s["rowval"] && token.(m.nzval)==s["nzval"] for (m,s) in zip(mats,f["matrices"][1:5])) &&
    all(t.j==s["j"] && token.(t.a)==s["a"] && token.(t.dse)==s["dse"] && token.(t.unit)==s["unit"] for (t,s) in zip(steps,f["steps"][1:5]))
end
function controls(b)
    F=b.factorization
    need(F isa SparseArrays.UMFPACK.UmfpackLU{Float64,Int64},"Unexpected backend")
    Dict("tokens"=>token.(F.control),"irstep_index"=>API.JL_UMFPACK_IRSTEP,
         "irstep_zero"=>iszero(F.control[API.JL_UMFPACK_IRSTEP]))
end
function reset_state(f,B0)
    c=f.row_cache;n=length(f.work);p=c.prepared
    Dict("empty_history"=>isempty(f.updates),"no_shared_updates"=>f.shared_update_count==0,
       "identity_upper"=>all(length(u.indices)==length(u.values)==1 && u.indices[1]==j && u.values[1]==1.0 for (j,u) in enumerate(f.upper)),
       "identity_columns"=>all(f.column_order[i]==i for i in 1:n),"identity_positions"=>all(f.positions[i]==i for i in 1:n),
       "identity_row_order"=>all(c.order[i]==i for i in 1:n),"empty_operations"=>isempty(c.operations),
       "zero_update_count"=>c.update_count==0,"not_permuted"=>!c.permuted,
       "empty_active_upper"=>isempty(c.active_upper),"upper_clean"=>!c.upper_dirty,
       "prepared_invalid"=>!isnothing(p) && all(e.destination===nothing for e in p.entries),
       "no_sparse"=>isnothing(f.sparse),"spare_present"=>!isnothing(f.base.spare),
       "spare_is_original"=>f.base.spare===B0,"new_active"=>f.base.factorization!==B0)
end
# One installed get_lunz + one get_numeric per context, no orientation solve.
# CSR L is retained directly; no diagnostic CSR->CSC copy or extra extraction.
function snapshot(b,B)
    F=b.factorization;need(F isa SparseArrays.UMFPACK.UmfpackLU{Float64,Int64},"Snapshot type")
    lnz,unz,m,n,nzd=API.umf_lunz(F)
    need(m==n==96 && 0<=lnz<=n*(n+1)÷2 && 0<=unz<=n*(n+1)÷2,"Factor dimensions/fill")
    lp=Vector{Int64}(undef,n+1);lj=Vector{Int64}(undef,lnz);lx=Vector{Float64}(undef,lnz)
    up=Vector{Int64}(undef,n+1);ui=Vector{Int64}(undef,unz);ux=Vector{Float64}(undef,unz)
    p=Vector{Int64}(undef,n);q=Vector{Int64}(undef,n);rs=Vector{Float64}(undef,n);recip=Ref{Int64}(-1)
    status=API.umfpack_dl_get_numeric(lp,lj,lx,up,ui,ux,p,q,C_NULL,recip,rs,F.numeric)
    API.umferror(status)
    for v in (lp,lj,up,ui,p,q);v .+= 1;end
    native_owned=!Base.mightalias(F.colptr,B.colptr) && !Base.mightalias(F.rowval,B.rowval) && !Base.mightalias(F.nzval,B.nzval)
    native_match=length(F.colptr)==length(B.colptr) && length(F.rowval)==length(B.rowval) && length(F.nzval)==length(B.nzval) && all(F.colptr[i]+1==B.colptr[i] for i in eachindex(B.colptr)) && all(F.rowval[i]+1==B.rowval[i] && token(F.nzval[i])==token(B.nzval[i]) for i in eachindex(B.nzval))
    Dict("n"=>n,"lnz"=>lnz,"unz"=>unz,"nzd"=>nzd,"status"=>status,"do_recip"=>recip[],
       "L"=>Dict("format"=>"csr","ptr"=>lp,"indices"=>lj,"values"=>token.(lx)),
       "U"=>Dict("format"=>"csc","ptr"=>up,"indices"=>ui,"values"=>token.(ux)),
       "p"=>p,"q"=>q,"Rs"=>token.(rs),"control"=>token.(F.control),"info"=>token.(F.info),
       "native_owned"=>native_owned,"native_match"=>native_match,
       "native_colptr"=>copy(F.colptr),"native_rowval"=>copy(F.rowval),"native_nzval"=>token.(F.nzval))
end
function fwd!(x,f,b,c;backend=false)
    c["ftran"]+=1
    backend ? J._backend_forward_solve!(x,f,b) : J.forward_solve!(x,f,b)
end
function back!(x,f,b,c;backend=false)
    c["btran"]+=1
    backend ? J._backend_transpose_solve!(x,f,b) : J.transpose_solve!(x,f,b)
end
function main()
    raw=Dict{String,Any}("completed"=>false,"fatal"=>"","loaded_path"=>abspath(pathof(J)))
    counts=Dict("factorization"=>0,"ftran"=>0,"btran"=>0,"replace"=>0,"refactor"=>0,"snapshot"=>0)
    raw["counts"]=counts
    try
        need(abspath(pathof(J))==joinpath(PROJECT,"src","JSimplex.jl"),"Loaded source")
        need(Threads.nthreads()==1 && BLAS.get_num_threads()==1 && Int===Int64,"Threads/index type")
        f=only(filter(f->f["name"]=="sparse96",TOML.parsefile(INPUTS)["fixtures"]))
        mats,steps=decode(f);s=steps[5]
        # Fresh context is deliberately kept live through the prefix context.
        counts["factorization"]+=1;fresh=J._factorize_basis(mats[5],Val(:native))
        fresh_before=controls(fresh);fresh_out=[zeros(96) for _ in 1:3]
        fwd!(fresh_out[1],fresh,s.a,counts;backend=true)
        fwd!(fresh_out[2],fresh,s.dse,counts;backend=true)
        back!(fresh_out[3],fresh,s.unit,counts;backend=true)
        counts["snapshot"]+=1
        fresh_record=Dict("controls_before"=>fresh_before,"controls_after"=>controls(fresh),
             "outputs"=>[token.(x) for x in fresh_out],"factor"=>snapshot(fresh,mats[5]))
        save("fresh.toml",fresh_record)
        counts["factorization"]+=1;factor=J.ForrestTomlinFactorization(mats[1],Val(:native))
        original=factor.base.factorization;prefix_before=controls(factor.base)
        prefix=[zeros(96) for _ in 1:12]
        for k in 1:4
            st=steps[k];direction=prefix[3k-2]
            fwd!(direction,factor,st.a,counts)
            fwd!(prefix[3k-1],factor,st.dse,counts)
            counts["replace"]+=1;J.replace_column!(factor,direction,st.j)
            back!(prefix[3k],factor,st.unit,counts)
        end
        counts["refactor"]+=1;counts["factorization"]+=1;J.refactorize!(factor,mats[5])
        after_refactor=controls(factor.base);reset=reset_state(factor,original)
        tail=[zeros(96) for _ in 1:3]
        fwd!(tail[1],factor,s.a,counts)
        fwd!(tail[2],factor,s.dse,counts)
        # Capture immediately before the additional base-only call, no solve added.
        ordinary_snapshot=[token.(tail[1]),token.(tail[2])]
        fwd!(tail[3],factor.base,s.dse,counts;backend=true)
        counts["snapshot"]+=1
        record=Dict("controls_before"=>prefix_before,"controls_after_refactor"=>after_refactor,
             "controls_after"=>controls(factor.base),"reset"=>reset,
             "prefix_outputs"=>[token.(x) for x in prefix],"tail_outputs"=>[token.(x) for x in tail],
             "ordinary_before_base"=>ordinary_snapshot,"factor"=>snapshot(factor.base,mats[5]),
             "fresh_context_retained"=>fresh.factorization!==factor.base.factorization && fresh.factorization!==factor.base.spare)
        save("prefix.toml",record)
        raw["inputs_unchanged"]=unchanged(mats,steps,f)
        raw["completed"]=true
    catch e
        raw["fatal"]=sprint(showerror,e,catch_backtrace());println(stderr,raw["fatal"])
    finally
        save("raw.toml",raw)
    end
    need(raw["completed"] && raw["inputs_unchanged"],"Incomplete diagnostic")
    need(counts==Dict("factorization"=>3,"ftran"=>13,"btran"=>5,"replace"=>4,"refactor"=>1,"snapshot"=>2),"Call budget")
end
main()
