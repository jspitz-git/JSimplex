using Test,SparseArrays
@testset "Compact row maps retain immutable identity and absent slots" begin
 for T in (Float32,Float64,BigFloat),n in (0,3,1000)
  p=LinearProblem(spzeros(T,3,n),zeros(T,n))
  r=JSimplex._row_result(p,[1,3]);m=only(r.postsolve_stack)
  @test m.columns isa UnitRange{Int}
  @test collect(m.columns)==collect(1:n)
  @test collect(m.removed_values)==Vector{Union{Nothing,T}}(nothing,n)
  @test collect(m.removed_states)==fill(JSimplex.FREE_NONBASIC,n)
  @test !(m.removed_values isa Vector) && !(m.removed_states isa Vector)
  materialized=JSimplex.PresolveMap{T}(copy(m.rows),collect(1:n),Vector{Union{Nothing,T}}(nothing,n),fill(JSimplex.FREE_NONBASIC,n),3)
  x=fill(T(.5),n);out=JSimplex.postsolve_primal(m,x)
  @test out==x && out!==x
  basis=JSimplex.Basis(collect(n+1:n+2),vcat(fill(JSimplex.FREE_NONBASIC,n),fill(JSimplex.BASIC,2)))
  a=JSimplex.restore_basis(m,basis);c=JSimplex.restore_basis(materialized,basis)
  @test a.states==c.states && a.basic_indices==c.basic_indices
  @test a.states!==basis.states && a.basic_indices!==basis.basic_indices
  n==1000 && @test Base.summarysize(m)*10<Base.summarysize(materialized)
  if n>0
   copied=copy(m.removed_values);copied[1]=T(7)
   @test m.removed_values[1]===nothing
  end
  @test_throws BoundsError m.removed_values[0]
  @test_throws BoundsError m.removed_values[n+1]
 end
end
@testset "Ordinary vector map order, duplicates, bounds and broadcast fallback" begin
 for T in (Float32,Float64,BigFloat),columns in (Int[],[1,3],[3,1],[2,2],[0],[4]),k in (0,1,2,3)
  vals=Union{Nothing,T}[T(7),T(8),T(9)]
  m=JSimplex.PresolveMap{T}(Int[],columns,vals,fill(JSimplex.FREE_NONBASIC,3),0)
  x=T.(1:k)./T(2)
  reference=try
   a=T[7,8,9];a[columns].=x;(:ok,a)
  catch e;(:error,typeof(e));end
  actual=try;(:ok,JSimplex.postsolve_primal(m,x));catch e;(:error,typeof(e));end
  @test actual==reference
  @test vals==Union{Nothing,T}[T(7),T(8),T(9)] && x==T.(1:k)./T(2)
 end
end
@testset "BigFloat restore does not re-round stored scalars" begin
 high=setprecision(BigFloat,320) do;BigFloat(2)^100+1;end
 for bits in (32,64,128,240)
  setprecision(BigFloat,bits) do
   m=JSimplex.PresolveMap{BigFloat}(Int[],[2],Union{Nothing,BigFloat}[high,nothing],fill(JSimplex.FREE_NONBASIC,2),0)
   y=JSimplex.postsolve_primal(m,BigFloat[high])
   @test all(v->precision(v)==320,y)
   @test y==[high,high]
  end
 end
end
