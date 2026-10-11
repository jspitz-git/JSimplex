using JSimplex,Test,SparseArrays,LinearAlgebra,TOML
const JS=JSimplex
include(joinpath(@__DIR__,"hh_triplet_reference.jl"))

function fixture(::Type{T},n,dense) where T
    B=spdiagm(0=>fill(T(n+2),n))
    for j in 1:n,i in 1:n
        if i!=j && (dense || abs(i-j)==1)
            B[i,j]=T(mod(3i+5j,7)-3)/T(16)
        end
    end
    B
end
function exact_parts(F)
    w=JS.HHExtractWorkspace()
    a=original_markowitz_parts(F,w);b=JS._hh_extract_parts(F,w)
    for i in (1,2)
        @test isequal(a[i].colptr,b[i].colptr)
        @test isequal(a[i].rowval,b[i].rowval)
        @test isequal(a[i].nzval,b[i].nzval)
        @test !Base.mightalias(a[i].nzval,b[i].nzval)
        @test !Base.mightalias(b[i].nzval,F.core.factors)
    end
    @test isequal(a[3:end],b[3:end])
end
function measure(F,mode)
    w=JS.HHExtractWorkspace()
    if mode==:reference
        @timed original_markowitz_parts(F,w)
    else
        @timed JS._hh_extract_parts(F,w)
    end
end
function main(output)
    @assert Threads.nthreads()==BLAS.get_num_threads()==1
    @testset "exact Markowitz extraction" begin
        for T in (Float16,Float32,Float64,BigFloat,Rational{BigInt})
            for n in (0,1,8),dense in (false,true)
                F=JS.MarkowitzBackend(fixture(T,n,dense));exact_parts(F)
            end
            F=JS.MarkowitzBackend(T[0 2 1;3 1 0;1 0 4]);exact_parts(F)
            B=Matrix{T}(I,4,4)
            B[1,2]=T(-0.0);B[2,1]=T(1)/T(1024)
            exact_parts(JS.MarkowitzBackend(B))
        end
    end
    F=JS.MarkowitzBackend(fixture(Float64,256,true))
    measure(F,:reference);measure(F,:candidate)
    GC.gc(true)
    a=measure(F,:reference);b=measure(F,:candidate)
    data=Dict("reference_bytes"=>a.bytes,"candidate_bytes"=>b.bytes,
        "reference_compile"=>a.compile_time,"candidate_compile"=>b.compile_time,
        "allocation_gate"=>b.bytes<=0.8a.bytes)
    open(io->TOML.print(io,data),output,"w")
    @testset "triplet allocation reduction" begin
        @test a.compile_time==b.compile_time==0
        @test b.bytes <= 0.8a.bytes
    end
end
Base.invokelatest(main,ARGS[1])
