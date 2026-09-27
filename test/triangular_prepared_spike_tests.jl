using LinearAlgebra, SparseArrays
@testset "Prepared triangular spikes follow the exact forward output" begin
    available = isdefined(JSimplex, :_copy_prepared_spike!)
    @test available
    if available
        for Factor in (JSimplex.ForrestTomlinFactorization,
                       JSimplex.SuhlSuhlFactorization,JSimplex.BartelsGolubFactorization),
            T in (Float32,Float64)
            B=Matrix{T}(I,5,5)
            f=Factor(B)
            B[:,1]=T[2,1,0,1,0]
            JSimplex.replace_column!(f,B[:,1],1)
            rhs=T[3,2,1,4,2]
            expected=zeros(T,5)
            JSimplex._backend_forward_solve!(expected,f.base,rhs)
            JSimplex._apply_dense_row_updates!(expected,f)
            direction=JSimplex.forward_solve(f,rhs)
            # An intervening edge-weight FTRAN and a BTRAN both overwrite
            # ordinary factor scratch, but must preserve this prepared column.
            other=JSimplex.forward_solve(f,ones(T,5))
            JSimplex.transpose_solve(f,ones(T,5))
            @test JSimplex._copy_prepared_spike!(f,direction)
            @test isequal(f.spike,expected)
            @test !JSimplex._copy_prepared_spike!(f,copy(direction))
            saved=copy(direction)
            direction[2]+=T(1//8)
            @test !JSimplex._copy_prepared_spike!(f,direction)
            copyto!(direction,saved)
            @test JSimplex._copy_prepared_spike!(f,direction)
            copied=JSimplex.copy_basis_factorization(f)
            @test !JSimplex._copy_prepared_spike!(copied,direction)
            @test_throws SingularException JSimplex.refactorize!(f,zeros(T,5,5))
            @test JSimplex._copy_prepared_spike!(f,direction)
            JSimplex.replace_column!(f,direction,2)
            B[:,2]=rhs
            @test !JSimplex._copy_prepared_spike!(f,direction)
            @test B*JSimplex.forward_solve(f,ones(T,5))≈ones(T,5)
            @test B'*JSimplex.transpose_solve(f,ones(T,5))≈ones(T,5)
            JSimplex.forward_solve!(direction,f,rhs)
            @test JSimplex._copy_prepared_spike!(f,direction)
            JSimplex.refactorize!(f,Matrix{T}(I,3,3))
            @test !JSimplex._copy_prepared_spike!(f,direction)
            small=JSimplex.forward_solve(f,ones(T,3))
            @test JSimplex._copy_prepared_spike!(f,small)
            JSimplex.forward_solve(f,T[1,2,3])
            JSimplex.forward_solve(f,T[3,2,1])
            @test !JSimplex._copy_prepared_spike!(f,small)
            # Reusing one output buffer for another RHS replaces its entry.
            out=zeros(T,3)
            JSimplex.forward_solve!(out,f,T[2,3,4])
            JSimplex.forward_solve!(out,f,T[4,3,2])
            @test JSimplex._copy_prepared_spike!(f,out)
            @test f.spike==T[4,3,2]
            JSimplex.forward_solve!(out,f,T[Inf,1,2])
            copyto!(out,T[4,3,2])
            @test !JSimplex._copy_prepared_spike!(f,out)
            JSimplex.forward_solve!(out,f,T[0,2,3])
            @test !JSimplex._copy_prepared_spike!(f,view(out,:))
            out[1]=-zero(T)
            @test !JSimplex._copy_prepared_spike!(f,out)
        end
        for T in (BigFloat,Rational{BigInt})
            f=JSimplex.ForrestTomlinFactorization(Matrix{T}(I,3,3))
            direction=JSimplex.forward_solve(f,ones(T,3))
            @test !JSimplex._copy_prepared_spike!(f,direction)
        end
    end
end

@testset "Other solve destinations cannot retain FTRAN provenance" begin
    for Factor in (JSimplex.ForrestTomlinFactorization,
                   JSimplex.SuhlSuhlFactorization,JSimplex.BartelsGolubFactorization)
        f=Factor(Matrix{Float64}(I,2,2))
        JSimplex.replace_column!(f,[2.0,0.0],1)
        direction=JSimplex.forward_solve(f,[nextfloat(0.0),1.0])
        @test direction==[0.0,1.0]
        @test JSimplex._copy_prepared_spike!(f,direction)
        JSimplex.transpose_solve!(direction,f,[0.0,1.0])
        @test !JSimplex._copy_prepared_spike!(f,direction)
        # Private scratch is an accepted solve destination, but cannot retain
        # provenance because unrelated operations are allowed to overwrite it.
        JSimplex.forward_solve!(f.spike,f,[1.0,1.0])
        @test !JSimplex._copy_prepared_spike!(f,f.spike)
        for transposed in (false,true), mode in (:dense,:sparse)
            dest=JSimplex.IndexedVector{Float64}(2)
            rhs=JSimplex.IndexedVector{Float64}(2)
            JSimplex.set_entry!(rhs,2,1.0)
            JSimplex.forward_solve!(dest.values,f,[nextfloat(0.0),1.0])
            JSimplex.set_entry!(dest,2,dest.values[2])
            @test JSimplex._copy_prepared_spike!(f,dest.values)
            operation=transposed ? JSimplex.transpose_solve! : JSimplex.forward_solve!
            operation(dest,f,rhs;kernel_mode=mode)
            @test !JSimplex._copy_prepared_spike!(f,dest.values)
        end
    end
end

@testset "Pipeline alias copies invalidate the original destination" begin
    for Factor in (JSimplex.ForrestTomlinFactorization,
                   JSimplex.SuhlSuhlFactorization,JSimplex.BartelsGolubFactorization),
        transposed in (false,true), through_view in (false,true)
        f=Factor(Matrix{Float64}(I,2,2))
        JSimplex.replace_column!(f,[2.0,0.0],1)
        direction=JSimplex.forward_solve(f,[nextfloat(0.0),1.0])
        @test JSimplex._copy_prepared_spike!(f,direction)
        output=through_view ? view(direction,:) : direction
        JSimplex._pipeline_dense_basis!(output,f,output,transposed)
        @test direction==[0.0,1.0]
        @test !JSimplex._copy_prepared_spike!(f,direction)
    end
end
