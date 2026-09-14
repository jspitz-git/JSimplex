function read_mps_text(text; kwargs...)
    return mktemp() do path, io
        write(io, text)
        close(io)
        read_mps(path; kwargs...)
    end
end

@testset "MPS model construction" begin
    root = joinpath(@__DIR__, "fixtures", "parser")
    @testset "bounds, ranges, and domains" begin
        problem = read_mps(joinpath(root, "bounds-and-ranges.mps"); format=:free)
        @test problem.variable_domains ==
              [INTEGER, INTEGER, BINARY, SEMI_CONTINUOUS, SEMI_INTEGER]
        @test problem.column_lower == [-2.0, 0.0, 0.0, 2.0, 3.0]
        @test problem.column_upper == [9.0, 1.0, 1.0, 10.0, 7.0]
        @test problem.row_lower == [1.0, 5.0, 2.0]
        @test problem.row_upper == [5.0, 8.0, Inf]
        @test problem.objective_constant == -6.0
        @test problem.objective == [1.0, 0.0, 0.0, 0.0, 0.0]
        @test problem.row_names == ["EQ", "LE", "GE"]
        @test problem.column_names == ["XI", "XMARK", "XB", "XSC", "XSI"]
        @test Matrix(problem.A) == [1 0 0 0 1; 0 1 1 0 0; 0 0 0 1 0]
        @test problem.name == "DOMAINS"
        all_bounds = read_mps(joinpath(root, "all-bounds.mps"); format=:free)
        @test all_bounds.column_lower == [-2.0, 0.0, 3.0, -Inf, -Inf, 0.0]
        @test all_bounds.column_upper == [Inf, 5.0, 3.0, Inf, Inf, Inf]
        @test size(all_bounds.A) == (0, 6)
    end

    @testset "named set defaults and explicit selection" begin
        path = joinpath(root, "multiple-sets.mps")
        default = read_mps(path)
        @test default.row_lower == [0.0]
        @test default.row_upper == [1.0]
        @test default.column_upper == [4.0]
        selected = read_mps(path; rhs_name="SECOND", ranges_name="WIDE", bounds_name="HIGH")
        @test selected.row_lower == [-1.0]
        @test selected.row_upper == [2.0]
        @test selected.column_upper == [9.0]
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
        @test problem.row_lower == [-Inf]
        @test problem.row_upper == [0.0]
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
        @test no_objective.row_lower == [0.0, 0.0]
        @test no_objective.row_upper == [0.0, Inf]
        @test no_objective.column_lower == [0.0]
        @test no_objective.column_upper == [Inf]
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
            @test problem.row_lower == [lower]
            @test problem.row_upper == [upper]
        end
        problem = read_mps_text("NAME RANGE\nROWS\n G ROW\nCOLUMNS\n X ROW 1\nRANGES\n RNG ROW -2\nENDATA\n")
        @test problem.row_lower == [0.0]
        @test problem.row_upper == [2.0]
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
            @test problem.column_lower == [lower]
            @test problem.column_upper == [upper]
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

    @testset "fixed input and accumulator ownership" begin
        for format in (:fixed, :auto)
            problem = read_mps(joinpath(root, "basic-fixed.mps"); format)
            @test problem.objective == [1.0]
            @test problem.row_lower == [2.0]
            @test problem.row_upper == [Inf]
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
