using JSimplex, SparseArrays, Test

@testset "Exact presolve inequality proofs" begin
    JS = JSimplex
    Proofs = JS._InequalityProofs
    for T in (Float32, Float64)
        @testset "$T" begin
            @testset "Directional proof through an equality" begin
                p = LinearProblem(sparse(T[1 1 0; 1 0 1]), T[1, 0, 0];
                    row_lower=T[1, 0], row_upper=[nothing, T(0)],
                    column_lower=[nothing, T(0), nothing],
                    column_upper=[nothing, T(0), nothing])
                matrix = copy(p.A)
                cost = copy(p.objective)
                lower, upper = copy(p.row_lower), copy(p.row_upper)
                certs, _ = Proofs.infer(p)
                c = only(certs)
                @test c isa Proofs.DirectionCertificate
                @test c.row == 1 && c.side == :lower
                @test Proofs.check(p, c, nothing)[1] == -1
                active = Proofs.activate(p, certs)
                @test active.row_lower[1] == active.row_upper[1] == lower[1]
                @test active.row_lower[2] == active.row_upper[2] == lower[2]
                @test active.A == p.A == matrix
                @test active.objective == p.objective == cost
                @test active.A !== p.A && active.objective !== p.objective
                @test active.row_lower !== p.row_lower && active.row_upper !== p.row_upper
                @test p.row_lower == lower && p.row_upper == upper
                bad = Proofs.DirectionCertificate(c.row, c.side, c.columns, -c.values)
                @test_throws ArgumentError Proofs.activate(p, [bad])
                @test p.row_lower == lower && p.row_upper == upper
                limited, stats = Proofs.infer(p; expand_limit=0)
                @test isempty(limited)
                @test stats["proof_budget_rejections"] > 0

                calls = Ref(0)
                uninterrupted, _ = Proofs.infer(p; stop_requested=() -> (calls[] += 1; false))
                @test length(uninterrupted) == 1
                last_check = calls[]
                @test last_check > 1
                for stop_at in (1, last_check)
                    calls[] = 0
                    stopped, _ = Proofs.infer(p; stop_requested=() -> (calls[] += 1; calls[] >= stop_at))
                    @test isempty(stopped)
                    @test p.row_lower == lower && p.row_upper == upper
                end
            end

            @testset "Singleton box and exact obstruction" begin
                for sense in (JS.MIN_SENSE, JS.MAX_SENSE)
                    cost = sense == JS.MIN_SENSE ? T[1, 0] : T[-1, 0]
                    for upper in (T(4), prevfloat(T(3)))
                        p = LinearProblem(sparse(T[1 1]), cost;
                            objective_sense=sense, row_lower=T[3],
                            column_lower=T[0, 0], column_upper=T[upper, 2])
                        certs, _ = Proofs.infer(p)
                        if upper == T(4)
                            c = only(certs)
                            @test c isa Proofs.SingletonBoxCertificate
                            @test c.row == 1 && c.column == 1 && c.side == :lower
                            @test Proofs.activate(p, certs).row_upper[1] == p.row_lower[1]
                        else
                            @test isempty(certs)
                            c = Proofs.SingletonBoxCertificate(1, :lower, 1)
                            @test_throws ArgumentError Proofs.activate(p, [c])
                        end
                    end
                end
            end

            @testset "Individually valid directions conflict in a batch" begin
                p = LinearProblem(sparse(T[1 0; 1 1]), T[0, 0];
                    row_lower=[T(0), nothing], row_upper=[nothing, T(0)],
                    column_lower=[nothing, nothing], column_upper=[nothing, nothing])
                first = Proofs.DirectionCertificate(1, :lower, [1], [Proofs.Q(-1)])
                second = Proofs.DirectionCertificate(2, :upper, [2], [Proofs.Q(1)])
                @test Proofs.activate(p, [first]).row_upper[1] == p.row_lower[1]
                @test Proofs.activate(p, [second]).row_lower[2] == p.row_upper[2]
                @test_throws ArgumentError Proofs.activate(p, [first, second])
                @test_throws ArgumentError Proofs.activate(p, [second, first])
                @test !isfinite(p.row_upper[1]) && !isfinite(p.row_lower[2])
            end

            @testset "Work limit and stored zeros" begin
                p = LinearProblem(sparse(ones(T, 30, 1)), T[0]; row_upper=zeros(T, 30),
                    column_lower=[nothing], column_upper=[nothing])
                _, stats = Proofs.infer(p; work_limit=60)
                @test stats["term_visits"] <= 60
                @test stats["proof_edges"] <= 60
                @test stats["work_exhausted"] == 1

                p = LinearProblem(sparse(T[1 1]), T[0, 1]; row_lower=T[1],
                    column_lower=[nothing, nothing], column_upper=[nothing, nothing])
                p.A.nzval[1] = zero(T)
                stored = copy(p.A.nzval)
                certs, stats = Proofs.infer(p)
                @test isempty(certs)
                @test stats["stored_zero_declined"] == 1
                @test Proofs.activate(p, certs) === p
                @test p.A.nzval == stored
            end
        end
    end
end
