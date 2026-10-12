# S6-Z: reliable zero-budget artificial exchange qualification

Status: qualified; fresh independent review pending. No production or test change.
Base cdd474c. New attempt `qualification-1`, not a repeat of S6-X/Y.

## Intent and exact construction

Only `Reliable artificial exchanges need no reconstruction recovery` is addressed.
S6-Y distinguished relative basis reliability from original absolute feasibility;
its printed CI phase point is not a capture of the private export candidate. The
four historical scalar-unknown `accepted=false` assertions remain unresolved.

The new fixture uses A=I6, rhs=[1,1,0,0,0,0], zero objective and nonnegative columns.
Auxiliary column7 duplicates column6 with cost1. Initial phase basis[1,2,3,4,5,7]
is exactly I6; exchanging7 for6 leaves I6. The maintained artificial value is zero,
so the zero-step exchange preserves the exact known feasible point. This proof was
recorded before the run. It is a different feasible set, not an equivalent original
matrix or native reconstruction/cancellation stress test.

The diagnostic extracts the existing helper and replaces only its name and matrix
expression; every other helper byte is unchanged. It extracts the original target
oracle and substitutes the helper name, enables bounded kernel counters, and routes
one real `remove_artificials!` call through a capture wrapper. All four original
assertions are preserved. No factor stubs, injected arithmetic, forced qualities,
policy/tolerance/precision changes or observer callbacks are used. Existing native
helper, success test and recovery/cancel tests remain byte-identical on disk.

## Evidence and result

- Four Float32 cases: pfi,forrest_tomlin,suhl_suhl,bartels_golub; max_refinements0.
  All options and policy fields exactly equal their corresponding S6-X zero-budget
  records; no old case was executed again.
- 29/29 assertions:16 original,12 added (basis/point/original certificate per case),
  one ambient precision/rounding/subnormal preservation check. Guard exit0.
- All23 audit gates;621 pins independently verified for hashes, resolved paths and
  inventory membership;517 shared source/test/runtime/environment/launcher pins.
  Source is active checkout, Julia1.13.0 AArch64, Julia/BLAS1 and existing memory guard.
- Every result accepted. Original basis1:6; structural point[1,1,0,0,0,0], activity
  point equal rhs, exact equations and original certificate pass. Original iteration1.
- Within each remove call:5FTRAN,4BTRAN,2counted refactorization kernels;
  events artificial_removed1,refactor_other2,refactor_initial1,correction_attempt0.
  Phase work advances from0iterations/1refactor to1/2; original ends1/3.

The initial phase/original setup occurs before the counted remove window. Temporary
fresh export workspace factor construction occurs inside that window but is setup,
not one of the two refactorization kernels. Thus 2 does not mean only two total
factor constructions. Native quality/certification checks within production remain
unchanged. Four extra standalone original certificates and original post-call
basis-quality assertions are outside the counted remove window. No benchmark or
speedup inference follows from these cold counts.

Raw and portable evidence: `results/S6-Z/qualification-1-*`. Host runner401309,
child401310,driver401301 subsequently absent on boot20de7dde-704e-41c8-bee7-b8511c0a86b0
(the authoritative process.json retains the exact boot ID). No numerical job remains.

## Work and limitations

No production work, allocations or retained-memory change. Four small workspaces
pairs and temporary export workspaces are required by the actual exchange path;
bounded before/after copies and dictionaries are diagnostic only. No new solver,
reference/corpus/cost measurement, extra exchange, observer or callback solve.
The exact matrix makes the narrow reliable-case intent explicit; it does not test
the old homogeneous-row reconstruction difficulty. Those native testsets and S6-X/Y
remain separately preserved. Local qualification is not actual x64/fullsuite success,
a proof of historical rejection cause or closure of broader S6.

Next: separate S6-AA permanent test-only RED/GREEN plan. No production safeguards
or original assertions may change. Accepted S6-Z driver/audit must not be rerun.
