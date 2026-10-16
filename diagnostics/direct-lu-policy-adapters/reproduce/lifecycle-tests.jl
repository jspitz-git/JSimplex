# UNEXECUTED prospective tests. Ordinary candidate overlay loads implementation.
# Admission must bind an explicit run_direct_lu_lifecycle_tests() call and all counts.
using Test, LinearAlgebra, SparseArrays, JSimplex
include("fixtures.jl")
using .DirectLUFixtures: export_fixtures, coupled_basis, singular_basis, replacement,
                         export_identity, solve_residual
const JDL = JSimplex
const DIRECT_ARMS = ((:native,JDL._NATIVE_PIVOT_DEFAULT),(:native,JDL._NATIVE_PIVOT_ONE),
                     (:markowitz,JDL._NATIVE_PIVOT_DEFAULT))
const DIRECT_FACTORS = (JDL.ForrestTomlinFactorization,JDL.SuhlSuhlFactorization,
                        JDL.BartelsGolubFactorization)

# Numeric and structural snapshots are detached; owner tuples retain actual owners.
_dl_token(x::Float64) = reinterpret(UInt64,x)
_dl_token(x::BigFloat) = (string(Rational{BigInt}(x)),precision(x))
_dl_token(x::Rational) = (string(numerator(x)),string(denominator(x)))
_dl_token(x::Number) = x
_dl_token(x::AbstractArray) = (size(x),[_dl_token(y) for y in x])
_dl_token(x) = ntuple(i->_dl_token(getfield(x,i)),fieldcount(typeof(x)))
_dl_matrix_snapshot(B) = (copy(B.colptr),copy(B.rowval),_dl_token(B.nzval))
_dl_export_snapshot(e) = (_dl_matrix_snapshot(e.lower),_dl_matrix_snapshot(e.upper),
                          copy(e.rows),copy(e.columns),copy(e.scaling),e.divide_scaling)
_dl_export_arrays(e) = (e.lower.colptr,e.lower.rowval,e.lower.nzval,
                       e.upper.colptr,e.upper.rowval,e.upper.nzval,e.rows,e.columns,e.scaling)
_dl_factor_snapshot(f) = (copy(f.column_order),copy(f.positions),
    [(collect(c.indices),_dl_token(c.values)) for c in f.upper],
    _dl_token(f.updates),copy(f.work),copy(f.spike))
_dl_request(f) = JDL._direct_requested_backend(f.base)

function check_solutions(f,B,rhs)
    before = copy(rhs)
    for transposed in (false,true)
        operation = transposed ? JDL.transpose_solve : JDL.forward_solve
        x = operation(f,rhs)
        @test solve_residual(B,x,rhs;transposed)
        @test isequal(rhs,before)
    end
end

function test_exports()
    @testset "Owned export identity and core row relocation" begin
        for fixture in export_fixtures(), (R,policy) in DIRECT_ARMS
            B = fixture.B
            before = _dl_matrix_snapshot(B)
            owners = (B.colptr,B.rowval,B.nzval)
            backend = JDL._factorize_basis(B,Val(R),policy)
            e = JDL._export_basis_lu(backend)
            @test e isa JDL.BasisLUExport
            isnothing(e) && error("Required fixture export unavailable: $(fixture.name)/$R")
            @test export_identity(B,e)
            another = JDL._export_basis_lu(backend)
            @test all(a !== b for (a,b) in zip(_dl_export_arrays(e),_dl_export_arrays(another)))
            frozen = _dl_export_snapshot(e)
            if R === :markowitz && fixture.name === :coupled
                k = backend.sparse_pivots
                @test k == 2
                @test backend.row_order[1:2] == [4,3]
                @test backend.core.p != collect(1:length(backend.core.p))
                @test sort(backend.lower[1].values) == [1/8,1/2]
                # Deliberately omit Pc*Ls21 only. Correct L from e is not used
                # to derive these wrong positions; backend pre-core indices are.
                wrongL = copy(e.lower)
                wrongL[(k+1):end,1:k] .= 0.0
                for j in 1:k, slot in eachindex(backend.lower[j].indices)
                    row = backend.lower[j].indices[slot]
                    row > k && (wrongL[row,j] = backend.lower[j].values[slot])
                end
                wrong = JDL.BasisLUExport(wrongL,e.upper,e.rows,e.columns,e.scaling,e.divide_scaling)
                @test !export_identity(B,wrong)
            elseif R === :markowitz && fixture.name === :core
                @test backend.sparse_pivots == 0
            end
            if size(B,1)>0
                # Mutate/refactor the real source backend after both exports.
                if R === :native
                    # Preserve explicit stored zeros for symbolic reuse. The fixture
                    # and both exported factors must remain independently owned.
                    refactor_input = copy(B)
                    refactor_input.nzval .*= 2.0
                    @test refactor_input.colptr == B.colptr
                    @test refactor_input.rowval == B.rowval
                    @test all(a !== b for (a,b) in zip(
                        (refactor_input.colptr,refactor_input.rowval,refactor_input.nzval),owners))
                    @test all(isequal(refactor_input.nzval[k],2.0*B.nzval[k]) for k in eachindex(B.nzval))
                    lu!(backend.factorization,refactor_input)
                    @test issuccess(backend.factorization)
                else
                    backend.core.factors .= 7.0
                    backend.diagonal .+= 1.0
                    reverse!(backend.row_order)
                    for v in backend.lower; v.values .+= 1.0; end
                    for v in backend.upper; v.values .+= 1.0; end
                end
                @test isequal(_dl_export_snapshot(e),frozen)
                @test export_identity(B,e)
            end
            @test isequal(_dl_matrix_snapshot(B),before)
            @test all(a === b for (a,b) in zip(owners,(B.colptr,B.rowval,B.nzval)))
        end
    end
