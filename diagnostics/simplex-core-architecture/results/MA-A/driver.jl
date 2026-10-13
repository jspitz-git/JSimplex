# Isolated private-scratch dot experiment. No JSimplex import or solver call.
using MutableArithmetics, TOML
const MA = MutableArithmetics
realpath(pathof(MA)) == realpath("/home/jspitz/.julia/packages/MutableArithmetics/SaQfc/src/MutableArithmetics.jl") || error("unexpected MA source")
const Q = Rational{BigInt}

@noinline function plain!(sink,a::Vector{T},b,reps) where T
    for rep in 1:reps
        s=zero(T)
        for i in eachindex(a,b)
            s = s + a[i]*b[i]
        end
        sink[]=s
    end
    return nothing
end
@noinline function buffered!(sink,acc,buffer,a,b,reps)
    for rep in 1:reps
        MA.operate!(zero,acc)
        for i in eachindex(a,b)
            MA.buffered_operate!(buffer,MA.add_mul,acc,a[i],b[i])
        end
        sink[]=acc
    end
    return nothing
end
function scratch(::Type{T}) where T
    return zero(T), MA.buffer_for(MA.add_mul,T,T,T)
end
function owners!(out,x::BigFloat)
    push!(out,getfield(x,:d))
end
owners!(out,x::BigInt)=push!(out,x)
function owners!(out,x::Rational)
    owners!(out,numerator(x));owners!(out,denominator(x));return out
end
function owners!(out,x::Tuple)
    for y in x;owners!(out,y);end
    return out
end
function owners(x)
    result=Any[];owners!(result,x);return result
