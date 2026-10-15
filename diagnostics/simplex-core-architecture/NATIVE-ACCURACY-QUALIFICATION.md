# Native Float64 accuracy-policy component qualification

ONE admitted attempt completed in 4.1338797280041035 seconds inclusive, exit 0. The frozen 45-second allowance is CONSUMED. All 13 execution/integrity gates and nine supplemental postchecks passed. There was no retry, source change during execution or old benchmark replay.

Both P (pivot1/IRSTEP0) and R (pivot0.1/IRSTEP2) pass all 2126 scheduled solve residuals per arm and all ownership/copy/refactor/failure predicates. C (current0.1/0) passes1950/2126 and fails176 sparse96 DSE outputs, preserving the original failure. All176 C outputs match the saved diagnostic bits exactly. Maximum residual/bound ratios: C18.861415966018026, P0.001425219790415795, R0.0007814103158076206. All compared within-arm repeated window outputs have identical bits.

Actual counts:141fresh LU,9lu! attempts (three expected SingularException/status1),3shallow copies,4245FTRAN+2133BTRAN=6378solve entries and12factor snapshots.132windows comprise36warm and96measured windows; each includes one construction and48solves (16entering/DSE/unit triplets). All192measured timed regions have zero compile/recompile and zero in-window GC. Three lifecycle records and132window records plus six guard/raw files give141original files, with141byte-identical portable copies. Postcheck.py and summarize.py are post-exit supplements, not retrospective launch pins.

## Accuracy mechanism and memory

All sparse cases selected UNSYMMETRIC strategy1, all dense cases SYMMETRIC3. P is full partial-pivot acceptance only in the observed sparse strategy; unchanged symmetric pivot tolerance0.001 remains in all arms. P factors match C bit-for-bit on sparse32 and both dense cases. On sparse96, P reduces max|U|/max|scaledB| from245688.02631578944 to1.0. L fill remains234, U increases248→263; factorization Info FLOPS528→570 and NUMERIC_SIZE893→896units, with16bytes/unit (+48reported bytes). Reachable Julia graph remains8312bytes because it excludes native factor storage. Exact factor identities are nonzero for every arm/fixture; passing residuals do not imply exact factors or a general stability proof.

R retains exactly the same L/U/p/q/Rs/do_recip bits as C on every fixture, including sparse96 growth245688.026. It instead performs1232attempted and1232retained native refinements, with maximum one attempt observed per solve despite allowed maximum two. These are528dense32,176sparse96 DSE and528dense96 window calls; lifecycle and sparse32 have zero attempts. C/P have zero attempts. Aggregate per-solve native SOLVE_FLOPS are11365672(C),11381512(P),75594571(R); these exclude construction work and are metadata, not a complete instrumented native work trace. Even R calls taking no correction still use the refinement-capable path and can pay residual-evaluation overhead.

R workspace W is5n versus n, Wi=n in all arms. Extra4n Float64 payload is1024bytes at n32 or3072bytes at n96 per workspace, including copied workspace. Final reachable graph differences are exactly these values. Whole-process terminal resident high water is399924KiB; three sampled resource records and terminal memory show minimum available RAM22252120KiB, swap0. RSS/HWM/VmPeak are recorded separately; process peak includes compilation/import/retained diagnostic output and cannot be attributed to one arm. Native Info and graph sizes do not establish a native allocation/free ledger.

## Cost observations

All results below use eight matched measured rounds; none is excluded. Microseconds are side medians for one construction or48solves. Ratios are medians of paired arm/C ratios, not ratios of side medians. Short constructor windows and one process limit inference; no universal or end-to-end speedup is claimed. In particular P shows no material solve penalty in these observations, not a demonstrated solver speedup.

| Fixture | Region | C µs | P µs | R µs | P/C paired median [min,max]; MAD | R/C paired median [min,max]; MAD |
| --- | --- | ---: | ---: | ---: | --- | --- |
| sparse32 | construction | 12.400 | 12.650 | 12.600 | 1.0038 [0.5915,1.0826]; 0.0419 | 1.0127 [0.9385,2.5258]; 0.0445 |
| sparse32 | solve | 26.600 | 27.000 | 37.000 | 1.0093 [0.9710,1.0341]; 0.0169 | 1.3936 [1.3684,1.6558]; 0.0172 |
| dense32 | construction | 27.700 | 28.200 | 27.250 | 1.0054 [0.9467,1.0394]; 0.0218 | 0.9802 [0.9033,1.0221]; 0.0108 |
| dense32 | solve | 36.150 | 36.250 | 167.900 | 1.0014 [0.2478,1.2865]; 0.0930 | 4.6446 [1.1606,4.7632]; 0.0726 |
| sparse96 | construction | 35.250 | 36.200 | 37.450 | 1.0287 [0.9262,1.1170]; 0.0098 | 1.0618 [0.9833,1.2507]; 0.0225 |
| sparse96 | solve | 43.850 | 43.300 | 101.450 | 0.9977 [0.8600,1.2156]; 0.0767 | 2.2747 [1.8844,2.4839]; 0.1094 |
| dense96 | construction | 178.250 | 181.150 | 188.050 | 0.9995 [0.9632,1.0897]; 0.0256 | 1.0163 [0.9674,1.2186]; 0.0402 |
| dense96 | solve | 197.450 | 194.650 | 1418.151 | 1.0005 [0.9115,1.0198]; 0.0104 | 6.9845 [6.8353,10.0605]; 0.1184 |

