from pathlib import Path
import json,hashlib,subprocess,os,datetime,ast
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-local/2026-10-27');Q=D/'GREEN-run';S=D/'GREEN';M=Path('/home/jspitz/JSimplex.jl');R=D.parents[2];O=R/'diagnostics/generic-quality-devex/2026-10-27'
def need(v,m):
 if not v:raise RuntimeError(m)
def read(p):return json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
def git(*a,root=M):return subprocess.check_output(['git','-C',str(root),*a],env=dict(os.environ,GIT_OPTIONAL_LOCKS='0')).decode().strip()
pins=read(Q/'pins.json');need(len(pins['inventory'])==1229,'latest pins')
for n,v in pins['inventory'].items():p=Path(n);need(str(p.resolve(strict=True))==v['resolved'] and sha(p)==v['sha256'],'pin '+n)
for tree in pins['trees']:need({str(p) for p in Path(tree).rglob('*') if p.is_file()}=={n for n in pins['inventory'] if Path(n).is_relative_to(tree)},'tree membership')
for doc in [D/'comparison-2/result-review.json',D/'RED-run/result-review.json']:
 r=read(doc);need(r['accepted'] and r['findings']==[],'independent accepted '+str(doc))
 for n,h in r['bindings'].items():need(sha(Path(n))==h,'result binding '+n)
base=read(D/'baseline-tree.json');inv=read(D/'source-inverse.json');changes=read(D/'changes.json');names=['src/primal_updates.jl','src/simplex_numerics.jl','test/generic_quality_local_tests.jl','test/runtests.jl'];actual={str(p.relative_to(S)):sha(p) for p in S.rglob('*') if p.is_file()}
need(inv['accepted'] and inv['names']==names and inv['whole_stage']==actual,'exact whole stage')
need(sorted(n for n in actual.keys()|base.keys() if actual.get(n)!=base.get(n))==names,'only four changes')
for n,h in base.items():need(sha(D/'baseline'/n)==sha(M/n)==h,'authoritative base '+n)
for n in names:need(actual[n]==inv['candidate_sha256'][n],'changed stage '+n)
for name in ['primal_updates.jl','simplex_numerics.jl']:
 n='src/'+name;old=(D/'baseline'/n).read_text();s=old
 for k in ['A','B','C']:
  v=changes[k]
  if v['file']==name:need(s.count(v['old'])==1,'forward seam '+k);s=s.replace(v['old'],v['new'])
 need(s==(S/n).read_text(),'whole forward '+name)
 for k in ['C','B','A']:
  v=changes[k]
  if v['file']==name:need(s.count(v['new'])==1,'inverse seam '+k);s=s.replace(v['new'],v['old'])
 need(s==old,'whole inverse '+name)
need((S/'test/runtests.jl').read_text()==(D/'baseline/test/runtests.jl').read_text()+'\ninclude("generic_quality_local_tests.jl")\n','new ordinary include only')
need(sha(S/'test/generic_quality_local_tests.jl')==sha(D/'RED/test/generic_quality_local_tests.jl')==sha(D/'new-test.jl')==sha(D/'new-test-draft.jl')=='12c0b1a8d0be69095f9588fa3057ee0d86b31bf0efbb0e8f11492898aaf139ce','frozen permanent test')
# Reconstruct the measured private variants from the authoritative blocks.
s=(M/'src/simplex_numerics.jl').read_text();i=s.index('function _componentwise_backward_error(');j=s.index('\nend',s.index('function solve_quality!'))+5;quality=s[i:j]+'\n\n';p=(M/'src/primal_updates.jl').read_text();i=p.index('function _audit_primal_values!');j=p.index('\nend',i)+5;audit=p[i:j]+'\n\n';i=p.index('function _quality_components!(r::AbstractVector{W},scale,terms,B::_PriceAuditMatrix');j=p.index('\nend',i)+5;virtual='_quality_values(B::_PriceAuditMatrix) = nonzeros(B.matrix)\n'+p[i:j]+'\n\n'
reference=(D/'comparison-2/Reference.jl').read_text();head=reference[:reference.index('function _componentwise_backward_error(')];need(reference==head+quality+virtual+audit+'end\n','exact complete reference')
b=changes['B']['new'][:-len(changes['B']['old'])];c=changes['C']['new'][:-len(changes['C']['old'])]
for kind in ['CandidateA','CandidateB','CandidateAB','CandidateC']:
 q=quality
 if kind in ['CandidateA','CandidateAB']:q=q.replace(changes['A']['old'],changes['A']['new'])
 if kind in ['CandidateB','CandidateAB']:q+=b
 need((D/'comparison-2'/(kind+'.jl')).read_text()==head.replace('LocalReference','Local'+kind)+q+virtual+audit+(c if kind=='CandidateC' else '')+'end\n','exact measured variant '+kind)
