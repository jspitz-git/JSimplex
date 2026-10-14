# UNEXECUTED MA-L utilities. Admission supplies imported aliases; no top-level run.
qexact(x) = Q(x)
qexact(x::BigFloat) = setprecision(BigFloat, max(precision(x), precision(BigFloat))) do
    Q(x)
end
parseq(s) = isnothing(s) ? nothing : begin
    a,b = split(s, '/'); parse(BigInt,a)//parse(BigInt,b)
end
struct NoLengthRows{V}
    values::V
end
Base.iterate(r::NoLengthRows, state...) = iterate(r.values, state...)
Base.IteratorSize(::Type{<:NoLengthRows}) = Base.SizeUnknown()

function make_fixture(f)
    setprecision(BigFloat,f.stored) do
        T = f.scalar == "Q" ? Q : f.scalar == "Float64" ? Float64 : BigFloat
        co=T.(parseq.(f.co))
        if f.alias == "repeated"
            co[2]=co[1]
        elseif f.alias == "numerator"
            co[2]=Base.unsafe_rational(BigInt,numerator(co[1]),denominator(co[2]))
        elseif f.alias == "denominator"
            co[2]=Base.unsafe_rational(BigInt,numerator(co[2]),denominator(co[1]))
        end
        cast(s)=isnothing(s) ? nothing : T(parseq(s))
        rhs=T(parseq(f.rhs));n=length(co)
        p=LinearProblem(sparse(reshape(co,1,n)),zeros(T,n);
            row_lower=T[rhs],row_upper=T[rhs],column_lower=cast.(f.lo),column_upper=cast.(f.hi))
        terms=[(j,p.A[1,j]) for j in 1:n]
        rows=f.container=="tuple" ? Tuple(terms) : f.container=="iterator" ? NoLengthRows(terms) : terms
        (p,rows,f.pivot,qexact(co[f.pivot]),qexact(rhs))
    end
end

# Finite corner enumeration is independent of the candidate's accumulation.
function endpoint_oracle(args)
    p,terms,k,pivot,rhs=args
    vertices=Q[0];unbounded_min=false;unbounded_max=false
    for (j,c0) in terms
        j==k && continue
        c=qexact(c0);iszero(c) && continue
        lo,hi=p.column_lower[j],p.column_upper[j]
        unbounded_min |= !isfinite(c>0 ? lo : hi)
        unbounded_max |= !isfinite(c>0 ? hi : lo)
        endpoints=Q[qexact(bound_value(b)) for b in (lo,hi) if isfinite(b)]
        isempty(endpoints) && push!(endpoints,Q(0))
        vertices=[v+c*z for v in vertices for z in endpoints]
    end
    xmin=(rhs-(pivot>0 ? maximum(vertices) : minimum(vertices)))/pivot
    xmax=(rhs-(pivot>0 ? minimum(vertices) : maximum(vertices)))/pivot
    lower_inf=pivot>0 ? unbounded_max : unbounded_min
    upper_inf=pivot>0 ? unbounded_min : unbounded_max
    lo,hi=p.column_lower[k],p.column_upper[k]
    (!isfinite(lo) || (!lower_inf && xmin>=qexact(bound_value(lo)))) &&
    (!isfinite(hi) || (!upper_inf && xmax<=qexact(bound_value(hi))))
end

scalar_record(x::Q)=(string(x),numerator(x),denominator(x))
scalar_record(x::BigFloat)=(string(qexact(x)),precision(x),getfield(x,:d))
scalar_record(x::Float64)=(bitstring(x),)
function input_scalars(args)
    p,terms,_,pivot,rhs=args
    scalars=Any[p.A.nzval...;p.objective...;p.objective_constant]
    for bounds in (p.row_lower,p.row_upper,p.column_lower,p.column_upper)
        append!(scalars,[b.value for b in bounds])
    end
    append!(scalars,[c for (_,c) in terms]);push!(scalars,pivot,rhs)
    scalars
