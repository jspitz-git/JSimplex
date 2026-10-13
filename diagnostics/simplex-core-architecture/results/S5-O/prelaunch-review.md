# S5-O independent prelaunch numerical, work and admission review

Verdict: NOT ACCEPTED in this revision. Critical: none. Important: one
(review/manifest binding gate below). Minor: none. Do not edit the actual test or
launch Julia on this admission. Preserve the original artifacts and 813-entry
manifest; a separate offline correction and independently accepted final admission
are required. This review is not numerical qualification or publication approval.

## Important: acceptance does not require the identities it claims to bind

`results/S5-O/common.py:26-29` accepts any record with `accepted=true`,
`unresolved_findings=[]`, and a `reviewed_sha256` map whose supplied entries match.
It does not require any entries. The empty map satisfies `all(...)`. A nonempty
map containing only an unrelated unchanged file also satisfies this function.
`launcher.py:38-40` calls that function for the prelaunch acceptance, GREEN
acceptance when applicable, and per-run launch binding, without imposing their
required path membership. In particular the per-run binding need not include
`B/(label+'-pins.json')` at all. The review file, reviewed admission manifest and
GREEN review/acceptance identities likewise need not be present.

Consequently an incomplete author-written acceptance can pass the concrete launch
gates although it does not bind the actual manifest or independent review. The
guard still verifies the manifest it receives; that proves manifest consistency,
but does not supply the missing link to the accepted review. This conflicts with
the explicit S5-O admission contract and is significant before a nonrepeatable
numerical attempt. The finding follows directly from these branches; I did not
execute either launcher or manufacture an acceptance record.

Require the applicable exact review, admission-manifest, actual-run-manifest and
prior acceptance paths in each acceptance category, validate their digest values,
and retain the existing fresh-hash checks. Verify rejection of empty and partially
bound maps with bounded offline cases. Preserve original common.py, launcher.py,
this rejected review and admission-pins.json; use separate corrected artifacts and
a new manifest. No candidate, fixture, numerical option or assertion change is
needed. No other unresolved numerical or admission finding was identified.

## Independent identity and provenance evidence

I streamed all 813 admission inventory files in 1 MiB chunks, reading
3,578,619,270 bytes. Every SHA-256 and resolved path matched. Both complete source
and test tree memberships matched: 70 source files and 441 test files. The entire
N789 and M756 inventories are included with the same recorded digests. This is an
independent read-time verification, not reliance on preparation booleans.

| Reviewed artifact | SHA-256 |
| --- | --- |
| .superpowers/simplex-core-architecture/S5-O/admission-pins.json | 62734c4bbda7f19cf1e68b73d4c443bd038a259617fcb063ca17ae1f447ceab7 |
| results/S5-O/driver.jl | 948127a3225dc6a5d1f9ef385452729015d25f239a4ca2b698012563d65f977e |
| results/S5-O/common.py | be29b99d167945cd3d13b14ddba3c2abb6266562e3e59dc849bba53e2cd4d89c |
| results/S5-O/launcher.py | 7ab76a450acfd3acfa16041f4799e08c63a0c3ce722fc1721fb0d547e33a9de6 |
| results/S5-O/audit.py | 9afb2ee34d3d89255d0f46e3dbf3736a5e1a9f2742fc0bbde8b4a9b86ad906d3 |
| results/S5-O/schema.json | f046ed630f573c9a5ab8de0861bfba65461847b8764d2c840f2ac411e6415249 |

The later supplemental `offline-independent.json` has SHA-256
`cb687aa6015d0fb9df0aecb05638391884296da0d9f5f3a3e9329e9e0681a131`;
all 13 artifact bindings match. It records three new missing/malformed-input
failures, each `all_passed=false`; these are author offline evidence, not numerical
observations. The later success-only `postcheck.py` has SHA-256
`e8e84eaa04043a45e7f057f1d9910223091117b2ea51a9cc449ef022111df22c`.
I read it as text. Both are supplements added after the original admission freeze,
not retrospective members of its 813 inventory; a later accepted manifest must
bind the applicable supplements.

All six protected user-file hashes match. The actual adaptive-pricing test equals
the original 19,080-byte prefix, SHA-256
`1680b0f132c87c5b24422da56f3b848b22dc2b3547c3985b80fd2d0312c8989f`.
The diff against master for src/test/.github is empty. HEAD is
`476f28baebfffdb22c165501b7a28025736ffded`; master is
`513c05388a82531e4d8fbcfb383e8897fad14ba2`. Fresh host inspection found no Julia
or member of groups 23249/23257/49081/49084/52772/52774/53479/53481/60706/60708,
under boot `dade7243-9103-4398-bb45-fa28fbc0be72`. These are review-time facts,
not substitutes for launch-time absence checks.

I read STATUS, the O plan and all requested concrete O artifacts, N source inverse,
candidate/append/independent/closure, and M raw/audit/postcheck/closure plus its
rejected review, two fixes and final acceptance review. N independent seven and
closure eighteen bindings match. M raw six and postcheck six match; both fix maps
match. Forty-two of M closure's 44 bindings match their original current paths;
the two subsequently updated continuation documents match exactly their preserved
N `STATUS.md.before-N` and roadmap `before-N` copies. This preserves historical
closure rather than treating current continuation text as unchanged M evidence.

## Numerical source, driver and scope

