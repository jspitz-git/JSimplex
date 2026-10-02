# Isolate presolve rejection from simplex behavior without changing production.
const CORPUS_PATH=joinpath(@__DIR__,"broad_corpus.jl")
source=read(CORPUS_PATH,String)
needle="simplex_strategy=:adaptive,iteration_limit=1_000_000"
@assert count(needle,source)==1
source=replace(source,needle=>"presolve=false,"*needle)
needle="\"weak_pivot_preference\"=>false,\"original_retry_enabled\"=>false,\"records\"=>records"
@assert count(needle,source)==1
source=replace(source,needle=>"\"presolve\"=>false,"*needle)
needle="hashes=instrument!()"
@assert count(needle,source)==1
const PRESOLVE_DISABLED_SOURCE=source
source=replace(source,needle=>needle*"\nhashes[\"presolve_disabled_runner\"]=bytes2hex(sha256(Main.PRESOLVE_DISABLED_SOURCE))")
Base.include_string(Main,source,CORPUS_PATH)
