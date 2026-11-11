using Test, SparseArrays, JSimplex

@testset "Presolve work cache dependencies, ownership, and bounded storage" begin
    W = JSimplex._PresolveWork
    H = _PresolveWorkTestTools
    Q = Rational{BigInt}
    for T in (Float32, Float64, BigFloat)
        p = H.fixture(T)
        @test W.rows(p.A) !== W.rows(p.A)
        W.with_session(T) do
            s = W.current(T)
            rows = W.entries(p, false)
            @test rows === W.rows(p.A)
            @test s.matrix !== p.A
            @test s.matrix.colptr !== p.A.colptr
            @test s.matrix.rowval !== p.A.rowval
            @test s.matrix.nzval !== p.A.nzval
            W.remember!(p, 1, rows[1])
            @test W.rejected(p, 1, rows[1])
            W.clear_rejections!()
            @test isempty(s.rejected)
            @test W.rows(p.A) === rows
            W.remember!(p, 1, rows[1])
            p.column_upper[1] = JSimplex.Bound(T(2))
            @test !W.rejected(p, 1, rows[1])
            p.column_upper[1] = JSimplex.Bound(T(1))
            @test W.rejected(p, 1, rows[1])

            # The matrix/environment owner must invalidate rejection results even
            # when its first caller is a different row-reading reduction.
            old_digest = H.digest(rows)
            p.A.nzval[1] = -p.A.nzval[1]
            next = W.rows(p.A)
            @test next !== rows && isempty(s.rejected)
            @test H.digest(rows) == old_digest
            @test H.digest(next) == H.digest(JSimplex._row_entries(p.A))
            @test W.entries(p, false) === next

            for field in (:row_lower, :row_upper, :objective)
                rows = W.entries(p, false)
                W.remember!(p, 1, rows[1])
                values = getfield(p, field)
                values[1] = field === :objective ? -values[1] :
                    JSimplex.Bound(-values[1].value)
                @test W.entries(p, false) === rows
                @test isempty(s.rejected)
            end
            rows = W.entries(p, false)
            W.remember!(p, 1, rows[1])
            @test W.entries(p, true) === rows
            @test isempty(s.rejected)

            # Scalar and objective-direction changes use equal independent
            # matrices, so these cannot rely on matrix invalidation.
            for (constant, sense) in ((T(2), JSimplex.MIN_SENSE),
                                      (zero(T), JSimplex.MAX_SENSE))
                W.entries(p, true)
                W.remember!(p, 1, rows[1])
                changed = JSimplex.LinearProblem(p.A, p.objective;
                    objective_constant=constant, objective_sense=sense,
                    row_lower=p.row_lower, row_upper=p.row_upper,
                    column_lower=p.column_lower, column_upper=p.column_upper)
                @test W.entries(changed, true) === rows
                @test isempty(s.rejected)
            end

            # Spare CSC storage is part of the snapshot, even outside nnz(A).
            W.remember!(p, 1, rows[1])
            # More spare entries than the matrix's dense size catches a copy
            # constructor that silently truncates unused CSC buffers.
            append!(p.A.rowval, fill(1, prod(size(p.A))))
            append!(p.A.nzval, zeros(T, prod(size(p.A))))
            next = W.rows(p.A)
            @test next !== rows && isempty(s.rejected)
            @test length(s.matrix.nzval) == length(p.A.nzval)
            @test length(s.matrix.rowval) == length(p.A.rowval)
            W.entries(p, false)
            W.remember!(p, 1, next[1])
            p.A.rowval[end] = 2
            @test W.rows(p.A) !== next
            @test isempty(s.rejected)
            next = W.entries(p, false)
            W.remember!(p, 1, next[1])
            p.A.nzval[end] = one(T)
            @test W.rows(p.A) !== next && isempty(s.rejected)

            # Equal-valued independent matrices reuse the snapshot; structure
            # changes that preserve shape and nnz still rebuild it.
            next = W.entries(p, false)
            @test W.rows(deepcopy(p.A)) === next
            W.remember!(p, 1, next[1])
            p.A.rowval[1], p.A.rowval[2] = p.A.rowval[2], p.A.rowval[1]
            @test W.rows(p.A) !== next && isempty(s.rejected)
        end
        W.with_session(T; qcap=1, rcap=1) do
            s = W.current(T)
            first = W.exact(T(7))
            W.exact(T(8))
            @test length(s.exact) == 1 && W.exact(T(7)) === first
            rows = W.entries(p, false)
            W.remember!(p, 1, rows[1])
            W.remember!(p, 2, rows[2])
            @test length(s.rejected) == 1
        end
        W.with_session(T; bytecap=1) do
            @test W.exact(T(7)) == Q(7)
            @test isempty(W.current(T).exact) == (T === BigFloat)
            @test W.current(T).qbytes == 0
        end
        W.with_session(T; qcap=0, rcap=0) do
            rows = W.entries(p, false)
            W.remember!(p, 1, rows[1])
            @test isempty(W.current(T).rejected)
        end
        W.with_session(T) do
            # One logical entry moves between columns; sizes and buffers other
            # than colptr stay the same, and both resulting CSCs are ordered.
            a = SparseMatrixCSC{T,Int}(3, 2, [1, 2, 4], [1, 2, 3], T[1, 2, 3])
            rows = W.rows(a)
            a.colptr[2] = 3
            @test W.rows(a) !== rows
            @test W.rows(a) == JSimplex._row_entries(a)
            larger = SparseMatrixCSC{T,Int}(4, 2, copy(a.colptr),
                copy(a.rowval), copy(a.nzval))
            @test length(W.rows(larger)) == 4
        end
    end
