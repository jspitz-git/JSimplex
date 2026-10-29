using Serialization
include(joinpath(@__DIR__,"reused-prefix.jl"))
Base.include(J,joinpath(D,"candidate.jl"))
include(joinpath(D,"structure.jl"))
@assert sizeof(Int) == 8 && ENDIAN_BOM == 0x04030201
const WITNESS = abspath(only(ARGS))
const MODES = (("SS",J.SuhlSuhlFactorization,false),("FT",J.ForrestTomlinFactorization,false),
               ("BG",J.BartelsGolubFactorization,false),("BG-local",J.BartelsGolubFactorization,true))

function load_case(entry)
    path = entry["path"]
    @test bytes2hex(open(sha256,path)) == entry["sha256"]
    @test bytes2hex(open(sha256,entry["input"])) == entry["input_sha256"]
    d = deserialize(path)
    @test realpath(d.input) == realpath(entry["input"]) && d.input_sha256 == entry["input_sha256"]
    @test d.A isa SparseMatrixCSC{Float64,Int}
    n = size(d.A,1); m = size(d.A,2)
    @test length(d.basis) == n && length(unique(d.basis)) == n
    @test length(d.steps) >= 160 && all(isfinite,d.A.nzval)
    return (id=entry["id"], A=d.A, n=n, m=m, basis=copy(d.basis), steps=copy(d.steps[1:160]),
        iteration=d.iteration, input_hash=d.input_sha256, history_hash=entry["sha256"])
end
function casehash(c)
    io = IOBuffer()
    for a in (c.A.colptr,c.A.rowval,c.A.nzval,c.basis); write(io,a); end
    for (j,e) in c.steps; write(io,j,e); end
    bytes2hex(sha256(take!(io)))
end
function fill_entering!(column,c,index)
    fill!(column,0.)
    if index <= c.m
        for k in nzrange(c.A,index); column[c.A.rowval[k]] = c.A.nzval[k]; end
    else
        1 <= index-c.m <= c.n || error("invalid artificial column")
        column[index-c.m] = -1.
    end
    column
end
function assemble_basis(c,basis)
    total = sum(j -> basis[j] <= c.m ? length(nzrange(c.A,basis[j])) : 1,1:c.n)
    ptr = Vector{Int}(undef,c.n+1); rows = Vector{Int}(undef,total); vals = Vector{Float64}(undef,total)
    slot = 1
    for j in 1:c.n
        ptr[j] = slot; e = basis[j]
        if e <= c.m
            for k in nzrange(c.A,e)
                rows[slot] = c.A.rowval[k]; vals[slot] = c.A.nzval[k]; slot += 1
            end
        else
            1 <= e-c.m <= c.n || error("invalid basis artificial column")
            rows[slot] = e-c.m; vals[slot] = -1.; slot += 1
        end
    end
    ptr[end] = slot
    SparseMatrixCSC(c.n,c.n,ptr,rows,vals)
end
function advance!(basis,flags,row,entering)
    1 <= row <= length(basis) && 1 <= entering <= length(flags) || error("invalid exchange")
    !flags[entering] || error("entering column already basic")
    flags[basis[row]] = false; flags[entering] = true; basis[row] = entering
end
function relative_residual(B,x,b,transposed=false)
    all(isfinite,x) || return Inf
    y = transposed ? transpose(B)*x : B*x
    denominator = max(1.,(transposed ? opnorm(B,1) : opnorm(B,Inf))*norm(x,Inf),norm(b,Inf))
    norm(y-b,Inf)/denominator
end
function directed_check(B,x,b,tolerance,transposed=false)
    setprecision(BigFloat,256) do
        bx = BigFloat.(x); bb = BigFloat.(b)
        bounds = map((RoundDown,RoundUp)) do mode
            setrounding(BigFloat,mode) do
                r = -bb
                for j in 1:size(B,2), k in nzrange(B,j)
                    i = B.rowval[k]; target,source = transposed ? (j,i) : (i,j)
                    r[target] += BigFloat(B.nzval[k])*bx[source]
                end
                r
            end
        end
        residual = maximum(i -> max(abs(bounds[1][i]),abs(bounds[2][i])),eachindex(bb))
        bound = setrounding(BigFloat,RoundDown) do
            sums = zeros(BigFloat,size(B,1))
            for j in 1:size(B,2), k in nzrange(B,j)
                target = transposed ? j : B.rowval[k]
                sums[target] += abs(BigFloat(B.nzval[k]))
            end
            BigFloat(tolerance)*max(BigFloat(1),maximum(sums)*maximum(abs,bx),maximum(abs,bb))
        end
        residual <= bound
    end
