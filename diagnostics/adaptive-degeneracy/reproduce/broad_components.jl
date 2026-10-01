# Independent generated reconstruction families, not coefficients from runtime.
using JSimplex,SparseArrays,LinearAlgebra,Random,TOML,SHA,Test
BLAS.set_num_threads(1)
const ENABLED=Ref(true)
const ATTEMPTS=Ref(0)
function instrument_component!()
    path=joinpath(dirname(pathof(JSimplex)),"native_phase_transfer.jl")
    source=read(path,String)
    needle="function _native_phase_homogeneous_component!(x,B,rows,rhs,policy,cutoff,scratch,stop)"
    @assert count(needle,source)==1
    source=replace(source,needle=>needle*"\n    Main.ATTEMPTS[] += 1\n    Main.ENABLED[] || return false")
    Base.include_string(JSimplex,source,"diagnostic_component_toggle.jl")
    bytes2hex(sha256(source))
end
function trial(B,rhs,x,policy,cutoff;enabled=true)
    ENABLED[]=enabled;ATTEMPTS[]=0;candidate=copy(x)
    accepted=JSimplex._native_phase_local_rows!(candidate,B,rhs,policy,cutoff,()->false)
    q=JSimplex._compensated_solve_quality!(JSimplex.SolveQualityScratch(eltype(x),length(rhs)),B,candidate,rhs,policy,false)
    @test !accepted || (!isnothing(q) && q.reliable)
    @test accepted || isequal(candidate,x)
    accepted,candidate,ATTEMPTS[]
end
function main(output,hash)
    @assert !isfile(output)
    records=Dict{String,Any}[]
    @testset "Generated homogeneous recovery families" begin
        for T in (Float32,Float64),seed in 1:40
            rng=MersenneTwister(seed);n=rand(rng,3:10)
            dense=T.(rand(rng,-3:3,n,n))
            for i in 1:n
                dense[i,i]=zero(T)
                dense[i,i]=sum(abs,dense[i,:])+T(2)
            end
            # Nonsingular, diagonally dominant homogeneous block and an
            # independent tiny nonzero RHS. Known exact solution is available.
            B0=blockdiag(sparse(dense),sparse(T[1 1;0 1]))
            tiny=T===Float32 ? T(1e-20) : T(1e-66)
            noise=T===Float32 ? T(1e-10) : T(1e-30)
            x0=vcat(noise.*T.(rand(rng,-5:5,n)),T[noise,tiny])
            target0=vcat(zeros(T,n),T[-tiny,tiny])
            rhs0=vcat(zeros(T,n+1),tiny)
            for variant in ("original","permuted","scaled_permuted")
                rows=variant=="original" ? collect(1:n+2) : randperm(rng,n+2)
                cols=variant=="original" ? collect(1:n+2) : randperm(rng,n+2)
                rs=variant=="scaled_permuted" ? T(2).^rand(rng,-8:8,n+2) : ones(T,n+2)
                cs=variant=="scaled_permuted" ? T(2).^rand(rng,-8:8,n+2) : ones(T,n+2)
                B=spdiagm(0=>rs)*B0[rows,cols]*spdiagm(0=>cs)
                rhs=rhs0[rows].*rs;x=x0[cols]./cs;target=target0[cols]./cs
                cutoff=T(100)*maximum(abs,x)
                policy=JSimplex.NumericalPolicy(T)
                accepted,candidate,attempts=trial(B,rhs,x,policy,cutoff)
                @test accepted
                @test candidate==target
                old,_,old_attempts=trial(B,rhs,x,policy,cutoff;enabled=false)
                # Force a tiny nonzero equation inside the former homogeneous
                # block. Clearing that block must never be accepted as zero.
                nonzero=copy(rhs);nonzero[findfirst(==(1),rows)]=tiny
                forced,fx,forced_attempts=trial(B,nonzero,x,policy,cutoff)
                @test !forced || any(!iszero,fx[findall(j->j<=n,cols)])
                blocked,_,_=trial(B,rhs,x,policy,zero(T))
                @test !blocked
                push!(records,Dict("type"=>string(T),"seed"=>seed,"variant"=>variant,
                    "dimension"=>n+2,"accepted"=>accepted,"component_attempts"=>attempts,
                    "without_component_accepted"=>old,"without_component_attempts"=>old_attempts,
                    "nonzero_rhs_accepted"=>forced,"nonzero_rhs_component_attempts"=>forced_attempts))
            end
        end
    end
    open(output,"w") do io
        TOML.print(io,Dict("instrumentation_sha256"=>hash,"julia"=>string(VERSION),
            "scope"=>"Generated local reconstruction only; not LP solve convergence", "records"=>records))
    end
end
instrumentation_hash=instrument_component!()
Base.invokelatest(main,only(ARGS),instrumentation_hash)
