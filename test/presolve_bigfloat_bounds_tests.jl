using JSimplex, Test, SparseArrays

@testset "BigFloat directed endpoints enclose exact values at working precision" begin
    Q = Rational{BigInt}
    for bits in (32,64,128,256), mode in (RoundNearest,RoundDown,RoundUp,RoundToZero,RoundFromZero)
        setprecision(BigFloat,bits) do
            setrounding(BigFloat,mode) do
                for q in (Q(1,3),Q(-1,3),Q(1,10),Q(-1,10),Q(0),Q(1),Q(-1),
                          Q(2)^400+Q(1,3),Q(2)^(-400)/3,
                          Q(2big(2)^bits+1,2big(2)^bits-1),
                          Q(-(2big(2)^bits+1),2big(2)^bits-1),
                          Q(big(2)^(bits+2)-1,big(2)^bits+1)), upper in (false,true)
                    result=JSimplex._propagation_bound(BigFloat,q,upper,true)
                    @test !isnothing(result)
                    if !isnothing(result)
                        value,stored=result
                        @test precision(value)==bits
                        @test stored==Q(value)
                        @test upper ? stored>=q : stored<=q
                        @test stored==q || (upper ? Q(prevfloat(value))<q : Q(nextfloat(value))>q)
                    end
                end
                @test isnothing(JSimplex._propagation_bound(BigFloat,Q(1,3),true,false))
                @test precision(BigFloat)==bits && rounding(BigFloat)==mode
            end
        end
    end
end

@testset "BigFloat propagated caches use stored outward endpoints" begin
    Q=Rational{BigInt}
    for bits in (32,64,128,256), mode in (RoundNearest,RoundDown,RoundUp,RoundToZero), upper in (false,true)
        # Construct at a different precision: neither copying input nor later
        # exact-cache updates may round its stored scalars to the active context.
        p=setprecision(BigFloat,192) do
            LinearProblem(sparse(BigFloat[3 0;3 1]),zeros(BigFloat,2);
                row_lower=upper ? [nothing,BigFloat(1)] : [BigFloat(1),nothing],
                row_upper=upper ? [BigFloat(1),nothing] : [nothing,BigFloat(1)],
                column_lower=upper ? BigFloat[0,-1] : [nothing,nothing],
                column_upper=upper ? [nothing,nothing] : [nothing,BigFloat(1)])
        end
        before=deepcopy(p)
        setprecision(BigFloat,bits) do
            setrounding(BigFloat,mode) do
                dirty=falses(2)
                r=JSimplex._propagate_row_bounds(p,BitVector([true,false]),dirty)
                first=upper ? r.problem.column_upper[1] : r.problem.column_lower[1]
                second=upper ? r.problem.column_lower[2] : r.problem.column_upper[2]
                @test isfinite(first) && isfinite(second)
                if isfinite(first) && isfinite(second)
                    a,b=bound_value(first),bound_value(second)
                    @test precision(a)==bits && precision(b)==bits
                    @test upper ? Q(a)>Q(1,3) : Q(a)<Q(1,3)
                    implied=1-3Q(a)
                    @test upper ? Q(b)<=implied<0 : Q(b)>=implied>0
                    @test upper ? Q(nextfloat(b))>implied : Q(prevfloat(b))<implied
                    @test all(dirty)
                end
                @test precision(BigFloat)==bits && rounding(BigFloat)==mode
            end
        end
        @test p.A==before.A && p.column_lower==before.column_lower && p.column_upper==before.column_upper
        @test precision.(p.A.nzval)==precision.(before.A.nzval)
        @test precision.(getfield.(p.column_lower,:value))==precision.(getfield.(before.column_lower,:value))
    end
end

@testset "BigFloat mixed-precision implications retain low input bits" begin
    Q=Rational{BigInt}
    for inputbits in (64,256), workbits in (32,128,256), sign in (-1,1)
        rhs=setprecision(BigFloat,inputbits) do
            BigFloat(1)+BigFloat(2)^(-inputbits+4)
        end
        p=setprecision(BigFloat,64) do
            # Replace the bound explicitly to retain its independently owned
            # precision, as occurs in a mixed-precision LinearProblem.
            p=LinearProblem(sparse(reshape(BigFloat[3sign,sign],1,2)),BigFloat[0,0];
                row_lower=sign<0 ? [BigFloat(-1)] : [nothing],
                row_upper=sign>0 ? [BigFloat(1)] : [nothing], column_lower=BigFloat[0,0])
            signed=setprecision(BigFloat,inputbits) do; sign*rhs; end
            (sign>0 ? p.row_upper : p.row_lower)[1]=Bound(signed)
            p
        end
        setprecision(BigFloat,workbits) do
            r=JSimplex.propagate_row_bounds(p)
            @test isfinite(r.problem.column_upper[1])
            if isfinite(r.problem.column_upper[1])
                hi=bound_value(r.problem.column_upper[1])
                @test Q(hi)>=Q(rhs)/3
                @test Q(prevfloat(hi))<Q(rhs)/3
                @test precision(hi)==workbits
            end
            strict=JSimplex.propagate_row_bounds(p;directed_bounds=false)
            # Some high-precision dyadic numerators are divisible by three;
            # strict mode may only accept the exact quotient, never rounding.
            if isfinite(strict.problem.column_upper[1])
                @test Q(bound_value(strict.problem.column_upper[1]))==Q(rhs)/3
            end
            @test precision(bound_value(sign>0 ? p.row_upper[1] : p.row_lower[1]))==inputbits
            @test precision(BigFloat)==workbits
        end
    end
end