end
function reference_check(B,x,b,transposed=false)
    ref = lu(B)
    z = transposed ? transpose(ref)\b : ref\b
    norm(x-z,Inf)/max(norm(z,Inf),floatmin(Float64)) <= 1e-6
end
function reference_pair_check(B,x,b,y,c)
    ref = lu(B)
    zx = ref\b; zy = transpose(ref)\c
    norm(x-zx,Inf)/max(norm(zx,Inf),floatmin(Float64)) <= 1e-6 &&
        norm(y-zy,Inf)/max(norm(zy,Inf),floatmin(Float64)) <= 1e-6
end
function pre_spike(f,dir)
    cache = f.row_cache.prepared
    cache === nothing && error("missing spike cache")
    for e in cache.entries
        e.destination === dir && isequal(e.direction,dir) && return e.spike
    end
    error("spike provenance mismatch")
end
function spiked_matrix(f,spike,position)
    n = length(f.upper)
    total = count(!iszero,spike) + sum(j -> j == position ? 0 : length(f.upper[j].values),1:n)
    ptr = Vector{Int}(undef,n+1); rows = Vector{Int}(undef,total); vals = Vector{Float64}(undef,total)
    slot = 1
    for j in 1:n
        ptr[j] = slot
        if j == position
            for i in 1:n
                if !iszero(spike[i]); rows[slot]=i; vals[slot]=spike[i]; slot+=1; end
            end
        else
            col = f.upper[j]
            for k in eachindex(col.values); rows[slot]=col.indices[k]; vals[slot]=col.values[k]; slot+=1; end
        end
    end
    ptr[end] = slot
    SparseMatrixCSC(n,n,ptr,rows,vals)
end
function basis_profiles(c)
    records = Dict{String,Any}[]; basis = copy(c.basis); flags = falses(c.m+c.n); flags[basis] .= true
    for step in 0:160
        if step > 0
            row,e = c.steps[step]; advance!(basis,flags,row,e)
        end
        if step in (0,80,160)
            B = assemble_basis(c,basis)
            t = @timed structural_blocks(B)
            witness = write_witness(joinpath(WITNESS,c.id*"-B"*string(step)*".bin"),B,t.value)
            push!(records,Dict("step"=>step,"profile"=>t.value.summary,"seconds"=>t.time,
                "bytes"=>t.bytes,"compile_seconds"=>t.compile_time,"witness"=>witness))
        end
    end
    records
end

