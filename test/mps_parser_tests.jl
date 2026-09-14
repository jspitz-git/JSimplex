parse_mps_text(text; format=:free) =
    JSimplex._parse_mps(IOBuffer(text), "memory.mps"; format=format)

function fixed_mps_record(a="", b="", c="", d="", e="", f="")
    return " " * rpad(a, 2) * " " * rpad(b, 8) * "  " * rpad(c, 8) *
           "  " * rpad(d, 12) * "   " * rpad(e, 8) * "  " * rpad(f, 12)
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
end
