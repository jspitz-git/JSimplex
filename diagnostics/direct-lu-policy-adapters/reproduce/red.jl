# UNEXECUTED: load only in a NEW master overlay containing the frozen OLD adapter.
using Test, SparseArrays, JSimplex
function run_direct_lu_policy_red()
    @testset "Missing direct policy contract (seven expected failures)" begin
        B = spzeros(0,0)
        for Factor in (JSimplex.ForrestTomlinFactorization,JSimplex.SuhlSuhlFactorization,
                       JSimplex.BartelsGolubFactorization), R in (:native,:markowitz)
            @test applicable(JSimplex._direct_lu_factor,Factor,B,Val(R),JSimplex._NATIVE_PIVOT_DEFAULT)
        end
        @test :pivot_policy in fieldnames(JSimplex.DirectLowerBackend)
    end
end
# No auto-run, factorization, solve, import probe or parser invocation here.
