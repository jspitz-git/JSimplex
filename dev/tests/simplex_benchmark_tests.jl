using Test, TOML, SHA, JSimplex

const SIMPLEX_BENCHMARK_PATH = joinpath(@__DIR__, "..", "simplex_benchmarks.jl")
@testset "Numerical benchmark runner is available" begin
    @test isfile(SIMPLEX_BENCHMARK_PATH)
end
if isfile(SIMPLEX_BENCHMARK_PATH)
    include(SIMPLEX_BENCHMARK_PATH)
    using .JSimplexBenchmarks

    @testset "Stress reader budgets apply before full hashing and decompression" begin
        mktempdir() do root
            plain = joinpath(root, "big.mps")
            write(plain, repeat("* padding for bounded reader\n", 40000) *
                "NAME LIMIT\nROWS\n N COST\n E FIX\nCOLUMNS\n X COST 1 FIX 1\nRHS\n R FIX 1\nENDATA\n")
            compressed = plain * ".gz"
            run(pipeline(`gzip -c -- $plain`, stdout=compressed))
            for (input, operation) in ((plain, "reader"), (compressed, "reader"), (plain, "components"))
                output = joinpath(root, "result.toml")
                @test benchmark_main(["--file=" * input, "--mode=stress",
                    "--stress-operation=" * operation, "--time-limit=30",
                    "--memory-limit-mib=4096", "--read-limit-mib=1",
                    "--output=" * output]) == 0
                result = only(TOML.parsefile(output)["cases"])
                @test result["outcome"] == "resource_stop"
                @test !haskey(result, "rows")
                @test !haskey(result, "samples")
            end
        end
    end

    @testset "Report destinations cannot overwrite selected model inputs" begin
        mktempdir() do root
            path = joinpath(root,"input.mps")
            contents = "NAME KEEP\nROWS\n N COST\n E FIX\nCOLUMNS\n X COST 1 FIX 1\nRHS\n R FIX 1\nENDATA\n"
            write(path,contents)
            @test benchmark_main(["--file=" * path,"--output=" * path,"--samples=1","--algorithm=dual"]) == 1
            @test read(path,String) == contents
        end
    end

    @testset "Worker cancellation stops execution and quota stops have a distinct type" begin
        @test isdefined(JSimplexBenchmarks,:_bounded_wait)
        @test isdefined(JSimplexBenchmarks,:BenchmarkResourceLimit)
        if isdefined(JSimplexBenchmarks,:_bounded_wait) && isdefined(JSimplexBenchmarks,:BenchmarkResourceLimit)
            mktempdir() do root
                result = JSimplexBenchmarks.run_bounded(`sleep 10`,joinpath(root,"cancelled.log");
                    seconds=20.0,memory_mib=128,cancelled=()->true)
                @test result["outcome"] == "cancelled"
                source = joinpath(root,"input.mps")
                write(source,"more than one byte")
                @test_throws JSimplexBenchmarks.BenchmarkResourceLimit bounded_copy(source,
                    joinpath(root,"output.mps");byte_limit=1,seconds=10.0)
                @test !isfile(joinpath(root,"output.mps"))
            end
        end
    end

    @testset "Frozen generated cases have analytic LP references" begin
        for (name, objective) in (("degenerate-box",1),("scaled-diagonal",3),("phase-one",3))
            path = joinpath(@__DIR__,"..","..","test","fixtures","solver","generated",name * ".mps")
            problem = read_mps(path; value_type=Rational{BigInt})
            for algorithm in (:primal,:dual)
                result = solve(problem; options=SolverOptions(Rational{BigInt}; algorithm,verbose=false))
                @test result.status == JSimplex.OPTIMAL
                @test result.objective_value == objective
            end
        end
    end

    @testset "Known stress content cannot bypass exclusion by renaming" begin
        mktempdir() do root
            path, output, registry = joinpath(root,"renamed.mps"), joinpath(root,"report.toml"), joinpath(root,"registry.toml")
            write(path,"NAME COPIED\nROWS\n N COST\n E FIX\nCOLUMNS\n X COST 1 FIX 1\nRHS\n R FIX 1\nENDATA\n")
            digest = bytes2hex(open(sha256,path))
            open(registry,"w") do io
                TOML.print(io,Dict("cases"=>[Dict("id"=>"mps/big","collection"=>"mps","path"=>"big.mps",
                    "suites"=>["stress"],"decompressed_sha256"=>digest)]))
            end
            @test benchmark_main(["--file=" * path,"--samples=1","--algorithm=dual","--output=" * output];
                manifest_path=registry) == 1
            result = TOML.parsefile(output)["cases"][1]
            @test result["outcome"] == "input_error"
            @test !haskey(result,"samples")
        end
    end

    @testset "Input aliases are read-only and unavailable limits stay visible" begin
        mktempdir() do root
            source, alias = joinpath(root,"source.mps"), joinpath(root,"alias.mps")
            write(source,"preserve input bytes")
            Base.Filesystem.hardlink(source,alias)
            @test_throws ArgumentError bounded_copy(source,alias; byte_limit=1024,seconds=1.0)
            @test read(source,String) == "preserve input bytes"
            output = joinpath(root,"skipped.toml")
            withenv("PATH"=>"") do
                @test benchmark_main(["--file=" * source,"--mode=stress","--time-limit=1",
                    "--memory-limit-mib=128","--read-limit-mib=1","--output=" * output]) == 0
            end
            @test TOML.parsefile(output)["cases"][1]["outcome"] == "skipped"
        end
    end

    @testset "Reports preserve numerical failures, deadlines, and hash errors" begin
        mktempdir() do root
            path, output = joinpath(root,"overflow.mps"), joinpath(root,"report.toml")
            write(path, "NAME OVERFLOW\nROWS\n N COST\nCOLUMNS\n X COST 1e308\nBOUNDS\n LO B X 2\nENDATA\n")
            args = ["--file=" * path, "--algorithm=dual", "--samples=1", "--output=" * output]
            @test benchmark_main(vcat(args,["--time-limit=10"])) == 0
            sample = TOML.parsefile(output)["cases"][1]["samples"][1]
            @test sample["status"] == "NUMERICAL_ERROR"
            @test !haskey(sample,"objective")
            @test !sample["primal_error_available"]
            @test benchmark_main(vcat(args,["--time-limit=1e-12"])) == 0
            sample = TOML.parsefile(output)["cases"][1]["samples"][1]
            @test sample["status"] == "TIME_LIMIT"
            registry = joinpath(root,"cases.toml")
            open(registry,"w") do io
                TOML.print(io,Dict("cases"=>[Dict("id"=>"netlib/overflow","collection"=>"netlib",
                    "path"=>"overflow.mps","suites"=>["quick"],"source_sha256"=>repeat("0",64))]))
            end
            @test benchmark_main(["--netlib-root=" * root,"--samples=1","--output=" * output];
                manifest_path=registry) == 1
            failed = TOML.parsefile(output)["cases"][1]
            @test failed["outcome"] == "input_error"
            @test occursin("SHA-256 mismatch",failed["error"])
        end
    end

    @testset "Reader and component stress modes never report a simplex solve" begin
        mktempdir() do root
            source = joinpath(@__DIR__,"..","..","test","fixtures","solver","generated","phase-one.mps")
            path, output = joinpath(root,"big.mps"), joinpath(root,"stress.toml")
            cp(source,path)
            for (operation,outcome) in (("reader","completed_parse"),("components","component_completed"))
                # Component mode also compiles the bounded factor/update/pipeline
                # probes in a fresh worker. Keep its existing 60-second cap.
                seconds = operation == "components" ? 60 : 30
                @test benchmark_main(["--file=" * path,"--mode=stress","--stress-operation=" * operation,
                    "--time-limit=$seconds","--memory-limit-mib=4096","--read-limit-mib=1",
                    "--output=" * output]) == 0
                result = TOML.parsefile(output)["cases"][1]
                @test result["outcome"] == outcome
                @test !haskey(result,"samples")
                @test result["rows"] == 2
            end
        end
    end

    @testset "Corpus discovery ignores archives and logs" begin
        @test isdefined(JSimplexBenchmarks, :corpus_inventory)
        if isdefined(JSimplexBenchmarks, :corpus_inventory)
            mktempdir() do root
                for name in ("a.mps", "b.MPS.GZ", "collection.zip", "run.log")
                    write(joinpath(root,name), "inventory only")
                end
                options = parse_benchmark_args(["--netlib-root=" * root,
                    "--miplib-root=" * joinpath(root,"missing"), "--mps-root=" * root])
                inventory = JSimplexBenchmarks.corpus_inventory(options)
                @test inventory["netlib"]["mps_count"] == 1
                @test inventory["netlib"]["gzip_count"] == 1
                @test !inventory["miplib"]["available"]
            end
        end
    end

    @testset "Original dual errors detect an invalid optimality witness" begin
        @test isdefined(JSimplexBenchmarks, :original_dual_errors)
        if isdefined(JSimplexBenchmarks, :original_dual_errors)
            p = LinearProblem(JSimplex.sparse([1.0 1.0]), [1.0, 2.0]; row_lower=[1.0])
            errors = JSimplexBenchmarks.original_dual_errors(p, [1.0, 0.0], [1.0])
            @test errors["dual_sign_error"] == 0.0
            @test errors["complementarity_error"] == 0.0
            errors = JSimplexBenchmarks.original_dual_errors(p, [1.0, 0.0], [2.0])
            @test errors["dual_sign_error"] == 1.0
        end
    end

    @testset "Original-unit errors expose a falsely optimal candidate" begin
        @test isdefined(JSimplexBenchmarks, :original_primal_errors)
        if isdefined(JSimplexBenchmarks, :original_primal_errors)
            p = LinearProblem(JSimplex.sparse([1.0 1.0]), [1.0, 2.0]; row_lower=[1.0])
            errors = JSimplexBenchmarks.original_primal_errors(p, [0.5, 0.0], 0.5)
            @test errors["primal_error"] == 0.5
            @test errors["objective_error"] == 0.0
            errors = JSimplexBenchmarks.original_primal_errors(p, [1.0, 0.0], 2.0)
            @test errors["primal_error"] == 0.0
            @test errors["objective_error"] == 1.0
        end
    end

    @testset "Repair snapshots restore owned state and reject corruption" begin
        replay_path = joinpath(@__DIR__, "..", "simplex_replay.jl")
        @test isfile(replay_path)
        if isfile(replay_path)
            include(replay_path)
            mktempdir() do root
                p = JSimplex.LinearProblem(JSimplex.sparse([1.0 1.0]), [1.0, 2.0]; row_lower=[1.0])
                ws = JSimplex.initialize_workspace(p, JSimplex.SolverOptions(verbose=false))
                path = joinpath(root, "repair.bin")
                JSimplexReplay.save_snapshot(path, ws; original_hash=repeat("a",64))
                original = copy(ws.costs)
                fill!(ws.costs, 9.0)
                restored, metadata = JSimplexReplay.load_snapshot(path)
                @test restored.costs == original
                @test metadata["original_model_sha256"] == repeat("a",64)
                @test metadata["factorization_rebuilt"]
                result = JSimplex._solve_continuous_dual!(restored, () -> false)
                @test result.status == JSimplex.OPTIMAL
                @test result.objective_value == 1.0
                replay_output = joinpath(root,"replayed.toml")
                # The fresh worker includes compilation in its replay deadline.
                # This is a state-restoration test, not a cold-start timing gate.
                @test benchmark_main(["--replay=" * path,"--samples=1","--time-limit=60",
                    "--output=" * replay_output]) == 0
                @test TOML.parsefile(replay_output)["cases"][1]["status"] == "OPTIMAL"
                @test isdefined(JSimplexReplay, :TraceRecorder)
                if isdefined(JSimplexReplay, :TraceRecorder)
                    trace = JSimplexReplay.TraceRecorder(joinpath(root, "trace.bin"); byte_limit=1024*1024)
                    JSimplexReplay.record_trace!(trace, :phase_dual, restored)
                    JSimplexReplay.record_trace!(trace, :pivot_completed, restored)
                    records = JSimplexReplay.read_trace(trace.path)
                    @test [r.reason for r in records] == [:phase_dual, :pivot_completed]
                    @test records[1].state.basis.basic_indices == restored.basis.basic_indices
                    @test records[2].state.factorization !== restored.factorization
                    @test JSimplex.forward_solve(records[2].state.factorization,[1.0]) == [1.0]
                    tiny = JSimplexReplay.TraceRecorder(joinpath(root, "tiny.bin"); byte_limit=1)
                    JSimplexReplay.record_trace!(tiny, :phase_dual, restored)
                    @test tiny.truncated
                    @test filesize(tiny.path) <= 1
                end
                open(path, "a") do io
                    write(io, "corruption")
                end
                @test_throws ArgumentError JSimplexReplay.load_snapshot(path)
            end
        end
    end

    @testset "Oversized names are inspected without simplex work" begin
        mktempdir() do root
            path = joinpath(root, "AnyMOD.mps")
            write(path, repeat("bounded inspection input\n", 50000))
            output = joinpath(root, "stress.toml")
            @test benchmark_main(["--file=" * path, "--mode=stress", "--samples=1",
                "--time-limit=30", "--memory-limit-mib=4096", "--read-limit-mib=1",
                "--output=" * output]) == 0
            result = TOML.parsefile(output)["cases"][1]
            @test result["outcome"] == "partial_inspection"
            @test result["inspected_bytes"] == 1048576
            @test !haskey(result, "samples")
            @test !haskey(result, "source_sha256")
            @test result["prefix_sha256"] == bytes2hex(sha256(read(path)[1:1048576]))
        end
    end

    @testset "Benchmark reports retain input errors and isolated solve results" begin
        @test isdefined(JSimplexBenchmarks, :benchmark_main)
        if isdefined(JSimplexBenchmarks, :benchmark_main)
            mktempdir() do root
                output = joinpath(root, "results.toml")
                @test benchmark_main(["--file=" * joinpath(root, "missing.mps"),
                    "--samples=1", "--output=" * output]) == 1
                report = TOML.parsefile(output)
                @test report["cases"][1]["outcome"] == "input_error"
                fixture = normpath(joinpath(@__DIR__, "..", "..", "test", "fixtures", "solver", "afiro.mps"))
                @test benchmark_main(["--file=" * fixture, "--algorithm=dual", "--samples=1",
                    "--time-limit=10", "--output=" * output]) == 0
                result = TOML.parsefile(output)["cases"][1]
                @test result["samples"][1]["status"] == "OPTIMAL"
                @test result["samples"][1]["objective"] ≈ -464.7531428571429
                @test result["loaded_source"] == realpath(joinpath(@__DIR__, "..", "..", "src", "JSimplex.jl"))
                @test result["relax_integrality"]
                @test result["source_sha256"] == bytes2hex(open(sha256, fixture))
            end
        end
    end

    @testset "Worker watchdog enforces a deadline independently of the solver" begin
        @test isdefined(JSimplexBenchmarks, :run_bounded)
        if isdefined(JSimplexBenchmarks, :run_bounded)
            mktempdir() do root
                result = JSimplexBenchmarks.run_bounded(`sleep 10`, joinpath(root, "worker.log");
                    seconds=0.05, memory_mib=128)
                @test result["outcome"] == "resource_stop"
                @test result["exit_code"] in (124, 137)
                result = JSimplexBenchmarks.run_bounded(`true`, joinpath(root, "worker.log");
                    seconds=5.0, memory_mib=128)
                @test result["outcome"] == "completed"
            end
        end
    end

    @testset "Frozen solve selections preserve holdout separation" begin
        @test isdefined(JSimplexBenchmarks, :select_cases)
        if isdefined(JSimplexBenchmarks, :select_cases)
            options = parse_benchmark_args(String[])
            selected = JSimplexBenchmarks.select_cases(options)
            @test length(selected) == 8
            @test Set(case["id"] for case in selected) == Set([
                "netlib/afiro", "netlib/adlittle", "netlib/kb2", "netlib/sc50a",
                "miplib/pk1", "miplib/flugpl", "miplib/stein9inf", "miplib/markshare_4_0"])
            @test all(!stress_only(case["resolved_path"]) for case in selected)
            holdout = JSimplexBenchmarks.select_cases(parse_benchmark_args(["--suite=holdout"]))
            @test isempty(intersect(Set(c["decompressed_sha256"] for c in selected),
                                    Set(c["decompressed_sha256"] for c in holdout)))
        end
    end

    @testset "Benchmark arguments reject ambiguous or unbounded runs" begin
        o = parse_benchmark_args(["--algorithm=both", "--samples=7", "--time-limit=60"])
        @test o["algorithm"] == "both"
        @test o["samples"] == 7
        @test o["time-limit"] == 60.0
        for args in (["--unknown"], ["--samples=0"], ["--time-limit=Inf"],
                     ["--time-limit=NaN"], ["--algorithm=barrier"],
                     ["--samples=1", "--samples=2"], ["--file"],
                     ["--suite=stress"], ["--mode=stress", "--suite=quick"])
            @test_throws ArgumentError parse_benchmark_args(args)
        end
    end

    @testset "Stress-only classification survives aliases and compression" begin
        mktempdir() do root
            for name in ("big.mps", "LARGO.MPS", "AnyMod.mps.gz", "AnyMOD.mps")
                path = joinpath(root, name)
                write(path, "not a model")
                @test stress_only(path)
                @test_throws ArgumentError validate_selection(path, "solve")
                @test validate_selection(path, "stress") == realpath(path)
            end
            link = joinpath(root, "innocent.mps")
            symlink(joinpath(root, "big.mps"), link)
            @test stress_only(link)
            @test_throws ArgumentError validate_selection(link, "solve")
            for name in ("runtime.mps", "medium.mps")
                path = joinpath(root, name)
                write(path, "not a model")
                @test !stress_only(path)
                @test validate_selection(path, "solve") == realpath(path)
            end
            @test_throws ArgumentError validate_selection(joinpath(root, "missing.mps"), "solve")
        end
    end

    @testset "Bounded decompression preserves input and rejects truncation" begin
        mktempdir() do root
            content = "NAME SMALL\nROWS\n N COST\n E FIX\nCOLUMNS\n X COST 1 FIX 1\nRHS\n R FIX 2\nENDATA\n"
            source = joinpath(root, "model with spaces.mps")
            compressed = source * ".gz"
            write(source, content)
            run(pipeline(`gzip -c -- $source`, stdout=compressed))
            before = read(compressed)
            output = joinpath(root, "decompressed.mps")
            metadata = bounded_copy(compressed, output; byte_limit=1024, seconds=10.0)
            @test read(output, String) == content
            @test metadata["complete"]
            @test metadata["decompressed_sha256"] == bytes2hex(sha256(content))
            @test read(compressed) == before
            @test_throws Exception bounded_copy(compressed, output; byte_limit=10, seconds=10.0)
            @test !isfile(output)
            write(compressed, before[1:end-5])
            @test_throws Exception bounded_copy(compressed, output; byte_limit=1024, seconds=10.0)
            @test !isfile(output)
        end
    end
end
