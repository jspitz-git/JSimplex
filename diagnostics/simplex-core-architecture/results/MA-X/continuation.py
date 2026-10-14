from pathlib import Path
import json,hashlib,subprocess,time
D=Path(__file__).resolve().parent;R=D.parents[3]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rd(p):return json.loads(Path(p).read_text())
rev=rd(D/'admission-review.json');h=rd(D/'host.json')
if rev['accepted'] is not True or rev['findings'] or not all(sha(p)==v for p,v in rev['sha256'].items()):raise SystemExit('review not accepted/bound')
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  f=(p/'stat').read_text().rsplit(')',1)[1].split()
  if int(f[2]) in h['groups'] or int(f[3]) in h['groups'] or (p/'exe').resolve().name.startswith('julia'):matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,ProcessLookupError):pass
refs={k:subprocess.check_output(['git',*a],cwd=R,text=True).strip() for k,a in {'head':['rev-parse','HEAD'],'master':['rev-parse','master'],'branch':['branch','--show-current'],'remote':['ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture']}.items()}
if matches or boot!=h['boot_id'] or refs!=h['refs']:raise SystemExit('fresh host/ref')
status=R/'diagnostics/simplex-core-architecture/STATUS.md';road=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
for p,q in [(status,D/'STATUS.md.before-MA-X'),(road,D/'roadmap.md.before-MA-X')]:
 if p.read_bytes()!=q.read_bytes():raise SystemExit('continuation drift')
body='''MA-X complete DenseLU offline admission prepared and independently accepted.
See results/MA-X/admission.md, admission-review.md/json and the unchanged MA-W plan
Task1. Concrete driver uses original MA-R reference/tests/fixtures and exact MA-U
candidate/instrumented. Original52-case validators/reducers retained; new strict
per-process cost gate stops the sequence before another process. Partial metrics
are flushed before token/preservation checks; enriched records before assertions.
Byte-exact MA-V supervisor/guard retain TERM84/KILL88/wait90 and full identity checks.

No Julia/query/parser/import/compile/numerics/real launcher execution in MA-X.
All prepared scripts, manifests, checks and reviews are FROZEN; do not rerun their
exclusive writers. Failed initial test-builder selector and its corrected separate
builder are preserved; this was not a numerical attempt. No production/test/env/
CI/master changes. Old MA-S-2 rejected48/52 and MA-V local acceptance unchanged.

Next concrete step MA-Y: FIRST fresh refs/boot/start_ticks/command/full170 historical
groups OR sessions plus any later identities/noJulia, protected6/source514 and full
MA-X manifest membership/hash check. Create NEW launch-context and fresh independent
numerical-review binding then-current refs/context, MA-X pins and accepted preparation
review BEFORE reservation. Standing human permission covers this short sequence;
do not ask again solely for permission. Preparation acceptance is not the seal.

Then at most ONE sequence of3serial processes,90seconds inclusive each/270total,
original160correctness cases/488direct entries in process1 and52cost cases in each.
Total12,480cost entries/3,120windows (936warm/2,184measured),318setup factorizations
including2PFI constructors and2PFI copies; nested/native/import work additional.
Every process must pass original strict paired-ratio target and side-median control
gates before the next. Rational bytes/events have ZERO tolerance; no filtering,
baseline correction, tuning, retry or pooling rescue. Rational failure stops this
unchanged complete route without immediate allocator investigation. If all three
pass, new aggregate and independent result review; no automatic production merge.
Compatibility/direct dependency/clean loading/PFI/public afiro-sc50a remain separate.

Six MA-W current closure/publication/continuation STATUS/roadmap bindings map ONLY
to MA-X beforecopies through continuation-map.json. All older mappings remain.
Before later edits preserve exact current texts and map exact new bindings; old
host.json is not a fresh preflight. CIoff, HHdisabled, automationpaused. Master
6f68e24 unchanged; broader performance plan OPEN.
'''
s=status.read_text();marker='## Exact next action\n\n'
if s.count(marker)!=1:raise SystemExit('status marker')
s=s.replace(marker,marker+body+'\n## Previous MA-W design (completed)\n\n',1)
status.write_text(s);road.write_text(road.read_text().rstrip()+'\n\n## MA-X complete DenseLU offline admission (2026-10-14)\n\n'+body)
checks=dict(review=rev['accepted'] is True,host=not matches and refs==h['refs'],before_exact=all(sha(m['preserved'])==m['sha256']==rd(m['source'])['sha256'][m['path']] for m in rd(D/'continuation-map.json')['old_bindings']),source514=all(sha(R/p)==v for p,v in h['master_identity'].items()),protected6=all(sha(p)==v for p,v in h['protected'].items()))
with (D/'continuation.json').open('x') as f:json.dump(dict(all_passed=all(checks.values()),checks=checks,host=dict(time=time.time(),boot_id=boot,groups=h['groups'],matches=matches,refs=refs),sha256={str(p):sha(p) for p in [D/'continuation.py',D/'continuation-map.json',status,road]}),f,indent=2);f.write('\n')
if not all(checks.values()):raise SystemExit(1)
print('continuation PASS; current W binding maps preserved')
