from pathlib import Path
import json,hashlib,subprocess,datetime,os,sys,tempfile,copy,importlib.util,ast
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-devex/2026-10-27');M=Path('/home/jspitz/JSimplex.jl');R=D.parents[2];Q=D/'GREEN-run';S=D/'GREEN'
def read(p):return json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise RuntimeError(m)
def put(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
def git(*args):return subprocess.check_output(['git','-C',str(M),*args],text=True,env=dict(os.environ,GIT_OPTIONAL_LOCKS='0')).strip()
base=read(D/'baseline-tree.json');inv=read(D/'source-inverse.json');changes=read(D/'changes.json')
expected=sorted(['src/dual_simplex.jl','src/primal_simplex.jl','src/simplex_numerics.jl','test/generic_quality_devex_tests.jl','test/runtests.jl'])
need(inv['accepted'] and inv['names']==expected,'exact names')
actual={str(p.relative_to(S)):sha(p) for p in S.rglob('*') if p.is_file()};need(actual==inv['whole_stage'],'whole candidate')
need(sorted(n for n in base.keys()|actual.keys() if base.get(n)!=actual.get(n))==expected,'exact change set')
for n,h in base.items():need(sha(D/'baseline'/n)==h and sha(M/n)==h,'authoritative base '+n)
for n in expected:
 need(sha(S/n)==inv['candidate_sha256'][n],'candidate hash '+n)
 if n.startswith('src/'):
  original=(D/'baseline'/n).read_text();new=original
  for k in ['A1','A2','B','C']:
   x=changes[k]
   if n=='src/'+x['file']:need(new.count(x['old'])==1,'seam '+k);new=new.replace(x['old'],x['new'])
  need(new==(S/n).read_text(),'exact forward '+n)
  for k in ['C','B','A2','A1']:
   x=changes[k]
   if n=='src/'+x['file']:need(new.count(x['new'])==1,'inverse seam '+k);new=new.replace(x['new'],x['old'])
  need(new==original,'whole file inverse '+n)
need((S/'test/runtests.jl').read_text().replace('    include("generic_quality_devex_tests.jl")\n','',1)==(D/'baseline/test/runtests.jl').read_text(),'only new test include')
newtest=(D/'new-test.jl').read_text();need((D/'reference.jl').read_text() in newtest and (D/'fixtures.jl').read_text() in newtest,'frozen reference/fixtures')
need((S/'test/generic_quality_devex_tests.jl').read_text()==newtest==(D/'RED/test/generic_quality_devex_tests.jl').read_text(),'exact RED/GREEN test')
need('const SavingsCandidate=JSimplex' in newtest and 'Test.record' not in newtest and 'push_testset' not in newtest,'ordinary direct test')
# The measured candidate is the declared exact substitutions, not a second implementation.
r=(D/'reference.jl').read_text().replace('module SavingsReference','module SavingsCandidate',1)
for k in ['A1','A2','C']:
 x=changes[k];need(r.count(x['old'])==1,'private seam '+k);r=r.replace(x['old'],x['new'])
# B is inserted before _wide_solve_quality!, since _quality_roundoff remains an imported unchanged dependency.
x=changes['B'];insertion=x['new'][:-len(x['old'])];r=r.replace('function _wide_solve_quality!',insertion+'function _wide_solve_quality!',1)
need(r==(D/'candidate.jl').read_text(),'measured candidate reconstruction')
for ref in ['HEAD','master','origin/master']:need(git('rev-parse',ref)=='7e306e24f064a8aa214bc88379e059def77661ab','master ref')
need(not git('diff','--name-only','HEAD','--','src','test','Project.toml'),'M clean production')
pins=read(Q/'pins.json');need(len(pins['inventory'])==1221,'latest pins count')
need(pins['inventory'][str(D/'RED-run/result-review.json')]['sha256']==sha(D/'RED-run/result-review.json'),'RED review pinned')
for n,v in pins['inventory'].items():p=Path(n);need(str(p.resolve(strict=True))==v['resolved'] and sha(p)==v['sha256'],'inventory '+n)
for tree in pins['trees']:need({str(p) for p in Path(tree).rglob('*') if p.is_file()}=={n for n in pins['inventory'] if Path(n).is_relative_to(tree)},'membership '+tree)
for n in ['entry_gate.py','guard_reviewed.py','supervisor_reviewed.py']:need((Q/'guard'/n).read_bytes()==(D/'RED-run/guard'/n).read_bytes()==(D/'guard'/n).read_bytes(),'reviewed guard unchanged '+n)
need((Q/'launch.py').read_bytes()==(D/'RED-run/launch.py').read_bytes(),'reviewed launch unchanged')
need((Q/'common.py').read_bytes()==(D/'RED-run/common.py').read_bytes(),'reviewed common unchanged')
contract=read(Q/'contract.json');prior=read(R/'diagnostics/generic-residual-magnitudes/2026-10-26/GREEN-run/contract.json')
need(contract['files']==['generic_quality_devex_tests.jl',*prior['files'],'simplex_numerics_tests.jl','primal_simplex_tests.jl'] and len(contract['files'])==34,'ordinary closure')
need(contract['expected_exit']==contract['expected_failures']==0 and contract['expected_failure_locations']==[] and contract['attempts']==1,'allpass single attempt')
need(contract['source_root']==str(S) and contract['shared_limit_seconds']==1800 and contract['guard_limit_seconds']==1792,'source/time contract')
need(not (Q/'output').exists() and not (Q/'reservation.json').exists(),'not already launched')
for group in read(Q/'protected-before.json').values():
 for n,h in group.items():need(sha(Path(n))==h,'protected '+n)
# Fresh independent /proc scan, including every historical group and session.
seed=read(Q/'host-seed.json');groups=set(seed['groups']);processes=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  st=(p/'stat').read_text().rsplit(')',1)[1].split();a=[x.decode(errors='replace') for x in (p/'cmdline').read_bytes().split(b'\0') if x];comm=(p/'comm').read_text().strip();pgid,sid=int(st[2]),int(st[3])
  need(pgid not in groups and sid not in groups,'historical process active');need(not any(Path(x).name.lower().startswith('julia') for x in [comm]+a[:1]),'Julia active');processes.append(dict(pid=int(p.name),pgid=pgid,sid=sid,start_ticks=int(st[19]),command=a))
 except (FileNotFoundError,ProcessLookupError):pass
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();need(boot==seed['boot_id'],'boot')
mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()};need(mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2,'memory')
host=dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),boot_id=boot,groups=sorted(groups),processes=processes,no_Julia=True,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree'])
# Pure helper exercise on synthetic disposable files; no repository writes or Git mutations.
spec=importlib.util.spec_from_file_location('publication_checks_review',D/'publication_checks.py');pub=importlib.util.module_from_spec(spec);spec.loader.exec_module(pub);checks=0
with tempfile.TemporaryDirectory(prefix='quality-publication-review-') as t:
 root=Path(t);master=root/'master';stage=root/'stage'
 for p in [master,stage]:
  for tree in ['src','test']:(p/tree).mkdir(parents=True);(p/tree/'a').write_text(tree)
 pinned={'inventory':{str(p):dict(resolved=str(p.resolve()),sha256=sha(p)) for p in master.rglob('*') if p.is_file()}}
 def verify():pub.verify_tested_trees(master,stage,pinned,need,sha)
 def reject(f):
  global checks
  try:f()
  except RuntimeError:checks+=1
  else:raise RuntimeError('failed to reject changed publication evidence')
 verify();checks+=1
 (master/'src/extra').write_text('x');reject(verify);(master/'src/extra').unlink()
 (stage/'test/extra').write_text('x');reject(verify);(stage/'test/extra').unlink()
 (master/'src/a').write_text('altered');(stage/'src/a').write_text('altered');reject(verify)
 (master/'src/a').write_text('src');(stage/'src/a').write_text('src')
 pinned['inventory'][str(master/'src/a')]['resolved']='wrong';reject(verify)
 baseline={'src/a':'sourcehash'};b=root/'baseline/src/a';b.parent.mkdir(parents=True);b.write_text('source');baseline['src/a']=sha(b)
 before=root/'before-master/master.index';before.parent.mkdir();before.write_text('index');idx=str(master/'.git/index');protected={'indexes':{idx:sha(before)}}
 hist={'master_before':'base','source_before':{str(master/'src/a'):{'before':str(b),'sha256':sha(b)}},'master_index_before':{idx:{'before':str(before),'sha256':sha(before)}}};cont={'master_source_before':hist['source_before'],'master_index_before':hist['master_index_before']}
 def maps(h=hist,c=cont):pub.verify_historical_maps(root,master,idx,'base',['src/a','test/new'],h,c,protected,baseline,need,sha)
 maps();checks+=1
 bad=copy.deepcopy(hist);bad['source_before'][str(master/'src/a')]['before']='wrong';reject(lambda:maps(bad,{'master_source_before':bad['source_before'],'master_index_before':bad['master_index_before']}))
 bad=copy.deepcopy(cont);bad['master_source_before']={};reject(lambda:maps(hist,bad))
 bad=copy.deepcopy(hist);bad['master_index_before'][idx]['sha256']='wrong';reject(lambda:maps(bad,{'master_source_before':bad['source_before'],'master_index_before':bad['master_index_before']}))
