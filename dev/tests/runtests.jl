using Test
using SHA
using TOML
using Pkg.Artifacts

const REPOSITORY_ROOT = normpath(joinpath(@__DIR__, "..", ".."))
include(joinpath(@__DIR__, "..", "datasets.jl"))
include(joinpath(@__DIR__, "..", "run_suite.jl"))
using .JSimplexDevSuite

@testset "Suite arguments and deterministic selection" begin
    manifest = load_dataset_manifest(joinpath(@__DIR__, "..", "datasets.toml"))
    @test select_datasets(manifest, parse_suite_args(String[])) == ["afiro"]
    options = parse_suite_args(["--dataset", "greenbea", "--dataset=afiro",
                                "--dataset", "afiro", "--tag", "netlib",
                                "--data-root=/private path", "--compare-glpk"])
    @test options.data_root == "/private path"
    @test options.compare_glpk
    @test select_datasets(manifest, options) == ["afiro", "greenbea"]
    @test select_datasets(manifest, parse_suite_args(["--tag=quick"])) == ["afiro"]
    for args in (["--unknown"], ["afiro"], ["--dataset"], ["--tag"],
                 ["--data-root"], ["--dataset="], ["--tag", "--compare-glpk"],
                 ["--compare-glpk=yes"], ["--data-root=a", "--data-root=b"])
        @test_throws ArgumentError parse_suite_args(args)
    end
    for args in (["--dataset=absent"], ["--tag=absent"],
                 ["--dataset=greenbea", "--tag=quick"])
        @test_throws ArgumentError select_datasets(manifest, parse_suite_args(args))
    end
end

@testset "GLPK reference and suite comparisons" begin
    afiro = joinpath(REPOSITORY_ROOT, "test/fixtures/solver/afiro.mps")
    reference = solve_with_glpk(afiro)
    @test reference.status == JSimplexDevSuite.OPTIMAL
    @test isapprox(reference.objective, -464.7531428571429; atol=1e-7)
    @test_throws ErrorException solve_with_glpk(joinpath(REPOSITORY_ROOT, "missing.mps"))
    @test glpk_status(JSimplexDevSuite.GLPK.GLP_NOFEAS) == JSimplexDevSuite.INFEASIBLE
    @test glpk_status(JSimplexDevSuite.GLPK.GLP_UNBND) == JSimplexDevSuite.UNBOUNDED
    @test isnothing(glpk_status(JSimplexDevSuite.GLPK.GLP_UNDEF))
    output = IOBuffer()
    errors = IOBuffer()
    @test suite_main(["--dataset=afiro", "--compare-glpk"]; io=output, err=errors) == 0
    @test occursin("afiro", String(take!(output)))
    @test isempty(String(take!(errors)))
    @test suite_main(["--unknown"]; io=output, err=errors) == 1
    @test occursin("--unknown", String(take!(errors)))
    manifest = load_dataset_manifest(joinpath(@__DIR__, "..", "datasets.toml"))
    mktemp() do path, stream
        manifest["datasets"]["afiro"]["expected_objective"] = 0.0
        TOML.print(stream, manifest)
        close(stream)
        @test suite_main(["--dataset=afiro"]; manifest_path=path,
                         repository_root=REPOSITORY_ROOT, io=output, err=errors) == 1
        @test occursin("objective", String(take!(errors)))
    end
    mktemp() do path, stream
        manifest["datasets"]["afiro"]["expected_status"] = "INFEASIBLE"
        TOML.print(stream, manifest)
        close(stream)
        @test suite_main(["--dataset=afiro"]; manifest_path=path,
                         repository_root=REPOSITORY_ROOT, io=output, err=errors) == 1
        @test occursin("status", String(take!(errors)))
    end
end
function check_argument_error(f, fragments...)
    error = try
        f()
        nothing
    catch exception
        exception
    end
    @test error isa ArgumentError
    if error isa ArgumentError
        for fragment in fragments
            @test occursin(fragment, sprint(showerror, error))
        end
    end
end

