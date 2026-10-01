# Observe selected direction disagreements, with bounded snapshots per basis.
path=joinpath(@__DIR__,"broad_corpus.jl")
Base.include_string(Main,first(split(read(path,String),"\nhashes=instrument!()")),path)
const PRICE_RECORDS=Dict{String,Any}[]
const PRICE_KEYS=Set{Any}()
function capture_triangular_price(ws,entering,column,tolerance)
    key=(CAPTURE_PREFIX[],ws.iterations,ws.refactorizations,
        hash(ws.reduced_costs),length(ws.factorization.updates))
    key in PRICE_KEYS && return
    push!(PRICE_KEYS,key)
    prefix=CAPTURE_PREFIX[]*"-price-"*string(length(PRICE_KEYS))
    record=Dict{String,Any}("prefix"=>prefix,"iteration"=>ws.iterations,
        "refactorizations"=>ws.refactorizations,"entering"=>entering,
        "cached"=>ws.reduced_costs[entering],
        "implied"=>ws.costs[entering]-dot(ws.costs[ws.basis.basic_indices],column),
        "basis_updates"=>length(ws.factorization.updates),"direction_norm"=>maximum(abs,column))
    push!(PRICE_RECORDS,record)
    detach(ws,prefix*"-rejected.bin")
    serialize(prefix*"-direction.bin",(;entering,column=copy(column),tolerance))
    open(ARGS[4]*"-prices.toml","w") do io;TOML.print(io,Dict("captures"=>PRICE_RECORDS));end
    println("PRICE_REJECT ",record);flush(stdout)
end
hashes=instrument!()
source=read(joinpath(dirname(pathof(JSimplex)),"legacy_primal_pivot.jl"),String)
a=first(findfirst("function _legacy_primal_direction_price_ok",source))
b=first(findnext("\n# Repair only a demonstrated native BTRAN",source,a))-1
body=replace(source[a:b],"function _legacy_primal_direction_price_ok"=>"function _diagnostic_triangular_price_ok")
Base.include_string(JSimplex,body,"diagnostic_triangular_price.jl")
Base.include_string(JSimplex,"""
function _legacy_primal_direction_price_ok(ws::SimplexWorkspace{T},entering::Int,column::Vector{T},tolerance::T) where {T<:Union{Float32,Float64}}
    accepted=_diagnostic_triangular_price_ok(ws,entering,column,tolerance)
    accepted || Main.capture_triangular_price(ws,entering,column,tolerance)
    return accepted
end
""","diagnostic_triangular_capture.jl")
hashes["triangular_price_capture"]=bytes2hex(sha256(read(@__FILE__,String)))
Base.invokelatest(main,ARGS,hashes)
