# runtime_markowitz_cache_tests.jl supplies scan-counting dictionary wrappers.
@testset "Markowitz preserves maxima of unchanged columns" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        D = JSimplex.OrderedCollections.OrderedDict{Int,T}
        rows, columns = runtime_maximum_problem(T,D)
        cache = (zeros(T,3),falses(3))
        search() = JSimplex._markowitz_pivot(rows,columns,trues(4),trues(3),
            [1,2],Int[],BitSet([2,3]),cache,true)
        expected = JSimplex._markowitz_pivot(rows,columns,trues(4),trues(3),
            [1,2],Int[],BitSet([2,3]))
        foreach(c -> c.scans=0, columns)
        @test search() == expected
        @test [c.scans for c in columns] == [1,1,1]
        @test search() == expected
        @test [c.scans for c in columns] == [1,1,1]
        for row in (3,4)
            rows[row].data[1] = columns[1].data[row] = T(2)
        end
        cache[2][1] = false
        @test search() == (2,1)
        @test [c.scans for c in columns] == [2,1,1]
        @test cache[1][1] == T(2)
    end
end

@testset "Markowitz elimination invalidates affected column maxima" begin
    # Removing the first pivot row and applying its Schur update changes which
    # threshold-admissible pivot wins next. Stale maxima choose row 1 instead.
    B = JSimplex.sparse([
        2 0 0 0 0 0 0 0 0 100 -100 0;
        0 5 0 0 0 .01 0 0 0 .01 0 0;
        1 0 6 0 0 0 0 0 0 100 100 0;
        0 -100 0 1 0 0 0 100 0 0 -1 0;
        0 0 0 -100 3 1 0 0 0 0 0 -100;
        0 0 0 0 0 3 100 0 100 -1 0 0;
        0 0 100 0 -1 0 6 0 .01 0 0 0;
        0 100 0 0 -100 0 100 3 0 0 0 0;
        0 0 -100 0 0 -100 0 1 8 0 0 0;
        0 0 0 0 0 1 100 0 0 1 0 0;
        .01 0 0 0 0 -1 0 0 0 0 1 0;
        0 -100 0 0 0 .01 0 0 0 -1 0 9;
    ])
    backend = JSimplex.MarkowitzBackend(B)
    @test backend.row_order[1:2] == [5,12]
    @test backend.column_order[1:2] == [4,12]
    rhs = collect(1.0:12.0)
    result = similar(rhs)
    JSimplex._backend_forward_solve!(result,backend,rhs)
    @test B * result ≈ rhs
    JSimplex._backend_transpose_solve!(result,backend,rhs)
    @test B' * result ≈ rhs
end
