using JSimplex,Test,LinearAlgebra
const target=Ref{Any}(nothing);const scans=Ref(0)
# Count separate full-vector finite scans of the prepared direction only.
function Base.all(f::typeof(isfinite),v::Vector{T}) where {T<:Union{Float32,Float64}}
 v===target[] && (scans[]+=1)
 Base._all(f,v,:)
end
@testset "Prepared handoff avoids a separate finite traversal" begin
 for T in (Float32,Float64)
  f=JSimplex.HuangfuHallFactorization(Matrix{T}(I,8,8));d=JSimplex.forward_solve(f,ones(T,8))
  target[]=d;scans[]=0
  JSimplex.replace_column!(f,d,1)
  @test scans[]==0
  target[]=nothing
  for F in (JSimplex.ForrestTomlinFactorization,JSimplex.SuhlSuhlFactorization,JSimplex.BartelsGolubFactorization)
   f=F(Matrix{T}(I,8,8));d=ones(T,8);entry=JSimplex._begin_prepared_spike!(f,d)
   JSimplex._save_prepared_spike!(entry,d);target[]=d;scans[]=0
   JSimplex._finish_prepared_spike!(entry,d)
   @test scans[]==0
   @test JSimplex._copy_prepared_spike!(f,d)
   target[]=nothing
  end
 end
end
