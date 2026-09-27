using JSimplex, SparseArrays, LinearAlgebra, Printf
# Isolate the cost of traversing permutations in an otherwise identity basis.
# Actual column replacements generate the history; no synthetic internal updates.
function main()
    n = parse(Int, get(ARGS, 1, "28000"))
    repeats = parse(Int, get(ARGS, 2, "100"))
    for count in (20, 80, 320)
        f = JSimplex.BartelsGolubFactorization(spdiagm(0 => ones(n)))
        rhs = ones(n); direction = zeros(n); 
        update_seconds = @elapsed for k in 1:count
            fill!(direction, 0.0); direction[k] = 1.0
            JSimplex.replace_column!(f, direction, k)
        end
        out = similar(rhs)
        JSimplex.forward_solve!(out, f, rhs)
        JSimplex.transpose_solve!(out, f, rhs)
        GC.gc()
        forward = @elapsed for _ in 1:repeats
            JSimplex.forward_solve!(out, f, rhs)
        end
        backward = @elapsed for _ in 1:repeats
            JSimplex.transpose_solve!(out, f, rhs)
        end
        @assert out == rhs
        @printf("n=%d updates=%d forward_us=%.3f transpose_us=%.3f steps=%d update_us=%.3f\n", n,count,1e6*forward/repeats,1e6*backward/repeats,sum(length(u.steps) for u in f.updates),1e6*update_seconds/count)
        flush(stdout)
    end
end
main()
