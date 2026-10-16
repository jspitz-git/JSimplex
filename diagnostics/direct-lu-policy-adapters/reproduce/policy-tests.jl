# UNEXECUTED. Include lifecycle-tests.jl first (helpers/fixtures); call explicitly
# only from a future independently admitted driver. No auto-run.

# A dropped policy can leave the enum intact but use default native controls.
# Inspect the REAL backend before extraction releases it. Empty native has no LU.
function policy_exporter(policy, seen; unavailable=false)
    return backend -> begin
        seen.calls += 1
        if backend isa JDL.UMFPACKBackend
            @test backend.pivot_policy === policy
            if isnothing(backend.factorization)
                @test JDL._backend_dimension(backend)==0
                seen.empty += 1
            else
                control = copy(backend.factorization.control)
                expected = SparseArrays.UMFPACK.get_umfpack_control(Float64,Int)
                pivot = SparseArrays.LibSuiteSparse.UMFPACK_PIVOT_TOLERANCE+1
                refine = SparseArrays.LibSuiteSparse.UMFPACK_IRSTEP+1
                if policy === JDL._NATIVE_PIVOT_ONE
                    expected[pivot] = 1.0
                    expected[refine] = 0.0
                end
                @test length(control)==length(expected)==20
                @test isequal(control,expected)
                # Actual strategy is an observation, not an unsymmetric guarantee.
                seen.strategy = backend.factorization.info[SparseArrays.LibSuiteSparse.UMFPACK_STRATEGY_USED+1]
                @test isfinite(seen.strategy)
                seen.nonempty += 1
            end
        else
            @test backend isa JDL.MarkowitzBackend{Float64}
            @test policy === JDL._NATIVE_PIVOT_DEFAULT
            seen.markowitz += 1
        end
        return unavailable ? nothing : JDL._export_basis_lu(backend)
    end
end
mutable struct PolicyObservations
    calls::Int
    empty::Int
    nonempty::Int
    markowitz::Int
    strategy::Float64
end
PolicyObservations() = PolicyObservations(0,0,0,0,NaN)

function test_policy_transitions()
    @testset "Policy survives empty/copy/refactor/fallback and real controls" begin
        for Factor in DIRECT_FACTORS, (R,policy) in DIRECT_ARMS, normalize in (false,true)
            seen=PolicyObservations(); exporter=policy_exporter(policy,seen)
            empty=spzeros(0,0); B=spdiagm(0=>[2.0,4.0]); before=_dl_matrix_snapshot(B)
            f=JDL._direct_lu_factor_with_exporter(Factor,empty,Val(R),policy,exporter;normalize)
            original_type=typeof(f)
            @test f.base.pivot_policy===policy
            @test f.base.normalize_requested===normalize
            @test length(f.work)==0
            JDL._direct_refactorize_with_exporter!(f,B,exporter)
            @test typeof(f)===original_type && f.base.pivot_policy===policy
            check_solutions(f,B,[2.0,4.0])
            saved=JDL.copy_basis_factorization(f)
            @test saved.base.pivot_policy===policy && saved.base.work!==f.base.work
            @test saved.work!==f.work && saved.spike!==f.spike
            resized=spdiagm(0=>[2.0,4.0,8.0])
            JDL._direct_refactorize_with_exporter!(f,resized,exporter)
            @test typeof(f)===original_type && length(f.work)==3
            @test length(saved.work)==2 && saved.base.pivot_policy===policy
            check_solutions(f,resized,[2.0,4.0,8.0]); check_solutions(saved,B,[2.0,4.0])
            fields=ntuple(i->getfield(f,i),fieldcount(typeof(f))); snapshot=_dl_factor_snapshot(f)
            calls=seen.calls
            @test_throws SingularException JDL._direct_refactorize_with_exporter!(f,singular_basis(),exporter)
            @test seen.calls==calls # singular LU throws before extraction
            @test all(getfield(f,i)===fields[i] for i in eachindex(fields))
            @test isequal(_dl_factor_snapshot(f),snapshot)
            # Force unsupported export only after real policy-aware factorization.
            JDL._direct_refactorize_with_exporter!(f,B,policy_exporter(policy,seen;unavailable=true))
            @test typeof(f)===original_type && JDL._direct_mode(f)===:fallback
            @test f.base.pivot_policy===policy
            check_solutions(f,B,[2.0,4.0])
            saved_fallback=JDL.copy_basis_factorization(f)
            @test saved_fallback.base.pivot_policy===policy
            @test saved_fallback.base.fallback!==f.base.fallback
            if R===:native
                @test saved_fallback.base.fallback.pivot_policy===policy
                @test isequal(saved_fallback.base.fallback.factorization.control,f.base.fallback.factorization.control)
            end
            fields=ntuple(i->getfield(f,i),fieldcount(typeof(f))); snapshot=_dl_factor_snapshot(f)
            sentinel=ErrorException("policy adapter export failure")
            failing = backend -> begin
                exporter(backend) # real controls and export checked before injected error
                throw(sentinel)
            end
            caught=try
                JDL._direct_refactorize_with_exporter!(f,resized,failing)
                nothing
            catch err
                err
            end
            @test caught===sentinel
            @test all(getfield(f,i)===fields[i] for i in eachindex(fields))
            @test isequal(_dl_factor_snapshot(f),snapshot)
            JDL._direct_refactorize_with_exporter!(f,resized,exporter)
            @test JDL._direct_mode(f)===(normalize ? :normalized : :direct)
            @test f.base.pivot_policy===policy && typeof(f)===original_type
            check_solutions(saved_fallback,B,[2.0,4.0])
            JDL._direct_refactorize_with_exporter!(f,empty,exporter)
            @test length(f.work)==0 && f.base.pivot_policy===policy
            JDL._direct_refactorize_with_exporter!(f,B,exporter)
            @test length(f.work)==2 && f.base.pivot_policy===policy
            @test typeof(f)===original_type && f.base.normalize_requested===normalize
            check_solutions(f,B,[2.0,4.0]);check_solutions(saved,B,[2.0,4.0])
            @test seen.calls==8
            if R===:native
                @test seen.empty==2 && seen.nonempty==6 && seen.markowitz==0
            else
                @test seen.markowitz==8 && seen.empty==0 && seen.nonempty==0
            end
            @test isequal(_dl_matrix_snapshot(B),before)
        end
    end
