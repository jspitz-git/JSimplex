# OFFLINE candidate regression suite. Unexecuted until separate admission.
module NativePivotPolicyTests
using Test, LinearAlgebra, SparseArrays, JSimplex
const J = JSimplex
const MODES = (:pfi, :forrest_tomlin, :suhl_suhl, :bartels_golub)
const TYPES = (Float16, Float32, Float64, BigFloat, Rational{Int}, Rational{BigInt})
const POLICIES = (:default, :threshold_one)
const B = sparse([4.0 1; 1 3])
const C = sparse([5.0 1; 1 4])

# Catches lost intent or collateral option changes in each reconstruction path.
function same_options(a, b; changed...)
    for name in fieldnames(typeof(a))
        expected = haskey(changed, name) ? changed[name] : getfield(a, name)
        @test isequal(getfield(b, name), expected)
    end
end

# Catches control mutation, policy reset and drift in the other 18 settings.
function controls(backend, symbol)
    @test backend.pivot_policy === J._native_pivot_policy(symbol)
    if backend.factorization === nothing
        @test backend.dimension == 0
        return
    end
    want = SparseArrays.UMFPACK.get_umfpack_control(Float64, Int)
    if symbol === :threshold_one
        want[SparseArrays.LibSuiteSparse.UMFPACK_PIVOT_TOLERANCE + 1] = 1.0
        want[SparseArrays.LibSuiteSparse.UMFPACK_IRSTEP + 1] = 0.0
    end
    @test length(want) == 20
    @test reinterpret(UInt64, backend.factorization.control) == reinterpret(UInt64, want)
end

# Catches stale history/spare publication and mutation of matrix/RHS inputs.
function solves(f, matrix)
    n = size(matrix, 1)
    rhs = collect(1.0:n)
    before_matrix = copy(matrix); before_rhs = copy(rhs)
    for (op, solve) in ((identity, Main.NP.forward_solve), (transpose, Main.NP.transpose_solve))
        x = solve(f, rhs)
        Main.NP.equation!(matrix,rhs,x,op===transpose)
        @test length(x) == n
        if n > 0
            m = op(matrix)
            @test norm(m*x-rhs, Inf) <= 128n*eps(Float64)*max(1.0,norm(m,Inf)*norm(x,Inf),norm(rhs,Inf))
        end
    end
    @test matrix == before_matrix
    @test rhs == before_rhs
end

freeze(x::AbstractArray) = map(freeze, x)
freeze(x) = isbitstype(typeof(x)) ? x :
    NamedTuple{fieldnames(typeof(x))}(map(n -> freeze(getfield(x,n)), fieldnames(typeof(x))))
history(f) = (freeze(f.updates), hasproperty(f,:upper) ? freeze(f.upper) : nothing)
function updated(f)
    matrix = copy(B)
    column = matrix[:,1] + matrix[:,2]/4
    direction = Main.NP.forward_solve(f, column)
    Main.NP.replace_column!(f, direction, 1)
    matrix[:,1] = column
    @test !isempty(f.updates)
    return matrix
end