All solve regions allocate zero recorded bytes/events. Constructor aggregate GC-counter medians and ranges follow. These counters can include native callback traffic; they are not pure Julia-object counts or live retained memory. P adds24median bytes on sparse32, removes8on sparse96, and matches dense cases; events match C. Thus P is not a universal no-allocation-increase claim. R pays the stated additional workspace and generally higher constructor bytes/events.

| Fixture | Arm | Bytes median [min,max] | Events median [min,max] |
| --- | --- | --- | --- |
| sparse32 | C | 63232 [63144,63288] | 79 [79,79] |
| sparse32 | P | 63256 [63208,63288] | 79 [79,79] |
| sparse32 | R | 64320 [64216,64360] | 79 [79,79] |
| dense32 | C | 179240 [179144,179320] | 85 [85,85] |
| dense32 | P | 179240 [178984,179320] | 85 [85,85] |
| dense32 | R | 180296 [180136,180376] | 85 [85,85] |
| sparse96 | C | 134672 [134664,134696] | 81 [81,81] |
| sparse96 | P | 134664 [134664,134712] | 81 [81,81] |
| sparse96 | R | 137728 [137728,137824] | 82 [82,82] |
| dense96 | C | 1.06953e+06 [1.06951e+06,1.06961e+06] | 84 [84,84] |
| dense96 | P | 1.06953e+06 [1.06951e+06,1.06966e+06] | 84 [84,84] |
| dense96 | R | 1.07259e+06 [1.07258e+06,1.07259e+06] | 85 [85,85] |

The dense32 C solve timing has an observed upper sample that produces P/C minimum0.24775 and R/C minimum1.16055; it remains included, with compile/recompile/GC zero. Its cause is unknown. No second measurement is authorized by this outlier.

## Bounded decision (Task 3)

Both alternatives qualify only as remedies for this fixed component experiment. P is the better next design candidate: it directly removes the observed sparse96 factor growth with small fill/native-size increases and near-reference timings. R also restores accuracy but its solve windows cost about1.39×,4.64×,2.27×,6.98× C across sparse32,dense32,sparse96,dense96 and retain extra scratch. This does not justify changing the production default now.

For P versus R, the paired denominator (R solve time−P solve time)/16 is positive in all eight rounds for every fixture. The following empirical break-even triplet counts use max(0,(P constructor−R constructor)/denominator). Fractional triplets express a timing model, not extra executed calls. Constructor differences change sign and are noisy; these ranges and the max-numerator/min-denominator spread bounds are descriptive, not confidence bounds or a real simplex workload forecast.

| Fixture | Paired break-even median [min,max] | Observed-spread upper bound |
| --- | --- | --- |
| sparse32 | 0.0000 [0.0000,1.7204] | 1.7204 |
| dense32 | 0.1496 [0.0000,0.2183] | 0.2332 |
| sparse96 | 0.0000 [0.0000,1.7275] | 1.7275 |
| dense96 | 0.0000 [0.0000,0.1267] | 0.1273 |

The next concrete step is a separate SOURCE/DESIGN plan for an immutable optional Float64 native-backend pivot policy, initially considering P with IRSTEP0. It must preserve current defaults and specify propagation through fresh construction, independent candidate, spare reuse, copy/shared active factors, empty transitions, failed refactor and recovery; never mutate shared active controls. It must account for all supported precisions and source-level hot-path work. No production type/option, implementation or manager qualification is introduced here. A later independently accepted integration design is required before changing the three-prototype/Markowitz comparison. Originalcost1 remains FAILED/CONSUMED and cost2BLOCKED.

## Scope and review

The fixed output retention is405504Float64 elements (3244032payload bytes),25344Info elements (202752bytes), plus lifecycle vectors and12snapshots. Ownership scans, token serialization, four scalar stores per solve, counters and dimension/alias checks are diagnostic overhead and not neutral. Constructor timing includes private controls, CSC copies and scratch. Numerical safeguards, original128*n*eps residual bound, inputs and caller owners were unchanged. All514baseline production/test/environment hashes remain unchanged. No unnecessary NEW production work or memory is introduced; prospective policy integration must still be reviewed separately.

Exact-stage admission had50checks/1189sealed files/1190review bindings; launched manifest adds seal/admission and is verified by the guard and supplemental postcheck. Fresh independent result review, final continuation mappings and exact publication closure are separate records. No old driver/auditor was rerun, no new LP/full solver/precision change, no production/src/test/env/CI/master modification. Master6f68e24, CIoff, HHreuse disabled and automation paused remain. Broader plan remains open.
