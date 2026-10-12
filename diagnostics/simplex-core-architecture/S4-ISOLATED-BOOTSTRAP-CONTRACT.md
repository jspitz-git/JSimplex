# S4-U: existing-cache bootstrap boundary

SOURCE/EVIDENCE ONLY at diagnosticc6702f2 / master0eb75c3. No Julia, module load,
compilation, native call, hook, solver/factor/workspace or cache creation occurred.
The CLI-only proposal on the current writable depot is NOT qualified for the required
no-cache-mutation bootstrap. bootstrap_qualified=false is preserved. This is not a proof
that a separately confined bootstrap is impossible. No numerical plan is created.

## Installed loading policy, not an exploratory import

The pinned installed Julia1.13.0 aarch64 distribution provides loading.jl, client.jl,
options.jl and command-line documentation. Installed documentation enumerates the modes;
loading.jl supplies their control-flow distinction. No Julia --help/version query or
C option-parser execution was used. No upstream build-equivalence claim is needed.

| Mode | Missing/unusable cache | New compilecache path | S4-U disposition |
|---|---|---|---|
| compiled-modules=yes | May attempt precompilation, then source fallback | enabled | Not eligible |
| compiled-modules=existing | May reach ordinary source include | skipped | Does not fail closed against source work |
| compiled-modules=strict | Errors after failed cache search, before source include | skipped | Necessary candidate policy, insufficient alone |
| pkgimages=existing | Existing native images may be used; creation disabled | separate native-image policy | Not a package-source fallback or filesystem write barrier |

loading.jl2727 first searches caches. Mode3 errors at2735 before mode1's compilecache
branch2752; ordinary source include remains below2828 for other paths. A strict import
failure is not whole-process rollback: cache search can already restore dependencies,
run their initializers or callbacks, and retain state before a later failure. Startup
scripts and custom sysimages/driver imports would require their own explicit confinement;
--startup-file=no is a prospective requirement, not a flag exercised in this task.

A successfully restored cache does not re-evaluate the original package's source-level
precompile workload merely because that source has an include. But this does not remove
runtime __init__, extension/package callbacks, native library initialization, JIT or
metadata work. Existing-mode source fallback would again expose T's conditional workload.
The exact installed PrecompileTools guard remains
`(generating_output && workload_enabled(module)) || verbose[]`, including enabled and
module preferences; none of those values was mutated or read from a live Julia process.
T's82 public/4factor/4refactor/16backend entries remain conditional source counts only.

## A concrete prohibited write remains on the cache route

loading.jl2160–2166 attempts `touch(path_to_try)` during stalechecked cache loading.
__require_prelocked invokes this search with stalecheck=true. Strict mode does not bypass
that touch. If the file is writable, mtime changes even though its content/hash does not.
The installed code catches touch failure and explicitly tolerates a read-only file.
Therefore content SHA stability alone would not establish no cache mutation.

cache-metadata.json is a67-entry lstat/name snapshot of the JSimplex cache directory,
including .ji/.so, temporary and pidfile names. It is NOT a selected cache graph or a
validity assertion. Cache contents were not read, hashed, parsed or deserialized. The
snapshot records uid/gid/mode/inode/size/mtime; names or pidfile presence do not prove a
live process, a usable cache, or a reason to delete anything. No cache file was removed,
chmodded, touched by an import, or otherwise deliberately changed. Reading ordinary
source/hash inputs is separate from executing the loader's explicit cache touch.

The precise filesystem gap is lack of an established read-only execution view of every
reachable cache/depot path. Changing cache permissions or replacing loader methods is
not proposed. The source's caught failure suggests a possible read-only confinement,
but no mount/namespace/permission experiment or exception-based bypass was performed.
Even perfect write confinement alone would not establish cache validity or zero init work.

## Validity and initialization are separate gates

