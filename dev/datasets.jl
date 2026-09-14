using TOML
using SHA
using Pkg.Artifacts

load_dataset_manifest(path) = TOML.parsefile(path)

function dataset_field(entry, key, name)
    value = get(entry, key, nothing)
    value isa AbstractString && !isempty(value) ||
        throw(ArgumentError("Dataset '$name' needs '$key'; correct dev/datasets.toml."))
    return value
end

function dataset_relative_path(root, path, name)
    # Reject lexical traversal and symlink escapes before returning any file.
    if isabspath(path) || any(==(".."), splitpath(path)) || path in ("", ".")
        throw(ArgumentError("Dataset '$name' needs a safe relative path; correct dev/datasets.toml."))
    end
    candidate = normpath(joinpath(abspath(root), path))
    if ispath(candidate) && isdir(root)
        relative = relpath(realpath(candidate), realpath(root))
        if isabspath(relative) || any(==(".."), splitpath(relative))
            throw(ArgumentError("Dataset '$name' resolves outside its data root; correct dev/datasets.toml."))
        end
    end
    return candidate
end

"""
    resolve_dataset(manifest, name; repository_root, data_root=nothing)

Resolve a repository instance or an installed artifact and check its SHA-256.
`data_root` replaces only the artifact root. Artifact bindings are read relative
to `repository_root/dev`; this function does not download data automatically.
"""
function resolve_dataset(manifest, name; repository_root, data_root=nothing)
    datasets = get(manifest, "datasets", Dict())
    haskey(datasets, name) ||
        throw(ArgumentError("Unknown dataset '$name'; choose --dataset NAME from dev/datasets.toml."))
    entry = datasets[name]
    kind = dataset_field(entry, "kind", name)
    path = dataset_field(entry, "path", name)
    checksum = dataset_field(entry, "sha256", name)
    occursin(r"^[0-9a-fA-F]{64}$", checksum) ||
        throw(ArgumentError("Dataset '$name' needs a 64-digit SHA-256; correct dev/datasets.toml."))
    if kind == "repository"
        root = repository_root
        remediation = "restore the checked-in file and set repository_root to the repository checkout"
    elseif kind == "artifact"
        binding = dataset_field(entry, "artifact", name)
        remediation = "install the collection with Pkg.Artifacts.ensure_artifact_installed or provide --data-root PATH"
        if isnothing(data_root)
            registry = get(manifest, "registry", Dict())
            bindings = dataset_relative_path(joinpath(repository_root, "dev"),
                get(registry, "artifacts_toml", "Artifacts.toml"), name)
            isfile(bindings) || throw(ArgumentError(
                "Dataset '$name' is missing $bindings; restore dev/Artifacts.toml or provide --data-root PATH."))
            hash = artifact_hash(String(binding), bindings)
            isnothing(hash) && throw(ArgumentError(
                "Dataset '$name' has no artifact binding '$binding'; use Pkg.Artifacts.bind_artifact! in dev/Artifacts.toml or provide --data-root PATH."))
            root = artifact_path(hash)
        else
            root = data_root
        end
    else
        throw(ArgumentError("Dataset '$name' has unknown kind '$kind'; correct dev/datasets.toml to use repository or artifact."))
    end
    isdir(root) || throw(ArgumentError("Dataset '$name' is missing data root '$root'; $remediation."))
    resolved = dataset_relative_path(root, path, name)
    isfile(resolved) || throw(ArgumentError("Dataset '$name' is missing file '$resolved'; $remediation."))
    actual = bytes2hex(open(sha256, resolved))
    actual == lowercase(checksum) || throw(ArgumentError(
        "Dataset '$name' SHA-256 mismatch for '$resolved' (expected $checksum, got $actual); restore the verified instance from its documented source."))
    return resolved
end