@testset "Development data registry" begin
    manifest = load_dataset_manifest(joinpath(@__DIR__, "..", "datasets.toml"))
    afiro = resolve_dataset(manifest, "afiro"; repository_root=REPOSITORY_ROOT)
    @test afiro == joinpath(REPOSITORY_ROOT, "test/fixtures/solver/afiro.mps")
    @test bytes2hex(open(sha256, afiro)) ==
          "28c80012b6e7da7df5d2e1e7220ee26e4f684a34b6958f77b14f0277225d65fd"
    @test isfile(resolve_dataset(manifest, "greenbea"; repository_root=REPOSITORY_ROOT))
    @test resolve_dataset(manifest, "afiro"; repository_root=REPOSITORY_ROOT,
                          data_root="/missing/private/data") == afiro
    check_argument_error("unknown", "--dataset") do
        resolve_dataset(manifest, "unknown"; repository_root=REPOSITORY_ROOT)
    end
    broken = deepcopy(manifest)
    broken["datasets"]["afiro"]["sha256"] = repeat("0", 64)
    check_argument_error("afiro", "SHA-256", "restore") do
        resolve_dataset(broken, "afiro"; repository_root=REPOSITORY_ROOT)
    end
    broken["datasets"]["afiro"]["kind"] = "invalid"
    check_argument_error("afiro", "kind", "datasets.toml") do
        resolve_dataset(broken, "afiro"; repository_root=REPOSITORY_ROOT)
    end
    mktempdir() do root
        check_argument_error("afiro", "repository_root") do
            resolve_dataset(manifest, "afiro"; repository_root=root)
        end
        mkpath(joinpath(root, "dev"))
        write(joinpath(root, "sample.mps"), "synthetic test data\n")
        checksum = bytes2hex(sha256("synthetic test data\n"))
        entry = Dict{String,Any}("kind" => "artifact", "artifact" => "test_collection",
                                "path" => "sample.mps", "sha256" => checksum)
        local_manifest = Dict("datasets" => Dict("sample" => entry),
                              "registry" => Dict("artifacts_toml" => "Artifacts.toml"))
        check_argument_error("sample", "Artifacts.toml", "--data-root") do
            resolve_dataset(local_manifest, "sample"; repository_root=root)
        end
        @test resolve_dataset(local_manifest, "sample"; repository_root=root,
                              data_root=root) == joinpath(root, "sample.mps")
        write(joinpath(root, "sample.mps"), "corrupted\n")
        check_argument_error("sample", "SHA-256", "restore") do
            resolve_dataset(local_manifest, "sample"; repository_root=root, data_root=root)
        end
        entry["path"] = "missing.mps"
        check_argument_error("sample", "--data-root") do
            resolve_dataset(local_manifest, "sample"; repository_root=root, data_root=root)
        end
        for path in ("../sample.mps", "/sample.mps", "nested/../../sample.mps")
            entry["path"] = path
            check_argument_error("sample", "relative", "datasets.toml") do
                resolve_dataset(local_manifest, "sample"; repository_root=root, data_root=root)
            end
        end
        entry["path"] = "escape.mps"
        symlink(joinpath(REPOSITORY_ROOT, "test/fixtures/solver/afiro.mps"),
                joinpath(root, "escape.mps"))
        check_argument_error("sample", "outside", "datasets.toml") do
            resolve_dataset(local_manifest, "sample"; repository_root=root, data_root=root)
        end
        entry["path"] = "sample.mps"
        check_argument_error("sample", "--data-root") do
            resolve_dataset(local_manifest, "sample"; repository_root=root,
                            data_root=joinpath(root, "absent"))
        end
        write(joinpath(root, "dev", "Artifacts.toml"), "# Local test bindings\n")
        check_argument_error("sample", "bind_artifact!", "--data-root") do
            resolve_dataset(local_manifest, "sample"; repository_root=root)
        end
        # A real local artifact exercises binding lookup without network access.
        hash = create_artifact() do artifact_root
            write(joinpath(artifact_root, "sample.mps"), "synthetic test data\n")
        end
        bind_artifact!(joinpath(root, "dev", "Artifacts.toml"), "test_collection", hash)
        @test resolve_dataset(local_manifest, "sample"; repository_root=root) ==
              joinpath(artifact_path(hash), "sample.mps")
        entry["sha256"] = repeat("0", 64)
        check_argument_error("sample", "SHA-256") do
            resolve_dataset(local_manifest, "sample"; repository_root=root)
        end
    end
end