stale_cachefile4176+ checks header/build identity, cache flags, CPU clone targets, native
image availability, dependency module/build IDs, content checksums and preferences. The
future process's sysimage, already loaded modules, project/depot/load paths, environment
and flags contribute to selection. A .ji/.so pair's existence or recent timestamp does
not satisfy those checks. The67 files were not promoted into a prospective load manifest.
No source parser pretends to decide all runtime cache validity; no cache was selected.

_include_from_serialized and dependency restoration run module initializers; package
callbacks include extension callbacks. loading.jl2168 even notes that dependency __init__
can run before the module graph is fully restored. The complete transitive initialization
closure of production JSimplex (including MOI dependencies) is NOT qualified here. S's
exclusion of MOI/precompile from the isolated cores does not exclude them from a preceding
production `using JSimplex` bootstrap.

Necessary inspected installed-source boundaries are:

- LinearAlgebra.__init__ registers its OpenBLAS callback. The installed
  libblastrampoline_jll compatibility shim calls it directly. It forwards BLAS symbols,
  invokes BLAS.check, installs a threading hook and may choose thread count from the
  environment. BLAS.check here validates LBT interface configuration; it is not a matrix
  multiply, LP solve or factorization test. This code still makes native configuration
  calls and allocations. Whether it ran in any historical process is not established.
- OpenBLAS_jll and SuiteSparse_jll initializers contain dlopen/dlpath/native-handle setup.
  Those are real native loader activity, not counted as HH factorization attempts and
  not safely described as zero work. No native initialization was executed by S4-U.
- SparseArrays LibSuiteSparse declares a OncePerProcess initializer with version checks
  and allocation callback configuration. Its declaration alone does not prove execution
  during package import: work can be deferred to first SuiteSparse access. This deferred
  cost belongs explicitly in a future whole-process/first-factor budget. N/O evidence is
  reused read-only; no allocator hook or actual callback-pointer capture was introduced.

These are selected necessary boundaries, not an exhaustive dependency inventory. Installed
source bytes plus runtime binary hashes do not prove which cached body a future process
will execute. No absence of numerical work is inferred for the unexamined transitive
initializer/extension/native-loader closure.

## Work, ownership and disposition

20 source/provenance checks and627 read-time hashes pass; T's604 original inventory is
reconciled603 current plus its preserved pre-review report, and T's corrected report hash
is independently matched. The six user files are unchanged. Existing whole process groups
23249/23257 and old leaders23256/23257 are absent on the recorded boot; no Julia process
was found. No old accepted script, cost run or LP calculation was repeated.

No production computational work, allocation or retention was added. This source-only
artifact performs finite file reads/hashes and67 metadata stats. A future bootstrap can
allocate/retain loaded module graphs, native handles and JIT/code metadata, traverse cache
files/dependencies, and execute initializers before either reference or candidate begins.
Those costs are setup, separate from the same-pattern guard and LP work. Two isolated
cores still retain their own64-file types/methods/Core.kwcall/metadata and local inputs.
Nothing here establishes neutral overhead, native frees, speedup or complete work caps.

CLI-only `existing` is rejected as fail-closed source isolation; CLI-only `strict` on an
ordinary writable depot does not meet no-cache-mutation. Overall bootstrap remains OPEN
because filesystem confinement, actual cache selection and complete initializer work are
not qualified. This finding is sufficient to withhold a numerical plan; it does not require
an exploratory import or repeating the S module inventory/T exact LP/Q timing.

ONE next bounded decision is S4-V source/host-read-only feasibility of an OS read-only
view for the strict-cache bootstrap. Determine whether available confinement can protect
all existing dependency/cache/native paths without permission changes, copies or hidden
writable fallbacks; enumerate the proposed launcher and failure behavior offline. Do not
implement a mount/namespace, run Julia, or claim the remaining initializer/validity gates
closed. If no supported confinement is available, record that decision and stop this
bootstrap route rather than trying imports. The future controller attempt ledger also
remains OPEN. S manifest and T LP stay frozen. Production/test/env/master/CI unchanged,
HH reuse disabled, native retention/broader S4/S6/fullsuite OPEN, all rejections and Q
GC-dominance/outlier evidence unchanged.
