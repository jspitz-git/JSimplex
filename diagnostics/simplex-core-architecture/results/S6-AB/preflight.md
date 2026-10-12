# S6-AB preflight (before adapter/numerics)

Base4030ce4/master74f7835; host403571/403572/403563 absent, no Julia, boot
20de7dde-704e-41c8-bee7-b8511c0a86b0 (host authoritative full boot is recorded in process pins).

The current test success oracle has seven assertions per accepted exchange: initial
legacy certificate, accepted, one iteration, basis1:6, reliable reconstructed basis,
legacy certificate, original certificate. X has all local accepted; Y shows a printed
phase point is not a private export candidate. Neither diagnoses historical rejection.
Reuse X/Y/Z/AA evidence; no old driver execution.

Source contracts:
- simplex_phase_one.jl144-244: candidate unit BTRAN, ordinary candidate FTRAN and
  prepared FTRAN precede replace_column!, then basis states/iteration and checkpoint
  invalidation. _phase_refactor! calls recompute!, which refactors before RHS/solves.
- simplex.jl412-481: refactor event precedes primal FTRAN and cost BTRAN. Native
  policy does not refine ordinary solves; assert solve_refinement=false, recovery=false,
  hypersparse=false before subject. Relative homogeneous-row quality rejects nonzero
  coordinate3 regardless of its small absolute size. Native phase correction uses
  actual residual RHS -2^-10*e3, solves once and publishes only after quality checks.
- hypersparse_pipeline.jl448: invalidate destination then ordinary/prepared/transpose
  dispatch. Forward each exact inner method once, retaining prepared-update semantics.
- original workspace is never wrapped. fresh export initialize_workspace uses ordinary
  concrete factor; adoption copies it into original. Phase wrapper never exported.
- remove/recompute native path has no copy_basis_factorization call. Copy is not
  required here; define explicit fail-fast copy guard rather than claim untested copy
  forwarding. Any attempted copy fails qualification. No general lifecycle claim.

Adapter contract: wrap phase after setup, sharing only its already owned fields;
original has independent storage. After successful update6, first successful phase
refactor arms one ordinary primal FTRAN; require identity B, actual [1,1,0,0,0,0]
RHS, zero initial coordinate3 and add dyadic2^-10 after real solve. Count calls before
forward, record owned RHS/output. Refactor/update disarm before forwarding; only first
post-update refactor can arm, hits never reset. Destination invalidation forwards and
does not reset one-shot lifetime. Prepared candidate solves and all BTRAN untouched.
New update/refactor/invalidation paths checked by each subject exchange with exact
counter/ordering gates; copy unsupported and zero calls, not numerically qualified.

Work oracle: per phase subject exactly4FTRAN(2ordinary+1prepared+1correction),2BTRAN,
1update,1refactor,1hit,1primal-RHS call,1correction-RHS call; counters continue after hit.
Whole remove expected6FTRAN/4BTRAN/2refactor kernels vs control5/4/2, fresh initialization
additional. If observed counts disagree retain outcome and diagnose, never weaken
oracle silently. Static negative oracle adds a fresh primal-RHS call while retaining
endpoint/events/hit; it must reject without another numerical call.
At most16exchanges; postcall seven-assertion contract and exactpoint checks distinct
from timed/counted remove. No callback solves/refactors/certificates/mutations.
