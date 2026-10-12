using JSimplex, SparseArrays, LinearAlgebra, TOML, SHA, Test
const JS=JSimplex
fields(x)=Dict(string(k)=>repr(getfield(x,k)) for k in fieldnames(typeof(x)))
bits(x)=string.(reinterpret(UInt32,x);base=16,pad=8)
function bound_data(x)
 Dict("finite"=>isfinite.(x),"values"=>[isfinite(v) ? Float64(JS.bound_value(v)) : 0.0 for v in x])
end
function model_data(p)
 Dict("colptr"=>copy(p.A.colptr),"rowval"=>copy(p.A.rowval),"nzval"=>Float64.(p.A.nzval),"objective"=>Float64.(p.objective),
 "column_lower"=>bound_data(p.column_lower),"column_upper"=>bound_data(p.column_upper),"row_lower"=>bound_data(p.row_lower),"row_upper"=>bound_data(p.row_upper))
end
function main(input,output)
 @assert !ispath(output)
 data=TOML.parsefile(input)
 A=sparse(reduce(vcat,permutedims.(Float32.(row) for row in data["matrix"])))
 rhs=Float32.(data["rhs"])
 p=LinearProblem(A,Float32.(data["costs"]);row_lower=rhs,row_upper=rhs)
 options=SolverOptions(Float32;algorithm=:primal,basis_update=:pfi,basis_refactorization=:native,verbose=false)
 policy=JS.NumericalPolicy(Float32;max_refinements=3)
 before=model_data(p);op=fields(options);pol=fields(policy)
 globals=(precision(BigFloat),rounding(BigFloat),get_zero_subnormals())
 records=Dict[]
 @testset "S6-Y immutable point component contract" begin
  for entry in data["points"]
   x=collect(reinterpret(Float32,parse.(UInt32,entry["bits"];base=16)))
   original=bits(x)
   scratch=JS.SolveQualityScratch(Float32,6)
   quality=JS.solve_quality!(scratch,A,x,rhs,policy)
   certified=JS._original_primal_feasible(p,x,options.primal_tolerance)
   push!(records,Dict("name"=>entry["name"],"input_bits"=>original,"output_bits"=>bits(x),"point"=>Float64.(x),
    "quality"=>fields(quality),"quality_absolute"=>Float64(quality.absolute_error),"quality_relative"=>Float64(quality.relative_error),
    "quality_finite"=>quality.finite,"quality_reliable"=>quality.reliable,"quality_residual"=>Float64.(scratch.residual),
    "original_primal_feasible"=>certified,"quality_calls"=>1,"certificate_calls"=>1))
   @test original==entry["bits"]==bits(x)
   @test before==model_data(p)
   @test op==fields(options) && pol==fields(policy)
   @test globals==(precision(BigFloat),rounding(BigFloat),get_zero_subnormals())
  end
 end
 open(output,"w") do io
  TOML.print(io,Dict("source"=>pathof(JS),"input_sha256"=>bytes2hex(sha256(read(input))),"driver_sha256"=>bytes2hex(sha256(read(@__FILE__))),
   "model"=>before,"options"=>op,"policy"=>pol,"primal_tolerance"=>Float64(options.primal_tolerance),"solve_tolerance"=>Float64(policy.solve_tolerance),
   "records"=>records,"julia_version"=>string(VERSION),"arch"=>string(Sys.ARCH),"julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),
   "globals_preserved"=>globals==(precision(BigFloat),rounding(BigFloat),get_zero_subnormals()),"model_preserved"=>before==model_data(p)))
 end
end
main(ARGS...)
