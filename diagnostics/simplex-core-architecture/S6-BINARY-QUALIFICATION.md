# S6-O/P: binary fixture qualification

Status: qualification complete; no permanent replacement accepted. Independent
final review accepted diagnostic evidence without blockers; see S6-BINARY-QUALIFICATION-REVIEW.md. Production, tests, tolerances, precision and CI configuration unchanged.

## Decision and evidence

S6-O triangular A=[s s;0 d],s=2^-20,d=2^-43,row bounds[-1,-2]..[1,2] passes all
13 original assertions. Raw `.superpowers/simplex-core-architecture/S6-O/qualify-1`,
portable `results/S6-O/qualify-1-*`: exit0,24audit checks,608pins. All four scalar
types return exact optimum-2^44 and strictly feasible points. However, every
presolve log reports1row/2columns/2nnz (original2/2/4). Float32 takes1iteration/
1refactor; other types0iterations/2refactors with postsolve projection/cleanup.
This is a valid bounded LP with an optimal edge, not preservation of the original
nearly-dependent two-row solve. **Do not promote it as a replacement on this pass.**
The original two-row matrix may still be used during original-model cleanup; the
report does not claim it is absent from all factorization paths. The observed main
presolve topology and numerical route have changed substantially.

S6-P balanced A=[s s;s s-d], same original bounds[-1,-1]..[1,1], costs[0,-1], free
columns and defaults, retains the4nonzeros and observed2/2/4presolve topology.
Raw `.superpowers/simplex-core-architecture/S6-P/qualify-1`, portable
`results/S6-P/qualify-1-*`: **12pass/1original objective equality failure**, exit1
preserved. The audit has23passing checks and2explicit failed acceptance checks
(original_oracle_passed/exact_returned_optima); `all_passed=false` is retained.
All609pins, actualsource/testSHA, model snapshots/globals and single-thread guard
verify. All cases2iterations/1refactor. Float32,BigFloat,rational return strict
optima; **Float64 again returns gap-1/16**, rows[1,-1-2^-47]. Its objective equals
exact c'x, original primal and separately supplied analytic witness certificates
accept within unchanged tolerances. **Balanced candidate REJECTED for repair.**
Do not relabel its failed gates as a successful qualification or change equality.

Both drivers reconstruct the original testset by reversing their precise matrix/
bound/recording substitutions. No original assertion or public @inferred solve
was changed. Only S6-O changes second-row bounds. Diagnostic SolverOptions/policy
are reconstructed after solve, not injected. The postsolve analytic witness is not
runtime basis/dual capture. Julia1.13.0aarch64, BigFloat256nearest, Julia/BLAS1,
heap2GiB/VM8GiB/minRAM6GiB/maxswap1GiB; raw process/log/pins retained. No accepted
S6-N measurement, broad corpus, long baseline or cost series was repeated.

## Exact proofs and the failed hypothesis

Triangular determinant=s*d=2^-63. Infinity condition number is
2s*(1/s+1/d)=2^24+2. Its unique maximizing x2=2/d=2^44 leaves an optimal edge
x1∈[-2^44-2^20,-2^44+2^20]. The free columns and bounded invertible row map exclude
nonzero recession directions. A separately supplied dual[0,-1/d] is stationary.
The maximum objective improvement admitted by independent row tolerance t follows
from x2<= (2+t)/d, not the old two-row difference formula.

Balanced determinant=-s*d=-2^-63. Infinity norm condition=4s/d=2^25. For y=A*x,
x2=(y1-y2)/d, so strict optimum-2^44 is uniquely attained at y=[1,-1] and
x=[-2^44+2^20,2^44]. Dual[-1/d,1/d] satisfies exact stationarity and proper row
signs. With r=y-[1,-1], objective gap=(r2-r1)/d. Float64 r=[0,-2^-47] therefore
gives gap=-1/16. Independent rational audit recomputes the actual returned rows,
objective and residual identity. The relaxed feasibility lower bound remains
-2(1+t)/d, but this does not redefine the problem as a relaxed optimization LP.

The hypothesis that a binary maximum matrix coefficient would alone make the
native calculation exact is disproved by S6-P. It is not evidence identifying
UMFPACK scaling, pivot choice, incremental basis update, reconstruction or final
certification as the originating arithmetic step. No runtime intermediate trace
was captured. Avoid further input tuning based on an unobserved backend path.

## Work/memory and scope

No production work, scans, solves, allocations or retention changed. Each diagnostic
runs exactly four tiny public solves plus bounded snapshots/exact proof/certificate
checks. New drivers reuse their single postsolve model snapshot; accepted old S6-N
remains unchanged. No timing or allocation saving claim, performance benchmark,
full-suite/x64 success, or unchanged numerical trajectory claim is made.

Next is a separate S6-Q Float64 runtime-point provenance plan. Reuse the accepted
S6-N endpoint as a control; a new bounded observer trace adds previously missing
intermediate-state coverage, not another census/baseline or speculative repair.
