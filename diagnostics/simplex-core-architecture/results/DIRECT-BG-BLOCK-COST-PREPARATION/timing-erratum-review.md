# Independent timing-count erratum

Accepted bounded textual correction, scope **block BG timing-count erratum**. The original review.md incorrectly says “fourteen time_ns reads per lifecycle.” Fourteen is the number of literal time_ns() call sites in cost.jl's lifecycle source, not their executed count.

A completed lifecycle executes **70 explicit time_ns() reads**:2 for construction +8iterations ×(2 entering FTRAN +2 distinct DSE FTRAN +2 update +2 BTRAN) +2 for refactor4 +2 for refactor8 =70. Equivalently,35 executed operation intervals each have a start and end clock read. The six clock buckets and one48-byte element-payload clock vector are unchanged. This count excludes any internal clock operations performed by Julia's @timed implementation.

Both reference and candidate execute this same70-read instrumentation schedule. This correction changes no source, fixture, policy, numerical behavior, memory formula, timing result or admission condition. No numerical run or new performance evidence was produced. The original reviewer-source-v1 check counted seven literal interval pairs correctly; its source-count evidence does not establish seven executed intervals.

The original review.md/review.json, all existing reviewer check sources/results/logs, and the already-passed initial closure are preserved byte-for-byte. timing-erratum-check.json records the new bounded source inspection and preservation checks. timing-erratum-acceptance.json binds the exact current cost.jl, original review.md, this erratum and the new check evidence without circular or self-hashes. No old checker, closure, Julia/query/parser/import/compiler, seal, launcher or auditor was executed. This remains OFFLINE preparation acceptance and grants no numerical execution permission.
