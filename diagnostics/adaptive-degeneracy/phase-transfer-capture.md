# Actual runtime Phase-I transfer replay

This follows [the longer runtime continuation](structural-runtime-continuation.md).
The proposed experiment captures the actual auxiliary endpoint, then tests
mapped-point completion through the existing export checks. No production code,
pricing policy, tolerance or solve precision is changed in this step.

## Capture and trajectory control

The baseline is `643c91b`, with complete production source digest
`d338c92dd9e92c5064c4621291796bf3808341aa7d56668ff931d34452dcc6d4`.
The input remains `/home/jspitz/mps/runtime.mps`, SHA-256
`d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68`.
Float64, primal steepest-edge, PFI/native/80, one million iterations and the
isolated adaptive policy are unchanged: stagnation monitoring, pricing and
perturbations enabled; other adaptive interventions, independent weak-pivot
preference and original-input retry disabled. The internal Phase-I construction
remains enabled. See the captured policy and diagnostic method hashes in the
text result for the exact configuration.

The solver limit is 1,800 seconds, with a 2,040-second outer guard. Julia 1.13.0
on aarch64 uses one Julia thread and one BLAS thread. The existing wrapper limits
virtual memory to 8 GiB, available RAM to at least 6 GiB and swap use to at most
1 GiB; it can terminate only its owned process group. Only one numerical Julia
process runs at a time. Local precompilation remains disabled.

Two process-local observation hooks serialize the auxiliary/original workspaces
immediately before export, and the fresh original-dimension workspace after
refactorization but before acceptance. Observer closures are removed from saved
progress contexts. The snapshots support local numerical boundary replay, not
an exact restart of the outer driver or its timer. The hook body is hashed.

The capture ends with **NUMERICAL_ERROR at iteration 102,446**, after
**1,310.131505956 seconds**, with **25,475 refactorizations** and **60,103 rejected
candidates**. All **137 recorded events**, including the terminal reconstruction,
match the previous run in every field except seconds and process-local workspace
and monitor identities. The status, work counts, intervention counts, source,
input and pre-existing diagnostic method hashes also match. Peak process RSS is
2,218,999,808 bytes; no guard or time-limit termination occurs.

At the captured boundary there are no basic artificials. Sixteen nonbasic
artificials are nonzero within tolerance: the maximum magnitude is
2.9103830456733704e-11 and their signed sum is -3.1616536180009494e-11.
The auxiliary full-point and optimality certificates pass. These are certificates
for the auxiliary model, not optimality of the original input.

## What the actual replay establishes

The unmodified export rejects the snapshot and leaves the original primal
vector and basis unchanged. The manual baseline reconstruction matches the
captured fresh primal vector bitwise, with identical basis indices and states.
Consumed work counters are retained by the normal export path.

The fresh initialization changes **1,678 nonbasic values**, including **448
structural variables** and 1,230 row activities, to their selected bounds. The
largest change is 9.982596842974829e-8. The two alternatives differ only in whether
the mapped nonbasic values are supplied before refactorization. Both pass the
same mapped basic candidate to `_finish_legacy_primal_point!` afterward.

| Local variant | Basic bound violations | Full point certificate | Reduced original-model primal certificate | Point completion | Complete export |
| --- | ---: | --- | --- | --- | --- |
| Baseline nonbasic values | 10; sum 1.981218994982207e-5 | fails | fails | rejects | rejects |
| Mapped nonbasic values | 0 | passes | passes | returns success | rejects |

For the mapped variant, the reconstructed point already passes the certificates
**before** point completion. The completion routine therefore takes its existing
fast path; its successful return is not evidence that candidate restoration or
native correction ran. The result is not bitwise equal to the mapped auxiliary
point: the maximum coordinate difference is 1.8533319234848022e-7. Dropping the
small nonzero artificials does not prevent this reconstructed point from passing
the reduced original-model primal certificate.

Thus the loss of maintained nonbasic values is a demonstrated cause of the
bound infeasibility at this endpoint. Preserving them removes that obstacle,
but it is insufficient to make the complete export pass.

## Remaining numerical acceptance failure

The complete diagnostic export variant copies the mapped point before
refactorization and invokes the existing native point-completion routine. It
retains **all existing export checks**, pricing inheritance, adoption and reset
operations. It still returns false at `_recomputed_basis_reliable`.

| Reconstruction | Primal absolute residual | Primal componentwise relative residual | Dual absolute residual | Dual componentwise relative residual |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 1.3715973603750895e-9 | 1.0 | 6.136599495221162e-8 | 1.6185177693375135e-12 |
| Mapped nonbasic values | 1.1214388970031154e-9 | 1.0000000000000002 | 6.136599495221162e-8 | 1.6185177693375135e-12 |

Both primal and dual solve-quality checks reject. Their componentwise relative
criterion uses `solve_tolerance = 256*eps(Float64)` (5.684341886080802e-14), whereas
point feasibility uses the absolute primal tolerance of 1e-7. These checks answer
different questions. A componentwise relative residual near one is not a
measurement of relative solution error and does not establish bad conditioning
of the basis. The source comments require the dual-price scratch buffer from
recomputation; the diagnostic point checks and completion leave it intact.

The feasible reduced-model point has cost dot product 61,547,897.970084. It is
neither an optimality certificate nor a returned, postsolved original-input
solution. No Phase-II continuation, original-input feasibility check or complete
runtime solve is claimed. The previous dual optimum is consequently not used as
an acceptance condition for this boundary experiment.

The next investigation should localize the rows responsible for the primal and
dual residual rejection, check a bounded correction in the problem's precision,
and establish how to certify a feasible transferred point together with usable
dual prices. Loosening or bypassing the current check merely because the point
is feasible is not justified by these results.

## Reproduction and verification

Run the Julia commands sequentially through the same guard and one-thread
wrapper, with outer limits of 2,040 and 360 seconds respectively. The replay
resets observation timers and journal ownership for deserialized workspaces.

```sh
julia --project=. diagnostics/adaptive-degeneracy/reproduce/capture_phase_transfer.jl runtime primal both 1800 /tmp/runtime-transfer-capture
julia --project=. diagnostics/adaptive-degeneracy/reproduce/replay_phase_transfer.jl /tmp/runtime-transfer-capture /tmp/runtime-transfer-replay
python3 diagnostics/adaptive-degeneracy/reproduce/analyze_phase_transfer.py /tmp/runtime-transfer-capture.toml diagnostics/adaptive-degeneracy/results/structural-continuation/runtime-structural-1800.toml /tmp/runtime-transfer-replay.toml /tmp/runtime-transfer-summary.json
python3 diagnostics/adaptive-degeneracy/reproduce/validate_phase_transfer.py
```

All **8 replay assertions** pass with normal compilation. They verify auxiliary
certification, baseline rejection and state preservation, exact reconstruction
replay, and unchanged nonbasic values during completion. Counterfactual acceptance
is recorded as an outcome, not assumed by the test. The retained report validator
also checks the observed certificate and residual outcomes. The prior structural
retention and continuation validators pass against unchanged production sources.
No new whole-project or external-matrix regression result is claimed.

Committed text evidence is in [results/phase-transfer](results/phase-transfer/).
Binary snapshots, complete capture log, injected method bodies and as-run scripts
remain under `.superpowers/adaptive-degeneracy/phase-transfer/`, with SHA-256
hashes in the committed artifact manifest. They allow further local diagnostics
without repeating the 102,446-iteration prefix.
