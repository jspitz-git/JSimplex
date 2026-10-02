# Paired whole-model control: disable only the new native price recovery.
path=joinpath(@__DIR__,"broad_corpus.jl")
Base.include_string(Main,first(split(read(path,String),"\nhashes=instrument!()")),path)
hashes=instrument!()
source="""
function _try_native_primal_price_recovery!(workspace::SimplexWorkspace{T},stop) where {T<:Union{Float32,Float64}}
    return false
end
"""
Base.include_string(JSimplex,source,"diagnostic_no_native_price_recovery.jl")
hashes["native_price_recovery_disabled"]=bytes2hex(sha256(source))
Base.invokelatest(main,ARGS,hashes)
