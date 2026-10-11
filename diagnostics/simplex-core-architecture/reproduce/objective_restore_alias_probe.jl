# Diagnostic counterexample to Base.mightalias as a byte-disjointness proof.
using TOML, SHA
function range_overlap(a::Vector,b::Vector)
    (isempty(a) || isempty(b)) && return false
    GC.@preserve a b begin
        pa,pb=UInt(pointer(a)),UInt(pointer(b))
        # Checked products; subtraction only in the nonnegative direction.
        na=Base.checked_mul(UInt(length(a)),UInt(Base.elsize(a)))
        nb=Base.checked_mul(UInt(length(b)),UInt(Base.elsize(b)))
        return pa<=pb ? pb-pa<na : pa-pb<nb
    end
end
rows=Any[]
for offset in (0,1,2,4),reverse in (false,true)
    backing=Float64.(1:12)
    GC.@preserve backing begin
        a=unsafe_wrap(Vector{Float64},pointer(backing,1),4;own=false)
        b=unsafe_wrap(Vector{Float64},pointer(backing,1+offset),4;own=false)
        destination,source=reverse ? (a,b) : (b,a)
        overlap=range_overlap(destination,source)
        @assert overlap==(offset<4)
        library=Base.mightalias(destination,source)
        original=copy(backing)
        copyto!(destination,source);first=copy(destination)
        copyto!(destination,source);second=copy(destination)
        naive_would_skip=!library
        wrong_skip=naive_would_skip && !isequal(first,second)
        @assert offset in (1,2) ? wrong_skip : !wrong_skip
        # Proposed conservative diagnostic predicate retains both on overlap.
        copyto!(backing,original);copyto!(destination,source)
        range_overlap(destination,source) && copyto!(destination,source)
        @assert isequal(destination,second)
        push!(rows,Dict("offset"=>offset,"reverse"=>reverse,"base_mightalias"=>library,
          "range_overlap"=>overlap,"naive_wrong_skip"=>wrong_skip,"range_predicate_matches_legacy"=>true))
    end
end
@assert !range_overlap(Float64[],Float64[])
@assert !range_overlap(zeros(4),ones(4))
open(only(ARGS),"w") do io
 TOML.print(io,Dict("rows"=>rows,"naive_counterexamples"=>count(r->r["naive_wrong_skip"],rows),
  "empty_and_distinct_pass"=>true,"script_sha256"=>bytes2hex(sha256(read(@__FILE__))),
  "scope"=>"Float64 Vector storage counterexample and diagnostic range predicate only; not a production implementation or all-scalar validation"))
end
println("ALIAS_PROBE_PASS naive_counterexamples=4 range_cases=10")