for n in ['commit-integrate-publish.py','publication_checks.py','GREEN-run/launch.py','GREEN-run/common.py','GREEN-run/audit.py']:ast.parse((D/n).read_text())
put(D/'independent-production-host.json',host)
report='''Verdict: production source and tests ACCEPTED for the guarded GREEN qualification; publication preparation ACCEPTED. No unresolved findings. This does not assert that GREEN, an actual commit, or actual master has passed: their independent reviews remain mandatory before their next stages.

The actual GREEN tree differs from authoritative master 7e306e24f064a8aa214bc88379e059def77661ab in exactly five paths: three source files, the new ordinary regression, and one added runtests include. Applying the declared substitutions independently reconstructs each complete source file; reversing them reproduces the entire original files. The measured private candidate is those exact substitutions. All original tests remain byte-identical, including the prior Rational allocation threshold. No old exception authorizes a new failure.

Numerical review: A changes only original abs sites to the pre-existing signbit conditional. Julia's pinned Base abs(Real) eagerly evaluates negation but selects the same signed/precision/owner result; both old and new preserve signed zero. All residual order, bounds, finiteness, tolerance and pipeline invalidation checks remain. B retains product conversions, both x reads, residual/scale/counter order and both original nonzero predicates before the underflow comparison. Dispatch is restricted to ordinary BigFloat matrix/CSC and plain BigFloat vectors with Int term storage. Custom matrices/views, virtual matrices, hardware and exact routes retain the original method. The limit is created only at the first eligible comparison within the fixed precision scalar loop, comparison-only, and dies on return. Outer stored-precision scans, wide allocation and all alias/dimension/finiteness/reliability checks are unchanged. C computes the identical fresh ambient-precision product. Every finite product fits ambient floatmax; only positive infinity requires a fresh scalar cap. NaN, negative infinity, signed zero and mixed input precision keep the prior selected product; each overflow output has its own owner. No tolerance, coefficient, arithmetic precision or safeguard changes.

Computational work and memory: no unnecessary new full-vector/matrix scan, basis solve, copy, conversion, invariant check or retained cache/root was found. A runs during residual validation and remains O(m+nnz(basis)), using the original scratch, removing unused negations only at nonnegative sites. B runs during quality evaluation and remains O(m+nnz) sparse or O(m*n) dense plus unchanged outer scans/wide scratch. K eligible floatmin constructions become at most one; a local readiness branch and tuple propagation are the added per-term work. C runs per eligible Devex candidate and retains O(number of states) plus unchanged solved-path BTRAN and pricing. It replaces unconditional cap construction/min by isinf/signbit and a fresh overflow cap. There is no added update-chain-length factor, recovery loop, setup cache or final-certification scan.

Evidence for material hot-path costs is the accepted 1160-cell whole-call experiment: 33807 correctness passes; all pairs retained, cold/warm/setup/GC separated, zero measured compilation. Direction allocations fall in all 180 cells; row in 150/180 with 30 unchanged; all 360 quality and 360 Devex cells reduce both events and bytes. Quality byte reductions are 14.825–41.204%, but three cell median times exceed one (1.1344,1.1114,1.0122); they remain visible, so acceptance is local allocation/work savings, not universal time improvement. Solved Devex includes a four-row BTRAN/price path. Native/exact controls have unchanged event counts. No inference is made from iteration counts. End-to-end trajectories, recovery/refactorization/update-chain stress, x64 and native allocator/free behavior remain unmeasured.

The permanent ordinary Test module contains the exact measured reference and correctness fixtures, compares actual JSimplex, and uses three fixed warmed alternating pairs for six whole-call bytes/events thresholds. It compares values, BigFloat precision/sign, exceptions, scratch/pipeline state, input owners, overflow owners, sparse/dense, five roundings, BF64/128/256, mixed512, empty/zero/nonfinite/underflow and generic fallback controls. RED independently witnessed 9465 passes plus exactly six intended cost failures, no errors, with equal baseline/reference bytes/events in all 18 pairs. GREEN runs all 34 ordinary test files: the previous 31 unchanged files, this new test and core numerics/primal tests.

Publication review: a private index contains exactly the five paths against the authoritative base, with diff checks and exact blob verification; real indexes remain protected until ff-only master integration. Actual-commit review is a separate prerequisite. Source and master-index beforeimages are preserved, unrelated index entries/staged changes compared, protected files and diagnostic index retained. Push requires a fresh independent all-pass MASTER result matching GREEN's total, exact complete tested/pinned current source/test trees, preserved historical maps and baseline, the expected local ref, an approved origin and remote base/target. It uses normal nonforce push and checks the remote/tracking refs afterward. The pure publication helper checks were exercised on disposable fixtures for accepted evidence and rejection of extra files, common source drift, path-resolution drift and corrupted historical maps. No source/index/ref changed and no Julia launched during this review.
'''
with (D/'PRODUCTION-REVIEW.md').open('x') as f:f.write(report)
production_files=[D/n for n in ['PLAN.md','WORK-MEMORY.md','changes.json','baseline-tree.json','source-inverse.json','reference.jl','candidate.jl','fixtures.jl','new-test.jl','result-review.json','RESULT-REVIEW.md','RED-run/result-review.json','PRODUCTION-REVIEW.md','independent-production-host.json','independent-production-check.py']]+[S/n for n in expected]
put(D/'production-review.json',dict(accepted=True,findings=[],reviewer='independent production reviewer',verdict='Exact production source and tests accepted for GREEN qualification; final GREEN/commit/master results pending',unnecessary_work_or_memory_found=False,names=expected,bindings={str(p):sha(p) for p in production_files}))
publication_files=[D/n for n in ['commit-integrate-publish.py','publication_checks.py','prepare-publication.py','common.py','protected-before.json','baseline-tree.json','source-inverse.json','PLAN.md','PRODUCTION-REVIEW.md','independent-production-check.py']]
put(D/'publication-preparation-reviewed.json',dict(accepted=True,findings=[],reviewer='independent production reviewer',helper_fixture_checks=checks,remaining_gates=['GREEN all-pass independent result','actual commit independent review','actual MASTER fresh all-pass independent result','unchanged tested/pinned trees and preserved historical maps before nonforce push'],bindings={str(p):sha(p) for p in publication_files}))
admission='''Verdict: ACCEPTED for one guarded GREEN attempt with an inclusive 1800-second limit. No unresolved findings. This is launch admission, not a passing result or release exception.

Latest pins.json contains 1221 independently streamed SHA256 inputs and now binds the independent witnessed RED result. All four complete production/stage source/test memberships, authoritative baseline, exact five changes and whole-source inverse were verified. Source/tests are reviewed in PRODUCTION-REVIEW.md. The previous 31-file closure is unchanged; the new test and simplex_numerics/primal_simplex files give 34 ordinary test files. The driver asserts actual package/project identity and single Julia/BLAS threads. Expected exit is zero with no failures, skips, broken tests or transferred older allocation exception.

Guard, entry gate, supervisor, common checks and launch exactly match the witnessed RED guard chain. They enforce exclusive output/attempt, revalidate hashes/ref/protected files/environment, record full process identity and entry permit, retain parent-death and owned cleanup, Julia/BLAS1/GC1,0, heap2GiB/AS8GiB and RAM6GiB/swap1GiB bounds, and share the 1800-second budget with a 1792-second guard cutoff. Fresh independent host evidence verifies all historical groups/sessions, boot/startticks/commands and absence of Julia. The launch must refresh these checks. No Julia was launched by this reviewer. Preserve any failing evidence; do not retry numerical failure for a pass.
'''
with (Q/'ADMISSION-REVIEW.md').open('x') as f:f.write(admission)
admit_files=[p for p in Q.rglob('*') if p.is_file()]+[D/'RED-run/result-review.json',D/'PRODUCTION-REVIEW.md',D/'production-review.json',D/'independent-production-host.json',D/'independent-production-check.py',D/'source-inverse.json']
put(Q/'admission.json',dict(accepted=True,findings=[],attempts=1,expected_failures=0,review=str(Q/'ADMISSION-REVIEW.md'),bindings={str(p):sha(p) for p in admit_files}))
print(json.dumps(dict(accepted=True,source_paths=expected,inventory=len(pins['inventory']),ordinary_files=len(contract['files']),historical_groups=len(groups),publication_helper_checks=checks,outputs={str(p):sha(p) for p in [D/'production-review.json',D/'publication-preparation-reviewed.json',Q/'admission.json']}),indent=2))