end
function snapshot(args)
    p,terms,_,_,_=args
    (records=scalar_record.(input_scalars(args)),
     owners=(p.A,p.A.nzval,p.A.colptr,p.A.rowval,p.objective,p.row_lower,p.row_upper,
             p.column_lower,p.column_upper,p.variable_domains,p.row_names,p.column_names,terms),
     structure=(copy(p.A.colptr),copy(p.A.rowval),copy(p.variable_domains),
                [[b.bounded for b in v] for v in (p.row_lower,p.row_upper,p.column_lower,p.column_upper)],
                copy(p.row_names),copy(p.column_names),p.name,p.objective_sense))
end
function preserved(a,b)
    a.structure==b.structure && length(a.records)==length(b.records) &&
    all(a.owners[i]===b.owners[i] for i in eachindex(a.owners)) &&
    all(begin
        x,y=a.records[i],b.records[i]
        x[1]==y[1] && length(x)==length(y) && all(x[k]===y[k] for k in 2:length(x))
    end for i in eachindex(a.records))
end

# Diagnostic-only trace. Never include in timed windows or production code.
mutable struct MALTrace
    position::Int
    eligible::Int
    additions::Int
    scratch::Int
    checked::Int
    equal_denominator_adds::Int
    expected_sum::String
    input_leaves::Vector{BigInt}
end
const MAL_TRACE=Ref{Union{Nothing,MALTrace}}(nothing)
function reset_trace!(args)
    leaves=BigInt[]
    for x in input_scalars(args)
        x isa Q && append!(leaves,(numerator(x),denominator(x)))
    end
    MAL_TRACE[]=MALTrace(0,0,0,0,0,0,"",leaves)
end
function _mal_note_eligible!(position,count)
    MAL_TRACE[].eligible=count
end
function _mal_note_scratch!(scratch,position)
    t=MAL_TRACE[];t.scratch+=1;t.position=position
    pool,buffer=scratch
    leaves=BigInt[numerator(x) for x in pool]
    append!(leaves,[denominator(x) for x in pool]);append!(leaves,buffer)
    length(leaves)==9 || error("nine scratch leaves required")
    all(leaves[i]!==leaves[j] for i in eachindex(leaves) for j in 1:i-1) || error("scratch leaves overlap")
    all(a!==b for a in leaves for b in t.input_leaves) || error("input/scratch overlap")
end
function _mal_note_add!(scratch,x,y,lo,hi)
    t=MAL_TRACE[];t.additions+=1;t.expected_sum=string(x+y)
    t.equal_denominator_adds += denominator(x)==denominator(y)
    pool,_=scratch
    out=pool[1]!==lo && pool[1]!==hi ? pool[1] : pool[2]!==lo && pool[2]!==hi ? pool[2] : pool[3]
    for live in (lo,hi,x,y)
        isnothing(live) && continue
        all(a!==b for a in (numerator(out),denominator(out)) for b in (numerator(live),denominator(live))) || error("destination aliases live scalar")
    end
end
function _mal_note_result!(out)
    t=MAL_TRACE[]
    string(out)==t.expected_sum || error("private addition value mismatch")
    t.checked+=1
    out
end

# Bind every constructed stored scalar to its frozen canonical fixture, outside timing.
function fixture_matches(f,args)
    p,terms,k,pivot,rhs=args
    vals=collect(terms)
    length(vals)==length(f.co) && k==f.pivot || return false
    all(vals[j][1]==j && qexact(vals[j][2])==parseq(f.co[j]) for j in eachindex(f.co)) || return false
    all(qexact(p.A[1,j])==parseq(f.co[j]) for j in eachindex(f.co)) || return false
    pivot==parseq(f.co[k]) && rhs==parseq(f.rhs) || return false
    for (bounds,encoded) in ((p.column_lower,f.lo),(p.column_upper,f.hi))
        for j in eachindex(encoded)
            isfinite(bounds[j]) == !isnothing(encoded[j]) || return false
            if !isnothing(encoded[j])
                qexact(bound_value(bounds[j]))==parseq(encoded[j]) || return false
            end
        end
    end
    all(qexact(bound_value(b))==parseq(f.rhs) for b in (p.row_lower[1],p.row_upper[1])) || return false
    if startswith(f.scalar,"BigFloat")
        all(precision(x)==f.stored for x in input_scalars(args) if x isa BigFloat) || return false
    end
    return true
end
