parse_mps_text(text; format=:free) =
    JSimplex._parse_mps(IOBuffer(text), "memory.mps"; format=format)

function fixed_mps_record(a="", b="", c="", d="", e="", f="")
    return " " * rpad(a, 2) * " " * rpad(b, 8) * "  " * rpad(c, 8) *
           "  " * rpad(d, 12) * "   " * rpad(e, 8) * "  " * rpad(f, 12)
end

@testset "Typed MPS numeric records" begin
    text = "NAME EXACT\nROWS\n N OBJ\n E EQ\nCOLUMNS\n X OBJ 1.25 EQ -2e-3\nRHS\n R EQ 3D+2\nENDATA\n"
    records = @inferred JSimplex._parse_mps(
        IOBuffer(text), "memory.mps", Rational{BigInt}; format=:free,
    )
    @test records isa JSimplex.MPSAccumulator{Rational{BigInt}}
    @test records.coefficients[1][3] == 5 // big(4)
    @test records.coefficients[2][3] == -1 // big(500)
    @test records.rhs_sets["R"][1][2] == 300 // big(1)

    float32_records = @inferred JSimplex._parse_mps(
        IOBuffer(text), "memory.mps", Float32; format=:free,
    )
    @test float32_records isa JSimplex.MPSAccumulator{Float32}
    @test float32_records.coefficients[1][3] === 1.25f0

    @test_throws MPSParseError JSimplex._parse_mps(
        IOBuffer(replace(text, "1.25" => "1e999999999999999999999")),
        "memory.mps", Rational{Int}; format=:free,
    )
    fixed_overflow = replace(text, "1.25" => string(big(typemax(Int)) + 1))
    error = try
        JSimplex._parse_mps(IOBuffer(fixed_overflow), "memory.mps",
                            Rational{Int}; format=:free)
    catch exception
        exception
    end
    @test error isa MPSParseError
    @test error.line == 6
    @test error.section == :COLUMNS

    @testset "exact decimal grammar and precision" begin
        for (token, expected) in (
            ("+.5", big(1) // 2), ("-2.", big(-2) // 1),
            (".125d+1", big(5) // 4), ("+001.2300E-2", big(123) // 10000),
            ("-0.000", big(0) // 1),
            ("9007199254740993", big(9007199254740993) // 1),
            ("0.123456789012345678901234567890", big"12345678901234567890123456789" // big"100000000000000000000000000000"),
        )
            parsed = JSimplex._parse_mps(IOBuffer(replace(text, "1.25" => token)),
                                        "memory.mps", Rational{BigInt}; format=:free)
            @test parsed.coefficients[1][3] == expected
        end
        for token in ("NaN", "Inf", "1//2", ".", "+", "1e", "1.2.3", "1e-999999999999999999999")
            @test_throws MPSParseError JSimplex._parse_mps(
                IOBuffer(replace(text, "1.25" => token)), "memory.mps",
                Rational{BigInt}; format=:free,
            )
        end
        for token in ("128", "0.001")
            error = try
                JSimplex._parse_mps(IOBuffer(replace(text, "1.25" => token)),
                                    "overflow.mps", Rational{Int8}; format=:free)
            catch exception
                exception
            end
            @test error isa MPSParseError
            if error isa MPSParseError
                @test (error.source, error.line, error.section) == ("overflow.mps", 6, :COLUMNS)
                @test occursin(token, error.message)
            end
        end
        for token in ("NaN", "Inf", "1e39")
            @test_throws MPSParseError JSimplex._parse_mps(
                IOBuffer(replace(text, "1.25" => token)), "memory.mps", Float32; format=:free,
            )
        end
        @test_throws ArgumentError JSimplex._parse_mps(IOBuffer(text), "memory.mps", Int)
    end

    @testset "typed fixed records, bounds, and file parsing" begin
        text = join(["NAME TYPED", "ROWS", fixed_mps_record("N", "OBJ"),
            fixed_mps_record("L", "LIMIT"), "COLUMNS",
            fixed_mps_record("", "M0", "'MARKER'", "", "'INTORG'"),
            fixed_mps_record("", "X", "OBJ", "1.25"),
            fixed_mps_record("", "", "LIMIT", "-.5"),
            fixed_mps_record("", "M1", "'MARKER'", "", "'INTEND'"),
            "RHS", fixed_mps_record("", "R", "LIMIT", "2.5"),
            "RANGES", fixed_mps_record("", "G", "LIMIT", "-.25"),
            "BOUNDS", fixed_mps_record("LO", "B", "X", "-.5"),
            fixed_mps_record("FR", "", "X"), "ENDATA"], '\n')
        for T in (Float32, BigFloat, Rational{Int}, Rational{BigInt}), format in (:fixed, :auto)
            records = JSimplex._parse_mps(IOBuffer(text), "memory.mps", T; format)
            @test records.coefficients == [("X", "OBJ", 5 // 4, 7), ("X", "LIMIT", -1 // 2, 8)]
            @test records.rhs_sets["R"] == [("LIMIT", 5 // 2, 11)]
            @test records.ranges_sets["G"] == [("LIMIT", -1 // 4, 13)]
            @test records.marker_domains == Dict("X" => INTEGER)
            @test records.bounds_order == ["B"]
            @test records.bounds_sets["B"] isa Vector{JSimplex.BoundRecord{T}}
            @test records.bounds_sets["B"][1].value == -1 // 2
            @test records.bounds_sets["B"][1].value isa T
            @test records.bounds_sets["B"][2].value === nothing
        end
        path = joinpath(@__DIR__, "fixtures", "parser", "basic-free.mps")
        records = @inferred JSimplex._parse_mps_file(path, Rational{BigInt}; format=:free)
        @test records.coefficients[1] == ("X", "COST", big(3) // 1, 9)
        @test JSimplex._parse_mps_file(path) isa JSimplex.MPSAccumulator{Float64}
    end
end

@testset "MPS symbolic parser" begin
    root = joinpath(@__DIR__, "fixtures", "parser")
    free_records = JSimplex._parse_mps_file(joinpath(root, "basic-free.mps"); format=:free)
    @test free_records.name == "BASICFREE"
    @test free_records.objective_sense == MAX_SENSE
    @test free_records.row_order == ["COST", "DEMAND", "CAPACITY"]
    @test free_records.column_order == ["X", "Y"]
    @test free_records.coefficients == [
        ("X", "COST", 3.0, 9), ("X", "DEMAND", 1.0, 9),
        ("X", "CAPACITY", 1.0, 10), ("Y", "COST", 2.0, 11),
        ("Y", "DEMAND", 1.0, 11), ("Y", "CAPACITY", 2.0, 12),
    ]
    @test free_records.rhs_sets["RHS1"] == [("DEMAND", 1.0, 14), ("CAPACITY", 4.0, 14)]
    fixed_records = JSimplex._parse_mps_file(joinpath(root, "basic-fixed.mps"); format=:fixed)
    @test fixed_records.name == "BASICFIX"
    @test fixed_records.objective_sense == MIN_SENSE
    @test fixed_records.column_order == ["X"]
    @test fixed_records.coefficients == [("X", "COST", 1.0, 6), ("X", "DEMAND", 1.0, 6)]
    @test fixed_records.rhs_sets["RHS1"] == [("DEMAND", 2.0, 8)]
    for (file, expected) in [("basic-fixed.mps", fixed_records), ("basic-free.mps", free_records)]
        actual = JSimplex._parse_mps_file(joinpath(root, file); format=:auto)
        @test actual.column_order == expected.column_order
        @test actual.coefficients == expected.coefficients
    end

    @testset "metadata, comments, and numeric records" begin
        records = parse_mps_text("""
            * leading comment
          NAME META
          OBJNAME
           COST
          OBJSEN
           MAX
          ROWS
           N COST
           E EQ
          COLUMNS
           X COST 1D+2 EQ -2d-1 \$ trailing data comment
           X EQ 3
          RHS
           FIRST EQ 2D0
           SECOND EQ 4
           FIRST COST -1
          RANGES
           NARROW EQ -2
           WIDE EQ 5
          BOUNDS
           LO LOW X -1
           FR HIGH X
          ENDATA
           * trailing comment
          """)
        @test records.objective_name == "COST"
        @test records.objective_sense == MAX_SENSE
        @test records.coefficients[1:2] == [("X", "COST", 100.0, 11), ("X", "EQ", -0.2, 11)]
        @test records.column_order == ["X"]
        @test records.row_types == Dict("COST" => 'N', "EQ" => 'E')
        @test records.rhs_order == ["FIRST", "SECOND"]
        @test records.ranges_order == ["NARROW", "WIDE"]
        @test records.bounds_order == ["LOW", "HIGH"]
        @test records.ranges_sets["NARROW"] == [("EQ", -2.0, 18)]
        bound = only(records.bounds_sets["LOW"])
        @test (bound.kind, bound.column, bound.value, bound.line) == (:LO, "X", -1.0, 21)
        @test only(records.bounds_sets["HIGH"]).value === nothing
        @test parse_mps_text("NAME P\nOBJSENSE MIN\nOBJNAME OBJ\nROWS\n N OBJ\nCOLUMNS\nENDATA\n").objective_name == "OBJ"
        padded_headers = "NAME PAD\n" * " "^30 * "ROWS\n N OBJ\n" *
                         " "^30 * "COLUMNS\n X OBJ 1\n" * " "^30 * "ENDATA\n"
        @test parse_mps_text(padded_headers; format=:auto).column_order == ["X"]
    end

    @testset "fixed continuations and marker domains" begin
        lines = ["NAME FIXED", "ROWS", fixed_mps_record("N", "OBJ"),
            fixed_mps_record("L", "LIMIT"), "COLUMNS",
            fixed_mps_record("", "MARK0", "'MARKER'", "", "'INTORG'"),
            fixed_mps_record("", "X", "OBJ", "1D0"),
            fixed_mps_record("", "", "LIMIT", "2"),
            fixed_mps_record("", "MARK1", "'MARKER'", "", "'INTEND'"),
            fixed_mps_record("", "Y", "OBJ", "3", "\$", "ignored"),
            "RHS", fixed_mps_record("", "R", "LIMIT", "4"),
            fixed_mps_record("", "", "OBJ", "5"),
            "RANGES", fixed_mps_record("", "G", "LIMIT", "6"),
            fixed_mps_record("", "", "LIMIT", "7"),
            "BOUNDS", fixed_mps_record("LO", "B", "X", "-2"),
            fixed_mps_record("UP", "", "X", "9"), "ENDATA"]
        for format in (:fixed, :auto)
            records = parse_mps_text(join(lines, '\n'); format)
            @test records.column_order == ["X", "Y"]
            @test records.marker_domains == Dict("X" => INTEGER)
            @test records.coefficients == [("X", "OBJ", 1.0, 7), ("X", "LIMIT", 2.0, 8), ("Y", "OBJ", 3.0, 10)]
            @test records.rhs_sets["R"] == [("LIMIT", 4.0, 12), ("OBJ", 5.0, 13)]
            @test records.ranges_sets["G"] == [("LIMIT", 6.0, 15), ("LIMIT", 7.0, 16)]
            @test [b.value for b in records.bounds_sets["B"]] == [-2.0, 9.0]
        end
        free = parse_mps_text("NAME P\nROWS\n N OBJ\nCOLUMNS\n M 'MARKER' 'INTORG'\n X OBJ 1\n M 'MARKER' 'INTEND'\n Y OBJ 2\nENDATA\n")
        @test free.marker_domains == Dict("X" => INTEGER)
        @test free.column_order == ["X", "Y"]
    end

    @testset "section keywords can be data names" begin
        for format in (:free, :fixed, :auto), metadata in ("OBJNAME ROWS", "OBJNAME\n ROWS")
            text = join(["NAME P", metadata, "ROWS", fixed_mps_record("N", "ROWS"),
                         "COLUMNS", fixed_mps_record("", "X", "ROWS", "1"), "ENDATA"], '\n')
            @test let parsed = parse_mps_text(text; format)
                (parsed.objective_name, parsed.row_order, parsed.column_order) ==
                    ("ROWS", ["ROWS"], ["X"])
            end
        end
        records = parse_mps_text("NAME P\nROWS\n N OBJ\nCOLUMNS\n NAME OBJ 1\n OBJSENSE OBJ 2\n OBJNAME OBJ 3\n QMATRIX OBJ 4\nRHS\n NAME OBJ 5\nENDATA\n")
        @test records.column_order == ["NAME", "OBJSENSE", "OBJNAME", "QMATRIX"]
        @test records.rhs_order == ["NAME"]
        lines = ["NAME P", "ROWS", fixed_mps_record("N", "NAME"),
            fixed_mps_record("L", "QMATRIX"), "COLUMNS",
            fixed_mps_record("", "X", "NAME", "1"),
            fixed_mps_record("", "", "NAME", "2"),
            fixed_mps_record("", "", "QMATRIX", "3"), "ENDATA"]
        for format in (:fixed, :auto)
            continued = parse_mps_text(join(lines, '\n'); format)
            @test continued.coefficients == [("X", "NAME", 1.0, 6), ("X", "NAME", 2.0, 7), ("X", "QMATRIX", 3.0, 8)]
        end
    end

    @testset "short free records in automatic format" begin
        text = "NAME SHORT\nROWS\n L LE\nCOLUMNS\n XB LE 1\nRHS\n R LE 2\nBOUNDS\n UP LOW XB 4\n SC B XB 5\nENDATA\n"
        records = parse_mps_text(text; format=:auto)
        @test records.column_order == ["XB"]
        @test records.coefficients == [("XB", "LE", 1.0, 5)]
        @test records.rhs_sets["R"] == [("LE", 2.0, 7)]
        @test records.bounds_order == ["LOW", "B"]
        @test only(records.bounds_sets["B"]).value == 5.0
    end

    @testset "trailing padding does not change automatic format" begin
        prefix = "NAME PADDED\nROWS\n N OBJ\nCOLUMNS\n X OBJ 1\nBOUNDS\n"
        for width in (20, 61), format in (:free, :auto)
            records = parse_mps_text(prefix * rpad(" UP B X 4", width) * "\nENDATA\n"; format)
            bound = only(records.bounds_sets["B"])
            @test (bound.kind, bound.column, bound.value) == (:UP, "X", 4.0)
        end
        fixed = join(["NAME PADDED", "ROWS", fixed_mps_record("N", "OBJ"),
            "COLUMNS", fixed_mps_record("", "X", "OBJ", "1"), "BOUNDS",
            fixed_mps_record("UP", "B", "X", "4"),
            fixed_mps_record("LO", "", "X", "2"), "ENDATA"], '\n')
        records = parse_mps_text(fixed; format=:auto)
        @test [(b.kind, b.column, b.value) for b in records.bounds_sets["B"]] ==
              [(:UP, "X", 4.0), (:LO, "X", 2.0)]
    end

    @testset "wide free BOUNDS spacing does not imply fixed fields" begin
        prefix = join(["NAME SPACING", "ROWS", fixed_mps_record("N", "OBJ"),
            "COLUMNS", fixed_mps_record("", "X", "OBJ", "1"), "BOUNDS"], '\n') * "\n"
        for record in (" UP B X         4", " UP B X                  4",
                       " UP           B X        4",
                       " UP B         X                        4",
                       " UP B         X                                  4",
                       " UP B         X                                                  4")
            for format in (:free, :auto)
                records = try
                    parse_mps_text(prefix * record * "\nENDATA\n"; format)
                catch exception
                    exception
                end
                @test records isa JSimplex.MPSAccumulator
                if records isa JSimplex.MPSAccumulator
                    @test records.bounds_order == ["B"]
                    bound = only(records.bounds_sets["B"])
                    @test (bound.kind, bound.column, bound.value) == (:UP, "X", 4.0)
                    @test bound_value.(JSimplex._build_mps(records).column_upper) == [4.0]
                end
            end
            @test_throws MPSParseError parse_mps_text(prefix * record * "\nENDATA\n"; format=:fixed)
        end
        text = prefix * fixed_mps_record("UP", "BOUNDS", "X", "4") * "\n" *
               fixed_mps_record("LO", "", "X", "2") * "\nENDATA\n"
        for format in (:auto, :fixed)
            records = parse_mps_text(text; format)
            @test records.bounds_order == ["BOUNDS"]
            problem = JSimplex._build_mps(records)
            @test bound_value.(problem.column_lower) == [2.0]
            @test bound_value.(problem.column_upper) == [4.0]
        end
        @test_throws MPSParseError parse_mps_text(text; format=:free)
    end

    @testset "automatic format preserves spaces in genuine fixed names" begin
        text = join(["NAME SPACES", "ROWS", fixed_mps_record("N", "O BJ"),
            fixed_mps_record("L", "L IMIT"), "COLUMNS",
            fixed_mps_record("", "X A", "O BJ", "1", "L IMIT", "2"),
            "RHS", fixed_mps_record("", "R HS", "L IMIT", "4"),
            "BOUNDS", fixed_mps_record("UP", "B SET", "X A", "4"),
            fixed_mps_record("LO", "", "X A", "2"), "ENDATA"], '\n')
        for format in (:auto, :fixed)
            records = try
                parse_mps_text(text; format)
            catch exception
                exception
            end
            @test records isa JSimplex.MPSAccumulator
            if records isa JSimplex.MPSAccumulator
                @test records.bounds_order == ["B SET"]
                problem = JSimplex._build_mps(records)
                @test problem.column_names == ["X A"]
                @test problem.row_names == ["L IMIT"]
                @test bound_value.(problem.row_upper) == [4.0]
                @test bound_value.(problem.column_lower) == [2.0]
                @test bound_value.(problem.column_upper) == [4.0]
            end
        end
    end

    @testset "diagnostics retain source, line, section, and reason" begin
        prefix = "NAME BAD\nROWS\n N OBJ\n L LIMIT\nCOLUMNS\n"
        cases = [
            ("NAME BAD\nROWS\n Z UNKNOWN\nENDATA\n", 3, :ROWS, "row type"),
            ("NAME BAD\nROWS\n N OBJ\n N OBJ\n", 4, :ROWS, "duplicate"),
            (prefix * " X MISSING 1\nENDATA\n", 6, :COLUMNS, "unknown row"),
            (prefix * " X OBJ\nENDATA\n", 6, :COLUMNS, "pair"),
            (prefix * " X OBJ 1 LIMIT\nENDATA\n", 6, :COLUMNS, "pair"),
            (prefix * " X OBJ nope\nENDATA\n", 6, :COLUMNS, "number"),
            (prefix * " X OBJ NaN\nENDATA\n", 6, :COLUMNS, "finite"),
            (prefix * " X OBJ 1e999\nENDATA\n", 6, :COLUMNS, "finite"),
            (prefix * "QMATRIX\n X X 1\nENDATA\n", 6, :QMATRIX, "unsupported"),
            (prefix * " FOO\nENDATA\n", 6, :FOO, "unsupported"),
            ("ROWS\n", 1, :ROWS, "NAME"),
            ("NAME BAD\nCOLUMNS\n", 2, :COLUMNS, "order"),
            (prefix * "ROWS\n", 6, :ROWS, "order"),
            (prefix * "OBJSENSE\n MAX\n", 6, :OBJSENSE, "order"),
            ("NAME BAD\nOBJSENSE\n MAX\nOBJSEN\n", 4, :OBJSENSE, "duplicate"),
            ("NAME BAD\nOBJSENSE\nROWS\n", 3, :OBJSENSE, "missing"),
            ("NAME BAD\nOBJSENSE\n OTHER\n", 3, :OBJSENSE, "sense"),
            (prefix * "BOUNDS\nRHS\n", 7, :RHS, "order"),
            (prefix * "RHS\nRHS\n", 7, :RHS, "duplicate"),
            (prefix * "RHS\n R MISSING 1\n", 7, :RHS, "unknown row"),
            (prefix * "RANGES\n G LIMIT\n", 7, :RANGES, "pair"),
            (prefix * "BOUNDS\n ZZ B X 1\n", 7, :BOUNDS, "bound type"),
            (prefix * " M 'MARKER' 'INTORG'\n X OBJ 1\nENDATA\n", 8, :ENDATA, "unterminated"),
            (prefix * " M 'MARKER' 'INTEND'\n", 6, :COLUMNS, "INTORG"),
            (prefix * " M 'MARKER' 'INTORG'\n M 'MARKER' 'INTORG'\n", 7, :COLUMNS, "nested"),
            (prefix * " M 'MARKER' 'OTHER'\n", 6, :COLUMNS, "marker"),
            (prefix * "ENDATA\n X OBJ 1\n", 7, :ENDATA, "after"),
            (prefix, 5, :COLUMNS, "ENDATA"),
        ]
        for (text, line, section, reason) in cases
            error = try
                parse_mps_text(text)
            catch exception
                exception
            end
            @test error isa MPSParseError
            if error isa MPSParseError
                @test error.source == "memory.mps"
                @test error.line == line
                @test error.section == section
                @test occursin(reason, error.message)
                @test occursin("memory.mps:$line [$section]", sprint(showerror, error))
            end
        end
        fixed_prefix = join(["NAME BAD", "ROWS", fixed_mps_record("N", "OBJ"),
                            fixed_mps_record("L", "LIMIT"), "COLUMNS"], '\n') * "\n"
        for (section, record) in [
            ("COLUMNS", fixed_mps_record("", "", "OBJ", "1")),
            ("RHS", fixed_mps_record("", "", "LIMIT", "1")),
            ("RANGES", fixed_mps_record("", "", "LIMIT", "1")),
            ("BOUNDS", fixed_mps_record("UP", "", "X", "1")),
        ]
            text = fixed_prefix * (section == "COLUMNS" ? "" : section * "\n") * record * "\nENDATA\n"
            error = try
                parse_mps_text(text; format=:fixed)
            catch exception
                exception
            end
            @test error isa MPSParseError
            if error isa MPSParseError
                @test error.section == Symbol(section)
                @test occursin("no preceding name", error.message)
            end
        end
        @test_throws ArgumentError parse_mps_text(prefix; format=:invalid)
    end

    @testset "all named BOUNDS sets receive symbolic validation" begin
        prefix = "NAME BOUNDS\nROWS\n N OBJ\nCOLUMNS\n X OBJ 1\nBOUNDS\n UP FIRST X 4\n"
        for (record, reason) in (
            (" FR SECOND UNKNOWN 1", "unknown column"),
            (" UP SECOND UNKNOWN 4", "unknown column"),
            (" LO SECOND X", "requires a value"),
            (" UP SECOND X", "requires a value"),
            (" FX SECOND X", "requires a value"),
            (" LI SECOND X", "requires a value"),
            (" UI SECOND X", "requires a value"),
            (" SC SECOND X", "requires a value"),
            (" SI SECOND X", "requires a value"),
            (" FR SECOND X 1", "does not accept"),
            (" MI SECOND X 0", "does not accept"),
            (" PL SECOND X 1", "does not accept"),
            (" BV SECOND X 2", "BV accepts"),
            (" LI SECOND X 0.5", "integral value"),
            (" UI SECOND X 1.5", "integral value"),
        )
            error = try
                parse_mps_text(prefix * record * "\nENDATA\n")
            catch exception
                exception
            end
            @test error isa MPSParseError
            if error isa MPSParseError
                @test error.source == "memory.mps"
                @test error.line == 8
                @test error.section == :BOUNDS
                @test occursin(reason, error.message)
            end
        end
    end
end