end

@testset "BigFloat exact keys and snapshots own stored-precision payloads" begin
    W = JSimplex._PresolveWork
    H = _PresolveWorkTestTools
    for bits in (32, 64, 128, 240, 256), mode in
        (RoundNearest, RoundDown, RoundUp, RoundToZero, RoundFromZero)
        setprecision(BigFloat, bits) do
            setrounding(BigFloat, mode) do
                x = setprecision(BigFloat, 320) do
                    BigFloat("0.1")
                end
                expected = setprecision(BigFloat, 320) do
                    Rational{BigInt}(x)
                end
                env = (precision(BigFloat), rounding(BigFloat))
                W.with_session(BigFloat) do
                    a = W.exact(x)
                    @test a == expected && W.exact(x) === a
                    key = first(keys(W.current(BigFloat).exact))
                    @test key !== x && precision(key) == 320
                    x.sign = -x.sign
                    @test W.exact(x) == -expected
                    @test setprecision(BigFloat, 320) do
                        Rational{BigInt}(key) == expected
                    end
                    x.sign = -x.sign
                    @test W.exact(x) === a
                end
                @test (precision(BigFloat), rounding(BigFloat)) == env
            end
        end
    end
    setprecision(BigFloat, 128) do
        p = H.fixture(BigFloat)
        W.with_session(BigFloat) do
            s = W.current(BigFloat)
            rows = W.entries(p, false)
            @test s.matrix.nzval[1] !== p.A.nzval[1]
            @test s.lower[1].value !== p.row_lower[1].value
            @test s.costs[1] !== p.objective[1]
            before = H.digest(rows)
            W.remember!(p, 1, rows[1])
            p.column_upper[1].value.sign = -p.column_upper[1].value.sign
            @test !W.rejected(p, 1, rows[1])
            p.column_upper[1].value.sign = -p.column_upper[1].value.sign
            @test W.rejected(p, 1, rows[1])
            p.A.nzval[1].sign = -p.A.nzval[1].sign
            @test H.digest(rows) == before
            rows = W.entries(p, false)
            @test isempty(s.rejected)
            W.remember!(p, 1, rows[1])
            p.A.nzval[1] = setprecision(BigFloat, 192) do
                BigFloat(p.A.nzval[1])
            end
            @test W.rows(p.A) !== rows && isempty(s.rejected)
            for field in (:row_lower, :row_upper, :objective)
                rows = W.entries(p, false)
                W.remember!(p, 1, rows[1])
                value = getfield(p, field)[1]
                scalar = value isa JSimplex.Bound ? value.value : value
                scalar.sign = -scalar.sign
                W.entries(p, false)
                @test isempty(s.rejected)
            end
            rows = W.entries(p, false)
            W.remember!(p, 1, rows[1])
            p.objective_constant.sign = -p.objective_constant.sign
            W.entries(p, false)
            @test isempty(s.rejected)
            rows = W.entries(p, false)
            W.remember!(p, 1, rows[1])
            @test s.constant !== p.objective_constant
            for field in (:row_lower, :row_upper, :objective)
                rows = W.entries(p, false)
                W.remember!(p, 1, rows[1])
                values = getfield(p, field)
                scalar = field === :objective ? values[1] : values[1].value
                replacement = setprecision(BigFloat, 192) do
                    BigFloat(scalar)
                end
                values[1] = field === :objective ? replacement : JSimplex.Bound(replacement)
                W.entries(p, false)
                @test isempty(s.rejected)
            end
            for change_env in (
                f -> setprecision(f, BigFloat, 64),
                f -> setrounding(f, BigFloat, RoundUp))
                rows = W.entries(p, false)
                W.remember!(p, 1, rows[1])
                change_env() do
                    @test W.rows(p.A) !== rows && isempty(s.rejected)
                end
            end
        end
    end
