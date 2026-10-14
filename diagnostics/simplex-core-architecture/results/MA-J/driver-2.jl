# Throwaway MA-J component experiment; no solver, factorization or presolve pass.
push!(LOAD_PATH, joinpath(@__DIR__, "env"))
using JSimplex, MutableArithmetics, SparseArrays, TOML
const MA = MutableArithmetics
const Q = Rational{BigInt}
const ExactValue = JSimplex.ExactValue
const ExactEndpoint = JSimplex.ExactEndpoint
const _exact_rational = JSimplex._exact_rational
realpath(pathof(JSimplex)) == realpath(joinpath(@__DIR__, "../../../../src/JSimplex.jl")) || error("wrong source")
realpath(pathof(MA)) == realpath("/home/jspitz/.julia/packages/MutableArithmetics/SaQfc/src/MutableArithmetics.jl") || error("wrong MA")
include("reference.jl")
include("candidate.jl")

# Diagnostic conversion must retain stored bits even under a lower ambient context.
qexact(x)=Q(x)
qexact(x::BigFloat)=setprecision(BigFloat,max(precision(x),precision(BigFloat))) do
    Q(x)
end

function endpoint_oracle(p, terms, pivot, rhs)
    values = Q[0]; low_unbounded=false; high_unbounded=false
    for (j,c0) in terms
        j==1 && continue
        c=qexact(c0);iszero(c) && continue
        lo=p.column_lower[j];hi=p.column_upper[j]
        low_unbounded |= !isfinite(c>0 ? lo : hi)
        high_unbounded |= !isfinite(c>0 ? hi : lo)
        # Enumerate finite endpoint corners; zero is a placeholder only on
        # an unbounded side. That extreme is excluded below using the flags.
        a=isfinite(lo) ? qexact(bound_value(lo)) : Q(0)
        b=isfinite(hi) ? qexact(bound_value(hi)) : Q(0)
        values=[v+c*z for v in values for z in (a,b)]
    end
    # For one-sided unbounded intervals enumerate the finite extreme separately.
    min_activity=Q(0);max_activity=Q(0)
    if !low_unbounded
        min_activity=minimum(values)
        # Placeholder endpoints cannot affect a finite extreme: use only the
        # actual finite endpoint where the other endpoint is unbounded.
        min_activity=sum((qexact(c)*qexact(bound_value(qexact(c)>0 ? p.column_lower[j] : p.column_upper[j])) for (j,c) in terms if j!=1 && !iszero(c));init=Q(0))
    end
    if !high_unbounded
        max_activity=sum((qexact(c)*qexact(bound_value(qexact(c)>0 ? p.column_upper[j] : p.column_lower[j])) for (j,c) in terms if j!=1 && !iszero(c));init=Q(0))
    end
    if !low_unbounded && !high_unbounded
        # Independent exhaustive finite corners are authoritative.
        min_activity=minimum(values);max_activity=maximum(values)
    end
    lower_inf=pivot>0 ? high_unbounded : low_unbounded
    upper_inf=pivot>0 ? low_unbounded : high_unbounded
    xlo=(rhs-(pivot>0 ? max_activity : min_activity))/pivot
    xhi=(rhs-(pivot>0 ? min_activity : max_activity))/pivot
    lo=p.column_lower[1];hi=p.column_upper[1]
    return (!isfinite(lo) || (!lower_inf && xlo>=qexact(bound_value(lo)))) &&
           (!isfinite(hi) || (!upper_inf && xhi<=qexact(bound_value(hi))))
end
function fixture(::Type{T},n,style,sgn,mode) where T
    cast(x)=isnothing(x) ? nothing : T(x)
    bigbase=BigInt(1)<<180
    co=Q[sgn*2];lo=Any[Q(-bigbase*100)];hi=Any[Q(bigbase*100)]
    for j in 2:n
        c=style=="units" ? Q(isodd(j) ? -1 : 1) :
          style=="zero" ? Q(j) :
          style=="cancel" ? Q(isodd(j) ? -3 : 3) :
          Q((isodd(j) ? -1 : 1)*(bigbase+2j+1),BigInt(2j+1))
        a=style=="zero" ? Q(0) : style in ("units","cancel") ? Q(1) : Q(j,BigInt(7))
        b=(style in ("fixed","units","cancel","zero") || (style=="prefix" && j<n)) ? a : a+Q(3,BigInt(11))
        push!(co,c);push!(lo,a);push!(hi,b)
    end
    if style=="unbounded";lo[2]=nothing; n>2 && (hi[n]=nothing);end
    if mode=="exclude";lo[1]=Q(bigbase*200);hi[1]=lo[1]+1
    elseif mode=="lower";hi[1]=nothing
    elseif mode=="upper";lo[1]=nothing
    elseif mode=="free";lo[1]=nothing;hi[1]=nothing
    end
    p=LinearProblem(sparse(reshape(T.(co),1,n)),zeros(T,n);row_lower=T[3],row_upper=T[3],column_lower=cast.(lo),column_upper=cast.(hi))
    terms=[(j,p.A[1,j]) for j in 1:n]
    return (p,terms,1,Q(terms[1][2]),Q(3))
