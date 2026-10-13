# New stage-specific Test collector; no production methods are replaced.
using JSimplex, Test, TOML, SHA
const cfg = TOML.parsefile(ARGS[1])
realpath(pathof(JSimplex)) == realpath(joinpath(cfg["root"],"src/JSimplex.jl")) || error("wrong loaded source")
bytes2hex(sha256(read(joinpath(cfg["root"],"src/markowitz_factorization.jl")))) == cfg["source_sha256"] || error("source hash")
mutable struct RecordedTests <: Test.AbstractTestSet
    description::String
    counts::Vector{Int}
    nonpasses::Vector{Dict{String,Any}}
    children::Vector{RecordedTests}
end
RecordedTests(description;kwargs...) = RecordedTests(description,zeros(Int,4),Dict{String,Any}[],RecordedTests[])
function Test.record(ts::RecordedTests,r::Test.Result)
    kind = r isa Test.Pass ? 1 : r isa Test.Fail ? 2 : r isa Test.Error ? 3 : r isa Test.Broken ? 4 : error("unknown Test result")
    ts.counts[kind] += 1
    if kind != 1
        source = hasproperty(r,:source) ? r.source : nothing
        push!(ts.nonpasses,Dict("kind"=>kind,"expression"=>string(r.orig_expr),
            "file"=>(source === nothing ? "" : string(source.file)),
            "line"=>(source === nothing ? 0 : source.line),"display"=>sprint(show,r)))
    end
    return r
end
Test.record(ts::RecordedTests,child::RecordedTests) = (push!(ts.children,child); child)
function Test.finish(ts::RecordedTests)
    Test.get_testset_depth() > 0 && Test.record(Test.get_testset(),ts)
    return ts
end
function snapshot(ts)
    Dict("name"=>ts.description,"counts"=>ts.counts,"nonpasses"=>ts.nonpasses,"children"=>snapshot.(ts.children))
end
function total(ts)
    counts=copy(ts.counts)
    for child in ts.children;counts .+= total(child);end
    return counts
end
const before_precision=precision(BigFloat)
const before_rounding=string(rounding(BigFloat))
const records=Any[]
const errors=String[]
for file in cfg["files"]
    bytes2hex(sha256(read(file))) == cfg["file_hashes"][file] || error("test hash")
    ts=RecordedTests(file)
    parent_testset=Test.get_testset()
    parent_depth=Test.get_testset_depth()
    try
        Test.@with_testset ts begin
            Base.include(Main,file)
        end
    catch err
        push!(errors,sprint(showerror,err,catch_backtrace()))
    finally
        Test.get_testset() === parent_testset && Test.get_testset_depth() == parent_depth || error("test scope restoration")
        push!(records,Dict("file"=>file,"tree"=>snapshot(ts),"counts"=>total(ts)))
    end
    println("completed ",file," counts=",total(ts)); flush(stdout)
    isempty(errors) || break
end
const ambient_ok=precision(BigFloat)==before_precision && string(rounding(BigFloat))==before_rounding
const all_passed=isempty(errors) && ambient_ok && length(records)==length(cfg["files"]) && all(r["counts"][2:4]==[0,0,0] for r in records)
const raw=Dict("stage"=>cfg["stage"],"source"=>pathof(JSimplex),"Julia_version"=>string(VERSION),
    "before_precision"=>before_precision,"before_rounding"=>before_rounding,
    "after_precision"=>precision(BigFloat),"after_rounding"=>string(rounding(BigFloat)),
    "ambient_ok"=>ambient_ok,"files"=>records,"errors"=>errors,"all_passed"=>all_passed)
open(joinpath(cfg["output"],"tests.toml"),"w") do io;TOML.print(io,raw);end
for r in records;println(r["file"]," counts=",r["counts"]);end
exit(all_passed ? 0 : 1)