Independent byte reconstruction confirms N's kept L core hash and exact recorded
inverse, original prefix plus append equals candidate, all 40 explicit named
assertions occur in the recorded order, and the three exact helpers each occur
once in the original prefix with matching hashes. Candidate SHA-256 remains
`10e77c9bc35956c8078f38df1be42511eea76642753a1a98ef2ed225c19783aa`.
Applying only the three recorded driver insertions reproduces expected-executed.jl
exactly, SHA-256 `99373e8cb4186ae6c71092834b0f05518f3b76121ab37cc2c5ada70306820a71`.
The insertions add PRE setup/handoff counters and one post-unwind record; their
inverse leaves the permanent suffix byte-exact. No Julia parser was used.

The driver reads the actual candidate, checks whole/prefix/suffix hashes and module
source root, extracts only the three helpers, instruments the actual suffix, and
executes only its one new testset. It does not include the old test file. There is
one initialization and one public make_dual_feasible! call, with the original
Float64 fixture/options/policy. Two driver-only assertions establish [1,1,1]
entries/completion and the exact ordered forty-key record, giving 42 expected
passes. Installed Test source confirms nested results contribute through cumulative
counts. A failed outer testset can prevent report.toml creation; that is failed
qualification, not missing evidence from which success can be inferred.

The root `_StageObserver.live === LIVE` latch excludes nested candidate roots.
The throw additionally requires LIVE identity and the adopted trial factor,
different from the entry factor. Current simplex_pivot staging buffers phase reset
but forwards refactor_other; dual_simplex.jl publishes checkpoint invalidation,
state, cleared history and factor before pending replay. Diagnostics record the
event before wrapping the sentinel, and public handoff rethrows the nonnumerical
wrapper. Actual `isa` and `cause === sentinel` checks are preserved; raw type
strings supplement, rather than replace, identity checks.

The selected array owners/value comparisons, private/adopted factor and refactor
policy, pricing owner and nineteen fields, history/checkpoint/phase, monotone work
and exact throw-time work/event prefix remain consistent with current source.
Trial is mutable until unwind; compared bounds are LIVE postrestoration bounds.
Entry cost equality passed M once and remains prospective in O because auxiliary
repair may change costs. Any mismatch must stop without tuning/retry or inference
of a solver defect. This establishes neither rollback nor full-state preservation,
certificate transfer, observer neutrality or historical CI cause.

## Guard, runtime and failure handling

Both wrapper layers are pinned. The outer wrapper reads the nested depot assignment
with sed as data, sets the combined depot list and VM limit, and execs the installed
Julia 1.13.0 aarch64 binary. I read installed CLI documentation and loading.jl:
existing compiled modules allow existing cache use while excluding the ordinary
loader's automatic compilecache branch; disabled Pkg auto-precompile is additional.
No runtime query or import probe was used. Complete import work, cache selection,
cache validity and cache confinement remain unproved.

The unchanged guard provides exclusive lock/output, no competing Julia, single
Julia/BLAS/OMP/MKL threads, heap hint 2G, VM 8GiB, sampled RAM >=6GiB/swap <=1GiB,
120s sampled wall budget including imports/compilation, recorded process identities
and owned-group cleanup. Guard resources are sampled observations, not a continuous
resource proof or benchmark. O permits one GREEN directory and one master directory;
master freeze requires complete source/test membership and byte identity with
GREEN, plus separate GREEN acceptance. The binding defect above must be fixed
before these mechanisms form an accepted launch contract.

The auditor requires 42/0/0/0 Test counts, forty literal true booleans, exact schema
and types, one latch/hit and case entries, actual root/test/helpers/insertion inverse,
command, current pins/tree membership/user hashes, resources and complete known
process groups. Read/parse/type/shape failures are caught and produce an exclusive
failed audit with the original error representation; missing raw cannot pass.
The generic failure record does not establish group absence or other unavailable
gates. Original guarded logs/process/resources remain authoritative evidence, and
separate fresh absence checks are still required after failures. The supplemental
postcheck is a success-only operation: it asserts complete accepted evidence before
portable copying; it is not an alternate early-failure auditor. Its N789 mapping
uses only the byte-identical preserved original test for the deliberate test edit.

## Computational work and memory

No unnecessary NEW production computation, allocation or retained memory was found:
production is unchanged. No hot-path change justifies a before/after benchmark.
The permanent test adds cold fixture/setup work once per case: three copies of
3(m+n) scalar entries, six here; post-unwind comparisons inspect m+8(m+n)
publication pairs, seventeen here, plus six entry pairs and nineteen pricing fields.
Owner checks can construct up to eighteen small nine-reference temporary tuples;
these are source work counts, not measured allocations. Callbacks perform fixed
scalar/identity work per notification with no vector copy/scan, extra solve or
growing observation ledger.

Driver additions are cold: three integer counters, one fixed reference, bounded
forty-check/fifteen-observation records and serialization, two Test assertions,
source-string extraction/hash/inverse work linear in source text size, and Test
result bookkeeping. Fixed reference-role counts do not cap retained object graphs:
live/trial/factor/history aliases can retain scratch, sparse metadata and update
chains. Runtime scalar widths, dimensions/nonzeros and update-chain memory remain
unmeasured outside this tiny Float64 case. Offline/guard pin hashing streams roughly
3.58GB per full pass with bounded buffers and is not solver work. No speedup,
complete PREforward/backend/import-work, GC/native-free, full-suite or x64 claim is
supported. Numerical safeguards, tolerances, coefficients and precision are intact.

I wrote only this new review file. I executed no saved preparation, launcher,
auditor, correction or closure script, no Julia/parser/import/compile/numerical
probe, and no test edit, package operation, commit or push. All prior failed reviews,
raw evidence, rejections, CI-off/HH-disabled and broader validation gates remain.
