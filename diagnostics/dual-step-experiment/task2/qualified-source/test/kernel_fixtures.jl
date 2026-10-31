function kernel_case(kind::Symbol,n::Int=8;time_limit=Inf,extra=:identity)
    B=Matrix{Float64}(I,n,n).*4
    if kind!=:diagonal
        for j in 1:n,i in 1:n
            i==j&&continue
            (kind==:dense || abs(i-j)<=2 || kind==:sparse && mod(13i+7j,23)==0) && (B[i,j]=(mod(3i+5j,7)-3)/512)
        end
    end
    B=sparse(B);C=spdiagm(0=>ones(n))
    extra==:overflow && (C[1,1]=floatmax(Float64))
    extra==:nonordered && (C[2,1]=0.5)
    A=hcat(B,C)
    if extra==:nonordered
        # Disorder only a nonbasic column, before the immutable ownership epoch.
        p=A.colptr[n+1];q=p+1
        A.rowval[p],A.rowval[q]=A.rowval[q],A.rowval[p]
        A.nzval[p],A.nzval[q]=A.nzval[q],A.nzval[p]
    end
    p=J.LinearProblem(A,zeros(2n);row_lower=fill(-100.,n),row_upper=fill(100.,n),column_lower=zeros(2n))
    ws=J.initialize_workspace(p,J.SolverOptions(Float64;pricing=:devex,verbose=false,time_limit=time_limit))
    ws.basis.basic_indices.=1:n;fill!(ws.basis.states,J.AT_LOWER);ws.basis.states[1:n].=J.BASIC
    J.recompute!(ws;refactorize=true)
    clock=J._SolveDeadline(ws.progress.start_ns,ws.options.time_limit)
    e=E.import_phase(ws,clock,E.EnginePolicy(ws))
    (e=e,source=ws,B=B,A=A)
end
struct KernelThrowFactor{F,X}
    inner::F
    work::Vector{Float64}
    exception::X
end
J.forward_solve!(out,f::KernelThrowFactor,rhs)=throw(f.exception)
J.transpose_solve!(out,f::KernelThrowFactor,rhs)=throw(f.exception)
function throwing_engine(e,exception)
    old=e.ws;f=KernelThrowFactor(old.factorization,old.factorization.work,exception)
    ws=J.SimplexWorkspace((k==:factorization ? f : getfield(old,k) for k in fieldnames(typeof(old)))...)
    ks=E.KernelState(e.owner,length(old.basis.basic_indices),e.supports,f)
    E.EngineState((k==:ws ? ws : k==:kernels ? ks : getfield(e,k) for k in fieldnames(typeof(e)))...)
end
function full_direction_reference(ws,d,rhs,pivot)
    copyto!(ws.scratch.row_rhs,rhs)
    J._dual_direction_residual_ok!(ws,d,pivot)
end

# Test-only genuine-forward perturbation exercises residual rejection of an
# actual solve receipt. It does not model an observed native solver defect.
struct KernelPerturbedFactor{F}
    inner::F
    work::Vector{Float64}
    perturbation::Float64
end
function J.forward_solve!(out,f::KernelPerturbedFactor,rhs)
    J.forward_solve!(out,f.inner,rhs)
    out[1]+=f.perturbation
    out
end
J.transpose_solve!(out,f::KernelPerturbedFactor,rhs)=J.transpose_solve!(out,f.inner,rhs)
function perturbed_engine(e,amount)
    old=e.ws;f=KernelPerturbedFactor(old.factorization,old.factorization.work,amount)
    ws=J.SimplexWorkspace((k==:factorization ? f : getfield(old,k) for k in fieldnames(typeof(old)))...)
    ks=E.KernelState(e.owner,length(old.basis.basic_indices),e.supports,f)
    E.EngineState((k==:ws ? ws : k==:kernels ? ks : getfield(e,k) for k in fieldnames(typeof(e)))...)
end