end
function scalar_record(x)
    if x isa BigFloat
        return (string(qexact(x)),precision(x),getfield(x,:d))
    elseif x isa Q
        return (string(x),numerator(x),denominator(x))
    end
    return (bitstring(x),)
end
function snapshot(args)
    p,terms,_,pivot,rhs=args
    scalars=Any[p.A.nzval...;p.objective...;p.objective_constant]
    for bounds in (p.row_lower,p.row_upper,p.column_lower,p.column_upper)
        for b in bounds;push!(scalars,b.value);end
    end
    append!(scalars,[x[2] for x in terms]);push!(scalars,pivot,rhs)
    return (records=scalar_record.(scalars), arrays=(p.A,p.A.nzval,p.A.colptr,p.A.rowval,p.objective,p.row_lower,p.row_upper,p.column_lower,p.column_upper,terms), structural=(copy(p.A.colptr),copy(p.A.rowval),copy(p.variable_domains),[[b.bounded for b in v] for v in (p.row_lower,p.row_upper,p.column_lower,p.column_upper)]))
end
function preserved(a,b)
    a.structural==b.structural && length(a.records)==length(b.records) && all(a.arrays[i]===b.arrays[i] for i in eachindex(a.arrays)) && all(begin
        x,y=a.records[i],b.records[i]
        x[1]==y[1] && length(x)==length(y) && all(x[k]===y[k] for k in 2:length(x))
    end for i in eachindex(a.records))
end
@noinline function batch(f,args,reps)
    result=0
    for _ in 1:reps;result+=f(args...);end
    return result
end
function timing(f,args,reps)
    t=@timed batch(f,args,reps)
    return Dict{String,Any}("seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),"gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time,"true_count"=>t.value)
