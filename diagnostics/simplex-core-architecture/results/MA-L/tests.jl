# MA-L UNEXECUTED tests; no imports, includes, timing, CLI or automatic invocation.
# Admission provides @test/@testset, aliases, frozen fixtures and source files.
function check_fixture(f)
    saved_precision=precision(BigFloat);saved_rounding=rounding(BigFloat)
    args=make_fixture(f)
    setprecision(BigFloat,f.ambient) do
        want=endpoint_oracle(args)
        @test want == f.expected
        before=snapshot(args)
        for fun in (JSimplex._equality_implies_column_bounds,reference_bounds,candidate_bounds)
            @test fun(args...) == want
            @test preserved(before,snapshot(args))
        end
        reset_trace!(args)
        try
            @test traced_bounds(args...) == want
            @test preserved(before,snapshot(args))
            t=MAL_TRACE[]
            @test t.position == f.route_position
            @test t.eligible == f.route_count
            @test t.additions == f.route_adds
            @test t.scratch == (f.route_position>0 ? 1 : 0)
            @test t.checked == f.route_adds
            if f.id=="same-denominator-after-selection"
                @test t.equal_denominator_adds >= 2
            end
        finally
            MAL_TRACE[]=nothing
        end
        if !isempty(f.alias)
            c=[x[2] for x in args[2]]
            if f.alias=="repeated"
                @test c[1] === c[2]
            elseif f.alias=="numerator"
                @test numerator(c[1]) === numerator(c[2])
            else
                @test denominator(c[1]) === denominator(c[2])
            end
        end
        if startswith(f.id,"lowbits-") && f.ambient==64 && !f.expected
            lossy=make_fixture(merge(f,(stored=64,)))
            @test endpoint_oracle(lossy) != want
        end
    end
    @test precision(BigFloat) == saved_precision
    @test rounding(BigFloat) == saved_rounding
end
function selection_boundaries(fixtures)
    @testset "selection_boundaries" begin
        for f in fixtures;f.group=="selection" && check_fixture(f);end
    end
end
function private_leaf_ownership(fixtures)
    @testset "private_leaf_ownership" begin
        for f in fixtures;f.group=="ownership" && check_fixture(f);end
    end
end
function exact_bound_decisions(fixtures)
    @testset "exact_bound_decisions" begin
        for f in fixtures;f.group=="boundary" && check_fixture(f);end
    end
end
function fallback_precision(fixtures)
    @testset "fallback_precision" begin
        for f in fixtures;f.group=="fallback" && check_fixture(f);end
    end
end
function tail_controls(fixtures)
    @testset "tail_controls" begin
        for f in fixtures;f.group=="tail" && check_fixture(f);end
    end
end
function snapshot_negative_control(fixtures)
    f=first(fixtures);args=make_fixture(f);s=snapshot(args)
    changed=copy(s.records);changed[1]=(changed[1][1]*"!",changed[1][2:end]...)
    @test !preserved(s,merge(s,(records=changed,)))
end
# Run only inside admitted expected-failure stage; exactly two expected route failures.
function original_route_red(fixtures)
    for id in ("target-160-1--1-0","target-160-8--1-0")
        f=only(x for x in fixtures if x.id==id);args=make_fixture(f);s=snapshot(args)
        @test reference_bounds(args...) == endpoint_oracle(args) == f.expected
        @test preserved(s,snapshot(args))
        reset_trace!(args)
        try
            @test reference_bounds(args...) == f.expected
            @test preserved(s,snapshot(args))
            @test MAL_TRACE[].scratch == 1
        finally
            MAL_TRACE[]=nothing
        end
    end
end
