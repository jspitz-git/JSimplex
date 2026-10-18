from pathlib import Path
import json,re
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');D=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-WORKSPACE-DRIVER-PREPARATION';O=D.parent/'DIRECT-BG-SPLIT-DRIVER-PREPARATION';C=R/'diagnostics/direct-bg-export-workspace/reproduce'
def new(n,s):
 with (D/n).open('x') as f:f.write(s)
new('author.py',Path(__file__).read_text())
counts=[42,6,35,56,108,53,303,6236,378,108,610]
names=[]
for n in ['workspace-tests.jl','import-tests.jl','lifecycle-tests.jl']:names+=re.findall(r'@testset "([^"]+)"', (C/n).read_text())
assert len(names)==11 and sum(counts)==7935
expected={'red':{'assertions':6,'groups':[['Missing BG export workspace contracts (six expected failures)',0,6,0,0]]},'green':{'assertions':7935,'groups':[[n,k,0,0,0] for n,k in zip(names,counts)]}}
new('expected-tests.json',json.dumps(expected,indent=2)+'\n')
t=''
for mode,x in expected.items():
 t+=f'[{mode}]\nassertions = {x["assertions"]}\n'
 for name,p,f,e,b in x['groups']:t+=f'[[{mode}.groups]]\nname = {json.dumps(name)}\npass = {p}\nfail = {f}\nerror = {e}\nbroken = {b}\n'
new('expected-tests.toml',t)
red='''# UNEXECUTED structural missing-contract RED; no factorization or solve.
function run_bg_export_red()
    @testset "Missing BG export workspace contracts (six expected failures)" begin
'''
for n in ['BGExportWorkspace','_bgx_scratch!','_bgx_scale_mode','_bgx_import_upper','BGExportFactor','_bgx_refactor_with!']:red+=f'        @test isdefined(JSimplex, :{n})\n'
new('red.jl',red+'    end\nend\n')
s=(O/'driver.jl').read_text().replace('split BG','BG export workspace').replace('run_split_bg_red','run_bg_export_red')
a=s.index('    include(joinpath(@__DIR__,"split-suite.jl"))');b=s.index('function exact_tree',a)
s=s[:a]+''.join('    include('+json.dumps(str(C/n))+')\n' for n in ['workspace-tests.jl','import-tests.jl','lifecycle-tests.jl'])+'end\n'+s[b:]
a=s.index('                println(stderr,"BEGIN split storage")');b=s.index('            end\n        end\n        raw["complete"]',a)
s=s[:a]+'''                println(stderr,"BEGIN workspace tests");flush(stderr)
                BGExportWorkspaceTests.run_workspace_tests()
                println(stderr,"BEGIN import tests");flush(stderr)
                BGExportImportTests.run_import_tests()
                println(stderr,"BEGIN lifecycle tests");flush(stderr)
                BGExportLifecycleTests.run_lifecycle_tests()
                println(stderr,"END all BG export workspace tests");flush(stderr)
'''+s[b:]
new('driver.jl',s)
# New helper copies may be amended before freezing; original evidence is untouched.
p=D/'control.py';s=p.read_text();a=s.index('def full_host(');b=s.index('def preparation():',a)
s=s[:a]+'''def full_host(extra=()):
 groups=sorted(set(rd(D/'host.json')['groups'])|set(extra));matches=[];unreadable=[];unreadable_identity=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   a=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip()
   argv0=(p/'cmdline').read_bytes().split(b'\\0',1)[0].decode(errors='replace');exe=''
   try:exe=str((p/'exe').resolve(strict=True))
   except PermissionError:unreadable.append(int(p.name))
   except FileNotFoundError:pass
   if int(a[2]) in groups or int(a[3]) in groups or any(Path(v).name.lower().startswith('julia') for v in (comm,argv0,exe)):
    matches.append(dict(guard.process_identity(int(p.name)),comm=comm,argv0=argv0,exe=exe))
  except (FileNotFoundError,ProcessLookupError):pass
  except PermissionError:unreadable_identity.append(int(p.name))
 return dict(time=time.time(),groups=groups,matches=matches,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),head=git('rev-parse','HEAD'),master=git('rev-parse','master'),unreadable_exe_pids=unreadable,unreadable_identity_pids=unreadable_identity,scope='All groups AND sessions/stat/comm/argv0/readable exe; inaccessible exe links remain an explicit visibility limit, not a universal executable-identity proof')
def host_safe(h):return h.get('matches')==[] and h.get('unreadable_identity_pids')==[]
'''+s[b:];p.write_text(s)
for n in ['seal.py','launch.py','audit.py']:
 p=D/n;s=p.read_text().replace("not h['matches']","host_safe(h)").replace("all(not h['matches'] for h in [pre,hs,post])","all(host_safe(h) for h in [pre,hs,post])");p.write_text(s)
