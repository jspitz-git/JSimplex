# UNEXECUTED diagnostic helper regression; no factor/solver calls.
module DenseTokenRegression
using Test, SparseArrays, TOML
function snapshot(v)
    data = v isa SparseVector ? nonzeros(v) : v
    encoded = [x isa Float64 ? reinterpret(UInt64,x) : x isa Float32 ? reinterpret(UInt32,x) :
               x isa BigFloat ? (precision(x),deepcopy(x)) : deepcopy(x) for x in data]
    (length(v), v isa SparseVector ? copy(nonzeroinds(v)) : nothing, encoded)
end
owners(v) = [x isa BigFloat ? objectid(x) : x isa Rational{BigInt} ?
             (objectid(numerator(x)),objectid(denominator(x))) : nothing for x in v]
function run(dense_tokens, scalar, token)
    oldprecision=precision(BigFloat); oldrounding=rounding(BigFloat)
    @testset "Dense diagnostic tokens preserve sparse inputs" begin
        setprecision(BigFloat,128) do
            special=[0.0,-0.0,reinterpret(Float64,UInt64(1)),Inf,-Inf,
                     reinterpret(Float64,UInt64(0x7ff8000000000042)),1.0,-2.0]
            bits=["0000000000000000","8000000000000000","0000000000000001",
                  "7ff0000000000000","fff0000000000000","7ff8000000000042",
                  "3ff0000000000000","c000000000000000"]
            sparse_special=SparseVector(10,collect(2:9),copy(special))
            bf=BigFloat[0,BigFloat(1)/3,-2]
            ri=Rational{Int64}[0,1//3,-2//7]
            rb=Rational{BigInt}[big(0)//big(1),big(1)//big(3),-big(2)//big(7)]
            cases=[(special,bits),(sparse_special,vcat([bits[1]],bits,[bits[1]])),
                   (spzeros(Float64,5),fill(bits[1],5)),(Float64[],String[]),
                   (Float32[0,-0.0,1//3],nothing),(sparsevec(Float32[0,-0.0,1//3]),nothing),
                   (bf,nothing),(sparsevec(bf),nothing),(ri,nothing),(sparsevec(ri),nothing),
                   (rb,nothing),(sparsevec(rb),nothing)]
            # Original failure discriminator, outside any production solver.
            @test_throws MethodError scalar.(sparse_special)
            for (case_number,(v,explicit)) in enumerate(cases)
                before=snapshot(v); owner_before=owners(v)
                expected=explicit===nothing ? string.(Vector(v)) : explicit
                out=dense_tokens(scalar,v)
                @test out isa Vector{String}
                @test isequal(out,expected)
                @test length(out)==length(v)
                @test isequal(snapshot(v),before)
                @test owners(v)==owner_before
                @test out !== v
                text=sprint(io->TOML.print(io,Dict("tokens"=>out)))
                @test TOML.parse(text)["tokens"]==expected
                push!(out,"detached token")
                @test isequal(snapshot(v),before)
                @test owners(v)==owner_before
                if case_number<=4
                    @test dense_tokens(token,v)==explicit
                    @test isequal(snapshot(v),before)
                end
            end
        end
        @test precision(BigFloat)==oldprecision
        @test rounding(BigFloat)==oldrounding
    end
end
end