end
function fixture(n,mostlyzero)
    a=Q[];b=Q[]
    for i in 1:n
        na=BigInt(mod(17i,61)-30)*BigInt(2)^80+BigInt(isodd(i) ? -1 : 1)
        nb=BigInt(mod(13i,47)-23)
        push!(a,mostlyzero && mod(i,8)!=0 ? BigInt(0)//BigInt(1) : na//BigInt(17))
        push!(b,nb//BigInt(19))
    end
    return a,b
end
function measurement(f,args...)
    t=@timed f(args...)
    return Dict{String,Any}("seconds"=>t.time,"bytes"=>t.bytes,
        "allocations"=>Base.gc_alloc_count(t.gcstats),"gc_seconds"=>t.gctime,
        "compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time)
end
function run_case(::Type{T},bits,n,mostlyzero) where T
    qa,qb=fixture(n,mostlyzero)
    a=T[convert(T,x) for x in qa];b=T[convert(T,x) for x in qb]
    ac=MA.mutable_copy.(a);bc=MA.mutable_copy.(b)
    exact=sum(Q(a[i])*Q(b[i]) for i in eachindex(a))
    abs_sum=sum(abs(Q(a[i])*Q(b[i])) for i in eachindex(a))
    # Exact forward-error bound for 2n rounded operations, no overflow/underflow
    # for these bounded fixtures. Oracle uses actual rounded BigFloat inputs.
    u=bits==0 ? BigInt(0)//BigInt(1) : BigInt(1)//(BigInt(2)^bits)
    gamma=(2n*u)/(1-2n*u)
    setup=@timed scratch(T)
    acc,buffer=setup.value
    own=owners((acc,buffer));inputs=vcat([owners(x) for x in a]...,[owners(x) for x in b]...)
    private=all(x !== y for x in own for y in inputs) && all(own[i] !== own[j] for i in eachindex(own) for j in 1:i-1)
    private || error("scratch leaf alias")
    precision_ok=T!=BigFloat || (all(precision(x)==bits for x in (a...,b...,acc)) && precision(buffer)==bits)
    precision_ok || error("precision mismatch")
    sr=Ref{T}(zero(T));sc=Ref{T}(zero(T))
    # A separate unmeasured reference establishes the sequential rounded result.
    plain!(sr,a,b,1);expected=MA.mutable_copy(sr[])
    records=Any[]
    reps=32
    for pair in 1:10
        phase=pair<=3 ? "warm" : "measured"
        order=isodd(pair) ? ("plain","buffered") : ("buffered","plain")
        for side in order
            t=side=="plain" ? measurement(plain!,sr,a,b,reps) : measurement(buffered!,sc,acc,buffer,a,b,reps)
            value=side=="plain" ? sr[] : sc[]
            t["side"]=side;t["pair"]=pair;t["phase"]=phase;t["repetitions"]=reps
            t["output"]=string(Q(value))
            t["same_sequential_result"]=isequal(value,expected)
            t["exact_or_bounded"]=abs(Q(value)-exact)<=gamma*abs_sum
            t["inputs_preserved"]=all(isequal(a[i],ac[i]) && isequal(b[i],bc[i]) for i in eachindex(a))
            current=owners((acc,buffer));t["scratch_owners_preserved"]=length(own)==length(current) && all(own[i]===current[i] for i in eachindex(own))
            t["precision_preserved"]=T!=BigFloat || (precision(value)==bits && precision(acc)==bits && precision(buffer)==bits && all(precision(x)==bits for x in (a...,b...)))
            push!(records,t)
        end
    end
    checks=Dict("private_scratch"=>private,"precision"=>precision_ok,
        "outputs"=>all(r["same_sequential_result"] && r["exact_or_bounded"] for r in records),
        "input_and_owner_preservation"=>all(r["inputs_preserved"] && r["scratch_owners_preserved"] && r["precision_preserved"] for r in records),
        "measured_compile_zero"=>all(r["compile_seconds"]==0 && r["recompile_seconds"]==0 for r in records if r["phase"]=="measured"))
    return Dict{String,Any}("type"=>string(T),"bits"=>bits,"n"=>n,"mostlyzero"=>mostlyzero,
        "checks"=>checks,"windows"=>records,"exact_dot"=>string(exact),"absolute_error_bound"=>string(gamma*abs_sum),
        "input_a"=>string.(Q.(a)),"input_b"=>string.(Q.(b)),"scratch_leaf_count"=>length(own),
        "scratch_graph_bytes"=>Base.summarysize((acc,buffer)),
        "setup"=>Dict("seconds"=>setup.time,"bytes"=>setup.bytes,"allocations"=>Base.gc_alloc_count(setup.gcstats),"compile_seconds"=>setup.compile_time,"recompile_seconds"=>setup.recompile_time))
end
function main(out)
    cases=Any[];errors=String[];original_precision=precision(BigFloat);original_rounding=rounding(BigFloat)
    try
        setrounding(BigFloat,RoundNearest) do
            for bits in (128,256,512)
                setprecision(BigFloat,bits) do
                    for (n,z) in ((32,false),(256,false),(256,true))
                        c=run_case(BigFloat,bits,n,z);push!(cases,c)
                        all(values(c["checks"])) || error("BigFloat case failed")
                    end
                end
            end
            for (n,z) in ((32,false),(256,false),(256,true))
                c=run_case(Q,0,n,z);push!(cases,c)
                all(values(c["checks"])) || error("Rational case failed")
            end
        end
    catch e
        push!(errors,sprint(showerror,e,catch_backtrace()))
    end
    restored=precision(BigFloat)==original_precision && rounding(BigFloat)==original_rounding
    passed=isempty(errors) && length(cases)==12 && restored
    raw=Dict("cases"=>cases,"errors"=>errors,"all_passed"=>passed,"ambient_restored"=>restored,
        "MA_source"=>pathof(MA),"MA_version"=>string(Base.pkgversion(MA)),"Julia_version"=>string(VERSION))
    open(joinpath(out,"measurement.toml"),"w") do io;TOML.print(io,raw);end
    passed || error("measurement failed; preserve output")
end
length(ARGS)==1 || error("one output directory required")
main(ARGS[1])
