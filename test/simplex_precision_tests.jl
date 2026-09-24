using Test,JSimplex,SparseArrays,LinearAlgebra

@testset "Working precision transfer interfaces" begin
    @test isdefined(JSimplex,:copy_working_values)
    @test isdefined(JSimplex,:transfer_precision)
end

# Canonical exact binary values compare model contents across storage types.
function precision_model_key(p)
    exact(v)=Rational{BigInt}.(v)
    bounds(v)=[isfinite(b) ? Rational{BigInt}(bound_value(b)) : nothing for b in v]
    return hash((size(p.A),p.A.colptr,p.A.rowval,exact(p.A.nzval),exact(p.objective),
        Rational{BigInt}(p.objective_constant),p.objective_sense,
        bounds(p.column_lower),bounds(p.column_upper),bounds(p.row_lower),bounds(p.row_upper),
        p.variable_domains,p.name,p.row_names,p.column_names))
end

if isdefined(JSimplex,:copy_working_values) && isdefined(JSimplex,:transfer_precision)
    @testset "Precision copies preserve stored values and own storage" begin
        v=setprecision(BigFloat,512) do
            [BigFloat(1)+BigFloat(2)^(-200)]
        end
        for requested in (128,512,768)
            copied=setprecision(BigFloat,64) do
                JSimplex.copy_working_values(BigFloat,v;bits=requested)
            end
            @test copied==v
            @test precision(only(copied))>=max(512,requested)
            @test copied!==v && only(copied)!==only(v)
        end
        values=[0.1,nextfloat(1.0),floatmin(Float64),nextfloat(0.0),-3.5]
        wide=JSimplex.copy_working_values(BigFloat,values;bits=128)
        @test Rational{BigInt}.(wide)==Rational{BigInt}.(values)
        small=Float32[0.1,nextfloat(1f0),floatmin(Float32)]
        @test Rational{BigInt}.(JSimplex.copy_working_values(Float64,small;bits=53))==Rational{BigInt}.(small)
        limits=[Bound(only(v)),Bound{BigFloat}(nothing)]
        copied=setprecision(BigFloat,64) do
            JSimplex.copy_working_values(BigFloat,limits;bits=128)
        end
        @test copied==limits && copied!==limits
        @test precision(bound_value(copied[1]))>=512
        @test !isfinite(copied[2])
        A=sparse([1,2],[2,1],values[1:2],2,2)
        B=JSimplex.copy_working_values(BigFloat,A;bits=128)
        @test B isa SparseMatrixCSC{BigFloat,Int}
        @test B==A && B.colptr!==A.colptr && B.rowval!==A.rowval && B.nzval!==A.nzval
        @test JSimplex.copy_working_values(BigFloat,Float64[];bits=128)==BigFloat[]
        @test_throws ArgumentError JSimplex.copy_working_values(Float32,[1.0];bits=24)
        @test_throws ArgumentError JSimplex.copy_working_values(Float64,v;bits=53)
        @test_throws ArgumentError JSimplex.copy_working_values(BigFloat,[1//big(2)];bits=128)
        @test_throws ArgumentError JSimplex.copy_working_values(BigFloat,values;bits=1)
        exact=[1//big(3),2//big(7)]
        copied=JSimplex.copy_working_values(Rational{BigInt},exact;bits=0)
        @test copied==exact && copied!==exact
    end

    @testset "Transfer rebuilds the actual typed basis and retains cumulative work" begin
        for (T,S,bits) in ((Float32,Float64,53),(Float64,BigFloat,128),(BigFloat,BigFloat,512)),
            update in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub), backend in (:native,:markowitz)
            p=LinearProblem(sparse(T[2 1;1 3]),T[1,2];objective_constant=T(3.5),
                objective_sense=MAX_SENSE,column_lower=[Bound(zero(T)),Bound{T}(nothing)],
                column_upper=[Bound(T(2)),Bound{T}(nothing)],row_lower=T[2,0],row_upper=T[2,0],
                name="precision",row_names=["first","second"],column_names=["boxed","free"])
            options=SolverOptions(T;verbose=false,presolve=false,iteration_limit=30,
                basis_update=update,basis_refactorization=backend,pricing=:devex)
            policy=JSimplex.NumericalPolicy(T;simplex_strategy=:adaptive,phase_one=true,crash=true,
                sparse_pricing=true,hypersparse=true,refactor_timing=false,max_refinements=4,
                max_recovery_rounds=5,stagnation_window=8)
            progress=JSimplex.SimplexProgressContext{T,Nothing}(time_ns(),T[2,3,4,5],T(7),
                JSimplex.Scaling(T[2,4],T[0.5,2]),7,11,nothing,policy)
            basis=JSimplex.Basis([1,2],[JSimplex.BASIC,JSimplex.BASIC,JSimplex.AT_LOWER,JSimplex.AT_LOWER])
            ws=JSimplex.initialize_from_basis(p,basis,options;policy,progress)
            ws.iterations=3;ws.refactorizations=5
            budget=JSimplex.SimplexRunBudget(ws)
            budget.iterations=12;budget.refactorizations=20
            old_key=precision_model_key(p)
            saved=copy(ws.primal)
            fresh=JSimplex.transfer_precision(ws,S,bits,budget,policy)
            @test fresh isa JSimplex.SimplexWorkspace{S}
            @test fresh.problem!==p && precision_model_key(fresh.problem)==old_key
            @test precision_model_key(p)==old_key && ws.primal==saved
            @test fresh.problem.objective_sense==MAX_SENSE && fresh.problem.objective_constant==p.objective_constant
            @test fresh.basis.basic_indices==basis.basic_indices && fresh.basis.states==basis.states
            @test fresh.basis.basic_indices!==ws.basis.basic_indices && fresh.basis.states!==ws.basis.states
            @test fresh.costs==ws.costs && fresh.costs!==ws.costs
            @test fresh.lower==ws.lower && fresh.upper==ws.upper
            @test fresh.lower!==ws.lower && fresh.upper!==ws.upper
            @test fresh.factorization!==ws.factorization
            @test fresh.scratch!==ws.scratch
            @test all(c->JSimplex._checkpoint_matches(fresh,c) &&
                c.working_model!=JSimplex._checkpoint_model(ws),fresh.scratch.checkpoints)
            @test fresh.primal≈saved rtol=32eps(T)
            rhs=S[3,4];x=zeros(S,2)
            JSimplex.forward_solve!(x,fresh.factorization,rhs)
            @test JSimplex.basis_matrix(fresh)*x≈rhs
            @test JSimplex._recomputed_basis_reliable(fresh)
            @test fresh.iterations==ws.iterations==5
            @test fresh.refactorizations==ws.refactorizations==10
            @test budget.iterations==12 && budget.refactorizations==21
            @test fresh.progress.start_ns==progress.start_ns
            @test fresh.progress.iteration_offset==7 && fresh.progress.refactorization_offset==11
            @test fresh.progress.objective==progress.objective && fresh.progress.objective!==progress.objective
            @test fresh.progress.objective_constant==7
            @test fresh.progress.scaling.row_factors==progress.scaling.row_factors
            @test fresh.progress.scaling.column_factors==progress.scaling.column_factors
            @test fresh.progress.scaling.column_factors!==progress.scaling.column_factors
            @test fresh.options.iteration_limit==options.iteration_limit
            @test fresh.options.primal_tolerance==options.primal_tolerance
            @test fresh.options.dual_tolerance==options.dual_tolerance
            @test fresh.options.zero_tolerance==options.zero_tolerance
            @test fresh.options.basis_update==update && fresh.options.basis_refactorization==backend
            for field in fieldnames(typeof(policy))
                @test getfield(fresh.progress.numerical_policy,field)==getfield(policy,field)
            end
            if S===BigFloat
                @test minimum(precision,fresh.problem.A.nzval)>=bits
                @test minimum(precision,fresh.primal)>=bits
                @test fresh.options.primal_tolerance!==ws.options.primal_tolerance
                @test fresh.progress.numerical_policy.solve_tolerance!==policy.solve_tolerance
            end
        end
    end
end
