# Incomplete runtime dual solve on a second computer

Recorded on 2026-09-26 from a user-supplied excerpt. The user reports that the
reduced model failed numerically after approximately two hours and that the
subsequent full-model solve was still running. The excerpt contains neither the
failure message nor a final status; completion is not required to retain this
evidence.

Settings match the reported primal reproduction except for `algorithm=:dual`:
steepest-edge pricing, Bartels–Golub updates, native refactorization, interval 80,
legacy strategy, iteration limit 1,000,000, unlimited time, and relaxed
integrality. The second computer's code revision, Julia version, hardware, and
input hash were not supplied. Do not attribute this run to the current branch.

The original 7,076-byte excerpt is preserved byte-for-byte in
[`runtime-dual-partial.log`](runtime-dual-partial.log), with SHA-256
`c763acf63b4e307fb1f416aa0d6b0644078b6114dd48313efd90a51735d98aa0`.
[`runtime-dual-partial.json`](runtime-dual-partial.json) contains all 66 parsed
samples, settings, provenance, and summary values.

| Logged quantity | First sample | Last sample |
| --- | ---: | ---: |
| Iteration | 277,075 | 277,207 |
| Elapsed seconds | 21,085.8364252 | 21,105.681196 |
| Objective | 46,603,221.20803811 | 46,654,995.88246473 |
| Primal infeasibility | 5,677.826808136842 | 6,525.206205426235 |
| Primal infeasibility count | 4,866 | 4,869 |
| Dual infeasibility / count | 0 / 0 | 0 / 0 |

The final logged elapsed time is approximately 5 hours 51 minutes 46 seconds.
The excerpt spans only 19.845 seconds and an iteration-counter increase of 132;
it is not the complete run history. Logged primal infeasibility reaches
393,944.07665166474 at iteration 277,152 (count 5,305). Every logged dual
infeasibility is zero. These values document slow progress with large changes
in primal infeasibility; they do not independently identify the cause, establish
cycling, or certify an original-model solution. Refactorization counts and
reasons are absent.

The user subsequently reported a severalfold increase in compilation time on
the same second computer. No compiler profile or measured compilation duration
was supplied. This corroborates the symptom observed locally, but does not yet
identify its cause. A separate compilation investigation is scheduled after the
current stability verification.