@testset "options_and_copy_intent" begin
    setprecision(BigFloat,256) do
        @test SolverOptions().native_pivot_policy === :default
        @test_throws ArgumentError SolverOptions(native_pivot_policy=:bad)
        for T in TYPES
            @test_throws ArgumentError SolverOptions(T; native_pivot_policy=:threshold_one,basis_refactorization=:markowitz)
            @test_throws ArgumentError SolverOptions(T; native_pivot_policy=:threshold_one,basis_update=:huangfu_hall)
            for mode in MODES, symbol in POLICIES
                o = SolverOptions(T; basis_update=mode,native_pivot_policy=symbol,
                    primal_tolerance=1//8,dual_tolerance=1//8,zero_tolerance=1//8,
                    iteration_limit=73,time_limit=19.0,refactorization_interval=7,
                    verbose=false,pricing=:devex,scaling=:off,partial_pricing=true)
                old = typeof(o)(ntuple(i->getfield(o,i),16)...)
                same_options(o,old; native_pivot_policy=:default)
                same_options(o,SolverOptions(T,o))
                same_options(o,J._phase_options(o,:primal);algorithm=:primal)
                same_options(o,J._remaining_options(o;iterations=3,time_limit=11.0,algorithm=:primal);
                    iteration_limit=70,time_limit=11.0,algorithm=:primal)
                budget=(iteration_limit=31,iterations=4,time_limit_seconds=9.0)
                same_options(o,J._lp_auxiliary_options(o,budget);
                    iteration_limit=27,time_limit=9.0,scaling=:off,presolve=false)
                same_options(o,J._copy_precision_options(T,o))
            end
        end
        o=SolverOptions(native_pivot_policy=:threshold_one,verbose=false)
        same_options(o,SolverOptions(Float64,SolverOptions(BigFloat,o)))
        same_options(o,J._copy_precision_options(Float64,J._copy_precision_options(BigFloat,o)))
        @test J._solver_options(J.Optimizer()).native_pivot_policy === :default
        @test !("native_pivot_policy" in J._RAW_OPTIMIZER_ATTRIBUTES)
    end
end

@testset "backend_owned_policy" begin
    for symbol in POLICIES
        policy=J._native_pivot_policy(symbol)
        a=Main.NP._factorize_basis(B,Val(:native),policy)
        b=Main.NP._factorize_basis(B,Val(:native),policy)
        controls(a,symbol);controls(b,symbol)
        @test a.factorization !== b.factorization
        @test a.factorization.control !== b.factorization.control
        @test_throws ErrorException setfield!(a,:pivot_policy,J._native_pivot_policy(symbol===:default ? :threshold_one : :default))
        controls(a,symbol)
        empty=Main.NP._factorize_basis(spzeros(0,0),Val(:native),policy)
        controls(empty,symbol)
        @test empty.factorization === nothing && empty.spare === nothing
    end
    singular=Main.NP.raw_lu(sparse([1.0 1;1 1]);check=false)
    for backend in (Main.NP.UMFPACKBackend(singular,2),Main.NP.UMFPACKBackend(singular,2,nothing,false))
        @test backend.pivot_policy === J._NATIVE_PIVOT_DEFAULT
        @test_throws SingularException Main.NP.sparse_solve_view(backend)
    end
    @test_throws ArgumentError J._native_pivot_policy(:bad)
end