end

function test_export_rejections()
    @testset "Malformed export versus unsupported backend" begin
        I2 = spdiagm(0=>ones(2))
        valid() = (copy(I2),copy(I2),[1,2],[1,2],ones(2))
        for change! in (x->(x[3][1]=2),x->(x[4][2]=3),x->(x[5][1]=0.0),
                        x->(x[1].nzval[1]=2.0),x->(x[2].nzval[2]=0.0),
                        x->(x[1].nzval[1]=NaN),x->(x[2].nzval[2]=Inf),
                        x->(x[1].rowval[1]=3),x->(x[2].colptr[end]=99))
            parts = valid(); change!(parts)
            @test_throws ArgumentError JDL._checked_basis_lu(parts...,false)
        end
        @test isnothing(JDL._export_basis_lu(nothing))
        setprecision(BigFloat,256) do
            for T in (Float32,BigFloat,Rational{BigInt}), R in (:native,:markowitz)
                B = sparse(T[2 1;0 3]); before = _dl_matrix_snapshot(B)
                leaves = Tuple(B.nzval)
                backend = JDL._factorize_basis(B,Val(R))
                @test isnothing(JDL._export_basis_lu(backend))
                for Factor in DIRECT_FACTORS
                    f = JDL._direct_lu_factor(Factor,B,Val(R))
                    @test !(f.base isa JDL.DirectLowerBackend)
                    @test JDL.forward_solve(f,T[1,1]) ≈ B\T[1,1]
                end
                @test isequal(_dl_matrix_snapshot(B),before)
                @test all(a === b for (a,b) in zip(leaves,B.nzval))
            end
        end
        for R in (:native,:markowitz)
            @test_throws SingularException JDL._factorize_basis(singular_basis(),Val(R))
        end
    end
end

function test_scale_selection()
    @testset "Actual orientation helper selects multiply, divide or neither" begin
        L,U = sparse([1.0 0;0.25 1.0]),sparse([-2.0 1;0.0 4.0])
        p,q,s = [2,1],[2,1],[2.0,0.5]
        parts = JDL.BasisLUExport(L,U,p,q,s,false)
        frozen = _dl_export_snapshot(parts)
        for divide in (false,true)
            scale = divide ? 1.0 ./ s : s
            B = zeros(2,2)
            B[p,q] = Matrix(L*U)./reshape(scale[p],2,1)
            before = copy(B)
            F = lu(B)
            observed = JDL._hh_scale_mode(F,L,U,p,q,s,zeros(2),zeros(2))
            @test observed === divide
            @test isequal(B,before)
            @test isequal(_dl_export_snapshot(parts),frozen)
        end
        # The real helper solves with an ordinary dense identity factor. No
        # solve mock or existing method is replaced. The first scale vector
        # matches neither convention, the second matches both within its bound.
        I2 = spdiagm(0=>ones(2)); F = lu(Matrix(I2))
        for scaling in ([2.0,0.5],[nextfloat(1.0),nextfloat(1.0)])
            snapshot = _dl_matrix_snapshot(I2); before = copy(scaling)
            @test isnothing(JDL._hh_scale_mode(F,I2,I2,[1,2],[1,2],scaling,zeros(2),zeros(2)))
            @test isequal(_dl_matrix_snapshot(I2),snapshot)
            @test isequal(scaling,before)
        end
    end
end

