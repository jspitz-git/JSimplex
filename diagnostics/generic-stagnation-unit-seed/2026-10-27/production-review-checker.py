from pathlib import Path
import importlib.util,json,hashlib,subprocess,ast,sys,datetime
sys.dont_write_bytecode=True
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-stagnation-unit-seed/2026-10-27');G=D/'GREEN-run';M=Path('/home/jspitz/JSimplex.jl')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def need(x,msg):
 if not x:raise AssertionError(msg)
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
def load(p,name):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
c=load(G/'common.py','green_review_common');c.unchanged();host=c.host();need(len(host['groups'])==613,'all 613 groups');put(D/'production-review-host.json',host)
base=read(D/'baseline-tree.json');inv=read(D/'source-inverse.json');changes=read(D/'changes.json')
need(len(base)==537 and len(inv['whole_stage'])==538,'tree sizes')
for root,mapping in [(D/'baseline',base),(D/'GREEN',inv['whole_stage'])]:
 need({str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}==set(mapping),'tree membership')
 for n,h in mapping.items():need(sha(root/n)==h,'tree hash '+n)
tracked=subprocess.check_output(['git','-C',str(M),'ls-tree','-r','--name-only',c.TARGET,'--','src','test','Project.toml']).decode().splitlines()
need(set(tracked)==set(base)-{'Manifest.toml','LocalPreferences.toml'},'authoritative tracked tree membership')
proc=subprocess.Popen(['git','-C',str(M),'cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
for n in tracked:
 proc.stdin.write((c.TARGET+':'+n+'\n').encode());proc.stdin.flush();header=proc.stdout.readline().decode().split();data=proc.stdout.read(int(header[2]));need(proc.stdout.read(1)==b'\n','batch record');need(hashlib.sha256(data).hexdigest()==base[n],'actual master baseline '+n)
proc.stdin.close();need(proc.wait()==0,'cat-file')
expected={n:(D/'baseline'/n).read_text() for n in ['src/primal_simplex.jl','src/simplex_stalling.jl']}
for change in changes:
 n=change['file'];need(expected[n].count(change['old'])==1,'unique inverse region');expected[n]=expected[n].replace(change['old'],change['new'],1)
for n,s in expected.items():need((D/'GREEN'/n).read_text()==s,'exact complete source '+n)
names=sorted(n for n in set(base)|set(inv['whole_stage']) if base.get(n)!=inv['whole_stage'].get(n));need(names==inv['names'] and len(names)==4,'exact four changed paths')
need((D/'GREEN/test/generic_stagnation_unit_seed_tests.jl').read_bytes()==(D/'new-test.jl').read_bytes(),'ordinary test source')
need((D/'GREEN/test/runtests.jl').read_text()==(D/'baseline/test/runtests.jl').read_text()+'\ninclude("generic_stagnation_unit_seed_tests.jl")\n','only include addition')
for n in ['result-review.json','RED-run/result-review.json']:
 r=read(D/n);need(r['accepted'] is True and r['findings']==[],'accepted prerequisite')
 for p,h in r['bindings'].items():need(Path(p).is_absolute() and sha(p)==h,'prerequisite binding '+p)
contract=read(G/'contract.json');need(contract['arm']=='GREEN' and contract['attempts']==1 and contract['expected_exit']==0 and contract['expected_failures']==0 and len(contract['files'])==len(set(contract['files']))==45,'GREEN shape')
need(contract['guard_limit_seconds']==2392 and contract['shared_limit_seconds']==2400,'deadlines')
need(not (G/'output').exists() and not (G/'reservation.json').exists(),'unexecuted GREEN')
for p in [*G.glob('*.py'),*(G/'guard').glob('*.py')]:ast.parse(p.read_text(),filename=str(p))
runtime=read(D/'runtime-readtime-pins.json');need(len(runtime['inventory'])==13,'13 scoped runtime binaries')
for p,v in runtime['inventory'].items():need(sha(p)==v['sha256'] and str(Path(p).resolve())==v['resolved'],'runtime pin')
need(subprocess.check_output(['git','-C',str(M),'ls-remote','origin','refs/heads/master']).decode().split()[0]==c.TARGET,'remote master')
(D/'production-review-checker.py').write_bytes(Path(__file__).read_bytes())
prod_paths=[D/n for n in ['PLAN.md','WORK-MEMORY.md','changes.json','source-inverse.json','baseline-tree.json','result-review.json','RESULT-REVIEW.md','RED-run/result-review.json','new-test.jl','production-review-host.json','production-review-checker.py']]+[D/'GREEN'/n for n in names]
put(D/'production-review.json',dict(accepted=True,findings=[],scope='Fresh independent whole-branch staged production numerical/work-memory and ordinary regression review; authorizes concrete GREEN, not merge/push before future reviews.',baseline=c.TARGET,changed_paths=names,baseline_files=537,candidate_files=538,unnecessary_added_production_work_or_memory_found=False,declined_to_judge=[],bindings={str(p):sha(p) for p in prod_paths}))
text='''# Independent whole-branch production review

No actionable numerical, ownership, computational-work or memory findings. Accept the exact four-path candidate for the separately bound GREEN attempt. This is not a claim that GREEN or actual-master tests have passed.

I independently reconstructed both complete production files from authoritative master c01900c2 and the three exact changes, checked all 537 baseline and 538 staged files, and verified only two production files, the new ordinary test and its runtests include differ. Generic methods and every older test/threshold remain byte-identical. The stale diagnostic worktree source was not used as baseline.

A runs in each monitored metric call, including observation and dual rebase. It removes m+u fresh BigFloat zero constructions and unused positive free-price negations, preserving O(n+m) loops and arithmetic order. The comparison reference retains the initial primal zero until call completion (O(precision) local lifetime extension); all three outputs remain independently fresh between calls. No new full scan, basis solve, copy, conversion, invariant check or persistent numeric owner is introduced. Context, finiteness, callback, history and rebase paths are unchanged.

B runs at cold steepest initialization and explicit unit-basis predicates. Structural traversal remains O(m), including colptr/row checks and early exceptions. BigFloat keeps sign-dependent negation and ambient rounding, then compares with exact machine integer one. RationalBigInt compares numerator/denominator against signed units without allocating result owners. Other types keep generic behavior. No new traversal or retained owner is added; comparison limb cost still scales with represented precision.

C runs once per uninitialized steepest setup. Column weight work remains two norm scans per column, O(nnz+n), and slack assignments remain O(m). Shared row cacheability falls from m checks to one for nonempty rows, at its original first site after the first weight write; zero rows skip it. A per-row Boolean branch and two local Boolean values replace repeated floatmax/abs2 work. Fresh row owner and existing within-call sharing remain; no callback or precision mutation intervenes. Short arrays preserve partial writes and initialized flag. Update-chain length has no new effect.

Evidence is the accepted independent comparison review: 105921 correctness checks, 3415 sparse/dense cells, 61470 alternating measured windows across BF64/128/256 and five rounding modes plus native/exact controls, measured compilation/recompilation zero. A whole metric/primal observation/dual observation median paired time ratios 0.9546/0.9656/0.9675 with 32–436 fewer events; B structural gates remove 32–256 BigFloat and 32–192 rational events depending on sign/shape; C saves 63/279 events at 8/32 rows; composed BC whole initializer ratio 0.8660. Setup, snapshots, first-state calls, explicit GC and measured calls are separately reported in RESULT-REVIEW.md. All 23 GC windows and slower cells remain. One A pair adds 7856 bytes despite 96 fewer events; no universal byte/time improvement, end-to-end gain, full native retention or complete loader coverage is claimed.

The permanent ordinary Test module retains hand-derived metric/weight oracles, all fifteen BigFloat contexts, stored 512-bit negatives, signed-zero/nonfinite/malformed gates, empty/initialized paths, shortened-array partial states, actual observer mutation/throw, dual rebase and cross-call owners. It imports Test before aliases/macros. Five fixed three-pair whole-call allocation gates require fewer events in every pair and lower median bytes, without timing thresholds, GC filtering or older-test weakening. Witnessed RED has 30806 passes and precisely five expected allocation failures, no errors.

No unnecessary added production work or memory was found. The added code/method footprint is cold and unmeasured; full-suite/x64, larger dimensions, public trajectories and native retained memory remain outside this scoped acceptance. Declined-to-judge behaviors: none; these are explicit coverage limits, not silently excluded correctness issues.
'''
(D/'PRODUCTION-REVIEW.md').write_text(text)
admission_paths=[G/n for n in ['pins.json','contract.json','launch.py','audit.py','common.py','tests.jl','host-seed.json','host-before.json','protected-before.json','environment.json']]+list((G/'guard').glob('*.py'))+[D/'production-review.json',D/'PRODUCTION-REVIEW.md',D/'production-review-host.json',D/'runtime-readtime-pins.json',D/'RED-run/result-review.json']
put(G/'admission.json',dict(accepted=True,findings=[],scope='One exact GREEN 45-whole-file attempt, 2392-second inner/2400-second inclusive limit; fresh launch unchanged/host checks remain mandatory.',pins_verified=1251,historical_groups_and_sessions=613,no_Julia=True,bindings={str(p):sha(p) for p in admission_paths}))
(G/'ADMISSION-REVIEW.md').write_text('''# Concrete GREEN admission

Accepted one exact prepared GREEN attempt: 45 frozen ordered whole files; expected exit 0, no failures/errors/broken tests, total frozen for subsequent actual master. Verified all 1251 current pins/resolutions and four tree memberships, protected actual user files/indexes, master/tracking/remote baseline, diagnostic ref, empty inherited overrides, and all 613 historical process groups AND sessions with boot/start ticks/commands and no Julia. Only the exact previously pinned unrelated WSL identity exception is allowed.

Read the actual launch, common, ordinary Test driver, audit, entry gate, guard and supervisor. Exclusive attempt/output creation and admission/pin binding precede launch. Absolute inner deadline is 2392 seconds and inclusive supervisor/launch limit 2400; one Julia and BLAS thread, GC1,0, 2 GiB heap hint, 8 GiB AS cap, minimum available RAM6 GiB and swap at most1 GiB. Entry handshake and parent-death signal, unreaped leader/pidfd identity checks, whole-session cleanup and terminal resources remain intact. Runtime scope is exactly thirteen installed binary readtime pins, not loader/cache/import closure. Test driver checks actual source/project and uses ordinary Test only; auditor rejects errors, skips/broken counts, wrong order, unexpected fails and changed pins. No Julia or old auditor/validator was run for this review.

No actionable admission findings. This prospective admission does not certify a future result; launch repeats fresh checks and independent result review remains required.
''')
print(json.dumps({'accepted':True,'names':names,'pins':1251,'groups':613,'host_available_kib':host['available_kib']}))