@testset "private_spare_copy_and_failure" begin
    for mode in MODES, symbol in POLICIES
        policy=J._native_pivot_policy(symbol)
        f=Main.NP._basis_factorization(B,Val(mode),Val(:native),policy)
        first=f.base.factorization
        @test f.base.spare === nothing
        Main.NP.refactorize!(f,C)
        @test f.base.factorization !== first && f.base.spare === first
        controls(f.base,symbol);solves(f,C)
        spare=f.base.spare;active=f.base.factorization;ctrl=spare.control
        Main.NP.refactorize!(f,B)
        @test f.base.factorization === spare && f.base.spare === active
        @test f.base.factorization.control === ctrl
        controls(f.base,symbol);solves(f,B)
        for matrix in (spdiagm(0=>[2.0,4.0]),sparse(Matrix{Float64}(I,3,3)),spzeros(0,0),spzeros(0,0),B)
            Main.NP.refactorize!(f,matrix)
            controls(f.base,symbol);solves(f,matrix)
        end

        # A copied nonempty prefix survives independent resets on each side.
        f=Main.NP._basis_factorization(B,Val(mode),Val(:native),policy)
        Main.NP.refactorize!(f,B) # Populate a private spare BEFORE the copy.
        private_spare=f.base.spare
        @test private_spare !== nothing
        matrix=updated(f);saved=Main.NP.copy_basis_factorization(f)
        @test f.base.spare === private_spare
        owner=saved.base.factorization;control_owner=owner.control
        ctrl=copy(owner.control);hist=history(saved)
        @test f.base !== saved.base && f.base.factorization === owner
        @test saved.base.spare === nothing
        Main.NP.refactorize!(f,C)
        @test saved.base.factorization === owner && history(saved)==hist
        @test owner.control === control_owner && owner.control == ctrl
        controls(f.base,symbol);controls(saved.base,symbol)
        solves(saved,matrix);solves(f,C)
        Main.NP.refactorize!(saved,B)
        @test f.base.factorization !== saved.base.factorization
        controls(saved.base,symbol);solves(f,C);solves(saved,B)

        # Fresh failure and private-spare failure are separate states.
        for with_spare in (false,true)
            f=Main.NP._basis_factorization(B,Val(mode),Val(:native),policy)
            if with_spare
                Main.NP.refactorize!(f,B)
            end
            matrix=updated(f)
            owner=f.base.factorization;control_owner=owner.control
            ctrl=copy(owner.control);hist=history(f)
            @test (f.base.spare !== nothing) == with_spare
            saved=Main.NP.copy_basis_factorization(f);saved_hist=history(saved)
            @test saved.base !== f.base && saved.base.factorization === owner
            @test saved.base.spare === nothing
            singular=copy(B);fill!(singular.nzval,0.0)
            @test_throws SingularException Main.NP.refactorize!(f,singular)
            @test f.base.factorization === owner && f.base.dimension==2
            @test owner.control === control_owner && owner.control == ctrl && history(f)==hist
            @test f.base.spare === nothing
            @test saved.base.factorization === owner && history(saved)==saved_hist
            controls(f.base,symbol);solves(f,matrix)
            controls(saved.base,symbol);solves(saved,matrix)
            Main.NP.refactorize!(f,C)
            controls(f.base,symbol);solves(f,C)
            @test saved.base.factorization === owner && history(saved)==saved_hist
            @test owner.control === control_owner && owner.control == ctrl
            controls(saved.base,symbol);solves(saved,matrix)
        end
    end
end

@testset "precision_and_factory_dispatch" begin
    setprecision(BigFloat,256) do
        for T in TYPES, mode in MODES
            T===Float64 && continue
            matrix=sparse(T[2 0;0 4]);rhs=T[2,8]
            ref=Main.NP._basis_factorization(matrix,Val(mode),Val(:native))
            for symbol in POLICIES
                o=SolverOptions(T;basis_update=mode,native_pivot_policy=symbol)
                f=Main.NP._basis_factorization(matrix,o)
                @test typeof(f.base)===typeof(ref.base)
                @test !(f.base isa J.UMFPACKBackend)
                @test Main.NP.forward_solve(f,rhs)==T[1,2]
                @test Main.NP.transpose_solve(f,rhs)==T[1,2]
            end
        end
        for mode in MODES
            o=SolverOptions(native_pivot_policy=:threshold_one,basis_update=mode)
            roundtrip=J._copy_precision_options(Float64,J._copy_precision_options(BigFloat,o))
            f=Main.NP._basis_factorization(B,roundtrip)
            controls(f.base,:threshold_one);solves(f,B)
        end
        for mode in (MODES...,:huangfu_hall), backend in (:native,:markowitz)
            # Rectangular input proves policy rejection precedes factorization.
            if backend===:markowitz || mode===:huangfu_hall
                @test_throws ArgumentError Main.NP._basis_factorization(zeros(1,2),Val(mode),Val(backend),J._NATIVE_PIVOT_ONE)
                f=Main.NP._basis_factorization(B,Val(mode),Val(backend),J._NATIVE_PIVOT_DEFAULT)
                ref=Main.NP._basis_factorization(B,Val(mode),Val(backend))
                @test typeof(f)===typeof(ref)
                solves(f,B)
            end
        end
        @test_throws ArgumentError Main.NP._factorize_basis(zeros(1,2),Val(:markowitz),J._NATIVE_PIVOT_ONE)
    end
end
end # module
