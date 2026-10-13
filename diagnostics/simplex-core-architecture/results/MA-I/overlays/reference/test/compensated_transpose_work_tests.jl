using Test,JSimplex,SparseArrays,Random

function reference_compensated_components!(scratch,B,x,transposed)
    for column in axes(B,2), p in nzrange(B,column)
        row=B.rowval[p]
        target,source=transposed ? (column,row) : (row,column)
        JSimplex._compensated_quality_term!(scratch,B.nzval[p],x[source],target)
    end
    nothing
end
function initialized_compensated_scratch(T,rhs)
    s=JSimplex.SolveQualityScratch(T,length(rhs))
    resize!(s.compensation,length(rhs));fill!(s.compensation,zero(T))
    resize!(s.error_sum,length(rhs));fill!(s.error_sum,zero(T))
    s.work_residual.=rhs;s.work_scale.=abs.(rhs);fill!(s.terms,1)
    s
end
function same_compensated_components(a,b)
    all(isequal(getfield(a,k),getfield(b,k)) for k in fieldnames(typeof(a)))
end
@testset "Transposed compensated accumulation preserves term order and storage" begin
    rng=MersenneTwister(124)
    for T in (Float32,Float64), (m,n) in ((0,0),(1,1),(7,11),(13,5)), density in (0.0,0.2,1.0)
        B=sprand(rng,T,m,n,density);x=randn(rng,T,m);rhs=randn(rng,T,n)
        reference=initialized_compensated_scratch(T,rhs);trial=deepcopy(reference)
        reference_compensated_components!(reference,B,x,true)
        JSimplex._compensated_transpose_components!(trial,B,x)
        @test same_compensated_components(reference,trial)
    end
    for T in (Float32,Float64)
        values=T[0,-0.0,nextfloat(zero(T)),-nextfloat(zero(T)),floatmin(T),1,-1,floatmax(T),Inf,-Inf,NaN]
        for value in values, component in values
            B=sparse([1,2,3,1,2,3],[1,1,1,2,2,2],T[value,one(T),-one(T),-one(T),value,one(T)],3,2)
            x=T[component,1,1];rhs=T[1,-0.0]
            reference=initialized_compensated_scratch(T,rhs);trial=deepcopy(reference)
            reference_compensated_components!(reference,B,x,true)
            JSimplex._compensated_transpose_components!(trial,B,x)
            @test same_compensated_components(reference,trial)
        end
    end
end
