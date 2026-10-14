# MA-P: MutableArithmetics in exact RHS propagation

## Decision

The isolated candidate is numerically qualified for the tested inputs, but **not accepted for general production integration**. Only 5/64 cases meet the frozen descriptive consistent-benefit rule. Rational{BigInt} has no qualifying case. BigFloat has two qualifying dense-column equal-bound cases (256 and 512 bits, 32 nonzeros). Float64 has three qualifying cases. These are local kernel results, not whole-presolver speedups or an automatic selective integration admission. No tuning or further run was made.

## Scope and correctness

The reference is an exact copy of the current `_presolve_basic` selected-column RHS staging loop. Candidate uses private rational multiplication/subtraction destinations and buffers, with explicit detachment of published Rational results. Input conversions, exact representability rejection, order, zero/unit shortcuts and equal-bound sharing remain. Source/test/CI/master/environment configuration are unchanged. No complete presolver, LP solver, factorization or broad suite was run.

112 fixtures cover Rational{BigInt}, BigFloat 256/512 and Float64; one/32 nonzeros; dense column and odd-index sparse column; general, unit, zero, equal-bound, unbounded, shared-input and rounding-rejection modes. All **1133/1133 flags in 117 records** pass: reference and candidate versus an independent exact oracle, unchanged values/scalar owners, retained outputs, scoped zero identity/equal sharing, precision and rejected floating roundoff; four explicit scratch-poison tests; one isolated mutation-detection negative control. Mode-specific checks outside their mode are conditional. This is not an exhaustive alias/exception proof or mixed-precision/rounding qualification.

## Measurement

Three serial guarded processes exited 0; stage audits each 14/14 PASS. All 4000 launch pins and 73 source/runtime/dependency trees were verified, with fresh independent admission (4001 bindings). The post-exit independent check passes 17/17, independently recomputing all 64 result rows. Postcheck.py was prepared after manifest freeze and is explicitly not a launch pin.

64 cases per process; three warm and seven measured alternating pairs; 16 full calls per window. Total **3840 windows / 61440 timed calls** (1152 warm, 2688 measured), plus 384 separately timed first calls and process-one correctness calls. All measured compile/recompile counters are zero. All 28 GC windows are retained. Fresh scratch setup, exact conversions, representability checks, output copies and result-vector construction are included; fixture construction, snapshots/oracle and serialization are outside windows. Separately recorded first-call and load observations remain in raw TOML, not added to steady-state kernel ratios. These first calls are not guaranteed cold specializations: process-one correctness precedes cost cases, and earlier fixtures can compile shared methods.

The predeclared descriptive rule requires lower median time/bytes/events in each process, pooled median ratio <=0.95 and >=18/21 faster pairs. It does not authorize production integration. All 64 cases, including regressions and outliers, are reported below. Ratio is candidate/reference; bytes/events are the median of three process medians per 16 calls. Complete per-process values are in cost-processes.csv and aggregate.json.

