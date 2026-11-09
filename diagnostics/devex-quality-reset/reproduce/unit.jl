include("common.jl")
include("policy.jl")
const seen_raw=Ref(NaN)
quality_observed(ws,raw,stored,computed,bad,row)=(seen_raw[]=raw;nothing)
deadline()=JS._guard_stop_callback(JS._SolveDeadline(time_ns(),Inf))
function workspace(;interval=160)
    lp=LinearProblem(sparse([1.0 0.0;0.0 1.0]),[1.0,10.0];row_lower=[1.0,-Inf])
    JS.initialize_workspace(lp,opts(100;interval))
end
# Behavioural RED is the same real pivot with the original off arm.
w=workspace(); w.pricing_weights .= 1000.0
before=quality_counts[5]
terminal=JS.dual_iteration!(w,deadline())
observed=isnothing(terminal) && all(==(1.0),w.pricing_weights) && quality_counts[5]==before+1
if mode=="off"
    open(io->TOML.print(io,Dict("expected_original_failure"=>!observed,
        "passed"=>observed,"ordinary_pivot_completed"=>isnothing(terminal),
        "iterations"=>w.iterations)),output,"w")
    @testset "Original Devex does not reset on finite bad estimate" begin
        @test observed
    end
else
    @testset "Actual accepted pivot triggers deferred reset" begin
        @test observed
        @test w.iterations==1 && w.refactorizations==0
        @test JS._finite_workspace(w)
        @test findall(w.devex_reference)==sort(w.basis.basic_indices)
        @test JS._dual_optimize!(w,deadline()).status==OPTIMAL
    end
    @testset "Independent tiny reference-frame norm" begin
        lp=LinearProblem(sparse([2.0 3.0;1.0 4.0]),[1.0,2.0])
        v=JS.initialize_workspace(lp,opts(100))
        v.basis.basic_indices .= [1,2]
        v.scratch.selected_row=1
        fill!(v.devex_reference,false);v.devex_reference[[1,4]].=true
        B=Matrix(lp.A)
        r=transpose(B)\[1.0,0.0]
        JS.price!(v.scratch.tableau_row,v,r)
        expected=sum(abs2,transpose(r)*hcat(Matrix(lp.A),-Matrix{Float64}(I,2,2))[:,[1,4]])
        seen_raw[]=NaN
        JS.update_devex!(v,v.scratch.tableau_row,[0.5,1.5],3,0.5)
        @test seen_raw[]≈expected
        @test v.pricing_weights[3]≈max(1.0,expected/0.25)
    end
    @testset "Threshold and invalid operands" begin
        @test !quality_bad(9.0,1.0)
        @test !quality_bad(1.0,9.0)
        @test quality_bad(nextfloat(9.0),1.0)
        @test quality_bad(1.0,nextfloat(9.0))
        @test quality_bad(floatmax(Float64),floatmin(Float64))
        for x in (0.0,-1.0,Inf,-Inf,NaN)
            @test !quality_bad(x,1.0) && !quality_bad(1.0,x)
        end
        w=workspace();w.scratch.selected_row=1;w.pricing_weights.=10
        observe_reference!(w,0.25)
        @test quality_state(w).requested # compared against max(1, 0.25)
    end
    @testset "No reset across failed or invalidated attempts" begin
        for kind in (:terminal,:stage,:refactor,:phase,:reset,:callback,:alias,:rejected_index)
            w=workspace();w.scratch.selected_row=1;w.pricing_weights.=1000
            observe_reference!(w,1.0)
            index=w.basis.basic_indices[1]
            w.iterations+=1
            stop=deadline(); result=nothing
            if kind==:terminal
                result=JS._numerical_failure()
            elseif kind==:stage || kind==:rejected_index
                index=0
            elseif kind==:refactor
                w.refactorizations+=1
            elseif kind==:phase
                w.scratch.phase_generation+=1
            elseif kind==:reset
                JS.reset_devex!(w)
            elseif kind==:callback
                stop=JS._guard_stop_callback(()->false)
            elseif kind==:alias
                w.costs=w.pricing_weights
            end
            old=quality_counts[5]
            @test finish_quality!(w,result,stop,index)===result
            @test quality_counts[5]==old
            @test quality_state(w).iteration==-1
        end
        w=workspace(); c=JS._candidate_workspace(w); c.scratch.selected_row=1
        c.pricing_weights.=1000;old=quality_counts[1]
        observe_reference!(c,1.0)
        @test quality_counts[1]==old && !haskey(quality_states,c)
    end
    @testset "Preserved state, finite guard and refactor reset" begin
        w=workspace();w.scratch.selected_row=1;w.pricing_weights.=1000
        observe_reference!(w,1.0); index=w.basis.basic_indices[1];w.iterations+=1
        fields=(:primal,:reduced_costs,:costs,:lower,:upper)
        saved=Dict(k=>copy(getproperty(w,k)) for k in fields)
        basis=copy(w.basis.basic_indices); states=copy(w.basis.states)
        @test isnothing(finish_quality!(w,nothing,deadline(),index))
        @test all(isequal(saved[k],getproperty(w,k)) for k in fields)
        @test basis==w.basis.basic_indices && states==w.basis.states
        @test all(==(1.0),w.pricing_weights) && JS._finite_workspace(w)
        w=workspace();w.pricing_weights.=1000;w.primal[end]=NaN;old=quality_counts[5]
        @test JS.dual_iteration!(w,deadline()).status==NUMERICAL_ERROR
        @test quality_counts[5]==old
        w=workspace(;interval=1); w.pricing_weights.=1000;old=quality_counts[5]
        @test JS._dual_optimize!(w,deadline()).status==OPTIMAL
        @test w.refactorizations>0 && quality_counts[5]==old
        w=workspace();w.scratch.selected_row=1;w.pricing_weights.=1000;observe_reference!(w,1.0)
        invalidate_quality!(w)
        @test quality_state(w).iteration==-1
        w=workspace(); w.scratch.selected_row=1;w.pricing_weights.=1000
        observe_reference!(w,1.0)
        @test JS._retry_simplex_step!(w,JS._guard_stop_callback(()->true),:dual,1e-7,false,true).status==TIME_LIMIT
        @test quality_state(w).iteration==-1
        observe_reference!(w,1.0)
        @test_throws ErrorException JS._retry_simplex_step!(w,JS._guard_stop_callback(()->error("unit stop")),:dual,1e-7,false,true)
        @test quality_state(w).iteration==-1
        @test all(fieldtype(QualityState,i)<:Union{Int,UInt,Bool} for i in 1:fieldcount(QualityState))
    end
    open(io->TOML.print(io,Dict("passed"=>true,"profile"=>profile,
        "counts"=>quality_counts_report())),output,"w")
end
