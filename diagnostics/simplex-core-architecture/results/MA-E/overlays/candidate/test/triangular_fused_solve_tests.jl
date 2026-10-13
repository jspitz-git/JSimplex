using LinearAlgebra, SparseArrays
isdefined(@__MODULE__, :bg_replay_forward) || include("helpers/triangular_replay.jl")

@testset "Fused solve coordinate and buffer ownership" begin
    for Factor in (JSimplex.ForrestTomlinFactorization,JSimplex.SuhlSuhlFactorization,
                   JSimplex.BartelsGolubFactorization), T in (Float32,Float64,BigFloat)
        B=Matrix{T}(I,6,6); f=Factor(B)
        for (pivot,row,coefficient) in ((2,5,1//8),(1,4,-1//4),(3,6,1//16))
            a=copy(B[:,pivot]); a[row]+=T(coefficient)
            JSimplex.replace_column!(f,B\a,pivot); B[:,pivot]=a
        end
        for g in (f,JSimplex.copy_basis_factorization(f))
            rhs=T[1,-2,3,-4,5,-6]
            for transpose in (false,true)
                solve! = transpose ? JSimplex.transpose_solve! : JSimplex.forward_solve!
                reference=transpose ? bg_replay_transpose(g,rhs) : bg_replay_forward(g,rhs)
                for storage in (:separate,:same,:work_rhs,:spike_destination,:view_rhs)
                    source=copy(rhs); destination=similar(rhs)
                    storage==:same && (destination=source)
                    storage==:work_rhs && (source=copyto!(g.work,rhs))
                    storage==:spike_destination && (destination=g.spike)
                    storage==:view_rhs && (source=view(copy(rhs),:))
                    solve!(destination,g,source)
                    @test isequal(destination,reference)
                    @test (transpose ? B' : B)*destination≈rhs
                end
            end
        end
    end
end

@testset "Fused solve trivial and exceptional inputs" begin
    for Factor in (JSimplex.ForrestTomlinFactorization,JSimplex.SuhlSuhlFactorization,
                   JSimplex.BartelsGolubFactorization), n in (0,1,4)
        f=Factor(Matrix{Float64}(I,n,n))
        for rhs in (fill(-0.0,n),fill(Inf,n),fill(NaN,n),ones(n))
            @test isequal(JSimplex.forward_solve(f,rhs),bg_replay_forward(f,rhs))
            @test isequal(JSimplex.transpose_solve(f,rhs),bg_replay_transpose(f,rhs))
        end
    end
end

@testset "Copied BG saves logical prepared spike after coordinate rebasing" begin
    B=Matrix{Float64}(I,6,6); f=JSimplex.BartelsGolubFactorization(B)
    for (pivot,row,value) in ((2,5,0.125),(1,4,-0.25),(3,6,0.0625))
        a=copy(B[:,pivot]); a[row]+=value
        JSimplex.replace_column!(f,B\a,pivot); B[:,pivot]=a
    end
    g=JSimplex.copy_basis_factorization(f)
    a=copy(B[:,4]); a[6]+=0.125
    expected=similar(a)
    JSimplex._backend_forward_solve!(expected,g.base,a)
    for update in g.updates
        JSimplex._apply_row_update!(expected,update)
    end
    direction=JSimplex.forward_solve(g,a)
    @test JSimplex._copy_prepared_spike!(g,direction)
    @test isequal(g.spike,expected)
    JSimplex.replace_column!(g,direction,4); B[:,4]=a
    @test B*JSimplex.forward_solve(g,ones(6))≈ones(6)
    @test B'*JSimplex.transpose_solve(g,ones(6))≈ones(6)
end
