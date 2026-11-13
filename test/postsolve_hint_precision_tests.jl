module HintPrecisionTests
using JSimplex,Test,SparseArrays
const JS=JSimplex
@testset "Singular-hint unsupported arithmetic preserves stored precision and ownership" begin
    for T in (Float32,BigFloat),backend in (:native,:markowitz),
        (stored,working) in ((64,64),(128,128),(240,240),(512,512),(256,64),(64,256))
        p,target=setprecision(BigFloat,stored) do
            a=T===BigFloat ? one(BigFloat)+BigFloat(2)^(-stored+8) : T(1.25)
            LinearProblem(sparse(T[1 a;1 a]),T[0,0];row_lower=T[1,1],row_upper=T[1,1]),T[1,0]
        end
        original=deepcopy((p.A,p.objective,target))
        setprecision(BigFloat,working) do
            o=SolverOptions(T;verbose=false,presolve=false,scaling=:off,basis_update=:huangfu_hall,
                basis_refactorization=backend)
            w=JS.initialize_workspace(p,o)
            w.basis=JS.Basis([1,2],[JS.BASIC,JS.BASIC,JS.AT_LOWER,JS.AT_LOWER])
            numbers=deepcopy((w.basis.basic_indices,w.basis.states,w.primal,w.costs,w.lower,w.upper))
            f=w.factorization;calls=Ref(0)
            q=JS._repair_postsolve_hint(w,target,()->(calls[]+=1;false))
            @test isnothing(q) && calls[]==0 && w.factorization===f
            @test isequal(numbers,(w.basis.basic_indices,w.basis.states,w.primal,w.costs,w.lower,w.upper))
            @test isequal(original,(p.A,p.objective,target)) && precision(BigFloat)==working
            T===BigFloat && @test all(x->precision(x)==stored,p.A.nzval)
        end
    end
end
end