function replay_real(::Type{F},backend::V,localized::Bool,c::C,interval::Int,cold::Bool,prefix::String) where {F,V,C}
    n = c.n; basis = copy(c.basis); flags = falses(c.m+n); flags[basis] .= true
    column = zeros(n); dir = zeros(n); xf = zeros(n); xb = zeros(n); rhs = ones(n); unit = zeros(n); midpoint = zeros(2n)
    clocks = zeros(UInt64,6); trace = Dict{String,Any}[]; graphs = Dict{String,Any}[]
    init = ""; f = nothing; completed = 0; refactors = 0
    tolerance = min(1e-10,128*n*eps(Float64))
    try
        t = time_ns(); B0 = assemble_basis(c,basis); clocks[6] += time_ns()-t
        t = time_ns(); f = J._direct_lu_factor(F,B0,backend,policy(backend);normalize=true); clocks[1] += time_ns()-t
        J._direct_mode(f) == :normalized && f.base.pivot_policy == policy(backend) || error("factor mode/policy")
        init = cold ? digest_factor(f;initial=true) : ""
        reference_storage = cold ? J._factor_storage_count(f) : 0
        cold && reference_storage > 5_000_000 && error("initial active factor entry budget")
        reference_growth = cold ? maximum(col -> maximum(abs,col.values;init=0.),f.upper;init=0.) : 0.
        cold && push!(trace,metrics(f,0,"initial",0,0,nnz(B0)))
        for (k,(row,e)) in enumerate(c.steps)
            fill_entering!(column,c,e); fill!(unit,0.); unit[row]=1.
            pos = cold ? f.positions[row] : 0
            t = time_ns(); J.forward_solve!(dir,f,column); clocks[2] += time_ns()-t
            all(isfinite,dir) || error("nonfinite direction")
            last = cold ? spike_last(f,dir) : -1
            if cold && (k-1)%16 == 0
                spike = pre_spike(f,dir); S = spiked_matrix(f,spike,pos)
                g = @timed structural_blocks(S)
                r = Dict{String,Any}("step"=>k,"position"=>pos,"spike_last"=>last,
                    "spike_diagonal_zero"=>iszero(spike[pos]),"profile"=>g.value.summary,
                    "seconds"=>g.time,"bytes"=>g.bytes,"compile_seconds"=>g.compile_time)
                if k in (1,81)
                    r["witness"] = write_witness(joinpath(WITNESS,prefix*"-spike"*string(k)*".bin"),S,g.value)
                end
                push!(graphs,r)
            end
            if cold && k%16 == 0
                before = assemble_basis(c,basis)
                r = relative_residual(before,dir,column)
                r <= tolerance || error("entering residual $k: $r")
                if k in (80,160)
                    directed_check(before,dir,column,tolerance) || error("directed entering residual $k")
                    reference_check(before,dir,column) || error("fresh entering difference $k")
                end
            end
            t = time_ns()
            if localized
                J._diagnostic_local_bg_replace!(f,dir,row)
            else
                J.replace_column!(f,dir,row)
            end
            clocks[4] += time_ns()-t
            advance!(basis,flags,row,e)
            t = time_ns(); J._ordinary_forward_solve!(xf,f,rhs); clocks[2] += time_ns()-t
            t = time_ns(); J.transpose_solve!(xb,f,unit); clocks[3] += time_ns()-t
            all(isfinite,xf) && all(isfinite,xb) || error("nonfinite output")
            if cold && k%16 == 0
                B = assemble_basis(c,basis)
                fr = relative_residual(B,xf,rhs); br = relative_residual(B,xb,unit,true)
                r = metrics(f,k,"update",pos,last,nnz(B))
                r["forward_residual"] = fr; r["transpose_residual"] = br
                r["storage_ratio_since_refactor"] = r["factor_storage_count"]/max(1,reference_storage)
                r["triangular_upper"] = all(j -> all(i -> i <= j,f.upper[j].indices),1:n)
                push!(trace,r)
                r["triangular_upper"] && fr <= tolerance && br <= tolerance || error("shape/post residual $k")
                isfinite(r["u_max"]) && r["u_max"] <= 1e8*reference_growth || error("normalized U growth $k")
                r["factor_storage_count"] <= 5_000_000 || error("active factor entry budget $k")
                if k in (80,160)
                    directed_check(B,xf,rhs,tolerance) && directed_check(B,xb,unit,tolerance,true) || error("directed post residual $k")
                    # Separate independent fresh solves, neither touches the aged factor.
                    reference_pair_check(B,xf,rhs,xb,unit) || error("fresh post difference $k")
                end
            end
            completed = k
            if k == 80
                copyto!(midpoint,1,xf,1,n); copyto!(midpoint,n+1,xb,1,n)
            end
            if k%interval == 0 && k < length(c.steps)
                t = time_ns(); B = assemble_basis(c,basis); clocks[6] += time_ns()-t
                t = time_ns(); J.refactorize!(f,B); clocks[5] += time_ns()-t; refactors += 1
                J._direct_mode(f) == :normalized && f.base.pivot_policy == policy(backend) || error("refactor mode/policy")
                if cold
                    push!(trace,metrics(f,k,"refactor",0,0,nnz(B)))
                    reference_storage = J._factor_storage_count(f)
                    reference_growth = maximum(col -> maximum(abs,col.values;init=0.),f.upper;init=0.)
                end
            end
        end
        return (ok=true,reason="",step=completed,refactors=refactors,factor=f,initial=init,
            trace=trace,graphs=graphs,clocks=clocks,dir=dir,xf=xf,xb=xb,middle=midpoint)
    catch err
        err isa InterruptException && rethrow()
        cold || rethrow()
        return (ok=false,reason=sprint(showerror,err),step=completed,refactors=refactors,factor=f,initial=init,
            trace=trace,graphs=graphs,clocks=clocks,dir=dir,xf=xf,xb=xb,middle=midpoint)
    end
end
function save_results(data)
    open(joinpath(D,"results-1.toml"),"w") do io; TOML.print(io,data); end