| Case | Ratio | Pair range | MAD | Faster /21 | Bytes ref→MA | Events ref→MA | Consistent benefit |
| --- | ---: | --- | ---: | ---: | --- | --- | --- |
| Q-1-dense-general | 2.295699 | 0.590–5.141 | 0.241935 | 2 | 24560→38032 | 529→961 | no |
| Q-1-dense-unit | 2.253333 | 0.487–7.592 | 0.286667 | 2 | 17056→28352 | 385→897 | no |
| Q-1-dense-zero | 4.666667 | 0.287–20.200 | 1.083333 | 1 | 4688→15504 | 65→449 | no |
| Q-1-dense-equal | 2.076923 | 0.430–4.827 | 0.213909 | 2 | 17120→26256 | 353→753 | no |
| Q-1-sparse-general | 2.148936 | 0.601–14.981 | 0.301997 | 2 | 24272→33408 | 529→961 | no |
| Q-1-sparse-unit | 2.460000 | 1.826–6.058 | 0.631053 | 0 | 16976→28112 | 385→897 | no |
| Q-1-sparse-zero | 6.000000 | 2.957–46.000 | 1.928571 | 0 | 4688→15440 | 65→449 | no |
| Q-1-sparse-equal | 2.052632 | 0.487–6.121 | 0.250940 | 2 | 17104→26192 | 353→753 | no |
| Q-32-dense-general | 1.111003 | 0.993–2.336 | 0.085519 | 1 | 702304→519008 | 15938→13890 | no |
| Q-32-dense-unit | 1.284280 | 0.585–6.540 | 0.268451 | 2 | 489312→468704 | 12098→14594 | no |
| Q-32-dense-zero | 1.178484 | 0.296–3.990 | 0.166719 | 2 | 77664→88416 | 1090→1474 | no |
| Q-32-dense-equal | 0.987482 | 0.006–3.929 | 0.288279 | 11 | 473184→289632 | 10306→7234 | no |
| Q-32-sparse-general | 1.637294 | 1.137–3.132 | 0.091203 | 0 | 702688→519376 | 15938→13890 | no |
| Q-32-sparse-unit | 1.439350 | 0.919–1.618 | 0.122500 | 1 | 489376→468816 | 12098→14594 | no |
| Q-32-sparse-zero | 1.373626 | 1.242–1.515 | 0.078172 | 0 | 77664→88416 | 1090→1474 | no |
| Q-32-sparse-equal | 1.313405 | 0.495–3.611 | 0.049834 | 2 | 473184→289664 | 10306→7234 | no |
| BF256-1-dense-general | 0.987637 | 0.442–1.467 | 0.025676 | 12 | 123616→120208 | 3665→3745 | no |
| BF256-1-dense-unit | 1.048077 | 0.369–1.715 | 0.024227 | 1 | 104816→105696 | 3121→3281 | no |
| BF256-1-dense-zero | 2.125000 | 1.421–2.889 | 0.193182 | 0 | 11088→21840 | 305→689 | no |
| BF256-1-dense-equal | 1.052174 | 0.824–1.201 | 0.035332 | 4 | 78816→80992 | 2321→2545 | no |
| BF256-1-sparse-general | 1.023669 | 0.524–1.162 | 0.020872 | 7 | 123344→119888 | 3665→3745 | no |
| BF256-1-sparse-unit | 1.038462 | 0.921–1.603 | 0.024602 | 3 | 104784→105680 | 3121→3281 | no |
| BF256-1-sparse-zero | 2.289474 | 1.723–5.026 | 0.139098 | 0 | 11088→21840 | 305→689 | no |
| BF256-1-sparse-equal | 1.062500 | 0.002–1.472 | 0.037669 | 4 | 78800→80976 | 2321→2545 | no |
| BF256-32-dense-general | 0.951813 | 0.045–1.539 | 0.026380 | 18 | 3.49118e+06→2.95989e+06 | 103890→90578 | no |
| BF256-32-dense-unit | 0.983117 | 0.052–13.899 | 0.059011 | 14 | 2.9152e+06→2.58277e+06 | 87250→78482 | no |
| BF256-32-dense-zero | 1.259740 | 0.528–1.522 | 0.059100 | 2 | 73056→83808 | 1330→1714 | no |
| BF256-32-dense-equal | 0.922851 | 0.029–1.650 | 0.022760 | 20 | 2.06547e+06→1.7145e+06 | 60882→52178 | yes |
| BF256-32-sparse-general | 0.958835 | 0.054–16.102 | 0.047563 | 14 | 3.49165e+06→2.96024e+06 | 103890→90578 | no |
| BF256-32-sparse-unit | 0.988279 | 0.884–37.380 | 0.018343 | 12 | 2.91522e+06→2.58285e+06 | 87250→78482 | no |
| BF256-32-sparse-zero | 1.329032 | 0.952–2.566 | 0.101737 | 1 | 73056→83824 | 1330→1714 | no |
| BF256-32-sparse-equal | 0.935605 | 0.741–1.141 | 0.039261 | 16 | 2.06547e+06→1.7145e+06 | 60882→52178 | no |
| BF512-1-dense-general | 1.007812 | 0.466–1.078 | 0.012980 | 7 | 152016→148560 | 4113→4193 | no |
| BF512-1-dense-unit | 1.038864 | 0.926–2.323 | 0.044443 | 6 | 129616→130512 | 3521→3681 | no |
| BF512-1-dense-zero | 2.088235 | 1.625–2.837 | 0.145378 | 0 | 11600→22352 | 337→721 | no |
| BF512-1-dense-equal | 1.018000 | 0.953–1.140 | 0.027346 | 7 | 96976→99152 | 2593→2817 | no |
| BF512-1-sparse-general | 1.011643 | 0.440–3.018 | 0.016778 | 7 | 152016→148560 | 4113→4193 | no |
| BF512-1-sparse-unit | 1.024316 | 0.480–5.419 | 0.013806 | 5 | 129616→130512 | 3521→3681 | no |
| BF512-1-sparse-zero | 1.945946 | 1.556–2.273 | 0.133001 | 0 | 11600→22352 | 337→721 | no |
| BF512-1-sparse-equal | 1.048096 | 0.980–1.106 | 0.017104 | 2 | 96976→99152 | 2593→2817 | no |
| BF512-32-dense-general | 0.969436 | 0.060–17.868 | 0.049210 | 15 | 4.28981e+06→3.75818e+06 | 116738→103426 | no |
| BF512-32-dense-unit | 1.034307 | 0.805–15.947 | 0.048926 | 7 | 3.59078e+06→3.25834e+06 | 98562→89794 | no |
| BF512-32-dense-zero | 1.274648 | 1.140–3.122 | 0.092999 | 0 | 73568→84320 | 1362→1746 | no |
| BF512-32-dense-equal | 0.936751 | 0.686–1.457 | 0.032659 | 18 | 2.52814e+06→2.1772e+06 | 68098→59394 | yes |
| BF512-32-sparse-general | 0.974576 | 0.786–12.042 | 0.047503 | 12 | 4.28994e+06→3.75846e+06 | 116738→103426 | no |
| BF512-32-sparse-unit | 0.991415 | 0.875–30.136 | 0.032236 | 11 | 3.59107e+06→3.25856e+06 | 98562→89794 | no |
| BF512-32-sparse-zero | 1.305344 | 0.912–1.489 | 0.075609 | 1 | 73568→84320 | 1362→1746 | no |
| BF512-32-sparse-equal | 1.001885 | 0.885–1.520 | 0.036546 | 10 | 2.52784e+06→2.17686e+06 | 68098→59394 | no |
| F64-1-dense-general | 1.044828 | 0.805–1.352 | 0.031827 | 4 | 63984→60400 | 1777→1841 | no |
| F64-1-dense-unit | 1.064257 | 0.826–1.510 | 0.018140 | 2 | 52704→54000 | 1441→1617 | no |
| F64-1-dense-zero | 2.520000 | 1.462–3.421 | 0.330000 | 0 | 7504→18256 | 177→561 | no |
| F64-1-dense-equal | 1.129730 | 0.899–1.757 | 0.034252 | 2 | 41824→43360 | 1169→1361 | no |
| F64-1-sparse-general | 1.003322 | 0.794–266.471 | 0.054501 | 10 | 63824→60256 | 1777→1841 | no |
| F64-1-sparse-unit | 1.059480 | 0.745–1.390 | 0.039785 | 6 | 52688→53968 | 1441→1617 | no |
| F64-1-sparse-zero | 2.400000 | 1.543–3.190 | 0.221429 | 0 | 7504→18256 | 177→561 | no |
| F64-1-sparse-equal | 1.116162 | 0.876–1.188 | 0.058702 | 4 | 41808→43344 | 1169→1361 | no |
| F64-32-dense-general | 0.880257 | 0.027–0.996 | 0.033400 | 21 | 1.8051e+06→1.31717e+06 | 49922→37586 | yes |
| F64-32-dense-unit | 0.979266 | 0.906–1.306 | 0.060192 | 14 | 1.46238e+06→1.14621e+06 | 39682→31922 | no |
| F64-32-dense-zero | 1.646154 | 1.459–2.280 | 0.078484 | 0 | 37728→48480 | 210→594 | no |
| F64-32-dense-equal | 0.897869 | 0.380–1.014 | 0.025317 | 20 | 1.09976e+06→775920 | 30466→22226 | yes |
| F64-32-sparse-general | 1.009240 | 0.410–1.854 | 0.081907 | 9 | 1.80426e+06→1.31658e+06 | 49922→37586 | no |
| F64-32-sparse-unit | 0.934184 | 0.022–66.496 | 0.053690 | 16 | 1.46336e+06→1.14694e+06 | 39682→31922 | no |
| F64-32-sparse-zero | 1.651515 | 1.013–1.938 | 0.071805 | 0 | 37728→48496 | 210→594 | no |
| F64-32-sparse-equal | 0.878478 | 0.650–1.758 | 0.038400 | 19 | 1.10005e+06→776128 | 30466→22226 | yes |