end

@testset "Native subnormal conversions and row environments preserve original behavior" begin
    W = JSimplex._PresolveWork
    old = get_zero_subnormals()
    try
        for T in (Float32, Float64), flush in (false, true)
            set_zero_subnormals(flush)
            tiny = T === Float32 ? reinterpret(Float32, UInt32(1)) :
                reinterpret(Float64, UInt64(1))
            W.with_session(T) do
                # Both paths must preserve Julia's current DAZ/FTZ conversion,
                # including its original exception when the mode rejects it.
                direct = try Rational{BigInt}(tiny) catch e; typeof(e) end
                cached = try W.exact(tiny) catch e; typeof(e) end
                @test isequal(cached, direct)
                @test isempty(W.current(T).exact)
                A = sparse(T[tiny 1; 1 0])
                rows = W.rows(A)
                set_zero_subnormals(!flush)
                @test W.rows(A) !== rows
                @test W.rows(A) == JSimplex._row_entries(A)
                set_zero_subnormals(flush)
            end
        end
    finally
        set_zero_subnormals(old)
    end
end

@testset "Presolve cache task interleaving and scope restoration" begin
    W = JSimplex._PresolveWork
    ready, resume = Channel{Nothing}(2), Channel{Nothing}(2)
    W.with_session(Float64) do
        s = W.current(Float64)
        @test isnothing(W.current(BigFloat))
        child = @async begin
            @test isnothing(W.current(Float64))
            W.with_session(Float64) do
                c = W.current(Float64)
                @test c !== s
                put!(ready, nothing)
                take!(resume)
                @test W.current(Float64) === c
            end
            @test isnothing(W.current(Float64))
        end
        take!(ready)
        @test W.current(Float64) === s
        @test_throws ErrorException W.with_session(BigFloat) do
            @test isnothing(W.current(Float64))
            @test !isnothing(W.current(BigFloat))
            error("restore outer cache")
        end
        @test W.current(Float64) === s
        put!(resume, nothing)
        fetch(child)
        @test W.current(Float64) === s
    end
    @test isnothing(W.current(Float64))
end

@testset "Cached reductions preserve the complete model and postsolve history" begin
    W = JSimplex._PresolveWork
    H = _PresolveWorkTestTools
    function compare(T)
        accepted = LinearProblem(sparse(T[1 1; 1 0; 0 1]), T[1, 2];
            row_lower=T[1, -10, -10], row_upper=T[1, 10, 10],
            column_lower=T[-10, -10], column_upper=T[10, 10])
        for p in (H.fixture(T), accepted), rounded in (false, true)
            before = H.digest(p)
            reference_history = JSimplex._PostsolveHistory(T)
            reference = JSimplex.presolve_problem(p; history=reference_history,
                rounded_costs=rounded)
            W.with_session(T) do
                for _ in 1:2
                    history = JSimplex._PostsolveHistory(T)
                    result = JSimplex.presolve_problem(p; history,
                        rounded_costs=rounded)
                    @test H.digest((result, history)) ==
                        H.digest((reference, reference_history))
                    @test H.digest(p) == before
                end
            end
        end
    end
    compare(Float32)
    compare(Float64)
    for bits in (32, 64, 128, 240, 256), mode in (RoundNearest, RoundDown, RoundUp)
        setprecision(BigFloat, bits) do
            setrounding(BigFloat, mode) do
                compare(BigFloat)
            end
        end
    end
end
