using Test, LinearAlgebra, SparseArrays, Serialization, SHA, TOML
using JSimplex
const JS = JSimplex
const D = @__DIR__
function digestarrays(arrays...)
    io=IOBuffer()
    for v in arrays
        write(io,Int(length(v)));write(io,v)
    end
    bytes2hex(sha256(take!(io)))
end
matrixhash(B)=digestarrays(B.colptr,B.rowval,B.nzval)
bitsequal(a,b)=reinterpret(UInt64,a)==reinterpret(UInt64,b)
bits(v::Float64)=string(reinterpret(UInt64,v);base=16,pad=16)
qualitydict(q)=Dict("absolute_error"=>q.absolute_error,"relative_error"=>q.relative_error,"finite"=>q.finite,"reliable"=>q.reliable)
function assemble(A,basis)
    n,N=size(A);ptr=Int[1];rows=Int[];vals=Float64[]
    for e in basis
        if e<=N
            for k in nzrange(A,e)
                push!(rows,A.rowval[k]);push!(vals,A.nzval[k])
            end
        else
            1<=e-N<=n || error("invalid artificial column")
            push!(rows,e-N);push!(vals,-1.0)
        end
        push!(ptr,length(rows)+1)
    end
    SparseMatrixCSC(n,n,ptr,rows,vals)
end
# Isolated proposal wrapper, never included by production. The saved point is
# read-only; only a new private vector may be changed. No policy switch is enabled.
function attempt_cleanup(B,x::Vector{T},rhs::Vector{T},policy;transposed) where T
    scratch=JS.SolveQualityScratch(T,length(rhs))
    before=JS.solve_quality!(scratch,B,x,rhs,policy;transposed)
    proposal=copy(x)
    if !before.finite
        return (;before,proposed=before,returned=before,proposal,point=copy(x),changed=false,accepted=false,skipped=true)
    end
    changed=JS._clean_homogeneous_terms!(proposal,B,rhs,transposed,zeros(Int,length(rhs)),policy)
    proposed=JS.solve_quality!(scratch,B,proposal,rhs,policy;transposed)
    accepted=changed && proposed.finite && proposed.reliable
    point=accepted ? proposal : copy(x)
    returned=accepted ? proposed : before
    (;before,proposed,returned,proposal,point,changed,accepted,skipped=false)
end
function small_tests(records)
    for T in (Float32,Float64), transposed in (false,true)
        tiny=ldexp(one(T),T===Float32 ? -40 : -60)
        policy=JS.NumericalPolicy(T)
        # Two essential tiny components cancel in a homogeneous equation;
        # deleting both satisfies that equation but violates a different one.
        C=sparse(T[1 0 0;1 1 0;0 0 1])
        B=transposed ? sparse(transpose(C)) : C
        x=T[tiny,-tiny,1];rhs=T[tiny,0,1];saved=copy(x);bh=matrixhash(B)
        a=attempt_cleanup(B,x,rhs,policy;transposed)
        @test a.before.reliable && a.changed && !a.proposed.reliable && !a.accepted
        @test a.returned.reliable && isequal(a.point,saved) && isequal(x,saved)
        @test iszero(a.proposal[1]) && iszero(a.proposal[2])
        @test matrixhash(B)==bh && rhs==T[tiny,0,1] && policy.solve_tolerance==T(256)*eps(T)
        push!(records,Dict("type"=>string(T),"transposed"=>transposed,"case"=>"essential-small-components",
            "before"=>qualitydict(a.before),"proposed"=>qualitydict(a.proposed),"returned"=>qualitydict(a.returned),"accepted"=>a.accepted))
        # Positive control: a tiny false component in an identity system.
        B=spdiagm(0=>ones(T,2));x=T[1,tiny];rhs=T[1,0];saved=copy(x)
        a=attempt_cleanup(B,x,rhs,policy;transposed)
        @test !a.before.reliable && a.changed && a.accepted && a.returned.reliable
        @test a.point==T[1,0] && isequal(x,saved) && rhs==T[1,0]
        push!(records,Dict("type"=>string(T),"transposed"=>transposed,"case"=>"removable-small-component",
            "before"=>qualitydict(a.before),"proposed"=>qualitydict(a.proposed),"returned"=>qualitydict(a.returned),"accepted"=>a.accepted))
        # A large, genuinely wrong component cannot be excused by cleanup.
        x=T[2,tiny];saved=copy(x);a=attempt_cleanup(B,x,rhs,policy;transposed)
        @test !a.before.reliable && !a.proposed.reliable && !a.accepted && !a.returned.reliable
        @test isequal(a.point,saved) && isequal(x,saved)
        push!(records,Dict("type"=>string(T),"transposed"=>transposed,"case"=>"genuinely-bad-point",
            "before"=>qualitydict(a.before),"proposed"=>qualitydict(a.proposed),"returned"=>qualitydict(a.returned),"accepted"=>a.accepted))
        for value in (T(Inf),T(NaN))
            x=T[value,tiny];saved=copy(x);a=attempt_cleanup(B,x,rhs,policy;transposed)
            @test a.skipped && !a.accepted && !a.returned.reliable && isequal(a.point,saved) && isequal(x,saved)
        end
    end
