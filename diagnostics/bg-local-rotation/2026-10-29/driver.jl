include(joinpath(@__DIR__, "reused-prefix.jl"))
Base.include(J, joinpath(D, "candidate.jl"))
include(joinpath(D, "replay-core.jl"))

function component_checks()
    examples = ((sparse(Matrix{Float64}(I, 3, 3)), [1.,1.,0.], [2.,1.,4.], [-1.,3.,4.]),
                (sparse([1. 1. 0.; 0. 1. 0.; 0. 0. 1.]), [0.,1.,0.], [1.,2.,4.], [1.,2.,4.]))
    for backend in (Val(:native), Val(:markowitz)), localized in (false,true), (B,a,xf_expected,xb_expected) in examples
        old = copy(B); olda = copy(a)
        f = J._direct_lu_factor(J.BartelsGolubFactorization, B, backend, policy(backend); normalize=true)
        dir = zeros(3)
        J.forward_solve!(dir, f, a)
        if localized
            J._diagnostic_local_bg_replace!(f, dir, 1)
        else
            J.replace_column!(f, dir, 1)
        end
        x = zeros(3); y = zeros(3); rhs = [2.,3.,4.]
        J.forward_solve!(x, f, rhs); J.transpose_solve!(y, f, rhs)
        @test x == xf_expected
        @test y == xb_expected
        @test all(j -> all(i -> i <= j, f.upper[j].indices), 1:3)
        @test B == old && a == olda
        # Copy preserves the nonempty transformation chain; no new factor is built.
        saved = J.copy_basis_factorization(f)
        J.forward_solve!(x, saved, rhs); J.transpose_solve!(y, saved, rhs)
        @test x == xf_expected && y == xb_expected
    end
end

function run_local_bg()
    data = Dict{String,Any}("cold"=>Any[], "windows"=>Any[], "preparation"=>Any[],
        "scope"=>"private localized BG experiment, not production integration")
    arms = ((false,128), (true,128), (false,64), (true,64))
    for kind in ("band","blocks","sparse","dense")
        prep = @timed makecase(kind)
        c = prep.value; before = inputhash(c)
        push!(data["preparation"], Dict("fixture"=>kind, "seconds"=>prep.time, "bytes"=>prep.bytes,
            "events"=>Base.gc_alloc_count(prep.gcstats), "compile_seconds"=>prep.compile_time))
        for backend in (Val(:native), Val(:markowitz))
            bname = string(typeof(backend).parameters[1]); refs = Any[]; eligible = true
            for (localized, interval) in arms
                t = @timed replay_local(backend, c, interval, localized, true)
                r = t.value; @test r.ok; @test inputhash(c) == before; eligible &= r.ok
                signature = r.factor === nothing ? "" : digest_factor(r.factor)
                push!(refs, (initial=r.initial, signature=signature, dir=copy(r.dir), xf=copy(r.xf), xb=copy(r.xb), middle=copy(r.middle)))
                push!(data["cold"], Dict("fixture"=>kind, "backend"=>bname, "localized"=>localized,
                    "interval"=>interval, "ok"=>r.ok, "reason"=>r.reason, "updates"=>r.step,
                    "refactors"=>r.refactors, "seconds"=>t.time, "bytes"=>t.bytes,
                    "events"=>Base.gc_alloc_count(t.gcstats), "initial_factor_hash"=>r.initial,
                    "final_factor_hash"=>signature, "trace"=>r.trace))
                r = nothing; t = nothing
            end
            @test all(r -> r.initial == refs[1].initial, refs)
            if eligible
                GC.gc()
                for repetition in 0:5
                    for i in mod1.(collect(1:4) .+ repetition, 4)
                        localized, interval = arms[i]
                        t = @timed replay_local(backend, c, interval, localized, false)
                        r = t.value
                        @test r.ok && digest_factor(r.factor) == refs[i].signature
                        @test isequal((r.dir,r.xf,r.xb,r.middle), (refs[i].dir,refs[i].xf,refs[i].xb,refs[i].middle))
                        @test oracle(c,collect(1:c.n),r.xf,c.rhs,c.norms[end]) && oracle(c,collect(1:c.n),r.xb,c.rhs2,c.norms[end],true)
                        @test inputhash(c) == before
                        @test r.refactors == div(256,interval)-1
                        if repetition > 0
                            @test t.compile_time == t.recompile_time == 0
                        end
                        push!(data["windows"], Dict("fixture"=>kind,"backend"=>bname,"localized"=>localized,
                            "interval"=>interval,"repetition"=>repetition,"warm"=>repetition==0,
                            "seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),
                            "gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time,
                            "construct_seconds"=>r.clocks[1]/1e9,"ftran_seconds"=>r.clocks[2]/1e9,
                            "btran_seconds"=>r.clocks[3]/1e9,"update_seconds"=>r.clocks[4]/1e9,
                            "refactor_seconds"=>r.clocks[5]/1e9,"assembly_seconds"=>r.clocks[6]/1e9,
                            "updates"=>r.step,"refactors"=>r.refactors,"retained_bytes"=>Base.summarysize(r.factor)))
                        r = nothing; t = nothing
                    end
                end
            end
            open(joinpath(D,"results-1.toml"),"w") do io
                TOML.print(io,data)
            end
            println("COMPLETED ",kind,"/",bname," eligible=",eligible); flush(stdout)
        end
    end
end
@testset "Local BG component examples and copied history" begin
    component_checks()
end
@testset "Localized BG versus original BG" begin
    run_local_bg()
end
