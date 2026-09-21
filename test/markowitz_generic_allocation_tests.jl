@testset "Markowitz magnitudes preserve stored precision and ownership" begin
    stored=setprecision(BigFloat,256) do
        [BigFloat(10)+ldexp(BigFloat(1),-40), -BigFloat(10)-ldexp(BigFloat(1),-40),
         ldexp(BigFloat(1),-1_000_000), -ldexp(BigFloat(1),1_000_000),
         BigFloat(0), -BigFloat(0), BigFloat(Inf), BigFloat(-Inf), BigFloat(NaN), -BigFloat(NaN)]
    end
    for bits in (24,128,512), mode in (RoundNearest,RoundUp,RoundDown,RoundToZero)
        setprecision(BigFloat,bits) do
            setrounding(BigFloat,mode) do
                for x in stored
                    before=deepcopy(x)
                    expected=JSimplex._pivot_magnitude(x)
                    actual=JSimplex._markowitz_magnitude(x)
                    @test isequal(actual,expected)
                    @test signbit(actual)==signbit(expected)
                    @test precision(actual)==precision(expected)
                    @test signbit(x) ? actual !== x : actual === x
                    @test precision(BigFloat)==bits
                    @test rounding(BigFloat)==mode
                    @test isequal(x,before)
                    @test JSimplex._markowitz_threshold_pass(actual,stored[1]) ==
                          JSimplex._markowitz_threshold_pass(expected,stored[1])
                end
            end
        end
    end
    positive=stored[1]
    JSimplex._markowitz_magnitude(positive)
    @test (@allocated JSimplex._markowitz_magnitude(positive)) == 0
    original=stored[2]; saved=deepcopy(original)
    result=JSimplex._markowitz_magnitude(original)
    ccall((:mpfr_set_si,Base.MPFR.libmpfr),Cint,
          (Ref{BigFloat},Clong,Base.MPFR.MPFRRoundingMode),result,Clong(1),Base.MPFR.MPFRRoundNearest)
    @test isequal(original,saved)
    @test result==1
end

function markowitz_rational_candidates(values,maximum)
    threshold=JSimplex._markowitz_column_threshold(maximum)
    count(x->JSimplex._markowitz_candidate_pass(x,threshold),values)
end
function markowitz_rational_reference(values,maximum)
    count(x->x>=maximum/Rational{BigInt}(10),values)
end

@testset "Markowitz exact rational column thresholds" begin
    for maximum in Rational{BigInt}[0,1,10,big(10)^100//3,1//big(10)^100,1//0],
        magnitude in Rational{BigInt}[0,1,10,big(10)^99//3,1//big(10)^101,1//0]
        expected=magnitude>=maximum/Rational{BigInt}(10)
        @test JSimplex._markowitz_threshold_pass(magnitude,maximum)==expected
        @test JSimplex._markowitz_candidate_pass(magnitude,
            JSimplex._markowitz_column_threshold(maximum))==expected
    end
    values=Rational{BigInt}[i//13 for i in 1:64]
    maximum=values[end]
    @test markowitz_rational_candidates(values,maximum)==markowitz_rational_reference(values,maximum)
    before=@allocated markowitz_rational_reference(values,maximum)
    after=@allocated markowitz_rational_candidates(values,maximum)
    @test after < before÷2
end
