module RecordedTests
using Test
mutable struct Capture <: Test.AbstractTestSet
    description::String
    passed::Int
    failed::Int
    errored::Int
    broken::Int
    failures::Vector{String}
    children::Vector{Capture}
end
Capture(s;kwargs...)=Capture(s,0,0,0,0,String[],Capture[])
Test.record(t::Capture,r::Test.Pass)=(t.passed+=1)
Test.record(t::Capture,r::Test.Fail)=(t.failed+=1;push!(t.failures,sprint(show,r));println(stderr,"TEST FAILURE: ",sprint(show,r));flush(stderr))
Test.record(t::Capture,r::Test.Error)=(t.errored+=1;push!(t.failures,sprint(show,r));println(stderr,"TEST FAILURE: ",sprint(show,r));flush(stderr))
Test.record(t::Capture,r::Test.Broken)=(t.broken+=1;println(stderr,"BROKEN TEST: ",sprint(show,r));flush(stderr))
Test.record(t::Capture,r::Capture)=push!(t.children,r)
function Test.finish(t::Capture)
    Test.get_testset_depth()>0 && Test.record(Test.get_testset(),t)
    t
end
function dictionary(t)
    Dict("name"=>t.description,"pass"=>t.passed,"fail"=>t.failed,"error"=>t.errored,"broken"=>t.broken,"failures"=>t.failures,"children"=>dictionary.(t.children))
end
end
