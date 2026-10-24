using Test, JSimplex, LinearAlgebra, SparseArrays, TOML
const TP=JSimplex
const TP_DATA=TOML.parsefile(joinpath(@__DIR__,"fixtures","native_terminal_primal.toml"))
tp_bits(s)=reinterpret(Float32,parse(UInt32,s;base=16))
function tp_workspace(T; manager=:huangfu_hall,budget=3,observer=nothing,extra=false)
    A=sparse(Matrix{T}(I,32,32)+fill(T(1)/T(128),32,32))
    extra && (A=hcat(A,spzeros(T,32,1)))
    n=size(A,2)
    p=LinearProblem(A,ones(T,n);row_lower=ones(T,32))
    o=SolverOptions(T;algorithm=:dual,basis_update=manager,basis_refactorization=:native,
        presolve=false,scaling=:off,verbose=false)
    d=TP.SimplexDiagnostics(;observer,kernel_timing=true)
    policy=TP.NumericalPolicy(T;max_refinements=budget)
    ws=TP.initialize_workspace(p,o;progress=TP.SimplexProgressContext(p;numerical_policy=policy,diagnostics=d))
    ws.basis=TP.Basis(collect(1:32),vcat(fill(TP.BASIC,32),fill(TP.AT_LOWER,n)))
    TP.recompute!(ws;refactorize=true)
    ws.primal[1:32] .= T.(tp_bits.(TP_DATA["after"]["point_bits"][1:32]))
    ws.primal[n+1:end] .= one(T)
    extra && (ws.primal[33]=-one(T))
    ws,d
end
function tp_state(ws)
    deepcopy((ws.primal,ws.costs,ws.lower,ws.upper,ws.reduced_costs,ws.scratch.rho,
        ws.basis.basic_indices,ws.basis.states,ws.iterations,ws.refactorizations,
        ws.options,ws.problem.A.colptr,ws.problem.A.rowval,ws.problem.A.nzval))
end
@testset "Saved terminal primal is corrected privately and certified" begin
    for T in (Float32,Float64), manager in (:pfi,:huangfu_hall), observing in (false,true)
        calls=Ref(0);observer=observing ? ((reason,ws)->(calls[]+=1;nothing)) : nothing
        ws,d=tp_workspace(T;manager,observer)
        @test !TP._original_primal_feasible(ws,ws.primal[1:32])
        before=tp_state(ws);owners=(ws.primal,ws.basis,ws.basis.basic_indices,ws.basis.states,ws.factorization)
        f=d.kernel_calls[:ftran];r=TP._internal_solution(ws,OPTIMAL,"saved point")
        @test r.status==OPTIMAL
        @test d.kernel_calls[:ftran]-f==1
        @test tp_state(ws)==before
        @test owners==(ws.primal,ws.basis,ws.basis.basic_indices,ws.basis.states,ws.factorization)
        @test all(owners[i]===((ws.primal,ws.basis,ws.basis.basic_indices,ws.basis.states,ws.factorization)[i]) for i in 1:5)
        if r.status==OPTIMAL
            x=Rational{BigInt}.(r.primal);tau=Rational{BigInt}(ws.options.primal_tolerance)
            @test all(v+sum(x)/128>=1-tau for v in x)
            @test TP._original_primal_feasible(ws.problem,r.primal,ws.options.primal_tolerance)
            @test r.objective_value==dot(ws.problem.objective,r.primal)+ws.problem.objective_constant
            @test r.basis.basic_indices==collect(1:32)
            @test r.primal !== ws.primal
        end
        observing && (@test calls[]>0)
    end
end
@testset "Terminal correction retains true rejection and zero budgets" begin
    for T in (Float32,Float64), mode in (:budget,:nonbasic,:deadline,:checked)
        ws,d=tp_workspace(T;budget=mode==:budget ? 0 : 3,extra=mode==:nonbasic)
        mode==:deadline && (ws.options=TP._remaining_options(ws.options;iterations=0,time_limit=0.0))
        if mode==:checked
            TP._install_driver_policy!(ws,TP.NumericalPolicy(T;numerical_profile=:checked))
        end
        before=tp_state(ws);f=d.kernel_calls[:ftran]
        r=TP._internal_solution(ws,OPTIMAL,"rejected point")
        @test r.status==NUMERICAL_ERROR
        @test r.primal===nothing && r.objective_value===nothing && r.basis===nothing
        @test tp_state(ws)==before
        @test d.kernel_calls[:ftran]-f==(mode==:nonbasic ? 1 : 0)
    end
end
@testset "Already feasible terminal point avoids primal correction" begin
    for T in (Float32,Float64)
        ws,d=tp_workspace(T)
        ws.primal[1:32] .= T(4)/T(5)
        f=d.kernel_calls[:ftran]
        @test TP._internal_solution(ws,OPTIMAL,"valid point").status==OPTIMAL
        @test d.kernel_calls[:ftran]==f
    end
end
@testset "Ordinary original O solves and public results" begin
    for T in (Float32,Float64)
        ws,d=tp_workspace(T);p=ws.problem;o=ws.options
        result=TP._solve_continuous_dual(p,o)
        @test result.status==OPTIMAL
        if result.status==OPTIMAL
            @test TP._original_primal_feasible(p,result.primal,o.primal_tolerance)
            @test result.iterations==32
            @test result.refactorizations==1
        end
        public=TP.solve(p;options=o)
        @test public.status==OPTIMAL
        if public.status==OPTIMAL
            @test TP._original_primal_feasible(p,public.primal,o.primal_tolerance)
        end
    end
end

@testset "Private correction updates basic row activities and fixes no nonbasic" begin
    for T in (Float32,Float64)
        A=sparse(Matrix{T}(I,32,32)+fill(T(1)/T(128),32,32))
        A=blockdiag(A,sparse(ones(T,1,1)))
        lower=zeros(T,33);lower[33]=one(T)
        p=LinearProblem(A,ones(T,33);column_lower=lower,row_lower=ones(T,33))
        o=SolverOptions(T;algorithm=:dual,presolve=false,scaling=:off,basis_update=:huangfu_hall,verbose=false)
        ws=TP.initialize_workspace(p,o)
        ws.basis=TP.Basis(vcat(collect(1:32),66),vcat(fill(TP.BASIC,32),fill(TP.AT_LOWER,33),TP.BASIC))
        TP.recompute!(ws;refactorize=true)
        ws.primal[1:32] .= T.(tp_bits.(TP_DATA["after"]["point_bits"][1:32]))
        ws.primal[66]=one(T)-T(8)*eps(T)
        before=copy(ws.primal)
        trial=TP._native_terminal_primal_candidate(ws,()->false)
        @test trial!==nothing
        if trial!==nothing
            @test trial[66]==one(T)
            @test trial[33:65]==before[33:65]
            @test all(isfinite,trial)
        end
        @test ws.primal==before
    end
end
@testset "Certification observers retain original-model rejection" begin
    for T in (Float32,Float64)
        observer=(reason,ws)->begin
            reason==:certification && (ws.problem.row_lower[1]=TP.Bound(T(2)))
            nothing
        end
        ws,d=tp_workspace(T;observer)
        @test TP._internal_solution(ws,OPTIMAL,"caller changed bound").status==NUMERICAL_ERROR
    end
end
