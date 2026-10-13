# Initial independent S4-Y review — REJECTED, preserved

Fresh gpt-6-astra/high, /root/s4y_retention_review, read-only. No Julia or
repository verifier/auditor execution; no files changed by reviewer.

Verdict: REJECT initial S4-Y preparation pending offline corrections.
This is unexecuted text/source review, not runtime or numerical acceptance.

P2: driver.jl:43–44 array isapprox uses default norm2; report:79–81 promises
componentwise/infinity acceptance. Preserve initial driver and implement explicit
componentwise comparison with the same 64*eps(Float64), without output tuning.
Installed LinearAlgebra/src/generic.jl:1995–2019 and714–718 confirm norm2.

P3: report:106–108 incorrectly says twenty helpers each allocate five vectors.
Actual ten retention_solves calls produce fifty explicit vector results, plus
library/internal work. Twenty counts backend solves and comparison predicates.
Author regrades this Important because the bounded work/memory ledger is part of
admission; correct it together with the oracle in the one offline fix pass.

Historical addition is appropriate: test/markowitz_tests.jl:181–187 already has
initial512 graph bounds; the September plan approves retained capacity. Scope
the new gap to sparse/dense shrink-history graph observations.

Other conclusions accepted: 2constructors2copies6refactors8captures20solves66keys;
382/22 stored tridiagonal entries, sparse route at128/8, dense pre-reset return;
active dimensions8/128; grow-only dictionary/maxima ownership; active/spare
workspace sharing and saved-copy isolation; failure does not roll back scratch.
An incomplete case is omitted after exception; future auditor must reject missing
raw/serialization failure/partial schema/wrong Boolean types. Graphs overlap and
saved factors stay live; no native/free/RSS/timing/optimization proof.
No unnecessary new production work, allocation or retention found: src/test/CI
unchanged. Bounded diagnostic graph walks and retained-length scans are relevant.
Next offline preparation does not authorize numerics or reopen stopped routes.

Independently verified all21 source hashes,11 entry source hashes,3 user hashes,
all6 G continuation mappings and both before copies against HEAD; exact HEAD/
master, empty index, only2 tracked continuation changes, no src/test/CI diff;
boot/full28groups ANDsessions absent/noJulia. Old audits/scripts not executed.

Bound hashes:
source.json b7bb220efc8994ec74487274afbec5f6caca5c717b7285897fe5a1a034e2c010
initial driver.jl 930525a3172ff6bc877b99c2e2be4790c77cd95abe8d8a611ae7d51a8e4c69b9
initial report d5382bb641902407400367fdcea9d0ea01ac858361fca20a217831053f75b2c8
initial next plan e172fee9a5bc747aa4098b09ad8e72581773af09c443049418c56662f18f10ac
installed LinearAlgebra generic.jl d0c72640bcddc1eca86f35dc7f35a79aa757a09c1d77e8f768c6ef0e38ae1b33
September plan e1df539fa045f0f22529ec8ef20125c068f16e33c94e9b13989dbdf03167c5c6
markowitz reuse report a66de5795205135f9d3038af8bbfeedac8af3604348e9db9f81043bbba85bf34
All other hashes exactly the21-entry source.json map above.
