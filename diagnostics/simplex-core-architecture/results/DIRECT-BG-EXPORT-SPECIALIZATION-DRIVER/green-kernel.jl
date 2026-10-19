# UNEXECUTED. Exact old lifecycle/window body except save name and candidate namespace.
token(x::Float64) = string(reinterpret(UInt64,x);base=16,pad=16)
number(s) = reinterpret(Float64,parse(UInt64,s;base=16))
function save_window(name,data)
    p=joinpath(OUTPUT,name);require(!ispath(p),"Existing output")
    open(p,"w") do io; TOML.print(io,data);flush(io);end
end
function decode_fixture(f)
    mats=[SparseMatrixCSC(m["n"],m["n"],Int.(m["colptr"]),Int.(m["rowval"]),number.(m["nzval"])) for m in f["matrices"]]
    steps=[(j=Int(s["j"]),a=number.(s["a"]),dse=number.(s["dse"]),unit=number.(s["unit"])) for s in f["steps"]]
    return (name=f["name"],n=Int(f["n"]),matrices=mats,steps=steps)
end
function unchanged(f,source)
    all(m.colptr==s["colptr"] && m.rowval==s["rowval"] && token.(m.nzval)==s["nzval"] for (m,s) in zip(f.matrices,source["matrices"])) &&
    all(t.j==s["j"] && token.(t.a)==s["a"] && token.(t.dse)==s["dse"] && token.(t.unit)==s["unit"] for (t,s) in zip(f.steps,source["steps"]))
end
policy(::Val{:native}) = J._NATIVE_PIVOT_ONE
policy(::Val{:markowitz}) = J._NATIVE_PIVOT_DEFAULT
policy_name(::Val{:native}) = "threshold_one"
policy_name(::Val{:markowitz}) = "default"
factory(::Val{:reference},F,B,backend) = J._direct_lu_factor(F,B,backend,policy(backend);normalize=true)
factory(::Val{:candidate},F,B,backend) = J._bgxs_factor(B,backend,policy(backend))
mode(::Val{:reference},f) = J._direct_mode(f)
mode(::Val{:candidate},f) = J._direct_mode(f)
# Identical nested timers on both sides; times are subsets of @timed total.
# Detached output destinations are harness-owned and allocated outside both windows.
function lifecycle(F::Type, backend, side, fixture, outputs)
    clocks=zeros(UInt64,6) # construct, FTRAN, BTRAN, update, refactor1, refactor2
    t=time_ns();factor=factory(side,F,fixture.matrices[1],backend);clocks[1]=time_ns()-t
    m0=mode(side,factor);m1=m0;m2=m0
    for k in 1:8
        s=fixture.steps[k];direction=outputs[3k-2];dse=outputs[3k-1];dual=outputs[3k]
        t=time_ns();J.forward_solve!(direction,factor,s.a);clocks[2]+=time_ns()-t
        t=time_ns();J.forward_solve!(dse,factor,s.dse);clocks[2]+=time_ns()-t
        t=time_ns();J.replace_column!(factor,direction,s.j);clocks[4]+=time_ns()-t
        t=time_ns();J.transpose_solve!(dual,factor,s.unit);clocks[3]+=time_ns()-t
        if k==4
            t=time_ns();J.refactorize!(factor,fixture.matrices[5]);clocks[5]=time_ns()-t
            m1=mode(side,factor)
        elseif k==8
            t=time_ns();J.refactorize!(factor,fixture.matrices[9]);clocks[6]=time_ns()-t
            m2=mode(side,factor)
        end
    end
    return factor,clocks,(m0,m1,m2)
end
# No extra factor solves. Preliminary Float64 residual check outside timing;
# independent auditor evaluates every recorded output exactly from binary tokens.
function residual_ok(M,x,rhs,transposed)
    all(isfinite,x) || return false
    A=transposed ? transpose(M) : M
    bound=128*length(x)*eps(Float64)*max(1.,opnorm(A,Inf)*norm(x,Inf),norm(rhs,Inf))
    norm(A*x-rhs,Inf)<=bound
end
function window(F,backend,side,f,source,pair,order,outputs)
    timed=@timed lifecycle(F,backend,side,f,outputs)
    factor,clocks,modes=timed.value
    # Keep only this final factor until checks/graph accounting, no old factors.
    retained=Base.summarysize(factor)
    inputs_ok=unchanged(f,source);ok=inputs_ok
    for k in 1:8
        s=f.steps[k]
        ok &= residual_ok(f.matrices[k],outputs[3k-2],s.a,false)
        ok &= residual_ok(f.matrices[k],outputs[3k-1],s.dse,false)
        ok &= residual_ok(f.matrices[k+1],outputs[3k],s.unit,true)
    end
    allowed=(:normalized,:direct,:fallback)
    ok &= all(m->m in allowed,modes)
    row=Dict{String,Any}("pair"=>pair,"order"=>order,"measured"=>pair>3,
        "side"=>side===Val(:candidate) ? "candidate" : "reference",
        "policy"=>policy_name(backend),
        "seconds"=>timed.time,"bytes"=>timed.bytes,"events"=>Base.gc_alloc_count(timed.gcstats),
        "gc_seconds"=>timed.gctime,"compile_seconds"=>timed.compile_time,"recompile_seconds"=>timed.recompile_time,
        "nested_seconds"=>Float64.(clocks)./1e9,"retained_bytes"=>retained,
        "modes"=>string.(collect(modes)),"inputs_unchanged"=>inputs_ok,"correct"=>ok,
        "outputs"=>[token.(x) for x in outputs])
    return row
end