end
function main()
    output=ARGS[1];rows=Any[];tests=Any[];costs=Any[];errors=String[]
    start=time_ns();ambient=precision(BigFloat);rnd=rounding(BigFloat)
    try
        # Negative controls test the oracles without mutating any fixture.
        args=fixture(Q,4,"general",1,"contain");snap=snapshot(args)
        altered=(records=copy(snap.records),arrays=snap.arrays,structural=snap.structural);altered.records[1]=(altered.records[1][1]*"!",altered.records[1][2:end]...)
        !preserved(snap,altered) || error("snapshot negative control")
        expected=endpoint_oracle(args[1],args[2],args[4],args[5]);(!expected)!=expected || error("result negative control")
        pool=(zero(Q),zero(Q),zero(Q));buf=MA.buffer_for(+,Q,Q)
        leaves=[numerator(x) for x in pool];append!(leaves,[denominator(x) for x in pool]);append!(leaves,collect(buf))
        all(leaves[i]!==leaves[j] for i in eachindex(leaves) for j in 1:i-1) || error("scratch owner alias")
        for (label,T,bits) in (("Float64",Float64,256),("BigFloat256",BigFloat,256),("BigFloat512",BigFloat,512),("RationalBigInt",Q,256))
            setprecision(BigFloat,bits) do
                for n in (2,4,8), style in ("fixed","general","units","zero","cancel","unbounded"), sgn in (-1,1), mode in ("contain","exclude","lower","upper","free")
                    args=fixture(T,n,style,sgn,mode);before=snapshot(args)
                    want=endpoint_oracle(args[1],args[2],args[4],args[5])
                    actual=JSimplex._equality_implies_column_bounds(args...);reference=reference_bounds(args...);candidate=candidate_bounds(args...)
                    same=preserved(before,snapshot(args));ok=actual==reference==candidate==want && same
                    push!(tests,Dict("scalar"=>label,"n"=>n,"style"=>style,"sign"=>sgn,"mode"=>mode,"expected"=>want,"actual"=>actual,"reference"=>reference,"candidate"=>candidate,"inputs_preserved"=>same,"pass"=>ok))
                    ok || error("correctness $((label,n,style,sgn,mode))")
                end
                for n in (4,8),style in ("fixed","general","units","cancel","prefix"),sgn in (-1,1)
                    base=fixture(T,n,style,sgn,"contain");p,terms,_,pivot,rhs=base
                    vertices=Q[0]
                    for (j,c) in terms
                        j==1 && continue
                        vertices=[v+qexact(c)*qexact(bound_value(b)) for v in vertices for b in (p.column_lower[j],p.column_upper[j])]
                    end
                    points=[(rhs-v)/pivot for v in vertices];xmin,xmax=extrema(points)
                    delta=Q(1,BigInt(1)<<220)
                    for mode in ("exact","lower_outside","upper_outside","lower_exact","upper_exact")
                        lo=Any[bound_value(b) for b in p.column_lower];hi=Any[bound_value(b) for b in p.column_upper]
                        if mode=="exact";lo[1]=T(xmin);hi[1]=T(xmax)
                        elseif mode=="lower_outside";lo[1]=T(xmin+delta);hi[1]=nothing
                        elseif mode=="upper_outside";lo[1]=nothing;hi[1]=T(xmax-delta)
                        elseif mode=="lower_exact";lo[1]=T(xmin);hi[1]=nothing
                        else;lo[1]=nothing;hi[1]=T(xmax)
                        end
                        q=LinearProblem(p.A,p.objective;row_lower=p.row_lower,row_upper=p.row_upper,column_lower=lo,column_upper=hi)
                        args=(q,[(j,q.A[1,j]) for j in 1:n],1,pivot,rhs);before=snapshot(args)
                        want=endpoint_oracle(q,args[2],pivot,rhs)
                        actual=JSimplex._equality_implies_column_bounds(args...);a=reference_bounds(args...);b=candidate_bounds(args...);same=preserved(before,snapshot(args));ok=actual==a==b==want && same
                        push!(tests,Dict("scalar"=>label,"n"=>n,"style"=>style,"sign"=>sgn,"mode"=>"tight_"*mode,"expected"=>want,"actual"=>actual,"reference"=>a,"candidate"=>b,"inputs_preserved"=>same,"pass"=>ok))
                        ok || error("tight boundary")
                    end
                end
                for n in (2,4,8),style in ("fixed","general","units","cancel")
                    args=fixture(T,n,style,1,"contain");before=snapshot(args);expected=endpoint_oracle(args[1],args[2],args[4],args[5])
                    # First batch includes any remaining specialization. This is
                    # separately recorded, not compared to steady windows.
                    first_ref=timing(reference_bounds,args,1);first_ma=timing(candidate_bounds,args,1)
                    windows=Any[]
                    for pair in 1:10
                        for side in (isodd(pair) ? ("reference","candidate") : ("candidate","reference"))
                            f=side=="reference" ? reference_bounds : candidate_bounds
                            t=timing(f,args,32);t["pair"]=pair;t["side"]=side;t["phase"]=pair<=3 ? "warm" : "measured"
                            t["correct"]=t["true_count"]==32*expected;t["inputs_preserved"]=preserved(before,snapshot(args));push!(windows,t)
                            t["correct"] && t["inputs_preserved"] || error("window correctness")
                        end
                    end
                    push!(costs,Dict("scalar"=>label,"n"=>n,"style"=>style,"first_reference"=>first_ref,"first_candidate"=>first_ma,"windows"=>windows))
                end
            end
        end
        # Stored low bits must survive conversion even under lower ambient precision.
        for offset in (-1,0,1)
            lowargs=setprecision(BigFloat,256) do
                tiny=BigFloat(2)^(-200);p=LinearProblem(sparse(reshape(BigFloat[2,3+tiny,5-tiny+offset*tiny],1,3)),zeros(BigFloat,3);row_lower=BigFloat[10],row_upper=BigFloat[10],column_lower=BigFloat[1,1,1],column_upper=BigFloat[1,1,1])
                (p,[(j,p.A[1,j]) for j in 1:3],1,Q(2),Q(10))
            end
            for bits in (64,512)
                setprecision(BigFloat,bits) do
                    before=snapshot(lowargs);want=endpoint_oracle(lowargs[1],lowargs[2],lowargs[4],lowargs[5]);a=reference_bounds(lowargs...);b=candidate_bounds(lowargs...);same=preserved(before,snapshot(lowargs))
                    lossy_rejected=true
                    if bits==64 && offset!=0
                        p=lowargs[1]
                        rounded=BigFloat[BigFloat(c;precision=64) for c in p.A.nzval]
                        lossy=LinearProblem(sparse(reshape(rounded,1,3)),zeros(BigFloat,3);row_lower=BigFloat[10],row_upper=BigFloat[10],column_lower=BigFloat[1,1,1],column_upper=BigFloat[1,1,1])
                        lossy_rejected=endpoint_oracle(lossy,[(j,lossy.A[1,j]) for j in 1:3],Q(2),Q(10)) != want
                    end
                    ok=a==b==want==(offset==0) && same && lossy_rejected
                    push!(tests,Dict("scalar"=>"stored256ambient$bits","offset"=>offset,"expected"=>want,"reference"=>a,"candidate"=>b,"inputs_preserved"=>same,"lossy_control_rejected"=>lossy_rejected,"pass"=>ok));ok || error("low bits")
                end
            end
        end
    catch e
        push!(errors,sprint(showerror,e,catch_backtrace()))
    end
    raw=Dict("tests"=>tests,"costs"=>costs,"errors"=>errors,"body_seconds"=>(time_ns()-start)/1e9,"ambient_restored"=>precision(BigFloat)==ambient && rounding(BigFloat)==rnd,"scope"=>"throwaway component only; scratch setup inside every function call; no presolve/solver execution")
    open(output,"w") do io;TOML.print(io,raw);end
    isempty(errors) && raw["ambient_restored"] && length(tests)==1126 && length(costs)==48 || error("qualification incomplete: $(length(tests)), $(length(costs)), $errors")
    all(w["compile_seconds"]==0 && w["recompile_seconds"]==0 for c in costs for w in c["windows"] if w["phase"]=="measured") || error("measured compilation")
    println("MA-J 1126 cases and 48 cost cases completed")
end
main()
