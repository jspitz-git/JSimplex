# Diagnostic qualification, not an installed production helper.
using Test, TOML, SHA
function proven_disjoint(a::Vector{T}, b::Vector{T}) where T
    isconcretetype(T) || return false # excludes bits-union tag planes/abstract layout
    (isempty(a) || isempty(b)) && return true
    stride=UInt(Base.elsize(a))
    iszero(stride) && return false
    # Do not throw or wrap if a byte-length cannot be represented.
    limit=typemax(UInt) ÷ stride
    (UInt(length(a))<=limit && UInt(length(b))<=limit) || return false
    na,nb=UInt(length(a))*stride,UInt(length(b))*stride
    GC.@preserve a b begin
        pa,pb=UInt(pointer(a)),UInt(pointer(b))
        return pa<=pb ? pb-pa>=na : pa-pb>=nb
    end
end
rows=Any[]
@testset "Concrete numeric storage disjointness" begin
 for T in (Float16,Float32,Float64,BigFloat,Rational{Int64},Rational{BigInt})
  for offset in (0,1,2,4),reverse in (false,true)
   backing=T.(1:12)
   GC.@preserve backing begin
    a=unsafe_wrap(Vector{T},pointer(backing,1),4;own=false)
    b=unsafe_wrap(Vector{T},pointer(backing,1+offset),4;own=false)
    dest,src=reverse ? (a,b) : (b,a)
    @test UInt(pointer(backing,2))-UInt(pointer(backing,1))==Base.elsize(backing)
    @test proven_disjoint(dest,src)==(offset==4)
    saved=copy(backing)
    copyto!(dest,src);copyto!(dest,src);expected=copy(dest)
    copyto!(backing,saved);copyto!(dest,src)
    proven_disjoint(dest,src) || copyto!(dest,src)
    @test isequal(dest,expected)
    T===BigFloat && @test all(precision.(dest).==precision.(expected))
    push!(rows,Dict("type"=>string(T),"stride"=>Base.elsize(backing),"offset"=>offset,
        "reverse"=>reverse,"disjoint"=>proven_disjoint(dest,src),"legacy_match"=>true))
   end
  end
  @test proven_disjoint(T[],T[])
  @test proven_disjoint(T[],T[1])
  @test proven_disjoint(T[1],T[])
  @test proven_disjoint(T[1],T[2])
  @test proven_disjoint(T[1,2],T[1,2]) # independently allocated buffers
 end
 @test !proven_disjoint(Real[1.0],Real[2.0])
 @test !proven_disjoint(Union{Float32,Float64}[1.0],Union{Float32,Float64}[2.0])
end
@assert !ispath(only(ARGS))
open(only(ARGS),"w") do io
 TOML.print(io,Dict("rows"=>rows,"script_sha256"=>bytes2hex(sha256(read(@__FILE__))),
 "scope"=>"Six concrete numeric Vector layouts; unknown/union layout conservative fallback; diagnostic only"))
end
