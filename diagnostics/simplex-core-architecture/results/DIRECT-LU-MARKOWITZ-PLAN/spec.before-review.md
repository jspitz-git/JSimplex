# Common factor export and direct LU trials with Markowitz

## Decision and scope

The user requests a new architectural workstream: a common factor-export interface
and all three direct LU prototypes (Forrest–Tomlin, Suhl–Suhl, Bartels–Golub) with
Markowitz in short comparative tests. This document specifies that workstream.
The previous micro-optimization programme is not declared complete; its accepted
changes and rejected experiments remain valid and frozen.

Baseline: diagnostic branch 9ea533ebcba2d5611a839b8e4bb03b59c2b1c371;
master 6f68e24e8ddac42b948da8fcc2d636c010751194. Rebind actual refs before execution.
Current ordinary correction-factor managers already support Markowitz. The direct
prototype in diagnostics/basis-direct-lu/reproduce/direct.jl supports only native
Float64 legacy operation. It is historical evidence, not a script to reinstall.

First deliverable is an isolated Float64 experiment, not a production default.
Dynamic sparse storage, new CSR kernels, MA arithmetic, HH symbolic reuse and
changed pivot/refactorization policies are separate future workstreams.

## Factor contract

For exported L, U, row permutation p, column permutation q, and original-row
scaling S, define P*x=x[p], Q=I[:,q], and P*S*B*Q=L*U. L is canonical CSC unit
lower triangular with one explicit diagonal per column; U is canonical CSC upper
triangular with one finite nonzero diagonal per column. Both are Float64/Int.
A divide_scaling flag means S[i,i]=1/scaling[i], otherwise S[i,i]=scaling[i].
Scaling entries must be positive and finite; Markowitz uses ones and false.
Empty factors are valid. Duplicate entries are consolidated by the existing
extraction semantics, not by a new arithmetic order chosen by this project.

An export owns its L/U arrays, p/q/scaling arrays and never aliases the backend's
mutable buffers. Existing extraction from Markowitz already folds the dense
core's row permutation into L and p; reuse it rather than writing another block
LU decomposition. Native export must retain the established scaling-orientation
check, including its possible solve and temporary vectors. No orientation guess.
Unsupported backend/type or unresolvable orientation returns nothing. Singular
factorization and unexpected extraction errors propagate; do not catch all errors.
Malformed claimed exports are rejected before publishing a direct factor.

The direct manager represents B=B0*inv(R)*U*Q', B0=inv(S)*P'*L initially.
For safe optional normalization D=diag(U), use B0=inv(S)*P'*L*D and Unew=inv(D)*U.
Keep the historical finite/nonzero/underflow rejection rule. Failed normalization
retains the unnormalized direct representation; unsupported export retains the
ordinary correction manager. Record these outcomes explicitly in every trial.
No small coefficients, tolerances, numerical recovery or certification are removed.

## Ownership and lifecycle

Copied managers may share only read-only extracted Float64 L/p/scaling/D data;
mutable U, permutations, solve scratch, prepared-spike caches and update-history
ownership follow existing manager contracts. A backend refactorization cannot
change an earlier export or a copied manager. Refactorization constructs a complete
candidate, then publishes it; failure preserves the old direct manager. Store the
requested backend and normalization mode so fallback never silently switches them.
No native factor or Markowitz workspace is retained after successful export merely
for convenience. Fallback alone retains the ordinary backend it actually needs.
Other precisions retain ordinary dispatch and original arithmetic. Generalization
to mutable BigFloat/BigInt scalar ownership is explicitly outside this first trial.

## Costs and decision

Count work at setup/refactor separately from every FTRAN/BTRAN/update. Export costs
include backend construction, extraction, core traversal, permutation assembly,
normalization, conversion to packed U and validation. Markowitz extraction currently
scans its dense core twice and creates triplets plus CSC output; do not call these
zero-copy exports. Avoid a second factorization, an unused identity-U construction,
an HH row index unused by this consumer, or keeping both temporary and packed U.
No export or full-factor validation may run on every solve or column replacement.

Compare ordinary correction versus normalized direct for all three managers and
native/Markowitz separately. Include initialization and refactorization in lifecycle
cost; show component costs, bytes/events and retained reachable memory separately.
A faster solve alone is not acceptance. No end-to-end claim from component tests,
short trajectories or old single-run results. Finite residuals and original-LP
certification, where solves are performed, take precedence over speed.

Use one Julia process at a time, Julia/BLAS threads=1, heap hint=2 GiB, VM limit=8 GiB,
available RAM floor=6 GiB, swap ceiling=1 GiB. All process limits include termination.
CI stays disabled, automation paused, HH reuse disabled; preserve user environments.
This request prepares/reviews documents only. Later execution uses standing human
permission for short runs plus a concrete independently accepted run admission.