end

function test_policy_rejections_and_forwarders()
    @testset "Markowitz policy rejected before Float64 factory/export; compatibility" begin
        for Factor in DIRECT_FACTORS, normalize in (false,true)
            for B in (spzeros(0,0),spdiagm(0=>[2.0,4.0]))
                fact_calls=Ref(0); export_calls=Ref(0); before=_dl_matrix_snapshot(B)
                factory=(args...)->(fact_calls[]+=1;error("rejected request reached factorization"))
                exporter=backend->(export_calls[]+=1;error("rejected request reached export"))
                @test_throws ArgumentError JDL._direct_lu_factor_with_exporter(
                    Factor,B,Val(:markowitz),JDL._NATIVE_PIVOT_ONE,exporter;normalize,factorize=factory)
                @test fact_calls[]==0 && export_calls[]==0
                @test isequal(_dl_matrix_snapshot(B),before)
            end
            for R in (:native,:markowitz)
                B=spdiagm(0=>[2.0,4.0]); seen=PolicyObservations()
                old=JDL._direct_lu_factor(Factor,B,Val(R);normalize)
                via_exporter=JDL._direct_lu_factor_with_exporter(
                    Factor,B,Val(R),policy_exporter(JDL._NATIVE_PIVOT_DEFAULT,seen);normalize)
                @test old.base.pivot_policy===via_exporter.base.pivot_policy===JDL._NATIVE_PIVOT_DEFAULT
                @test old.base.normalize_requested===via_exporter.base.normalize_requested===normalize
                check_solutions(old,B,[2.0,4.0]);check_solutions(via_exporter,B,[2.0,4.0])
                @test seen.calls==1
            end
        end
        # Invalid manager/backend must not reach either test seam.
        calls=Ref(0); factory=(args...)->(calls[]+=1;error("invalid factory"))
        exporter=backend->(calls[]+=1;error("invalid export"))
        B=spzeros(0,0)
        @test_throws ArgumentError JDL._direct_lu_factor_with_exporter(
            JDL.PFIFactorization,B,Val(:native),JDL._NATIVE_PIVOT_DEFAULT,exporter;factorize=factory)
        @test_throws ArgumentError JDL._direct_lu_factor_with_exporter(
            JDL.ForrestTomlinFactorization,B,Val(:unsupported),JDL._NATIVE_PIVOT_DEFAULT,exporter;factorize=factory)
        @test calls[]==0
    end
end

function test_generic_policy_forwarding()
    @testset "Other precisions retain ordinary arithmetic and input ownership" begin
        setprecision(BigFloat,256) do
            for T in (Float32,BigFloat,Rational{BigInt}), Factor in DIRECT_FACTORS
                B=sparse(T[2 1;0 4]); before=_dl_matrix_snapshot(B); owners=(B.colptr,B.rowval,B.nzval)
                leaves=Tuple(B.nzval)
                for (R,policy) in DIRECT_ARMS
                    f=JDL._direct_lu_factor(Factor,B,Val(R),policy)
                    @test !(f.base isa JDL.DirectLowerBackend)
                    @test JDL.forward_solve(f,T[3,4])==T[1,1]
                    @test JDL.transpose_solve(f,T[2,5])==T[1,1]
                    saved=JDL.copy_basis_factorization(f)
                    JDL.refactorize!(f,2B)
                    @test JDL.forward_solve(f,T[6,8])==T[1,1]
                    @test JDL.forward_solve(saved,T[3,4])==T[1,1]
                    @test saved.work!==f.work && saved.spike!==f.spike
                end
                for R in (:native,:markowitz)
                    f=JDL._direct_lu_factor(Factor,B,Val(R))
                    @test !(f.base isa JDL.DirectLowerBackend)
                    @test JDL.forward_solve(f,T[3,4])==T[1,1]
                end
                for rejected in (spzeros(T,0,0),B)
                    @test_throws ArgumentError JDL._direct_lu_factor(
                        Factor,rejected,Val(:markowitz),JDL._NATIVE_PIVOT_ONE)
                end
                # Generic rejection is tested by result + independently pinned source
                # forwarding; no generic injected factory or runtime-count claim.
                @test isequal(_dl_matrix_snapshot(B),before)
                @test all(a===b for (a,b) in zip(owners,(B.colptr,B.rowval,B.nzval)))
                @test all(a===b for (a,b) in zip(leaves,B.nzval))
            end
        end
    end
end

function run_direct_lu_policy_tests()
    @testset "Direct LU policy adapter intent and ownership" begin
        test_policy_transitions()
        test_policy_rejections_and_forwarders()
        test_generic_policy_forwarding()
    end
end