function test_normalization_and_scaling()
    @testset "Normalization rejection and both original-row scaling conventions" begin
        for U in (sparse([1e-300 1e300;0.0 1.0]),
                  sparse([1e300 1e-300;0.0 1.0]),
                  sparse([Inf 1.0;0.0 1.0]),sparse([0.0 1.0;0.0 1.0]))
            snapshot = _dl_matrix_snapshot(U)
            @test isnothing(JDL._direct_normalize_upper!(U))
            @test isequal(_dl_matrix_snapshot(U),snapshot)
        end
        for divide in (false,true), normalize in (false,true), Factor in DIRECT_FACTORS,
            R in (:native,:markowitz)
            L,U = sparse([1.0 0;0.25 1.0]),sparse([-2.0 1;0.0 4.0])
            p,q,s = [2,1],[2,1],[2.0,0.5]
            scale = divide ? 1.0 ./ s : s
            B = zeros(2,2)
            B[p,q] = Matrix(L*U)./reshape(scale[p],2,1)
            exporter = _ -> JDL._checked_basis_lu(copy(L),copy(U),copy(p),copy(q),copy(s),divide)
            f = JDL._direct_lu_factor_with_exporter(Factor,sparse(B),Val(R),exporter;normalize)
            @test export_identity(B,JDL.BasisLUExport(L,U,p,q,s,divide))
            @test JDL._direct_mode(f) === (normalize ? :normalized : :direct)
            check_solutions(f,B,[1.0,-2.0])
            for operation in (JDL.forward_solve!,JDL.transpose_solve!)
                rhs = [1.0,-2.0]; before = copy(rhs)
                operation(rhs,f,rhs)
                @test solve_residual(B,rhs,before;transposed=operation===JDL.transpose_solve!)
            end
        end
    end
end

function test_indexed_and_aliases(f,B)
    n = size(B,1); rhs = [Float64(i)/max(1,n) for i in 1:n]
    for operation in (JDL.forward_solve!,JDL.transpose_solve!)
        transpose_case = operation === JDL.transpose_solve!
        same = copy(rhs); operation(same,f,same)
        @test solve_residual(B,same,rhs;transposed=transpose_case)
        @test_throws ArgumentError operation(f.work,f,rhs)
        @test_throws DimensionMismatch operation(zeros(n+1),f,rhs)
        copyto!(f.work,rhs); operation(f.spike,f,f.work)
        @test solve_residual(B,f.spike,rhs;transposed=transpose_case)
        for mode in (:sparse,:dense,:auto)
            source = JDL.IndexedVector{Float64}(n)
            destination = JDL.IndexedVector{Float64}(n)
            JDL.load_indexed!(source,rhs)
            operation(destination,f,source;kernel_mode=mode)
            @test solve_residual(B,destination.values,rhs;transposed=transpose_case)
            @test Set(destination.indices) == Set(findall(!iszero,destination.values))
            @test isequal(source.values,rhs)
            operation(source,f,source;kernel_mode=mode)
            @test solve_residual(B,source.values,rhs;transposed=transpose_case)
        end
    end
end

