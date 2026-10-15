# UNEXECUTED. Task3 exact whole-lifecycle cost driver. No production overwrite.
using JSimplex, LinearAlgebra, SparseArrays, TOML
const J = JSimplex
const PHASE, OUTPUT, PROJECT = ARGS
require(v,s) = v || error(s)
token(x::Float64) = string(reinterpret(UInt64,x);base=16,pad=16)
number(s) = reinterpret(Float64,parse(UInt64,s;base=16))
function save(name,data)
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
factory(::Val{:reference},F,B,backend) = F(B,backend)
factory(::Val{:candidate},F,B,backend) = J._direct_lu_factor(F,B,backend;normalize=true)
mode(::Val{:reference},f) = :ordinary
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
function window(F,backend,side,f,source,pair,order)
    outputs=[zeros(f.n) for _ in 1:24]
    timed=@timed lifecycle(F,backend,side,f,outputs)
    factor,clocks,modes=timed.value
    # Keep only this final factor until checks/graph accounting, no old factors.
    retained=Base.summarysize(factor)
    ok=unchanged(f,source)
    for k in 1:8
        s=f.steps[k]
        ok &= residual_ok(f.matrices[k],outputs[3k-2],s.a,false)
        ok &= residual_ok(f.matrices[k],outputs[3k-1],s.dse,false)
        ok &= residual_ok(f.matrices[k+1],outputs[3k],s.unit,true)
    end
    expected=side===Val(:candidate) ? :normalized : :ordinary
    ok &= all(==(expected),modes)
    row=Dict{String,Any}("pair"=>pair,"order"=>order,"measured"=>pair>3,
        "side"=>side===Val(:candidate) ? "candidate" : "reference",
        "seconds"=>timed.time,"bytes"=>timed.bytes,"events"=>Base.gc_alloc_count(timed.gcstats),
        "gc_seconds"=>timed.gctime,"compile_seconds"=>timed.compile_time,"recompile_seconds"=>timed.recompile_time,
        "nested_seconds"=>Float64.(clocks)./1e9,"retained_bytes"=>retained,
        "modes"=>string.(collect(modes)),"inputs_unchanged"=>unchanged(f,source),"correct"=>ok,
        "outputs"=>[token.(x) for x in outputs])
    return row
end
function main()
    completed=false;fatal="";cells=0;windows=0
    try
        require(PHASE in ("cost1","cost2"),"Unexpected phase")
        require(abspath(pathof(J))==joinpath(PROJECT,"src","JSimplex.jl"),"Wrong loaded module")
        require(Threads.nthreads()==1 && BLAS.get_num_threads()==1,"Thread configuration")
        source=TOML.parsefile(joinpath(@__DIR__,"inputs.toml"))["fixtures"]
        for input in source
            f=decode_fixture(input)
            for (label,F) in (("FT",J.ForrestTomlinFactorization),("SS",J.SuhlSuhlFactorization),("BG",J.BartelsGolubFactorization)), backend in (:native,:markowitz)
                cell=cells+1
                save("started-$cell.toml",Dict("fixture"=>f.name,"manager"=>label,"backend"=>string(backend)))
                rows=Dict{String,Any}[]
                for pair in 1:10
                    reference_first=isodd(pair) ⊻ (PHASE=="cost2")
                    sides=reference_first ? (Val(:reference),Val(:candidate)) : (Val(:candidate),Val(:reference))
                    for (order,side) in enumerate(sides)
                        row=window(F,Val(backend),side,f,input,pair,order)
                        push!(rows,row);windows+=1
                        # Every finished window survives a subsequent error/timeout.
                        save("window-$cell-$(2*(pair-1)+order).toml",row)
                        require(row["correct"],"Correctness/mode/input failure; stop")
                        require(!row["measured"] || (row["compile_seconds"]==0 && row["recompile_seconds"]==0),"Measured compilation; stop")
                    end
                end
                save("cell-$cell.toml",Dict("fixture"=>f.name,"manager"=>label,"backend"=>string(backend),"windows"=>20))
                cells+=1
            end
        end
        completed=true
    catch e
        fatal=sprint(showerror,e,catch_backtrace());println(stderr,fatal)
    finally
        save("raw.toml",Dict("phase"=>PHASE,"loaded_path"=>abspath(pathof(J)),"completed"=>completed,"fatal"=>fatal,"cells"=>cells,"windows"=>windows))
    end
    completed || exit(2)
end
main()
