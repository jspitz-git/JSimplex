using JSimplex, Test, SparseArrays, LinearAlgebra, TOML, SHA
const ROOT=dirname(dirname(pathof(JSimplex)))
const INPUT=joinpath(ROOT,"diagnostics/simplex-core-architecture/results/S6-S/qualify-1-report.toml")
const REPORT=TOML.parsefile(INPUT)
const CONTROL=only(filter(x->x["type"]=="Float64",REPORT["records"]))
rat(s)=begin
    v=split(s,"//");parse(BigInt,v[1])//(length(v)==1 ? BigInt(1) : parse(BigInt,v[2]))
end
function val(v)
    q=rat(v["exact"]);x=Float64(q);@assert Rational{BigInt}(x)==q;x
end
str(x::Real)=isfinite(x) ? string(Rational{BigInt}(x)) : repr(x)
strings(x)=str.(vec(x))
const MODEL=CONTROL["model_before"]
A=SparseMatrixCSC(2,2,MODEL["colptr"],MODEL["rowval"],val.(MODEL["matrix"]))
problem=LinearProblem(A,val.(MODEL["objective"]);
 row_lower=val.(MODEL["bounds"]["row_lower"]),row_upper=val.(MODEL["bounds"]["row_upper"]),column_lower=[nothing,nothing])
opts=SolverOptions(Float64)
@assert Dict(string(k)=>repr(getfield(opts,k)) for k in fieldnames(typeof(opts)))==CONTROL["options"]
@assert CONTROL["policy"]["hypersparse"]==CONTROL["policy"]["solve_refinement"]=="false"
@assert Threads.nthreads()==BLAS.get_num_threads()==1
@assert precision(BigFloat)==256 && rounding(BigFloat)==RoundNearest
# One standalone scaling operation from immutable candidate input; no solver or workspace.
scaled,scaling=JSimplex.scale_problem(problem)
B=copy(scaled.A)
rhs=[bound_value(scaled.row_lower[1]),bound_value(scaled.row_upper[2])]
dual_rhs=copy(scaled.objective)
originalB=copy(B); original_rhs=copy(rhs); original_dual=copy(dual_rhs)
factor=JSimplex._basis_factorization(B,opts)
@assert factor isa JSimplex.PFIFactorization{Float64,JSimplex.UMFPACKBackend}
f=factor.base.factorization
control=copy(getfield(f,:control))
x=zeros(2);dual=zeros(2)
JSimplex._ordinary_forward_solve!(x,factor,rhs)
JSimplex.transpose_solve!(dual,factor,dual_rhs)
L,U,p,q,Rs=getproperty(f,Symbol(":")) # Supported owned arrays, AFTER both solves.
rec=Dict("matrix"=>strings(Matrix(B)),"original_matrix"=>strings(Matrix(A)),
 "rhs"=>strings(rhs),"dual_rhs"=>strings(dual_rhs),"primal"=>strings(x),"dual"=>strings(dual),
 "row_scaling"=>strings(scaling.row_factors),"column_scaling"=>strings(scaling.column_factors),
 "L"=>strings(Matrix(L)),"U"=>strings(Matrix(U)),"p"=>p,"q"=>q,"Rs"=>strings(Rs),
 "control_before"=>strings(control),"control_after"=>strings(getfield(f,:control)),
 "refinement_steps"=>getfield(f,:control)[SparseArrays.UMFPACK.JL_UMFPACK_IRSTEP],
 "scaling_mode"=>getfield(f,:control)[SparseArrays.UMFPACK.JL_UMFPACK_SCALE],
 "input_unchanged"=>B==originalB && rhs==original_rhs && dual_rhs==original_dual,
 "updates"=>length(factor.updates),"factorizations"=>1,"ftran_calls"=>1,"btran_calls"=>1)
@assert !ispath(only(ARGS))
try
 @testset "Row-balanced candidate component" begin
  @test rec["input_unchanged"]
  @test rec["control_before"]==rec["control_after"]
  @test rec["updates"]==0
  @test strings(JSimplex.unscale_primal(scaling,x))==[v["exact"] for v in CONTROL["primal"]]
  @test rec["column_scaling"]==["1//1","1//1"]
  @test rec["row_scaling"]==fill("1//2097152",2)
 end
finally
 open(only(ARGS),"w") do io
  TOML.print(io,Dict("source"=>pathof(JSimplex),"input_sha256"=>bytes2hex(sha256(read(INPUT))),
   "julia_version"=>string(VERSION),"arch"=>string(Sys.ARCH),"julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),
   "globals_preserved"=>precision(BigFloat)==256 && rounding(BigFloat)==RoundNearest,
   "options"=>Dict(string(k)=>repr(getfield(opts,k)) for k in fieldnames(typeof(opts))),"record"=>rec,
   "scope"=>"New single Float64 scaled basis component; no public solve, workspace or captured runtime factor. Two basis solves; metadata after solves."))
 end
end
