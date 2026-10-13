using LinearAlgebra, SparseArrays
@testset "Prepared hardware handoff preserves exceptional and corrected directions" begin
    for T in (Float32, Float64)
        for (direction, expected) in ((T[1,0,2], (true,true)),
                                     (T[1,-0.0,2], (true,false)),
                                     (T[2,0,2], (true,false)),
                                     (T[NaN,0,2], (false,false)),
                                     (T[1,0,Inf], (false,false)))
            @test JSimplex._hh_direction_status(direction,T[1,0,2],true) == expected
        end
        for count in (64,129,300), mismatch in (3,count÷2,count)
            prepared=ones(T,count);direction=copy(prepared)
            direction[mismatch]=T(2)
            @test JSimplex._hh_direction_status(direction,prepared,true)==(true,false)
            direction[end]=T(Inf)
            @test JSimplex._hh_direction_status(direction,prepared,true)==(false,false)
        end
        @test JSimplex._hh_direction_status(T[],T[],true)==(true,true)
        @test JSimplex._hh_direction_status(T[NaN],T[NaN],true)==(false,true)
        f=JSimplex.HuangfuHallFactorization(Matrix{T}(I,3,3))
        direction=JSimplex.forward_solve(f,T[2,1,0])
        direction[1]=zero(T);direction[2]=T(Inf)
        @test_throws ArgumentError JSimplex.replace_column!(f,direction,1)
        @test isempty(f.updates)
        @test f.prepared_valid
        direction[2]=one(T)
        @test_throws ZeroPivotException JSimplex.replace_column!(f,direction,1)
        direction[1]=T(3)
        JSimplex.replace_column!(f,view(direction,:),1)
        @test JSimplex.forward_solve(f,T[3,1,0]) ≈ T[1,0,0]
        for F in (JSimplex.ForrestTomlinFactorization,JSimplex.SuhlSuhlFactorization,JSimplex.BartelsGolubFactorization)
            factor=F(Matrix{T}(I,3,3));output=T[2,1,0]
            for bad in (:output,:spike)
                entry=JSimplex._begin_prepared_spike!(factor,output)
                JSimplex._save_prepared_spike!(entry,T[2,1,0])
                (bad==:output ? output : entry.spike)[2]=T(Inf)
                JSimplex._finish_prepared_spike!(entry,output)
                @test isnothing(entry.destination)
                output .= T[2,1,0]
                @test !JSimplex._copy_prepared_spike!(factor,output)
            end
            entry=JSimplex._begin_prepared_spike!(factor,output)
            JSimplex._save_prepared_spike!(entry,output)
            JSimplex._finish_prepared_spike!(entry,output)
            @test JSimplex._copy_prepared_spike!(factor,output)
            # An already published entry uses the atomic generic path.
            saved=copy(entry.direction);output[2]=T(Inf)
            JSimplex._finish_prepared_spike!(entry,output)
            @test isequal(saved,entry.direction)
            output[2]=one(T)
            @test JSimplex._copy_prepared_spike!(factor,output)
        end
    end
end