end
function examine(B,x,rhs,policy,arm,stage,records,cleaned)
    before_hash=digestarrays(x);rhs_hash=digestarrays(rhs);bh=matrixhash(B)
    t=@timed attempt_cleanup(B,x,rhs,policy;transposed=true)
    a=t.value
    q=JS.solve_quality!(JS.SolveQualityScratch(Float64,length(rhs)),B,a.point,rhs,policy;transposed=true)
    @test isequal(qualitydict(q),qualitydict(a.returned))
    @test !a.before.reliable && a.before.relative_error==1.0
    @test digestarrays(x)==before_hash && digestarrays(rhs)==rhs_hash && matrixhash(B)==bh
    @test !Base.mightalias(a.point,x) && !Base.mightalias(a.proposal,x)
    @test all(isfinite,a.point) && all(isfinite,a.proposal)
    @test !a.accepted || (q.reliable && q.finite)
    @test a.accepted || bitsequal(a.point,x)
    if stage=="post-correction"
        @test a.accepted && q.reliable
    end
    changed=findall(i->reinterpret(UInt64,a.proposal[i])!=reinterpret(UInt64,x[i]),eachindex(x))
    push!(records,Dict("arm"=>arm,"stage"=>stage,"before"=>qualitydict(a.before),
        "proposed"=>qualitydict(a.proposed),"returned"=>qualitydict(q),"changed"=>a.changed,
        "accepted"=>a.accepted,"changed_components"=>length(changed),"changed_indices"=>changed,
        "changed_before_bits"=>bits.(x[changed]),"changed_after_bits"=>bits.(a.proposal[changed]),
        "input_hash"=>before_hash,"proposed_hash"=>digestarrays(a.proposal),"returned_hash"=>digestarrays(a.point),
        "seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),"gc_seconds"=>t.gctime,
        "compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time))
    push!(cleaned,(;arm,stage,point=copy(a.point),accepted=a.accepted))
    println(arm," / ",stage," accepted=",a.accepted," before=",qualitydict(a.before)," proposed=",qualitydict(a.proposed)," changed=",length(changed));flush(stdout)
end
function main(out)
    ispath(out) && error("fresh output required")
    @test Threads.nthreads()==1 && BLAS.get_num_threads()==1 && sizeof(Int)==8
    # Static literal paths and hashes are launch-pinned; metadata JSON is not
    # parsed by a new package dependency in this small Julia driver.
    tape="/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/.superpowers/basis-chain-cost/histories/runtime-30000.bin"
    old="/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl/.superpowers/klu-weight-rejection/2026-10-29/first-rhs.bin"
    result=Dict{String,Any}("completed"=>false,"cases"=>Any[],"small_cases"=>Any[],"scope"=>"saved-point cleanup verification only; zero basis solves/factorizations; no production integration")
    cleaned=Any[]
    @testset "Validated homogeneous cleanup" begin
        small_tests(result["small_cases"])
        @test bytes2hex(open(sha256,tape))=="eff13aefe6693665694e74d6fc5c6f111d15e52752a093a600d4093211ebd28c"
        @test bytes2hex(open(sha256,old))=="3e8bf2b4c22471872fc8f72b0c7511b3fca7967139aa01a037b74ce341aaf66d"
        data=deserialize(tape);witness=deserialize(old);basis=copy(data.basis)
        @test basis==witness.basis && length(witness.arms)==3
        @test data.input_sha256=="d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68"
        A_hash=matrixhash(data.A);B=assemble(data.A,basis);bh=matrixhash(B)
        @test bh=="7b6ab789d7f49d73ec163eee3e2c5c5e9207dadd5f66a3b31972755b367c6d5c"
        rhs=copy(witness.rhs);policy=JS.NumericalPolicy(Float64)
        @test policy.solve_tolerance==2.0^-44 && !policy.solve_refinement && policy.max_refinements==3
        for arm in witness.arms
            @test length(arm.before)==length(arm.delta)==length(arm.correction_rhs)==1
            @test bitsequal(arm.initial,arm.before[1]) && bitsequal(arm.initial,arm.final)
            examine(B,arm.initial,rhs,policy,arm.name,"initial",result["cases"],cleaned)
            trial=[arm.before[1][i]+arm.delta[1][i] for i in eachindex(rhs)]
            examine(B,trial,rhs,policy,arm.name,"post-correction",result["cases"],cleaned)
            @test matrixhash(B)==bh && matrixhash(data.A)==A_hash && data.basis==basis
            GC.gc()
        end
        @test length(result["cases"])==6 && length(result["small_cases"])==12
        @test bytes2hex(open(sha256,old))=="3e8bf2b4c22471872fc8f72b0c7511b3fca7967139aa01a037b74ce341aaf66d"
        localpath="/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl/.superpowers/klu-homogeneous-cleanup/2026-10-30/cleaned-points.bin"
        ispath(localpath) && error("fresh cleaned witness required")
        mkpath(dirname(localpath))
        serialize(localpath,(;basis,rhs,cleaned))
        result["witness"]=Dict("path"=>localpath,"bytes"=>filesize(localpath),"sha256"=>bytes2hex(open(sha256,localpath)))
        result["policy"]=Dict(string(k)=>getfield(policy,k) for k in fieldnames(typeof(policy)))
        result["matrix_hash"]=bh;result["n"]=size(B,1);result["nnz"]=nnz(B);result["completed"]=true
        open(out,"w") do io
            TOML.print(io,result)
        end
    end
end
Base.invokelatest(main,abspath(ARGS[1]))
