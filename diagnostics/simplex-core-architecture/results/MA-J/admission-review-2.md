# MA-J repaired-record admission — accepted

Accepted for one separately authorized short attempt using driver-2.jl and launcher-2.py. The first attempt remains FAILED. No Julia was executed by this review, and no old driver/launcher/auditor was run or imported.

## Failure and preservation evidence

First process.json records exit1 after9.237906965994625s with unchanged pins. Raw data contains280 passing Float64 correctness records and zero complete cost records. Its stack trace shows setindex!(::Dict{String,Real}, ::String, ::String) failing at driver.jl:168. Numeric-only inference in timing() created the incompatible dictionary; this is instrumentation failure, not a candidate arithmetic failure. The original postcheck correctly rejects incomplete results and exit1. No performance conclusion is available from this failed attempt.

All217 new pins match actual SHA-256 and resolved paths. All197 original accepted-review bindings remain unchanged. All6 run-1 file hashes recorded by the first postcheck remain unchanged. The new inventory includes every run-1 file and its driver, launcher, manifest, admission, audit, log, reservation and invocation. No first-attempt evidence was rewritten. The five supplemental repair checks are bound as offline evidence, not numerical results.

## Exact repair and computational scope

Independent inverse check proves driver-2.jl differs from driver.jl at exactly one constructor: the timing record becomes Dict{String,Any}. Replacing that constructor with Dict reproduces the first driver byte-for-byte. This permits numeric values and String metadata without changing any arithmetic, fixtures, or schedule. Record construction occurs after the @timed batch, so this repair does not enter measured function windows. It may change unmeasured instrumentation boxing/storage overhead slightly; it does not add candidate work or retained production memory. No unnecessary computational or memory cost was identified in this repair.

Candidate, reference, exact conversion helper,1126 correctness cases,48 cost cases, warm/measured pairs, precision, tolerances, scratch creation, input preservation and compile-free checks remain unchanged. There is no benchmark tuning or outlier selection. First timed batches are after the relevant correctness qualification, not cold measurements. Prior candidate work/memory review continues to apply: nine lazy BigInt scratch objects, at most four identity checks per changed addition, exact normalization, no new scans/solves/input copies or retained scratch. Tiny synthetic component measurements cannot establish full presolver/solver or representative large sparse/dense performance.

## Separate admission controls

Launcher-2 and postcheck-2 differ from their frozen originals only in the new attempt paths. Their Python ASTs parse. Guard is unchanged. host-2 lists exactly the original134 group/session IDs plus223350 and223351 from the first runner/child, for136 total; recorded matches are empty and the launcher rechecks them freshly. New pins, review, reservation, invocation, log, output directory and postcheck filenames isolate the second attempt. Exclusive creation and absence checks prevent automatic retry. The launcher uses174s plus the existing six-second shutdown reserve; postcheck requires successful exit, elapsed<=180, unchanged pins/protected files, resource bounds and process/session closure. Use pinned /usr/bin/python3.

The user's standing authorization, as supplied in the review request, covers this separate repair attempt. The original single-attempt allowance is consumed; its artifacts are not reopened. Any failure of the repaired attempt remains evidence and requires assessment rather than an automatic loop. Admission does not assert numerical success or authorize production integration.
