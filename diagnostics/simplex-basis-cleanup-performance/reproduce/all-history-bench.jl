using JSimplex, SparseArrays, LinearAlgebra, Printf
function measure(Factor,n,count,repeats,coupled)
    f=Factor(spdiagm(0=>ones(n)))
    rhs=ones(n); column=zeros(n); out=similar(rhs)
    updates=@elapsed for k in 1:count
        fill!(column,0.0); column[k]=1.0
        coupled && (column[n]=0.125)
        JSimplex.replace_column!(f,column,k)
    end
    JSimplex.forward_solve!(out,f,rhs)
    expected=copy(rhs);coupled && (expected[n]-=count*0.125)
    @assert out≈expected
    JSimplex.transpose_solve!(out,f,rhs)
    expected=copy(rhs);coupled && (expected[1:count].-=0.125)
    @assert out≈expected
    GC.gc()
    ft=@elapsed for _ in 1:repeats;JSimplex.forward_solve!(out,f,rhs);end
    bt=@elapsed for _ in 1:repeats;JSimplex.transpose_solve!(out,f,rhs);end
    @printf("%s coupled=%s n=%d updates=%d update_us=%.3f forward_us=%.3f transpose_us=%.3f\n",
        nameof(Factor),coupled,n,count,1e6*updates/count,1e6*ft/repeats,1e6*bt/repeats)
    flush(stdout)
end
function main()
    n=parse(Int,get(ARGS,1,"28000")); repeats=parse(Int,get(ARGS,2,"100"))
    for Factor in (JSimplex.PFIFactorization,JSimplex.ForrestTomlinFactorization,
                   JSimplex.SuhlSuhlFactorization,JSimplex.BartelsGolubFactorization)
        measure(Factor,100,10,1,true) # compile outside reported large cases
        for coupled in (false,true),count in (20,80,320)
            measure(Factor,n,count,repeats,coupled)
        end
    end
end
main()
