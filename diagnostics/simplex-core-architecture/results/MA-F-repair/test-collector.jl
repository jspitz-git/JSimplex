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