end
function run_realistic()
    ispath(WITNESS) && error("choose fresh witness directory")
    mkdir(WITNESS)
    data = Dict{String,Any}("cases"=>Any[],"cold"=>Any[],"windows"=>Any[],
        "scope"=>"recorded actual basis exchanges, no new LP solve or production modification")
    for entry in TOML.parsefile(joinpath(D,"inputs.toml"))["cases"]
        prep = @timed load_case(entry); c = prep.value; before_hash = casehash(c)
        profiles = @timed basis_profiles(c)
        push!(data["cases"],Dict("id"=>c.id,"rows"=>c.n,"columns"=>c.m,"nonzeros"=>nnz(c.A),
            "captured_iteration"=>c.iteration,"history_sha256"=>c.history_hash,"input_sha256"=>c.input_hash,
            "structural_only"=>entry["structural_only"],"load_seconds"=>prep.time,"load_bytes"=>prep.bytes,
            "profile_seconds"=>profiles.time,"profile_bytes"=>profiles.bytes,"basis_profiles"=>profiles.value))
        save_results(data)
        if entry["structural_only"]
            @test casehash(c) == before_hash
            println("STRUCTURAL_ONLY ",c.id); flush(stdout); continue
        end
        backends = c.id == "fast0507-1000" ? (Val(:native),Val(:markowitz)) : (Val(:native),)
        for backend in backends
            bname = string(typeof(backend).parameters[1])
            arms = [(mode,i) for mode in 1:4 for i in (80,160)]
            refs = Any[]; eligible = true
            for (mode,interval) in arms
                name,F,localized = MODES[mode]
                prefix = c.id*"-"*name*"-"*bname*"-i"*string(interval)
                t = @timed replay_real(F,backend,localized,c,interval,true,prefix); r = t.value
                @test r.ok; @test casehash(c) == before_hash; eligible &= r.ok
                signature = r.factor === nothing ? "" : digest_factor(r.factor)
                push!(refs,(initial=r.initial,signature=signature,dir=copy(r.dir),xf=copy(r.xf),xb=copy(r.xb),middle=copy(r.middle)))
                push!(data["cold"],Dict("case"=>c.id,"mode"=>name,"backend"=>bname,"interval"=>interval,
                    "ok"=>r.ok,"reason"=>r.reason,"updates"=>r.step,"refactors"=>r.refactors,
                    "seconds"=>t.time,"bytes"=>t.bytes,"initial_factor_hash"=>r.initial,
                    "final_factor_hash"=>signature,"trace"=>r.trace,"spike_profiles"=>r.graphs))
                r = nothing; t = nothing; save_results(data)
            end
            @test all(r -> r.initial == refs[1].initial,refs)
            if eligible
                GC.gc()
                for repetition in 0:5
                    for a in mod1.(collect(1:8).+repetition,8)
                        mode,interval = arms[a]; name,F,localized = MODES[mode]
                        t = @timed replay_real(F,backend,localized,c,interval,false,""); r = t.value
                        @test r.ok && digest_factor(r.factor) == refs[a].signature
                        @test isequal((r.dir,r.xf,r.xb,r.middle),(refs[a].dir,refs[a].xf,refs[a].xb,refs[a].middle))
                        @test casehash(c) == before_hash
                        @test r.refactors == (interval==80 ? 1 : 0)
                        if repetition > 0; @test t.compile_time == t.recompile_time == 0; end
                        push!(data["windows"],Dict("case"=>c.id,"mode"=>name,"backend"=>bname,"interval"=>interval,
                            "repetition"=>repetition,"warm"=>repetition==0,"seconds"=>t.time,"bytes"=>t.bytes,
                            "events"=>Base.gc_alloc_count(t.gcstats),"gc_seconds"=>t.gctime,
                            "compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time,
                            "construct_seconds"=>r.clocks[1]/1e9,"ftran_seconds"=>r.clocks[2]/1e9,
                            "btran_seconds"=>r.clocks[3]/1e9,"update_seconds"=>r.clocks[4]/1e9,
                            "refactor_seconds"=>r.clocks[5]/1e9,"assembly_seconds"=>r.clocks[6]/1e9,
                            "updates"=>r.step,"refactors"=>r.refactors,"retained_bytes"=>Base.summarysize(r.factor)))
                        r = nothing; t = nothing
                    end
                end
            end
            save_results(data)
            println("COMPLETED ",c.id,"/",bname," eligible=",eligible); flush(stdout)
        end
    end
end
@testset "Matching SCC independent small cases" begin; graph_sanity(); end
@testset "Realistic basis structure and work" begin; run_realistic(); end
