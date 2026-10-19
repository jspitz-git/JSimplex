# Diagnostic-only counters. No production methods changed except Test's own custom testset API.
module HarnessRecords
using Test
export @check, @checkthrows
const active=Ref("")
const sites=Dict{String,Int}()
const events=Dict{String,Int}()
const apis=Dict{String,Int}()
const failures=Vector{Dict{String,String}}()
const failure_count=Ref(0)
function reset!()
    empty!(sites);empty!(events);empty!(apis);empty!(failures);failure_count[]=0;active[]=""
end
tick(s)=(events[s]=get(events,s,0)+1;nothing)
function api(kind,f,args...;kwargs...)
    apis[kind]=get(apis,kind,0)+1
    f(args...;kwargs...)
end
function enter!(id)
    isempty(active[]) || error("Nested assertion instrumentation")
    sites[id]=get(sites,id,0)+1;active[]=id
end
macro check(id,ex)
    test=Expr(:macrocall,GlobalRef(Test,Symbol("@test")),__source__,esc(ex))
    quote
        enter!($(esc(id)))
        try $test finally active[]="" end
    end
end
macro checkthrows(id,typ,ex)
    test=Expr(:macrocall,GlobalRef(Test,Symbol("@test_throws")),__source__,esc(typ),esc(ex))
    quote
        enter!($(esc(id)))
        try $test finally active[]="" end
    end
end
mutable struct Capture <: Test.AbstractTestSet
    description::String
    passed::Int
    failed::Int
    errored::Int
    broken::Int
    children::Vector{Capture}
end
Capture(s;kwargs...)=Capture(s,0,0,0,0,Capture[])
Test.record(t::Capture,r::Test.Pass)=(t.passed+=1)
function failure!(r,kind)
    failure_count[]+=1
    # Fixed bounded diagnostic output; overflow makes the auditor reject.
    if failure_count[]<=200
        push!(failures,Dict("site"=>active[],"kind"=>kind,"detail"=>sprint(show,r)))
        println(stderr,"TEST FAILURE: ",active[]," ",sprint(show,r));flush(stderr)
    end
end
Test.record(t::Capture,r::Test.Fail)=(t.failed+=1;failure!(r,"fail"))
Test.record(t::Capture,r::Test.Error)=(t.errored+=1;failure!(r,"error"))
Test.record(t::Capture,r::Test.Broken)=(t.broken+=1;failure!(r,"broken"))
Test.record(t::Capture,r::Capture)=push!(t.children,r)
function Test.finish(t::Capture)
    Test.get_testset_depth()>0 && Test.record(Test.get_testset(),t)
    t
end
function dictionary(t)
    Dict("name"=>t.description,"pass"=>t.passed,"fail"=>t.failed,"error"=>t.errored,"broken"=>t.broken,"children"=>dictionary.(t.children))
end
snapshot()=Dict("sites"=>copy(sites),"events"=>copy(events),"apis"=>copy(apis),"failures"=>copy(failures),"failure_count"=>failure_count[],"active"=>active[])
end
