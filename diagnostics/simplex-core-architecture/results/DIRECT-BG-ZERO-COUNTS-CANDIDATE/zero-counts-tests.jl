# UNEXECUTED. Definitions only; a future admitted harness must load the candidate
# once in a fresh parent with JSimplex and the frozen BGBlockedPanelTests fixtures.
module BGZeroCountsTests
using Test
import ..BGBlockedPanel
import ..BGBlockedPanelTests
const K = BGBlockedPanel
const T = BGBlockedPanelTests
const EXPECTED_ZERO = (0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)
decision_fields(d) = (d.start,d.count,d.accepted,d.reason,d.finite,d.counters)

function run_zero_counts_tests()
    @testset "zero statistics retain their complete immutable contract" begin
        # Catches wrong width/type/nonzero values in the shared initializer.
        @test K._BGB_ZERO_COUNTS isa NTuple{20,Int}
        @test !ismutabletype(typeof(K._BGB_ZERO_COUNTS))
        @test K._BGB_ZERO_COUNTS == EXPECTED_ZERO
        @test K.counts(K.BGNoCounts()) == EXPECTED_ZERO
        @test K.bump!(K.BGNoCounts(),Val(1),9) === nothing
        @test K.peak!(K.BGNoCounts(),9) === nothing
        @test K.counts(K.BGNoCounts()) == EXPECTED_ZERO
    end
    @testset "independent mutable counters and checked overflow at every slot" begin
        # Shared mutable counters, wrong slot updates, unchecked overflow, or a
        # nonzero default must fail. Expectations do not call candidate helpers.
        for i in 1:20
            a = K.BGPanelCounts()
            b = K.BGPanelCounts()
            @test a !== b
            @test K.counts(a) == EXPECTED_ZERO
            @test K.counts(b) == EXPECTED_ZERO
            saved = K.counts(a)
            @test K.bump!(a,Val(i)) === nothing
            @test K.counts(a) == Base.setindex(EXPECTED_ZERO,1,i)
            @test K.bump!(a,Val(i),2) === nothing
            @test K.counts(a) == Base.setindex(EXPECTED_ZERO,3,i)
            @test K.counts(b) == EXPECTED_ZERO
            @test saved == EXPECTED_ZERO
            @test K._BGB_ZERO_COUNTS == EXPECTED_ZERO
            @test K.counts(K.BGNoCounts()) == EXPECTED_ZERO
            a.values = Base.setindex(EXPECTED_ZERO,typemax(Int),i)
            before = K.counts(a)
            @test_throws OverflowError K.bump!(a,Val(i),1)
            @test K.counts(a) == before
            @test K.counts(b) == EXPECTED_ZERO
            @test K._BGB_ZERO_COUNTS == EXPECTED_ZERO
        end
    end
    @testset "peak replaces only its owning counter tuple" begin
        # Catches a shared mutable owner or peak overwriting another slot.
        a = K.BGPanelCounts()
        b = K.BGPanelCounts()
        K.bump!(a,Val(1),2)
        saved = K.counts(a)
        @test K.peak!(a,7) === nothing
        @test K.counts(a) == Base.setindex(Base.setindex(EXPECTED_ZERO,2,1),7,14)
        @test K.peak!(a,3) === nothing
        @test K.counts(a) == Base.setindex(Base.setindex(EXPECTED_ZERO,2,1),7,14)
        @test K.peak!(a,9) === nothing
        @test K.counts(a) == Base.setindex(Base.setindex(EXPECTED_ZERO,2,1),9,14)
        @test saved == Base.setindex(EXPECTED_ZERO,2,1)
        @test K.counts(b) == EXPECTED_ZERO
        @test K.counts(K.BGPanelCounts()) == EXPECTED_ZERO
        @test K._BGB_ZERO_COUNTS == EXPECTED_ZERO
    end
    @testset "dimension decisions preserve all fields and boundaries" begin
        # Literal hand-derived expectations; catches changed dimension/width gates
        # or incorrect fields hidden by merely inspecting accepted/rejected.
        cases = ((0,1,0,false), (32,1,0,false), (64,0,0,false),
                 (64,1,8,true), (64,60,4,false), (64,61,3,false),
                 (64,64,0,false), (96,33,8,true), (96,34,8,false),
                 (4096,4033,8,true), (4096,4034,8,false),
                 (4097,1,0,false), (typemax(Int),1,0,false))
        for (n,r,b,ok) in cases
            d = K._bgb_dimensions(n,r)
            @test d isa K.BGPanelDecision
            @test decision_fields(d) == (r,b,ok,ok ? :eligible : :dimensions,true,EXPECTED_ZERO)
        end
    end
    @testset "cheap eligibility returns zero decision without touching counters" begin
        # Uses the original concrete carrier. Catches accidental charged-counter
        # publication or input changes on the dimension-rejection path.
        f = T.carrier(zeros(32,32))
        before = T.snapshot(f)
        upper_owner = f.upper
        cache_owner = f.row_cache
        c = K.BGPanelCounts()
        K.bump!(c,Val(2),7)
        saved = K.counts(c)
        d = K._bgb_eligibility(f,1)
        counted = K._bgb_eligibility(f,1,c)
        @test decision_fields(d) == (1,0,false,:dimensions,true,EXPECTED_ZERO)
        @test decision_fields(counted) == decision_fields(d)
        @test K.counts(c) == saved
        @test f.upper === upper_owner
        @test f.row_cache === cache_owner
        @test isequal(T.snapshot(f),before)
        @test K._BGB_ZERO_COUNTS == EXPECTED_ZERO
    end
end
end