function test_lifecycles()
    @testset "Three managers preserve solves, copies and prepared direction provenance" begin
        for fixture in export_fixtures(), Factor in DIRECT_FACTORS,
            (R,policy) in DIRECT_ARMS, normalize in (false,true)
            input = fixture.B; input_before = _dl_matrix_snapshot(input)
            B = Matrix(input); n = size(B,1)
            f = JDL._direct_lu_factor(Factor,input,Val(R),policy;normalize)
            ordinary = Factor(input,Val(R),policy)
            @test f.base isa JDL.DirectLowerBackend
            @test _dl_request(f) === R
            @test f.base.pivot_policy === policy
            @test f.base.normalize_requested == normalize
            @test isnothing(JDL.sparse_solve_view(f.base))
            @test JDL._direct_mode(f) === (normalize ? :normalized : :direct)
            rhs = ones(n)
            check_solutions(f,B,rhs); check_solutions(ordinary,B,rhs)
            test_indexed_and_aliases(f,B)
            saved = nothing; savedB = nothing
            if n>=2
                for t in 0:7
                    j,a = replacement(B,t)
                    a_before = copy(a); dse = collect(1.0:n)./n
                    directions = (JDL.forward_solve(f,a),JDL.forward_solve(ordinary,a))
                    for (factor,direction) in zip((f,ordinary),directions)
                        original_direction = copy(direction)
                        @test solve_residual(B,direction,a)
                        other = JDL.forward_solve(factor,dse)
                        @test solve_residual(B,other,dse)
                        @test isequal(direction,original_direction)
                        @test JDL._copy_prepared_spike!(factor,direction)
                        JDL.replace_column!(factor,direction,j)
                        @test !JDL._copy_prepared_spike!(factor,direction)
                    end
                    B[:,j] = a
                    @test isequal(a,a_before)
                    unit_rhs = zeros(n); unit_rhs[j] = 1.0
                    check_solutions(f,B,unit_rhs); check_solutions(ordinary,B,unit_rhs)
                    if t==1
                        saved = JDL.copy_basis_factorization(f); savedB = copy(B)
                        @test saved.base.pivot_policy === policy
                        @test saved.base.work !== f.base.work
                        @test saved.work !== f.work && saved.spike !== f.spike
                        @test all(a.values !== b.values && a.indices !== b.indices for (a,b) in zip(saved.upper,f.upper))
                        @test isnothing(saved.row_cache.prepared)
                        if Factor === JDL.BartelsGolubFactorization
                            @test JDL._upper_order(saved.upper) !== JDL._upper_order(f.upper)
                        end
                        # Diverge the copied history while the original keeps advancing.
                        a2 = savedB[:,1]+[i==2 ? 1/64 : 0.0 for i in 1:n]
                        JDL.replace_column!(saved,JDL.forward_solve(saved,a2),1)
                        savedB[:,1] = a2
                    elseif t==3
                        JDL.refactorize!(f,sparse(B)); JDL.refactorize!(ordinary,sparse(B))
                        @test isempty(f.updates) && isnothing(f.row_cache.prepared)
                        @test !JDL._copy_prepared_spike!(f,directions[1])
                        @test _dl_request(f) === R && f.base.normalize_requested==normalize && f.base.pivot_policy===policy
                    end
                    isnothing(saved) || check_solutions(saved,savedB,rhs)
                end
                test_indexed_and_aliases(f,B)
            end
            # Failed candidate construction must not publish any field or mutate old data.
            fields = ntuple(i->getfield(f,i),fieldcount(typeof(f)))
            state = _dl_factor_snapshot(f)
            @test_throws SingularException JDL.refactorize!(f,singular_basis())
            @test all(getfield(f,i) === fields[i] for i in eachindex(fields))
            @test isequal(_dl_factor_snapshot(f),state)
            check_solutions(f,B,rhs)
            resized = spdiagm(0=>[2.0,3.0,4.0])
            JDL.refactorize!(f,resized)
            check_solutions(f,resized,ones(3))
            @test length(f.work)==3 && _dl_request(f)===R && f.base.pivot_policy===policy
            isnothing(saved) || check_solutions(saved,savedB,ones(size(savedB,1)))
            @test isequal(_dl_matrix_snapshot(input),input_before)
        end
    end
end

function test_fallback_transitions()
    @testset "Typed direct to fallback to direct refactors are transactional" begin
        for Factor in DIRECT_FACTORS, (R,policy) in DIRECT_ARMS, normalize in (false,true)
            B = spdiagm(0=>[2.0,3.0,4.0])
            f = JDL._direct_lu_factor(Factor,B,Val(R),policy;normalize)
            original_type = typeof(f); saved = JDL.copy_basis_factorization(f)
            calls = Ref(0)
            unavailable = backend -> (calls[]+=1; nothing)
            JDL._direct_refactorize_with_exporter!(f,2.0*B,unavailable)
            @test calls[]==1 && typeof(f)===original_type
            @test JDL._direct_mode(f)===:fallback
            @test _dl_request(f)===R && f.base.normalize_requested==normalize && f.base.pivot_policy===policy
            @test (R===:native ? f.base.fallback isa JDL.UMFPACKBackend : f.base.fallback isa JDL.MarkowitzBackend)
            check_solutions(f,2.0*B,ones(3)); check_solutions(saved,B,ones(3))
            saved_fallback = JDL.copy_basis_factorization(f)
            before = _dl_factor_snapshot(f); oldbase=f.base
            sentinel = ErrorException("test export failure")
            caught = try
                JDL._direct_refactorize_with_exporter!(f,B,_ -> throw(sentinel))
                nothing
            catch error
                error
            end
            @test caught === sentinel && f.base === oldbase
            @test isequal(_dl_factor_snapshot(f),before)
            JDL.refactorize!(f,3.0*B)
            @test typeof(f)===original_type && isnothing(f.base.fallback) && f.base.pivot_policy===policy
            @test saved_fallback.base.pivot_policy===policy
            @test JDL._direct_mode(f)===(normalize ? :normalized : :direct)
            check_solutions(f,3.0*B,ones(3))
            check_solutions(saved_fallback,2.0*B,ones(3))
        end
    end
end

function run_direct_lu_lifecycle_tests()
    @testset "Policy adapter common export and lifecycles" begin
        test_exports()
        test_export_rejections()
        test_scale_selection()
        test_normalization_and_scaling()
        test_lifecycles()
        test_fallback_transitions()
    end
end
# No auto-run. The later reviewed driver also selects unchanged focused tests
# and writes partial raw/log records. Neither that launcher nor cost tests run here.
