# Independent native-precision recovery probes on the same rejected basis.
using JSimplex, LinearAlgebra, SparseArrays, Serialization, TOML
const JS = JSimplex
function main(snapshot, output)
    ispath(output) && error("Choose a fresh report")
    d = deserialize(snapshot)
    ws = JS.initialize_workspace(d.problem,d.options); ws.basis = d.basis
    A = sparse(transpose(d.B)); rhs = zeros(size(A,1)); rhs[d.row] = 1
    reference = Float64.(deserialize(replace(snapshot,"pilotnov-rejection/failure-1.bin"=>"pilotnov-direct-row-reference.toml.256.bin")))
    records = []
    for mode in (:scaled_basis_native, :scaled_basis_markowitz)
        result = Dict{String,Any}("backend"=>string(mode))
        elapsed = @elapsed try
            if mode == :dense_lu
                f = lu(Matrix(A)); solve = b -> f\b
            elseif mode == :dense_qr
                f = qr(Matrix(A),ColumnNorm()); solve = b -> f\b
            elseif mode == :sparse_qr
                f = qr(A;tol=0.0); solve = b -> f\b
            elseif mode in (:scaled_basis_native, :scaled_basis_markowitz)
                rows = vec(maximum(abs,d.B;dims=2)); rows[iszero.(rows)] .= 1
                R = spdiagm(1 ./ rows); M = R*d.B
                cols = vec(maximum(abs,M;dims=1)); cols[iszero.(cols)] .= 1
                C = spdiagm(1 ./ cols)
                f = mode == :scaled_basis_native ? lu(M*C) : JS._factorize_basis(M*C,Val(:markowitz))
                solve = b -> R*JS._refinement_basis_solve(f,C*b,true)
            else
                rows = vec(maximum(abs,A;dims=2)); rows[iszero.(rows)] .= 1
                R = spdiagm(1 ./ rows); M = R*A
                cols = vec(maximum(abs,M;dims=1)); cols[iszero.(cols)] .= 1
                C = spdiagm(1 ./ cols); f = lu(M*C); solve = b -> C*(f\(R*b))
            end
            x = solve(rhs); trace = []
            scratch = JS.SolveQualityScratch(Float64,length(rhs))
            for k in 0:5
                q = JS._compensated_solve_quality!(scratch,d.B,x,rhs,ws.progress.numerical_policy,true)
                push!(trace,Dict("correction"=>k,"ratio"=>JS._dual_row_residual_ratio(ws,x,d.row),
                    "absolute_error"=>q.absolute_error,"maximum"=>norm(x,Inf),
                    "reference_difference"=>norm(x-reference,Inf)/norm(reference,Inf)))
                k<5 && (x .+= solve(scratch.residual))
            end
            result["trace"] = trace
        catch e
            result["exception"] = sprint(showerror,e)
        end
        result["seconds"] = elapsed; push!(records,result); println(result); flush(stdout)
        open(output,"w") do io; TOML.print(io,Dict("records"=>records)); end
    end
end
Base.invokelatest(main,ARGS...)
