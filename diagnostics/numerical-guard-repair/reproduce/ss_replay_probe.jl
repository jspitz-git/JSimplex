# Read-only diagnostic replay: use the preserved direct-factor harness with the
# currently loaded production manager. Additional checks never refactor early.
const EXPERIMENT = "/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl"
include(joinpath(EXPERIMENT,"diagnostics/basis-interval-sweep/reproduce/common.jl"))

# Apply the stored Float64 factors in high precision. This diagnoses factor
# storage versus application error; it is not a proposed production solve.
function precise_direct_forward(f,b)
    setprecision(BigFloat,256) do
        base=f.base; L=base.lower; D=base.diagonal; n=length(b)
        v=[base.divide_scaling ? BigFloat(b[base.row_order[i]])/base.scaling[base.row_order[i]] :
                                BigFloat(b[base.row_order[i]])*base.scaling[base.row_order[i]] for i in 1:n]
        for j in 1:n, pos in (L.colptr[j]+1):(L.colptr[j+1]-1)
            v[L.rowval[pos]]-=BigFloat(L.nzval[pos])*v[j]
        end
        isnothing(D) || (v ./= D)
        for u in f.updates
            old=v[u.pivot]
            for i in u.pivot:(u.last-1);v[i]=v[i+1];end
            v[u.last]=old
            for i in eachindex(u.indices)
                row=u.indices[i]
                # Preserve independent high-precision application after the
                # production history gained explicit local row interchanges.
                if hasproperty(u,:swapped_rows) && row in u.swapped_rows
                    v[row],v[u.last]=v[u.last],v[row]
                end
                v[u.last]+=BigFloat(u.multipliers[i])*v[row]
            end
        end
        for j in n:-1:1
            col=f.upper[j];v[j]/=JSimplex._upper_diagonal(col,j)
            for k in eachindex(col.indices)
                i=col.indices[k];i==j && continue
                v[i]-=BigFloat(col.values[k])*v[j]
            end
        end
        x=similar(v)
        for j in 1:n;x[f.column_order[j]]=v[j];end
        Float64.(x)
    end
end

function main(history,output)
    ispath(output) && error("Choose a fresh output path")
    data=load_history(history);A=augmented_history(data);basis=copy(data.basis);m=length(basis)
    arm=ARMS["direct-suhl_suhl-native"];f=build(arm,A[:,basis]);rhs=zeros(m);d=zeros(m)
    aux=zeros(m);dense=ones(m);unit=zeros(m);records=[]
    policy=JSimplex.NumericalPolicy(Float64,SolverOptions(verbose=false))
    scratch=JSimplex.SolveQualityScratch(Float64,m)
    for k in 1:640
        row,entering=data.steps[k];fill_column!(rhs,A,entering)
        JSimplex.forward_solve!(d,f,rhs)
        JSimplex.replace_column!(f,d,row;zero_tolerance=ZERO_TOL)
        advance_basis!(basis,row,entering)
        JSimplex._ordinary_forward_solve!(aux,f,dense)
        fill!(unit,0.0);unit[row]=1;JSimplex.transpose_solve!(aux,f,unit)
        if k%80==0 || k>=561
            B=A[:,basis];checks=validate(f,B,rhs,row)
            u=f.updates[end]
            record=Dict{String,Any}("step"=>k,"age"=>(k-1)%320+1,"checks"=>checks,
                "maximum_multiplier"=>maximum(abs,u.multipliers;init=0.0),
                "maximum_upper"=>maximum(c->maximum(abs,c.values;init=0.0),f.upper),
                "minimum_diagonal"=>minimum(i->abs(JSimplex._upper_diagonal(f.upper[i],i)),1:m))
            if k>=561
                JSimplex._ordinary_forward_solve!(aux,f,dense)
                q=JSimplex._compensated_solve_quality!(scratch,B,aux,dense,policy,false)
                correction=JSimplex.forward_solve(f,scratch.residual)
                record["corrected_dense_residual"]=relative_residual(B,aux+correction,dense)
                record["dense_absolute_error"]=q.absolute_error
            end
            if k==640
                record["precise_factor_dense_residual"]=relative_residual(B,precise_direct_forward(f,dense),dense)
            end
            push!(records,record)
        end
        k%320==0 && k<640 && reset!(f,arm,A[:,basis])
    end
    report=Dict("source_sha256"=>source_digest(),"history_sha256"=>bytes2hex(open(sha256,history)),
        "records"=>records,"arm"=>"direct-suhl_suhl-native","interval"=>320)
    save_report(output,report);println("Saved ",output)
end
Base.invokelatest(main,ARGS...)
