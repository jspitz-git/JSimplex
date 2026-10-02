# Observe the separate nonzero-RHS Float32 export limitation from the initial fixture.
using JSimplex,LinearAlgebra
BLAS.set_num_threads(1)
path=joinpath(dirname(dirname(pathof(JSimplex))),"test/native_artificial_row_tests.jl")
fixture=first(split(read(path,String),"\n@testset"))
@assert count("rhs=zeros(T,6)",fixture)==1
@assert count("fill!(phase.primal,zero(T))",fixture)==1
fixture=replace(fixture,"rhs=zeros(T,6)"=>"rhs=Vector(A*T[0,1,1,1,1,1])",
    "fill!(phase.primal,zero(T))"=>"phase.primal.=vcat(T[0,1,1,1,1,1,0],rhs)")
Base.include_string(Main,fixture,path)
source=read(joinpath(dirname(pathof(JSimplex)),"simplex_phase_one.jl"),String)
a=first(findfirst("function _remove_artificials!",source))
b=first(findnext("\n\"\"\"Eliminate basic artificials",source,a))-1
lines=split(source[a:b],'\n')
for i in eachindex(lines)
    lines[i]=replace(lines[i],"return false"=>"(println(\"REJECT local line $i: \",$(repr(lines[i])));return false)")
end
Base.include_string(JSimplex,join(lines,'\n'),"diagnostic_nonzero_rhs_removal.jl")
for T in (Float32,Float64)
    phase,mapping,original,policy=artificial_row_roundoff_fixture(T,:pfi)
    println("TYPE ",T)
    println("RESULT ",JSimplex.remove_artificials!(phase,mapping,original,policy,()->false),
        " iteration=",original.iterations)
end
