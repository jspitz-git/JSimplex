using Test, JSimplex, SparseArrays

@testset "Primal feasibility predicate retains summary decisions" begin
    # A missing entry point is reported as a failed contract, not a load error.
    available=isdefined(JSimplex,:_primal_feasible)
    @test available
    if available
        for T in (Float16,Float32,Float64,BigFloat,Rational{Int},Rational{BigInt})
            tol=T(1//4)
            p=LinearProblem(spzeros(T,3,2),zeros(T,2);
                row_lower=zeros(T,3),row_upper=ones(T,3))
            ws=JSimplex.initialize_workspace(p,SolverOptions(T;primal_tolerance=tol,verbose=false))
            check=JSimplex._primal_feasible
            # Individually tolerated violations must not be added into rejection.
            ws.primal[3:5].=-tol
            @test check(ws)
            for position in 3:5, value in (-2tol,-tol,zero(T),one(T),one(T)+tol,one(T)+2tol)
                ws.primal[3:5].=zero(T)
                ws.primal[position]=value
                @test check(ws)==(-tol<=value<=one(T)+tol)
                @test check(ws)==(JSimplex.primal_infeasibility(ws)<=tol)
            end
            # Bounds apply only to basics in this predicate, like the summary.
            fill!(ws.primal,zero(T));ws.primal[1]=-T(100)
            @test check(ws)
            ws.lower[3]=JSimplex.Bound{T}(nothing)
            ws.upper[3]=JSimplex.Bound{T}(nothing)
            ws.primal[3]=-T(100)
            @test check(ws)
            ws.lower[4]=JSimplex.Bound(one(T));ws.upper[4]=JSimplex.Bound(one(T))
            ws.primal[4]=one(T)+tol
            @test check(ws)
            ws.primal[4]=one(T)+2tol
            @test !check(ws)
            if T <: AbstractFloat
                ws.primal[4]=one(T)
                for value in (-T(Inf),T(Inf),T(NaN),-zero(T),nextfloat(one(T)+tol),prevfloat(-tol))
                    ws.primal[5]=value
                    @test check(ws)==(JSimplex.primal_infeasibility(ws)<=tol)
                    if !isfinite(value)
                        @test !JSimplex._finite_workspace(ws)
                    end
                end
            end
        end
        for T in (Float32,Float64)
            p=LinearProblem(spzeros(T,3,1),zeros(T,1);
                row_lower=fill(-floatmax(T),3),row_upper=zeros(T,3))
            ws=JSimplex.initialize_workspace(p,SolverOptions(T;verbose=false))
            fill!(ws.primal,floatmax(T))
            @test !JSimplex._primal_feasible(ws)
            @test JSimplex._primal_feasible(ws)==(JSimplex.primal_infeasibility(ws)<=ws.options.primal_tolerance)
            fill!(ws.primal,zero(T))
            JSimplex._primal_feasible(ws)
            @test (@allocated JSimplex._primal_feasible(ws))==0
            p=LinearProblem(spzeros(T,0,0),T[])
            ws=JSimplex.initialize_workspace(p,SolverOptions(T;verbose=false))
            @test JSimplex._primal_feasible(ws)
            JSimplex._primal_feasible(ws)
            @test (@allocated JSimplex._primal_feasible(ws))==0
        end
        ws=setprecision(BigFloat,256) do
            p=LinearProblem(spzeros(BigFloat,2,1),zeros(BigFloat,1);
                row_lower=zeros(BigFloat,2),row_upper=ones(BigFloat,2))
            w=JSimplex.initialize_workspace(p,SolverOptions(BigFloat;primal_tolerance=BigFloat(1//4),verbose=false))
            w.primal[2]=-nextfloat(w.options.primal_tolerance)
            w
        end
        setprecision(BigFloat,64) do
            @test JSimplex._primal_feasible(ws)==(JSimplex.primal_infeasibility(ws)<=ws.options.primal_tolerance)
            @test precision(ws.options.primal_tolerance)==256
        end
    end
end