s=(O/'offline-tests.py').read_text().replace('split BG','BG export workspace')
s=s.replace("from oracle import test_results,timeout_only","from oracle import test_results,timeout_only,warning_log")
s=s.replace("check(not (D/'runs').exists(),'no_seal_reservation_output_or_launch')",'''for token in ['WARNING: world age','Warning: a warning','world-age','world age']:
 check(warning_log(token),'warning_'+token)
check(not warning_log('normal output'),'ordinary_log')
check(c.host_safe(dict(matches=[],unreadable_identity_pids=[])),'readable_host')
check(not c.host_safe(dict(matches=[{}],unreadable_identity_pids=[])),'process_host_refusal')
check(not c.host_safe(dict(matches=[],unreadable_identity_pids=[1])),'identity_host_refusal')
# An exclusive reservation cannot be reused. Exercise only save on a temporary file.
with tempfile.TemporaryDirectory(prefix='bgx-reservation-') as td:
 p=Path(td)/'reservation.json';c.save(p,dict(one_attempt=True))
 try:c.save(p,dict(one_attempt=True))
 except FileExistsError:check(True,'exclusive_reservation_refuses_reuse')
 else:check(False,'exclusive_reservation_refuses_reuse')
check(not (D/'runs').exists(),'no_seal_reservation_output_or_launch')''')
new('offline-tests.py',s)
new('ASSERTION-INVENTORY.md','''# Prospective assertion inventory — no Julia execution

RED: six individual missing-symbol assertions in the original 75-file stage.
No factorization, basis construction, solve or candidate loading occurs in RED.
This demonstrates missing contracts, not numerical failure or performance.

GREEN calls the three frozen entry functions once, after all module includes at
file top level. Eleven exact leaf groups are bound in JSON and TOML. Expected
passing leaves: 42,6,35,56,108,53,303,6236,378,108,610 = **7935**.
These are prospective counts, not observed passes. Error/broken/unexpected nesting
or any group mismatch is rejected even when the total matches.

Independent source derivation:
- workspace: 5*5+(3*3+2)+6=42; reuse6; (3*3+2)+4*3+12=35.
- importer helper7; fused4*2*7=56; rejection6*(7+3)+4*(7+1)+2*8=108;
  validation17*3+2=53; fixtures14*18+6*6+6*2+3=303.
- paired_solutions15; aliases17; preserve_failure3.
- repeated:28*34+24*(8*23+2*18)+4=6236.
- failure:194+4*(M_native+M_markowitz)=378 with M_native25, M_markowitz21.
  n8 normalized importer20 requests, seen1; native orientation4, Markowitz0.
- copy:2*(8+2*15+1+15)=108.
- dimension:4*(6*17+49)+P+2=610 with P4 dense64 retained branches.

General count is7747+4*(M_native+M_markowitz)+P. Actual native orientation acceptance,
request reachability and dense64 retention are runtime premises. They MUST NOT be
retuned after output. Exact per-group counts reject differing reachability; actual
GREEN failure remains failure even if arithmetic outputs otherwise match. Warm
native64 and Markowitz witnesses additionally assert real owner reuse directly.
The recorder counts Test result leaves (including evaluated macro branches), not
lexical @test sites. All accepted candidate/test bytes remain unchanged.
''')
new('ADMISSION.md','''# Task3 RED/GREEN preparation — OFFLINE ONLY

No Julia query, parser, import, compile, native call, numerical run, phase seal,
reservation or output is authorized or created by this preparation. Task1/Task2
remain frozen. This package is not a numerical admission. Cost measurement needs
its own later driver/admission after accepted correctness results.

## Phase and entry contracts

red300 uses the original exact75-file stage; green300 uses79 files: original75,
four mapped candidate implementation files, and only four appended root includes.
Original root inverse is byte exact. Test modules are loaded from pinned canonical
absolute paths, preserving their relative fixture include. All includes occur
before main is defined/invoked. No eval/invokelatest/global overwrite. Reject every
warning including world-age from both Julia and launcher logs. Runtime pathof for
JSimplex and five dependencies must match pinned paths. --compiled-modules=existing,
precompile verbose false, Pkg auto-precompile0 and existing exact wrapper chain;
no cache-confinement or complete import-work claim.

RED expected exit1, precisely six failures/one group, no errors/broken. GREEN exit0,
precisely7935 passing leaves/eleven groups. Raw TOML is saved in finally before the
aggregate check when main is entered; early load/compile errors may have only logs
and fail closed. JSON/TOML inventories and independent derivation are pinned.

## Future launch sequence (not executed here)

A new explicit human request selects one phase. First freshly verify refs, full
historical groups AND sessions, boot/start ticks/command, comm/argv0 and readable
exe links, all source/runtime/stage/candidate/test hashes, exact environment and
resource thresholds. Inaccessible exe links are disclosed; unreadable stat/comm/
argv0 identities fail closed. This proves absence of recognizable Julia processes
within that visibility, not arbitrary disguised executable identity. Independent
exact-stage admission must explicitly accept these host facts; no old host record
or review substitutes for it.

Call seal.py for that phase only after preparation review passes. It snapshots
exact current head/master/boot/files/config with no numerical process. A fresh
independent reviewer writes runs/<phase>/admission.json with accepted true,
findings[], exact scope "BG export workspace exact-stage admission", phase,
pins_sha256 for sealed.json and exact bindings for every sealed file plus seal.
Only then may launch.py be explicitly called. It rechecks seal, refs, host,
environment and predecessor, creates an exclusive one-attempt reservation and
runs through the pinned supervisor/guard. Reuse or missing admission fails closed.
GREEN requires exactly one independently accepted RED result with unchanged inputs.

Outer300 seconds includes orchestration/termination; inner292. Julia/BLAS1,
heap hint2GiB (not hard live-memory cap), VM8GiB, available RAM>=6GiB,
swap used<=1GiB. Guard owns process identities/groups/sessions, records samples,
terminal memory and exit; supervisor bounds the guard. Host closure covers all
previous groups plus both runner/child PGID and SID; PID alone is insufficient.

Only a preserved, independently classified pure timeout at300 may receive a
separate600/592 phase with the same source/options and new admission. No automatic
retry, tuning, non-timeout retry or replacing output. Errors, resource pressure,
warning, pin drift and mixed timeout/failure remain rejected. Pure-timeout status
requires a driver BEGIN checkpoint; early unclassified load stalls remain failed
and need a separate reviewed plan. This conservative classifier is not permission
to rerun an error as a timeout. No multi-hour run is prepared.

Post-run audit validates exact output membership, invocation/reservation linkage,
all hashes, host identities, resource/terminal conditions, source paths, exact
per-group results and warning logs. Exit alone is insufficient. Every result
requires independent result review; failures and false gates remain preserved.
Master/source/test/env/CI remain unchanged and no integration is authorized here.
''')
new('WORK-MEMORY.md','''# Work and memory accounting for prepared correctness driver

Implementation work and retained-memory formulas are the frozen Task1
work-memory-ledger.md and Task2 composition-ledger.md, both pinned in full. The
wrapper adds cold O(1) budget/busy/type/hook checks, one setup holder, two references
and Bool; no extra hot solve scan/copy/conversion. Fused import removes one8u
normalization temporary and2u stores on successful normalization only. Retained
scratch policy is512+8*cld(n,64), optionally+32n, at most min(1MiB,P0/16),
P0=16(l+u)+8(n+1). This is a policy charge, not a physical-memory bound. Original
factor, prepared destinations, histories, capacities, old/new refactor coexistence,
backend/extraction/import temporaries and GC/native retention remain chargeable.

RED invokes only six isdefined checks plus loader/Test/recorder. GREEN executes
Task1 workspace, importer, then Task2 lifecycle entries exactly once. Task1 has14
original fixture exports (seven fixtures/two policies), plus synthetic invariant,
normalization, allocator and orientation cases. Task2 repeated path has56 manager
setups,384 updates,96 refactors,2984 valid explicit solve entries. Failure matrix
reaches bounded n8 cold allocation prefixes (native25/Markowitz21), six seam failures,
wrong type, five synthetic scratch failures, reentrancy, publication and genuine
warm64 owner-reuse cases. Warm witnesses add two candidate/two reference setups,
four candidate refactor entries, four updates, two copies and34 explicit solves.
Copy and dimension/fallback paths run once per original arm/mode, as fully listed
in the frozen composition ledger; no old suite, public solver or cost loop runs.
Internal orientation/update/backend/import work is additional. These source counts
are not complete PREforward/native-call or allocation measurements.

Tests retain bounded graph snapshots of reachable owners and detached bits, input
and output vectors, copied factors, CSCs, exact-rational residual scratch, synthetic
64x64 orientation fixtures and failure sentinels. Graph traversal scales with
n+l+u+history+cache and has IdDict/tuple/array overhead; physical capacities and
native memory are not inferred from graph snapshots. Repeated groups use bounded
per-step state, not a growing trajectory log. Recorder stores11 child summaries
and only failure text; successful Test.Pass leaves increment counters, not a list
of7935 records. Failure diagnostics and exception backtraces can allocate. Raw TOML
and exact-tree final check occur after tests. Output serialization is correctness
driver overhead, never an allocation/speedup measurement. Resource guards bound the
process, not an asserted full live-object graph. Cost comparisons remain deferred.

No extra numerical oracle calls were added to frozen tests. The newly added driver
only invokes the three planned entries and source/thread checks. This source review
finds no unnecessary new production work or memory; no production code is changed.
Runtime correctness, actual counts, dispatch/compilation and performance remain
unverified until separately admitted Julia runs.
''')
print('Authored new driver, expected trees, offline controls, admission and ledger')
