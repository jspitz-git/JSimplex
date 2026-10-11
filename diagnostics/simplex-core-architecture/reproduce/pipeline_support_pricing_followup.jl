# Execute only the testset whose fixture dependency was omitted by focused-1.
using Test,JSimplex,SparseArrays,LinearAlgebra
@assert Threads.nthreads()==BLAS.get_num_threads()==1
root=joinpath(dirname(dirname(pathof(JSimplex))),"test")
helper=read(joinpath(root,"sparse_pricing_integration_tests.jl"),String)
positions=findall("function sparse_pricing_workspace(",helper);@assert length(positions)==1
expression,_=Meta.parse(helper,first(only(positions)))
Core.eval(Main,expression)
source=Meta.parseall(read(joinpath(root,"sparse_pricing_edge_tests.jl"),String))
title="Sparse pricing checks aliases before changing matrix storage"
selected=filter(x->x isa Expr && x.head==:macrocall && title in x.args,source.args)
@assert length(selected)==1
Core.eval(Main,only(selected))
