using JSimplex, SparseArrays
const JS=JSimplex
Core.eval(JS, :(const PCW_PRODUCTS = Ref(0)))
source=read(joinpath(dirname(pathof(JS)),"primal_row_certification.jl"),String)
ex,_=Meta.parse(source,first(findfirst("function _native_row_product_pair(",source)))
insert!(ex.args[2].args,1,:(PCW_PRODUCTS[] += 1))
Core.eval(JS,Expr(:macrocall,Symbol("@inline"),LineNumberNode(0),ex))
function main()
 for T in (Float32,Float64)
  n=128;a=T(0.1)
  A=sparse(repeat(collect(1:n),3),vcat(fill(1,n),fill(2,n),fill(3,n)),vcat(fill(a,n),fill(-a,n),ones(T,n)),n,3)
  p=LinearProblem(A,zeros(T,3);row_lower=ones(T,n),row_upper=ones(T,n))
  w=JS._initialize_workspace_state(p,SolverOptions(T;algorithm=:primal,primal_tolerance=eps(T)^2))
  w.primal[1:3]=T[3,3,1];w.primal[4:end].=one(T)
  for repeat in 1:2
   JS.PCW_PRODUCTS[]=0
   @assert JS._legacy_primal_point_certified(w)
   println(T," products=",JS.PCW_PRODUCTS[]," expected=",3n);flush(stdout)
   @assert JS.PCW_PRODUCTS[]==3n
  end
 end
end
Base.invokelatest(main)
