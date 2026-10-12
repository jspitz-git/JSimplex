using JSimplex,Test,SparseArrays,LinearAlgebra,TOML,SHA
const JS=JSimplex
const ROOT=dirname(dirname(pathof(JS)))
const INPUT=joinpath(ROOT,"diagnostics/simplex-core-architecture/results/S6-AE/inputs.toml")
const DATA=TOML.parsefile(INPUT)
rat(s)=begin p=split(s,"/");parse(BigInt,p[1])//(length(p)==1 ? big(1) : parse(BigInt,p[2])) end
rf(s)=begin q=rat(s);x=Float64(q);@assert Rational{BigInt}(x)==q;x end
ex(x)=string(Rational{BigInt}(x))
vex(x)=ex.(vec(x))
bits(x)=string.(reinterpret(UInt64,vec(x));base=16,pad=16)
fields(x)=Dict(string(k)=>repr(getfield(x,k)) for k in fieldnames(typeof(x)))
bound(b)=Dict("finite"=>isfinite(b),"value"=>isfinite(b) ? ex(JS.bound_value(b)) : "infinite")
kernels(d)=Dict(string(k)=>get(d.kernel_calls,k,0) for k in (:ftran,:btran,:refactorization))
const GLOBALS=(precision(BigFloat),rounding(BigFloat),rounding(Float64),get_zero_subnormals())
@assert GLOBALS==(256,RoundNearest,RoundNearest,false) && Threads.nthreads()==BLAS.get_num_threads()==1
@assert !ispath(only(ARGS))
B=sparse(reduce(vcat,permutedims.(map(row->rf.(row),DATA["B"]))))
rhs=-Vector(B[:,2]);p=LinearProblem(sparse(hcat(B,B[:,1])),zeros(5);row_lower=rhs,row_upper=rhs)
options=SolverOptions(algorithm=:dual,simplex_strategy=:legacy,basis_update=:pfi,pricing=:dantzig,verbose=false)
policy=JS.NumericalPolicy(Float64)
d=JS.SimplexDiagnostics(;kernel_timing=true)
@assert isnothing(d.observer) && !policy.pivot_validation && !policy.recovery && !policy.solve_refinement && !policy.hypersparse
ws=JS.initialize_workspace(p,options;progress=JS.SimplexProgressContext(p;numerical_policy=policy,diagnostics=d))
ws.basis.basic_indices .= 1:4;ws.basis.states[1:4] .= JS.BASIC;ws.basis.states[6:9] .= JS.AT_LOWER
JS.recompute!(ws;refactorize=true)
model_before=fields(p);options_before=fields(options);policy_before=fields(policy)
before=(copy(ws.primal),copy(ws.basis.basic_indices),copy(ws.basis.states),ws.iterations,ws.refactorizations)
setup=kernels(d);initial_counts=copy(d.counts);factor=ws.factorization
rec=Dict{String,Any}("source"=>pathof(JS),"input_sha256"=>bytes2hex(sha256(read(INPUT))),"input"=>DATA,
  "public_calls"=>0,"setup_kernels"=>setup,"options"=>options_before,"policy"=>policy_before,
  "julia_version"=>string(VERSION),"arch"=>string(Sys.ARCH),"julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),
  "error"=>"none","global_precision"=>GLOBALS[1],"global_rounding"=>string(GLOBALS[2]))
try
    rec["public_calls"]+=1
    terminal=JS.dual_iteration!(ws,()->false)
    # Owned copies immediately after public return; no numerical helper calls.
    rec["rho"]=vex(copy(ws.scratch.rho));rec["rho_bits"]=bits(copy(ws.scratch.rho))
    rec["tableau"]=vex(copy(ws.scratch.tableau_row));rec["selected_row"]=ws.scratch.selected_row
    rec["selected_entering"]=ws.scratch.selected_entering
    rec["status"]=isnothing(terminal) ? "nothing" : string(terminal.status)
    rec["message"]=isnothing(terminal) ? "nothing" : terminal.message
    rec["primal"]=vex(copy(ws.primal));rec["basis"]=copy(ws.basis.basic_indices);rec["states"]=string.(ws.basis.states)
    rec["lower"]=bound.(ws.lower);rec["upper"]=bound.(ws.upper)
    rec["matrix_colptr"]=copy(p.A.colptr);rec["matrix_rowval"]=copy(p.A.rowval);rec["matrix_values"]=vex(copy(p.A.nzval));rec["matrix_bits"]=bits(copy(p.A.nzval))
    rec["column_scaling"]=vex(copy(ws.progress.scaling.column_factors));rec["row_scaling"]=vex(copy(ws.progress.scaling.row_factors))
    rec["iterations"]=ws.iterations;rec["refactor_delta"]=ws.refactorizations-before[5]
    rec["kernels"]=Dict(k=>v-setup[k] for (k,v) in kernels(d))
    rec["event_delta"]=Dict(string(k)=>v-initial_counts[k] for (k,v) in d.counts)
    rec["observer_absent"]=isnothing(d.observer);rec["factor_type"]=string(typeof(factor));rec["factor_preserved"]=ws.factorization===factor
    rec["model_preserved"]=fields(p)==model_before;rec["options_preserved"]=fields(options)==options_before && fields(policy)==policy_before
    rec["selected_state_preserved"]=(ws.primal,ws.basis.basic_indices,ws.basis.states,ws.iterations)==before[1:4]
    rec["globals_preserved"]=(precision(BigFloat),rounding(BigFloat),rounding(Float64),get_zero_subnormals())==GLOBALS
    @testset "One real dual certificate row provenance" begin
        @test !isnothing(terminal) && terminal.status==JS.NUMERICAL_ERROR
        @test rec["message"]=="row combination does not certify infeasibility at primal tolerance"
        @test rec["kernels"]==Dict("ftran"=>1,"btran"=>3,"refactorization"=>1)
        @test rec["rho"]==ex.(rf.(DATA["exact_rho"]))
        @test rec["selected_row"]==2 && rec["selected_entering"] == -1
        @test rec["selected_state_preserved"] && rec["iterations"]==0 && rec["refactor_delta"]==1
        @test rec["model_preserved"] && rec["options_preserved"]
        @test rec["observer_absent"] && rec["factor_preserved"] && factor isa JS.PFIFactorization
        @test all(rec["event_delta"][k]==0 for k in ("correction_attempt","pivot_rejected","pivot_completed","bound_flipped"))
        @test rec["globals_preserved"]
    end
catch exception
    rec["error"]=sprint(showerror,exception);rethrow()
finally
    open(only(ARGS),"w") do io;TOML.print(io,rec);end
end