for ref in ['HEAD','master','origin/master']:need(git('rev-parse',ref)=='ca64312f7f74b1d7bec047718399f229674b3e1d','master ref')
need(git('rev-parse','HEAD',root=R)==read(Q/'host-before.json')['diagnostic_head'],'diagnostic ref');need(not git('diff','--name-only','HEAD','--','src','test','Project.toml'),'M untouched')
for group in read(Q/'protected-before.json').values():
 for n,h in group.items():need(sha(Path(n))==h,'protected '+n)
c=read(Q/'contract.json');prior=read(O/'GREEN-run/contract.json');need(c['files']==['generic_quality_local_tests.jl',*prior['files']] and len(c['files'])==35,'same prior34 plus new')
need(c['expected_exit']==c['expected_failures']==0 and c['expected_failure_locations']==[] and c['attempts']==1 and c['shared_limit_seconds']==2400 and c['guard_limit_seconds']==2392 and c['source_root']==str(S),'one allpass2400 contract')
need(str(D/'RED-run/result-review.json') in pins['inventory'],'independent RED pinned')
for n in ['common.py','launch.py','audit.py']:need((Q/n).read_bytes()==(D/'RED-run'/n).read_bytes(),'reviewed RED execution helper '+n)
for n in ['entry_gate.py','guard_reviewed.py','supervisor_reviewed.py']:need((Q/'guard'/n).read_bytes()==(D/'RED-run/guard'/n).read_bytes()==(O/'MASTER-run/guard'/n).read_bytes(),'reviewed runtime')
need((D/'publication_checks.py').read_bytes()==(O/'publication_checks.py').read_bytes(),'previously exercised publication helpers unchanged')
need((D/'commit-integrate-publish.py').read_text()==(D/'commit-integrate-publish.before-identity.py').read_text().replace('import common as c','import common_next as c'),'only identity import adjustment')
# Prove the publication body changes only task-specific paths/names/message relative to the previously reviewed implementation.
old=(O/'commit-integrate-publish.py').read_text().replace(str(O),str(D)).replace('refs/heads/codex/generic-quality-devex','refs/heads/codex/generic-quality-local').replace("prefix='quality-devex-index-'","prefix='quality-local-index-'").replace('exact five names','exact four names').replace("precommit_qualification='fresh34wholefilesGREEN'","precommit_qualification='fresh35wholefilesGREEN'").replace('import common as c','import common_next as c');new=(D/'commit-integrate-publish.py').read_text()
def omit_message(t):i=t.index(" message='");j=t.index("\n (D/'commit-message.txt')",i);return t[:i]+t[j:]
need(omit_message(old)==omit_message(new),'publication semantic scope')
for n in ['commit-integrate-publish.py','publication_checks.py','common_next.py']:ast.parse((D/n).read_text())
allow=read(D/'host-identity-allowance.json');need(sha(D/'host-identity-allowance.json')=='f0b6a5093b9c1875ec8718bca8775bc44ba4d6d6ab98a1ac23adfe52d69f2a92' and sha(Path(allow['historical_record']))==allow['historical_sha256'],'fixed identity evidence')
seed=read(Q/'host-seed.json');need(seed==read(D/'RED-run/audit-host.json'),'continuous historical ledger');groups=set(seed['groups']);need(len(groups)==591,'all groups');boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();need(boot==seed['boot_id'],'boot');procs=[];collisions=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  st=(p/'stat').read_text().rsplit(')',1)[1].split();args=[x.decode(errors='replace') for x in (p/'cmdline').read_bytes().split(b'\0') if x];comm=(p/'comm').read_text().strip();a=dict(pid=int(p.name),pgid=int(st[2]),sid=int(st[3]),start_ticks=int(st[19]),command=args,boot_id=boot)
  if a['pgid'] in groups or a['sid'] in groups:need(a in allow['identities'],'changed historical collision');collisions.append(a)
  need(not any(Path(v).name.lower().startswith('julia') for v in [comm]+args[:1]),'Julia active');procs.append(a)
 except (FileNotFoundError,ProcessLookupError):pass
mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()};need(mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2,'memory')
need(not (Q/'output').exists() and not (Q/'reservation.json').exists(),'exclusive no launch')
put(D/'independent-production-host.json',dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),boot_id=boot,groups=sorted(groups),processes=procs,no_Julia=True,historical_numerical_identities_absent=True,verified_unrelated_collisions=collisions,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree']))
report='''Verdict: exact production source/tests ACCEPTED for GREEN qualification, no unresolved findings. Publication preparation ACCEPTED. Neither verdict claims GREEN, actual commit or actual master has already passed.

The entire GREEN stage was independently hashed and compared with authoritative ca64312f7f74b1d7bec047718399f229674b3e1d. Exactly four paths differ: src/simplex_numerics.jl, src/primal_updates.jl, the new test and its ordinary include. All three declared substitutions reconstruct the complete staged source; their inverse reconstructs both complete baseline source files byte-for-byte. All existing tests and thresholds are unchanged. The exact measured Reference and A/B/AB/C namespaces were independently reconstructed from authoritative function blocks. The permanent test is the frozen pre-cost-data draft, exact RED-installed bytes and comparison fixtures/reference, with actual JSimplex candidate aliases.

A numerical/ownership review: the term's magnitude is calculated after the same product/residual subtraction, at the original first scale site, and reused only for the same later underflow comparison. Both x reads, scale update, term count, nonzero guards, lazy floatmin and iteration order remain. The new scalar is a private product or private negation; BigFloat addition does not mutate it or publish it into scale. No callback/precision mutation occurs in the ordinary scalar-array loop. Sign, signed zero, mixed stored precision and underflow behavior remain.

B numerical/ownership review: componentwise ratio, maximum absolute value, residual conversion/publication, finiteness scan and term maximum are all separate and in original order. Error/zero/Inf objects still use the original fresh constructors. Conditional magnitude selects the same Base abs value/precision/owner including signed zero; exact Clong0/1 comparisons and the pinned direct signed-integer MPFR subtraction preserve exact constants and one rounded subtraction. Scale invalidity, dimensions, result conversion, underflow preservation, finite and reliability checks remain. Ordinary BigFloat vector methods are narrow; generic methods remain byte-exact, while the BigFloat scalar roundoff overload also dispatches from generic/custom work-vector paths and hardware-to-wide fallback. This expanded scalar dispatch is intentional and equivalent, not a claim of wholly unchanged generic dispatch. New ordinary tests cover custom matrices, view fallback, invalid scales, large terms and hardware result with BigFloat work. No pass fusion or callback-crossing cache is introduced.

C numerical/ownership review: both prediction copies, recompute!, workspace finiteness and basis reliability, per-entry finite old check and final complete price audit remain. The private unit is created only after recompute/guards and the first finite predicted value; the callback-free ordinary norm loop reuses it read-only and discards it before return. Three-way max argument/tie order, divisions/subtraction, tolerance and precision/rounding scope remain. The initial assignment unit=tolerance is not used before replacement by one(T). No unit is returned or stored in output. Generic/Rational audit is unchanged. Recompute-throw/unreliable and callback-boundary preservation follow source structure; this task does not claim new injected dynamic coverage of those paths.

Computational work and retained memory: no unnecessary new full-vector/matrix scan, basis solve, copy, conversion, invariant check or retained numeric cache was found. A runs per eligible ordinary quality term, O(nnz) sparse/O(m*n) dense, and removes a second magnitude evaluation (one negation for a negative eligible product). B runs during each quality finalization, remains O(n) across the same five traversals, and avoids eager nonnegative negations, per-scale zero construction and accepted-roundoff one construction. Original wide scratch and precision scans remain. C runs per primal audit, preserves two O(n) copies, recomputation/factor/solve work and complete price certification; q finite norm entries need at most one unit rather than q. Additional scalar liveness is O(1), with no update-chain-dependent cache or new persistent root. Cold method metadata/compilation is separate from ordinary-call savings. No numerical safeguard, tolerance, coefficient or arithmetic precision is weakened.

Focused evidence: the separately accepted corrected comparison has63391 ordinary passes,2172cells,39096windows and2210 preparation records; all805GC windows remain, measured compilation/recompilation is zero. A reduces bytes/events in all240 negative/mixed quality cells and leaves positive/zero allocation counts unchanged. B reduces both metrics in480 whole-quality and120 full-finalizer cells; C in480 full-audit cells; AB in480 quality cells with additive median allocation savings. Representative BF128 nearest N96 mixed dense A quality time6532.201us to6012.100us, bytes8190750 to7527200, events232596 to214164; B full finalizer44.4us to25.8us,51040 to26208bytes,1594 to818events. These are scoped measurements, not universal speedups:107/480A,90/600B,43/480AB and54/480C cell time medians exceed one. BigInt byte variability is retained despite unchanged event counts. Setup/cold/warm/reset/GC are separate. Per-variant live/native memory, end-to-end trajectories, long update chains, full-suite and x64 remain unmeasured.

Regression review: baseline RED independently witnesses16579 passes plus exactly four intended cost failures at line440, no correctness errors. All twelve baseline/reference pairs have equal bytes/events and matching sinks. New four gates require strictly lower bytes AND events for fixed three warmed alternating pairs; no timing assertion, GC selection, threshold weakening or numerical retry. Combined AB permanent gates do not independently enforce A; independent A acceptance is the isolated measurement. GREEN executes the previous34 complete files unchanged plus the new test, including prior allocation gates. The original comparison's two invalid Rational expectations remain a rejected historical diagnostic; corrected comparison and refused offline preflight configurations remain separately preserved.

Publication preparation review: exactly four paths enter a private index against the reviewed base; diff-check, exact committed blobs and actual-commit review gate local ff-only integration. Original source/index beforeimages and unrelated index entries/staged state are preserved; protected user files and diagnostic index are checked. Push requires independently accepted fresh actual-master all-pass evidence matching GREEN total, complete actual/tested/pinned source/test trees, preserved beforeimages/baseline, expected local ref and approved origin/remote state. It is normal nonforce push with remote/tracking verification. The publication helper bytes are identical to the previously reviewed helpers, including their prior nine disposable acceptance/rejection checks. Publication body differs only in task names/paths/message/four-file and35-file labels and the exact identity-aware common import. No additional test replay is needed for these unchanged helpers. The fixed full-tuple WSL identity allowance remains bound; all other historical occupants and Julia remain rejected.

The reviewer ran read-only Python/Git and wrote only new review evidence. No Julia or historical launcher/auditor was rerun; no source, index or ref changed. Actual GREEN result, actual-commit review, fresh actual-master admission/all-pass result and final publication checks remain mandatory. No old failure exception transfers.
'''
with (D/'PRODUCTION-REVIEW.md').open('x') as f:f.write(report)
files=[D/n for n in ['PLAN.md','WORK-MEMORY.md','changes.json','baseline-tree.json','source-inverse.json','new-test.jl','new-test-draft.jl','comparison-2/result-review.json','comparison-2/RESULT-REVIEW.md','RED-run/result-review.json','RED-run/RESULT-REVIEW.md','PRODUCTION-REVIEW.md','independent-production-host.json','independent-production-check.py']]+[S/n for n in names]
put(D/'production-review.json',dict(accepted=True,findings=[],names=names,unnecessary_work_or_memory_found=False,review=str(D/'PRODUCTION-REVIEW.md'),scope='Source/test acceptance for guarded GREEN; actual outcomes and publication still gated',bindings={str(p):sha(p) for p in files}))
pfiles=[D/n for n in ['commit-integrate-publish.py','publication_checks.py','common_next.py','host-identity-allowance.json','HOST-IDENTITY.md','protected-before.json','baseline-tree.json','source-inverse.json','PLAN.md','PRODUCTION-REVIEW.md','independent-production-check.py']]+[O/'publication-preparation-reviewed.json']
put(D/'publication-preparation-reviewed.json',dict(accepted=True,findings=[],scope='Preparation only; GREEN, actual commit and actual MASTER independent reviews required',bindings={str(p):sha(p) for p in pfiles}))
admission='''Verdict: GREEN ADMITTED for one guarded2400-second attempt,2392-second internal cutoff, zero expected failures. No unresolved findings. This is admission, not a passing result or publication approval.

All1229 latest inventory entries, resolved paths and complete actual/stage source/test trees were independently hashed. The pinned independent RED acceptance, corrected comparison acceptance and every result binding match. The full exact four-path production stage and permanent test are reviewed in PRODUCTION-REVIEW.md. This run includes35 ordinary complete test files: previous34 unchanged plus the new test. Driver source/project identity and thread checks are retained. All original numerical checks and older allocation thresholds must pass; there is no transferred failure exception.

Common, launch, auditor and all guard/entry/supervisor bytes match the witnessed RED configuration. Exclusive attempt, rechecked pins/ref/environment/protected files, owned process identity/entry permit/parent-death cleanup, Julia/BLAS1/GC1,0, heap2GiB/AS8GiB, RAMavailable6GiB/swap1GiB and inclusive shared2400 budget remain. The exact full-identity WSL allowance remains fixed under its reviewed hash; no historical numeric ID is removed. Fresh evidence inspects all591 historical groups AND sessions and records any exact unrelated collision separately, with no live Julia and sufficient memory. Launch must refresh these checks. No Julia or source/index/ref mutation was performed by the reviewer; preserve any failure without rerun-to-pass.
'''
with (Q/'ADMISSION-REVIEW.md').open('x') as f:f.write(admission)
afiles=[Path(n) for n in pins['inventory']]+[p for p in Q.rglob('*') if p.is_file()]+[D/n for n in ['production-review.json','PRODUCTION-REVIEW.md','publication-preparation-reviewed.json','independent-production-host.json','independent-production-check.py']]
put(Q/'admission.json',dict(accepted=True,findings=[],attempts=1,expected_failures=0,review=str(Q/'ADMISSION-REVIEW.md'),bindings={str(p):sha(p) for p in afiles}))
print(json.dumps(dict(accepted=True,pins=len(pins['inventory']),ordinary_files=len(c['files']),historical_groups=len(groups),unrelated_collisions=collisions,outputs={str(p):sha(p) for p in [D/'production-review.json',D/'publication-preparation-reviewed.json',Q/'admission.json']})))
