# S6-AG: real dual control certificate provenance

Status: accepted by fresh independent gpt-6-astra review, no findings.
Basee123b17/master3c0af5c.
One new Float64 PFI public dual_iteration! call, unwrapped real factor, no observer,
adapter or injection. No AF/AE driver rerun and no extra quality/certificate/component
or basis-solve calls outside required setup and public execution.

provenance-1:10/10,exit0,29audit gates628pins,517shared source/runtime/environment
pins,6raw/portable/driver/AF-rejection supplement checks. Actual source/inputbits/
options/policy/model/globals/user hashes match. Runner413092/child413093/group413083
separately absent,noJulia,boot20de7dde-704e-41c8-bee7-b8511c0a86b0.
Production/tests/master/CI unchanged. S6-AF remains NOT accepted, its4control failures
and three false gates preserved. AG's expected observation is not a replacement oracle.

## Captured input and source binding

Immediately after public return, owned scratch.rho is exactly
[-8388607/2,4194304,0,0], matching AE. Actual captured CSC gives B'rho=e2 exactly;
tableau is[0,1,0,0,0,-rho...]. Selected row2/below-lower, entering=-1. Model/bounds,
unit scaling, point/basis/states and options/policy captured without numerical helpers.
Primal remains[0,-1,0,0,0,-1,-1-2^-23,0,0], basis1:4,iterations0.

Source chain in results/S6-AG/PREFLIGHT.md: native _dual_iteration_core! directly
calls unchecked; final unit BTRAN uses scratch.rho as destination. In no-eligible
branch, final certificate receives that rho by reference and only reads it. Terminal
return and timing wrapper do not subsequently write rho. This ties post-return data
to THIS call's certificate input, not AF's four uncaptured control inputs. No branch
instrumentation or observation callback was added.

Status NUMERICAL_ERROR and message "row combination does not certify infeasibility
at primal tolerance" match AF. Public path uses1FTRAN/3BTRAN/1ordinaryrefactor,
separate from setup; no correction_attempt/pivot_rejected/pivot_completed/bound_flipped.
Initial and final factor identity preserved. No public candidate retry or pivot occurs.

## Conservative interval refusal

On the captured rho and ordered first CSC column, exact coefficient is0. Source
_add_product_bounds widens each product and sum with prevfloat/nextfloat. Replaying
that specified binary64 formula offline gives the interval
[-6755399441055745/4835703278458516698824704,
 +6755399441055745/4835703278458516698824704]. Its lower endpoint is negative and the
captured first column upper bound is infinite. Thus the source's conservative
unbounded-column check refuses the row certificate before bound penalties.

The interval is reconstructed from actual inputs and pinned source, not a captured
internal intermediate or proof of an individual machine instruction. It explains the
new PFI call under the recorded nearest-rounding/no-subnormal-flush settings. It does
not establish other managers' private branches, AF observer neutrality or historical
x64 cause. Exact factor equations alone do not guarantee interval certification.
There is no justification to drop enclosure safeguards, alter tolerance/precision,
change production or promote S6-J. No whole-solver correctness/performance claim.

## Work, decision boundary and next step

No unnecessary production work or memory introduced. One small workspace setup and
one public iteration; owned post-return vectors/model metadata only. Offline work is
bounded rational comparisons and two binary64 interval products. Setup kernels stored
separately. No timing benchmark, redundant certificate or numerical rerun needed.

AG closes the missing input provenance for one new PFI case. Next S6-AH is a separate
source/evidence-only acceptance-contract decision: what should a real negative control
prove for the recovery-budget fixture, independent of infeasibility certification?
It must retain AF's rejected overall qualification and use only clearly identified
subject observations, original assertions and AG provenance. No new Julia/adapter
implementation in AH. Any permanent repair needs its own later RED/GREEN and master
gates. CI disabled; broaderS6/fullsuite/x64 and original historical failures remain open.
