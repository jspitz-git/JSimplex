using JSimplex, SparseArrays, LinearAlgebra, TOML
function main(output)
 records=[]
 for name in (:ForrestTomlinFactorization,:SuhlSuhlFactorization,:BartelsGolubFactorization), tiny in (1e-8,1e-12,1e-16)
  B=sparse(Matrix{Float64}(I,2,2));f=getproperty(JSimplex,name)(B)
  for (row,a) in ((1,[tiny,1.0]),(2,[1.0,1.0]))
   d=JSimplex.forward_solve(f,a);JSimplex.replace_column!(f,d,row;zero_tolerance=0.0);B[:,row]=a
  end
  for b in ([1.0,0.0],[0.0,1.0],[1.0,1.0]), transposed in (false,true)
   x=transposed ? JSimplex.transpose_solve(f,b) : JSimplex.forward_solve(f,b)
   M=transposed ? transpose(B) : B
   r=Dict("manager"=>string(name),"tiny"=>tiny,"rhs"=>b,"transpose"=>transposed,"x"=>x,
      "residual"=>norm(M*x-b,Inf)/(opnorm(M,Inf)*norm(x,Inf)+norm(b,Inf)),
      "reference"=>Vector(M\b),"maximum_upper"=>maximum(c->maximum(abs,c.values;init=0.0),f.upper))
   push!(records,r);println(r)
  end
 end
 open(output,"w") do io;TOML.print(io,Dict("records"=>records));end
end
Base.invokelatest(main,ARGS...)
