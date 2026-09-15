function read_mps_text(text; kwargs...)
    return mktemp() do path, io
        write(io, text)
        close(io)
        read_mps(path; kwargs...)
    end
end

# Julia 1.13 Test.@inferred widens type-valued keywords to DataType. Keep the
# singleton type in a positional argument while exercising the public reader.
read_typed_mps(path, ::Type{T}; kwargs...) where {T} = read_mps(path; value_type=T, kwargs...)

@testset "Typed and exact MPS construction" begin
    path = joinpath(@__DIR__, "fixtures", "parser", "exact-rational.mps")
    default = @inferred read_mps(path)
    exact = @inferred read_typed_mps(path, Rational{BigInt})
    single = @inferred read_typed_mps(path, Float32)

    @test default isa LinearProblem{Float64}
    @test exact isa LinearProblem{Rational{BigInt}}
    @test single isa LinearProblem{Float32}
    @test exact.objective == Rational{BigInt}[5 // 4]
    @test exact.objective_constant == 1 // big(4)
    @test Matrix(exact.A) == reshape(Rational{BigInt}[3 // 10], 1, 1)
    @test bound_value(only(exact.row_lower)) == 3 // big(5)
    @test bound_value(only(exact.row_upper)) == 3 // big(5)

    maximum = string(typemax(Int))
    duplicate = "NAME SUM\nROWS\n N OBJ\nCOLUMNS\n X OBJ $maximum\n X OBJ 1\nENDATA\n"
    duplicate_error = try
        read_mps_text(duplicate; value_type=Rational{Int})
    catch exception
        exception
    end
    @test duplicate_error isa MPSParseError
    @test duplicate_error.line == 6
    @test duplicate_error.section == :COLUMNS

    ranged = "NAME RANGE\nROWS\n G ROW\nCOLUMNS\n X ROW 1\nRHS\n R ROW $maximum\nRANGES\n RNG ROW 1\nENDATA\n"
    range_error = try
        read_mps_text(ranged; value_type=Rational{Int})
    catch exception
        exception
    end
    @test range_error isa MPSParseError
    @test range_error.line == 9
    @test range_error.section == :RANGES
end

@testset "Typed MPS formats, bounds, and exact arithmetic" begin
    root = joinpath(@__DIR__, "fixtures", "parser")
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        for (filename, format) in (("basic-fixed.mps", :fixed),
                                   ("basic-fixed.mps", :auto),
                                   ("basic-free.mps", :free),
                                   ("basic-free.mps", :auto))
            problem = read_mps(joinpath(root, filename); format, value_type=T)
            @test problem isa LinearProblem{T}
            @test problem.objective == (format == :fixed || filename == "basic-fixed.mps" ? T[1] : T[3, 2])
        end
        domains = read_mps(joinpath(root, "bounds-and-ranges.mps"); value_type=T)
        @test domains.variable_domains == [INTEGER, INTEGER, BINARY, SEMI_CONTINUOUS, SEMI_INTEGER]
        @test bound_value.(domains.column_lower) == T[-2, 0, 0, 2, 3]
        @test bound_value.(domains.column_upper) == T[9, 1, 1, 10, 7]
        @test bound_value.(domains.row_lower) == T[1, 5, 2]
        @test !isfinite(last(domains.row_upper))
        unbounded = read_mps(joinpath(root, "all-bounds.mps"); value_type=T)
        @test isfinite.(unbounded.column_lower) == [true, true, true, false, false, true]
        @test isfinite.(unbounded.column_upper) == [false, true, true, false, false, false]
        selected = read_mps(joinpath(root, "multiple-sets.mps"); value_type=T,
                            rhs_name="SECOND", ranges_name="WIDE", bounds_name="HIGH")
        @test bound_value.(selected.row_lower) == T[-1]
        @test bound_value.(selected.row_upper) == T[2]
        @test bound_value.(selected.column_upper) == T[9]
    end
    for T in (Int, Real, AbstractFloat, Rational)
        @test_throws ArgumentError read_mps(joinpath(root, "exact-rational.mps"); value_type=T)
    end

    duplicate = "NAME EXACTSUM\nROWS\n N OBJ\n E EQ\nCOLUMNS\n X OBJ .1 EQ .2\n X OBJ .2 EQ .1\nENDATA\n"
    summed = read_mps_text(duplicate; value_type=Rational{BigInt})
    @test summed.objective == Rational{BigInt}[3 // 10]
    @test Matrix(summed.A) == reshape(Rational{BigInt}[3 // 10], 1, 1)
    for (kind, range, lower, upper) in (
        ("E", ".3", 1 // 2, 4 // 5), ("E", "-.3", 1 // 5, 1 // 2),
        ("E", "0", 1 // 2, 1 // 2), ("L", ".3", 1 // 5, 1 // 2),
        ("L", "-.3", 1 // 5, 1 // 2), ("G", ".3", 1 // 2, 4 // 5),
        ("G", "-.3", 1 // 2, 4 // 5),
    )
        problem = read_mps_text("NAME RANGE\nROWS\n $kind ROW\nCOLUMNS\n X ROW 1\nRHS\n R ROW .5\nRANGES\n RNG ROW $range\nENDATA\n"; value_type=Rational{BigInt})
        @test bound_value(only(problem.row_lower)) == lower
        @test bound_value(only(problem.row_upper)) == upper
    end

    maximum, minimum = string(typemax(Int)), string(typemin(Int))
    for (text, T, line, section) in (
        ("NAME SUM\nROWS\n E ROW\nCOLUMNS\n X ROW $maximum\n X ROW 1\nENDATA\n", Rational{Int}, 6, :COLUMNS),
        ("NAME SUM\nROWS\n E ROW\nCOLUMNS\n X ROW $minimum\n X ROW -1\nENDATA\n", Rational{Int}, 6, :COLUMNS),
        ("NAME RHS\nROWS\n N OBJ\nCOLUMNS\n X OBJ 1\nRHS\n R OBJ $minimum\nENDATA\n", Rational{Int}, 7, :RHS),
        ("NAME RANGE\nROWS\n L ROW\nCOLUMNS\n X ROW 1\nRHS\n R ROW $minimum\nRANGES\n RNG ROW 1\nENDATA\n", Rational{Int}, 9, :RANGES),
        ("NAME RANGE\nROWS\n G ROW\nCOLUMNS\n X ROW 1\nRANGES\n RNG ROW $minimum\nENDATA\n", Rational{Int}, 7, :RANGES),
        ("NAME SUM\nROWS\n N OBJ\nCOLUMNS\n X OBJ 3e38\n X OBJ 3e38\nENDATA\n", Float32, 6, :COLUMNS),
        ("NAME SUM\nROWS\n E ROW\nCOLUMNS\n X ROW 3e38\n X ROW 3e38\n X ROW -3e38\nENDATA\n", Float32, 6, :COLUMNS),
    )
        mktemp() do path, io
            write(io, text)
            close(io)
            error = try
                read_mps(path; value_type=T)
            catch exception
                exception
            end
            @test error isa MPSParseError
            if error isa MPSParseError
                @test error.source == path
                @test error.line == line
                @test error.section == section
            end
        end
    end
    # The absolute range magnitude can exceed T even when the endpoint fits.
    canceled = read_mps_text("NAME RANGE\nROWS\n G ROW\nCOLUMNS\n X ROW 1\nRHS\n R ROW $minimum\nRANGES\n RNG ROW $minimum\nENDATA\n"; value_type=Rational{Int})
    @test bound_value(only(canceled.row_lower)) == typemin(Int)
    @test bound_value(only(canceled.row_upper)) == 0
end

@testset "MPS model construction" begin
    root = joinpath(@__DIR__, "fixtures", "parser")
    @testset "bounds, ranges, and domains" begin
        problem = read_mps(joinpath(root, "bounds-and-ranges.mps"); format=:free)
        @test problem.variable_domains ==
              [INTEGER, INTEGER, BINARY, SEMI_CONTINUOUS, SEMI_INTEGER]
        @test bound_value.(problem.column_lower) == [-2.0, 0.0, 0.0, 2.0, 3.0]
        @test bound_value.(problem.column_upper) == [9.0, 1.0, 1.0, 10.0, 7.0]
        @test bound_value.(problem.row_lower) == [1.0, 5.0, 2.0]
        @test map(bound -> isfinite(bound) ? bound_value(bound) : nothing, problem.row_upper) == [5.0, 8.0, nothing]
        @test problem.objective_constant == -6.0
        @test problem.objective == [1.0, 0.0, 0.0, 0.0, 0.0]
        @test problem.row_names == ["EQ", "LE", "GE"]
        @test problem.column_names == ["XI", "XMARK", "XB", "XSC", "XSI"]
        @test Matrix(problem.A) == [1 0 0 0 1; 0 1 1 0 0; 0 0 0 1 0]
        @test problem.name == "DOMAINS"
        all_bounds = read_mps(joinpath(root, "all-bounds.mps"); format=:free)
        @test map(bound -> isfinite(bound) ? bound_value(bound) : nothing, all_bounds.column_lower) == [-2.0, 0.0, 3.0, nothing, nothing, 0.0]
        @test map(bound -> isfinite(bound) ? bound_value(bound) : nothing, all_bounds.column_upper) == [nothing, 5.0, 3.0, nothing, nothing, nothing]
        @test size(all_bounds.A) == (0, 6)
    end

    @testset "named set defaults and explicit selection" begin
        path = joinpath(root, "multiple-sets.mps")
        default = read_mps(path)
        @test bound_value.(default.row_lower) == [0.0]
        @test bound_value.(default.row_upper) == [1.0]
        @test bound_value.(default.column_upper) == [4.0]
        selected = read_mps(path; rhs_name="SECOND", ranges_name="WIDE", bounds_name="HIGH")
        @test bound_value.(selected.row_lower) == [-1.0]
        @test bound_value.(selected.row_upper) == [2.0]
        @test bound_value.(selected.column_upper) == [9.0]
        for kwargs in ((; rhs_name="MISSING"), (; ranges_name="MISSING"), (; bounds_name="MISSING"))
            @test_throws MPSParseError read_mps(path; kwargs...)
        end
        @test_throws MPSParseError read_mps(joinpath(root, "unsupported-quadratic.mps"))
    end

    @testset "objective precedence, duplicates, and defaults" begin
        text = "NAME OBJ\nOBJSENSE MAX\nOBJNAME SECOND\nROWS\n N FIRST\n L LIMIT\n N SECOND\nCOLUMNS\n X FIRST 2 LIMIT 3\n X SECOND 5 LIMIT -1\n X SECOND 4\nRHS\n R FIRST 7 SECOND -6\nENDATA\n"
        problem = read_mps_text(text)
        @test problem.objective == [9.0]
        @test problem.objective_sense == MAX_SENSE
        @test problem.objective_constant == 6.0
        @test Matrix(problem.A) == reshape([2.0], 1, 1)
        @test problem.row_names == ["LIMIT"]
        @test map(bound -> isfinite(bound) ? bound_value(bound) : nothing, problem.row_lower) == [nothing]
        @test bound_value.(problem.row_upper) == [0.0]
        override = read_mps_text(text; objective_name="FIRST")
        @test override.objective == [2.0]
        @test override.objective_constant == -7.0
        @test read_mps_text(replace(text, "OBJNAME SECOND\n" => "")).objective == [2.0]
        for name in ("MISSING", "LIMIT")
            @test_throws MPSParseError read_mps_text(text; objective_name=name)
        end
        @test_throws MPSParseError read_mps_text(replace(text, "OBJNAME SECOND" => "OBJNAME SECOND\nOBJNAME FIRST"))
        no_objective = read_mps_text("NAME ZERO\nROWS\n E EQ\n G GE\nCOLUMNS\n X EQ 1 GE 2\nENDATA\n")
        @test no_objective.objective == [0.0]
        @test no_objective.objective_constant == 0.0
        @test bound_value.(no_objective.row_lower) == [0.0, 0.0]
        @test map(bound -> isfinite(bound) ? bound_value(bound) : nothing, no_objective.row_upper) == [0.0, nothing]
        @test bound_value.(no_objective.column_lower) == [0.0]
        @test map(bound -> isfinite(bound) ? bound_value(bound) : nothing, no_objective.column_upper) == [nothing]
        @test no_objective.variable_domains == [CONTINUOUS]
        @test size(read_mps_text("NAME EMPTY\nROWS\nCOLUMNS\nENDATA\n").A) == (0, 0)
    end

    @testset "all range signs and missing RHS" begin
        for (kind, range, lower, upper) in [
            ("E", 3, 5.0, 8.0), ("E", -3, 2.0, 5.0), ("E", 0, 5.0, 5.0),
            ("L", 3, 2.0, 5.0), ("L", -3, 2.0, 5.0),
            ("G", 3, 5.0, 8.0), ("G", -3, 5.0, 8.0),
        ]
            problem = read_mps_text("NAME RANGE\nROWS\n $kind ROW\nCOLUMNS\n X ROW 1\nRHS\n R ROW 5\nRANGES\n RNG ROW $range\nENDATA\n")
            @test map(bound -> isfinite(bound) ? bound_value(bound) : nothing, problem.row_lower) ==
                  map(value -> isfinite(value) ? value : nothing, [lower])
            @test map(bound -> isfinite(bound) ? bound_value(bound) : nothing, problem.row_upper) ==
                  map(value -> isfinite(value) ? value : nothing, [upper])
        end
        problem = read_mps_text("NAME RANGE\nROWS\n G ROW\nCOLUMNS\n X ROW 1\nRANGES\n RNG ROW -2\nENDATA\n")
        @test bound_value.(problem.row_lower) == [0.0]
        @test bound_value.(problem.row_upper) == [2.0]
    end

    @testset "overflowing duplicate matrix coefficients retain source context" begin
        text = "NAME OVERFLOW\nROWS\n L R\nCOLUMNS\n X R 1e308\n X R 1e308\nENDATA\n"
        mktemp() do path, io
            write(io, text)
            close(io)
            error = try
                read_mps(path)
            catch exception
                exception
            end
            @test error isa MPSParseError
            if error isa MPSParseError
                @test error.source == path
                @test error.line == 6
                @test error.section == :COLUMNS
                @test occursin("finite", error.message)
            end
        end
    end

    @testset "finite RANGES arithmetic cannot create infinite endpoints" begin
        for (kind, rhs, range) in (("G", "1e308", "1e308"),
                                   ("G", "1e308", "-1e308"),
                                   ("L", "-1e308", "1e308"),
                                   ("L", "-1e308", "-1e308"),
                                   ("E", "1e308", "1e308"),
                                   ("E", "-1e308", "-1e308"))
            text = "NAME OVERFLOW\nROWS\n N OBJ\n $kind ROW\nCOLUMNS\n X OBJ -1 ROW 1\nRHS\n R ROW $rhs\nRANGES\n RNG ROW $range\nENDATA\n"
            mktemp() do path, io
                write(io, text)
                close(io)
                error = try
                    read_mps(path)
                catch exception
                    exception
                end
                @test error isa MPSParseError
                if error isa MPSParseError
                    @test error.source == path
                    @test error.line == 10
                    @test error.section == :RANGES
                    @test occursin("finite", error.message)
                end
            end
        end
        for (kind, rhs, range, lower, upper) in (
            ("G", "-1e308", "1e308", -1.0e308, 0.0),
            ("L", "1e308", "-1e308", 0.0, 1.0e308),
            ("E", "-1e308", "1e308", -1.0e308, 0.0),
            ("E", "1e308", "-1e308", 0.0, 1.0e308),
        )
            problem = read_mps_text("NAME FINITE\nROWS\n $kind ROW\nCOLUMNS\n X ROW 1\nRHS\n R ROW $rhs\nRANGES\n RNG ROW $range\nENDATA\n")
            @test map(bound -> isfinite(bound) ? bound_value(bound) : nothing, problem.row_lower) ==
                  map(value -> isfinite(value) ? value : nothing, [lower])
            @test map(bound -> isfinite(bound) ? bound_value(bound) : nothing, problem.row_upper) ==
                  map(value -> isfinite(value) ? value : nothing, [upper])
        end
        for section in ("RHS", "RANGES"), value in ("Inf", "-Inf", "NaN")
            @test_throws MPSParseError read_mps_text("NAME NONFINITE\nROWS\n G ROW\nCOLUMNS\n X ROW 1\n$section\n R ROW $value\nENDATA\n")
        end
    end

    bound_prefix = "NAME BOUNDS\nROWS\n N OBJ\nCOLUMNS\n X OBJ 1\nBOUNDS\n"
    @testset "objective selection diagnostics" begin
        for (metadata, line) in [("OBJNAME MISSING", 2), ("OBJNAME\n MISSING", 3),
                                 ("OBJNAME LIMIT", 2)]
            error = try
                read_mps_text("NAME BAD\n$metadata\nROWS\n N OBJ\n L LIMIT\nCOLUMNS\n X OBJ 1\nENDATA\n")
            catch exception
                exception
            end
            @test error isa MPSParseError
            if error isa MPSParseError
                @test error.line == line
                @test error.section == :OBJNAME
            end
        end
        error = try
            read_mps_text("NAME BAD\nROWS\n N OBJ\nCOLUMNS\n X OBJ 1\nENDATA\n"; objective_name="MISSING")
        catch exception
            exception
        end
        @test error isa MPSParseError
        if error isa MPSParseError
            @test error.line == 0
        end
    end
    @testset "bound order and special defaults" begin
        for (records, lower, upper, domain) in [
            (" SC B X 5", 1.0, 5.0, SEMI_CONTINUOUS),
            (" SI B X 5", 1.0, 5.0, SEMI_INTEGER),
            (" LO B X 2\n SC B X 5", 2.0, 5.0, SEMI_CONTINUOUS),
            (" SI B X 5\n LO B X 2", 2.0, 5.0, SEMI_INTEGER),
            (" LO B X 2\n SI B X 5", 2.0, 5.0, SEMI_INTEGER),
            (" UP B X -2", -Inf, -2.0, CONTINUOUS),
            (" UP B X -2\n LO B X -3", -3.0, -2.0, CONTINUOUS),
            (" LO B X -3\n UP B X -2", -3.0, -2.0, CONTINUOUS),
            (" LI B X -3\n UP B X -2", -3.0, -2.0, INTEGER),
            (" BV B X 1", 0.0, 1.0, BINARY),
            (" LI B X -2", -2.0, Inf, INTEGER),
            (" UI B X 4", 0.0, 4.0, INTEGER),
        ]
            problem = read_mps_text(bound_prefix * records * "\nENDATA\n")
            @test map(bound -> isfinite(bound) ? bound_value(bound) : nothing, problem.column_lower) ==
                  map(value -> isfinite(value) ? value : nothing, [lower])
            @test map(bound -> isfinite(bound) ? bound_value(bound) : nothing, problem.column_upper) ==
                  map(value -> isfinite(value) ? value : nothing, [upper])
            @test problem.variable_domains == [domain]
        end
    end

    @testset "contextual bound diagnostics" begin
        for record in [" LO B X", " UP B X", " FX B X", " LI B X", " UI B X",
                       " SC B X", " SI B X", " FR B X 1", " MI B X 0", " PL B X 1",
                       " BV B X 2", " LI B X 0.5", " UI B X 1.5", " UP B UNKNOWN 1",
                       " SC B X 0", " SI B X -1"]
            error = try
                read_mps_text(bound_prefix * record * "\nENDATA\n")
            catch exception
                exception
            end
            @test error isa MPSParseError
            if error isa MPSParseError
                @test error.line == 7
                @test error.section == :BOUNDS
                @test !isempty(error.source)
            end
        end
    end

    @testset "integrality and semi-domain declarations compose" begin
        marker_prefix = replace(bound_prefix, " X OBJ 1\n" =>
            " M0 'MARKER' 'INTORG'\n X OBJ 1\n M1 'MARKER' 'INTEND'\n")
        for (records, marker, lower, upper, domain, relaxed_lower) in (
            (" SC B X 10\n LI B X 3", false, 3.0, 10.0, SEMI_INTEGER, 0.0),
            (" LI B X 3\n SC B X 10", false, 3.0, 10.0, SEMI_INTEGER, 0.0),
            (" SC B X 10\n UI B X 8", false, 1.0, 8.0, SEMI_INTEGER, 0.0),
            (" UI B X 8\n SC B X 10", false, 1.0, 10.0, SEMI_INTEGER, 0.0),
            (" SC B X 10", true, 1.0, 10.0, SEMI_INTEGER, 0.0),
            (" LO B X -2\n SC B X 10", true, -2.0, 10.0, SEMI_INTEGER, -2.0),
            (" SC B X 10\n LI B X -2", false, -2.0, 10.0, SEMI_INTEGER, -2.0),
            (" LI B X -2\n SC B X 10", false, -2.0, 10.0, SEMI_INTEGER, -2.0),
            (" SI B X 10\n LO B X 3", false, 3.0, 10.0, SEMI_INTEGER, 0.0),
            (" SI B X 10\n SC B X 8", false, 1.0, 8.0, SEMI_INTEGER, 0.0),
            (" SC B X 10\n SI B X 8", false, 1.0, 8.0, SEMI_INTEGER, 0.0),
            (" SI B X 10\n LI B X 3", false, 3.0, 10.0, SEMI_INTEGER, 0.0),
            (" LI B X 3\n SI B X 10", false, 3.0, 10.0, SEMI_INTEGER, 0.0),
            (" LI B X -2\n UI B X 5", false, -2.0, 5.0, INTEGER, -2.0),
            (" SC B X 10", false, 1.0, 10.0, SEMI_CONTINUOUS, 0.0),
            (" LO B X -2\n SC B X 10", false, -2.0, 10.0, SEMI_CONTINUOUS, -2.0),
            (" SC B X 10\n LO B X -2", false, -2.0, 10.0, SEMI_CONTINUOUS, -2.0),
            (" FR B X\n SC B X 10", false, -Inf, 10.0, SEMI_CONTINUOUS, -Inf),
            (" BV B X", false, 0.0, 1.0, BINARY, 0.0),
            (" BV B X\n UI B X 4", false, 0.0, 1.0, BINARY, 0.0),
            (" UI B X 4\n BV B X", false, 0.0, 1.0, BINARY, 0.0),
            (" BV B X\n LI B X 0", false, 0.0, 1.0, BINARY, 0.0),
        )
            problem = read_mps_text((marker ? marker_prefix : bound_prefix) * records * "\nENDATA\n")
            @test problem.variable_domains == [domain]
            @test map(bound -> isfinite(bound) ? bound_value(bound) : nothing, problem.column_lower) ==
                  map(value -> isfinite(value) ? value : nothing, [lower])
            @test map(bound -> isfinite(bound) ? bound_value(bound) : nothing, problem.column_upper) ==
                  map(value -> isfinite(value) ? value : nothing, [upper])
            relaxed = JSimplex.relax_integrality(problem)
            @test relaxed.variable_domains == [CONTINUOUS]
            @test map(bound -> isfinite(bound) ? bound_value(bound) : nothing, relaxed.column_lower) ==
                  map(value -> isfinite(value) ? value : nothing, [relaxed_lower])
            @test map(bound -> isfinite(bound) ? bound_value(bound) : nothing, relaxed.column_upper) ==
                  map(value -> isfinite(value) ? value : nothing, [upper])
            @test map(bound -> isfinite(bound) ? bound_value(bound) : nothing, problem.column_lower) ==
                  map(value -> isfinite(value) ? value : nothing, [lower])
            @test solve(problem).status == MIP_NOT_SUPPORTED
            result = solve(problem; relax_integrality=true)
            @test result.status == (isfinite(relaxed_lower) ? OPTIMAL : UNBOUNDED)
            @test result.objective_value == (isfinite(relaxed_lower) ? relaxed_lower : nothing)
        end
    end

    @testset "binary and semi-domain declarations conflict in either order" begin
        for records in (" BV B X\n SC B X 10", " SC B X 10\n BV B X",
                        " BV B X\n SI B X 10", " SI B X 10\n BV B X")
            mktemp() do path, io
                write(io, bound_prefix * records * "\nENDATA\n")
                close(io)
                error = try
                    read_mps(path)
                catch exception
                    exception
                end
                @test error isa MPSParseError
                if error isa MPSParseError
                    @test error.source == path
                    @test error.line == 8
                    @test error.section == :BOUNDS
                    @test occursin("binary", error.message)
                    @test occursin("semi", error.message)
                end
            end
        end
    end

    @testset "fixed input and accumulator ownership" begin
        for format in (:fixed, :auto)
            problem = read_mps(joinpath(root, "basic-fixed.mps"); format)
            @test problem.objective == [1.0]
            @test bound_value.(problem.row_lower) == [2.0]
            @test map(bound -> isfinite(bound) ? bound_value(bound) : nothing, problem.row_upper) == [nothing]
        end
        records = JSimplex._parse_mps_file(joinpath(root, "bounds-and-ranges.mps"))
        before = deepcopy(records)
        first = JSimplex._build_mps(records)
        first.column_names[1] = "CHANGED"
        first.row_names[1] = "CHANGED"
        first.objective[1] = 99.0
        second = JSimplex._build_mps(records)
        @test second.column_names[1] == "XI"
        @test second.row_names[1] == "EQ"
        @test second.objective[1] == 1.0
        for field in fieldnames(typeof(records))
            if field == :bounds_sets
                @test [(b.kind, b.column, b.value, b.line) for b in records.bounds_sets["B"]] ==
                      [(b.kind, b.column, b.value, b.line) for b in before.bounds_sets["B"]]
            else
                @test getfield(records, field) == getfield(before, field)
            end
        end
    end
end
