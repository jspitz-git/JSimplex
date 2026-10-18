# R1 — additive transitive fixture binding

The initial independent review rejected the preparation because the canonical
fixtures.jl loaded by import-tests.jl was absent from the manifest. The original
1858-input manifest, required paths and rejected review are preserved byte-exactly
as *.before-R1. Their old canonical-path bindings resolve ONLY to those copies.
The initial author source26/synthetic123 remain unchanged; they did not establish
transitive fixture closure and cannot substitute for this correction.

The corrected preparation adds the actual fixture and checks its current SHA256
against accepted Task1 and Task2 reviews:835b6e4241705b4c7a6a2625c904999ffe30e90ec99c937d257cbe2a2c289517.
It contains no further includes. No fixture, candidate, test, driver, controls,
stage, source, environment, CI, STATUS or roadmap bytes change. The corrected
manifest also binds the preserved rejection, original manifests and new amendment
proof. It is still offline preparation, not a numerical seal or allowance.

The first independent checker used a wrong historical JSON field and stopped;
its source/error and separate v2 (83 PASS) are preserved. No old checker is rerun.
Only a fresh independent amendment review may accept the corrected manifest.