## Interpretation and work/memory review

Rational single-entry cases slow substantially (general about 2.15–2.30×; zero about 4.67–6× in tiny windows). Long general/equal cases reduce bytes and events but do not establish consistent time benefit; long unit cases even increase event counts. Fewer bytes alone therefore do not justify promotion. BigFloat long general cases reduce bytes/events but have only modest pooled timing gains; dense equal-bound 32-entry cases meet the descriptive rule at ratios about 0.923/0.937. Their sparse counterparts do not both qualify. Small-window timing, GC and only three processes limit generalization; no backend cause is assigned to between-layout differences.

Each selected-column call adds two private rational destinations and two buffers, initialized even when unused. This is **unnecessary work and allocation cost on zero/free/simple paths** in the measured candidate, and a concrete reason not to integrate it generally. Published Q scratch results require owned mutable leaves; these copies are necessary for correctness. No new full-column scan, basis solve, cache or retained update chain is introduced. Existing O(nnz(column)) staging remains, with operand-bit-length arithmetic costs. Result/scratch retention is bounded per call, but GC traffic is not a native live-memory or collection proof. No numerical safeguard, tolerance, coefficient, precision or failed result was changed to improve measurements.

## Execution and preservation

Inclusive invocation durations: 8.754622427, 7.766030401, 7.759190756 seconds; total 24.279843584. These are guard evidence, not benchmark speedup. 25 resource records, minimum available RAM 22749396 KiB, maximum swap 0 KiB. Full 152 old/new process groups AND sessions absent; no Julia after completion. Boot, start ticks and commands are preserved in process/postcheck evidence. All three slots consumed; no rerun.

MA-O remains rejected and frozen; this distinct RHS experiment does not reopen it. Six MA-O current STATUS/roadmap bindings map only to MA-P before copies; older maps remain unchanged. CI off, HH disabled, automation paused. Broader performance plan stays open. A future narrower design would need its own explicit plan and review; this result does not create one automatically.

Evidence: results/MA-P/plan.md, admission-review.md, run-{1,2,3}/raw.toml, audit-{1,2,3}.json, aggregate.json, postcheck.json, cost-processes.csv and independent result-review.md. The first author inspection expected a nonexistent optional reviewer `checks` key and raised KeyError before launch; author-admission.json records the error and actual required-schema verification. No reviewer data or numerical input was altered.
