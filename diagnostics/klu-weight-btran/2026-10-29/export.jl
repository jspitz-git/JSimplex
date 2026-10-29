# Diagnostic-only unchanged KLU controls and combined owned export.
function make_factor(B)
    f=KLU.KLUFactorization(B);f.common.tol=1.;f.common.btf=1;f.common.ordering=0;f.common.scale=1;f.common.maxwork=10.
    KLU.klu_factor!(f);f
end
function export_once(f)
    n=f.n;b=f.nblocks
    Lp=Vector{Int}(undef,n+1);Li=Vector{Int}(undef,f.lnz);Lx=Vector{Float64}(undef,f.lnz)
    Up=similar(Lp);Ui=Vector{Int}(undef,f.unz);Ux=Vector{Float64}(undef,f.unz)
    Fp=similar(Lp);Fi=Vector{Int}(undef,f.nzoff);Fx=Vector{Float64}(undef,f.nzoff)
    P=Vector{Int}(undef,n);Q=similar(P);R=Vector{Int}(undef,b+1);Rs=Vector{Float64}(undef,n)
    if isempty(Fi)
        fill!(Fp,0);KLU._extract!(f;Lp,Li,Lx,Up,Ui,Ux,P,Q,R,Rs)
    else
        KLU._extract!(f;Lp,Li,Lx,Up,Ui,Ux,Fp,Fi,Fx,P,Q,R,Rs)
    end
    for v in (Lp,Li,Up,Ui,Fp,Fi,P,Q,R);v .+= 1;end
    (Lp=Lp,Li=Li,Lx=Lx,Up=Up,Ui=Ui,Ux=Ux,Fp=Fp,Fi=Fi,Fx=Fx,P=P,Q=Q,R=R,Rs=Rs)
end
