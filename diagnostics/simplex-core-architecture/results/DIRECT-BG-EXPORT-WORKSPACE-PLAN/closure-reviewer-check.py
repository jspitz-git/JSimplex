from pathlib import Path
import hashlib
import json

R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
E=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-WORKSPACE-PLAN'
bindings={};checks={}
def read(p):
 p=Path(p);raw=p.read_bytes();bindings[str(p)]=hashlib.sha256(raw).hexdigest();return raw.decode()
def check(k,v):checks[k]=bool(v)
def verify(label,mapping):
 for name,digest in mapping.items():
  p=Path(name);p=p if p.is_absolute() else R/p
  read(p);check(label+':'+name,bindings[str(p)]==digest)
c=json.loads(read(E/'closure.json'))
h=json.loads(read(E/'host-closure.json'))
a=json.loads(read(E/'amendment-review.json'))
verify('failed-closure-preserved',c['sha256'])
verify('accepted-readtime',a['readtime_sha256'])
verify('accepted-evidence',a['evidence_sha256'])
check('sole-failed-gate',c['all_passed'] is False and [k for k,v in c['checks'].items() if not v]==['fresh_host'])
check('historical-host-evidence',not h['matches'] and len(h['groups'])==246 and len(h['unreadable_exe_pids'])==28)
check('design-review-accepted',a['accepted'] is True and not a['findings'] and all(a[k]==0 for k in ['critical','important','minor']))
s=read(E/'closure-supplement.py');p=read(E/'publication-final.py')
check('documentation-only', 'No numerical admission' in s and 'NOT verified executable identities' in s)
check('new-exclusive-output-files', "save('host-closure-supplement.json',host)" in s and "save('closure-supplement.json',record)" in s and ".open('x')" in s)
check('records-unavailable-executable-context','exe_unavailable.append(record)' in s and 'start_ticks=int(t[19])' in s and "command=b' '.join(args)" in s)
check('stat-command-unread-fails', 'except PermissionError:unread.append(int(p.name))' in s and 'not matches and not unread and len(groups)==246' in s)
check('groups-and-sessions-checked','int(t[2]) in groups or int(t[3]) in groups' in s)
check('three-visible-julia-signals',"startswith('julia') for s in [comm,exe,argv0]" in s)
check('previous-failure-remains-bound',"c['all_passed'] is False" in s and "original_bindings=verify(c['sha256'])" in s)
check('accepted-plan-and-correction-bound',"verify(review['readtime_sha256'])" in s and "verify(review['evidence_sha256'])" in s and "verify(cr['readtime_sha256'])" in s and "verify(cr['evidence_sha256'])" in s)
check('exact-new-file-set', 'actual==set(names)-excluded' in s and 'len(names)==len(set(names))' in s and "for p in E.rglob('*') if p.is_file()" in s)
check('refs-index-candidate-gates', 'refs_unchanged=' in s and 'tracked_unchanged=' in s and 'no_candidate=' in s)
check('publication-requires-supplement',"E/'closure-supplement.json'" in p and "c['all_passed'] is True" in p and 'closure bindings' in p)
check('publication-exact-blobs','exact stage names' in p and 'exact blobs' in p and 'final names' in p and 'final blobs' in p and "'--error-unmatch'" in p)
read(Path(__file__).resolve())
result=dict(accepted=all(checks.values()),findings=[],critical=0,important=0,minor=0,all_passed=all(checks.values()),checks=checks,readtime_sha256=bindings,evidence_sha256={k:v for k,v in bindings.items() if k.startswith(str(E)+'/')},scope='Offline source review of documentation-only closure correction; no process scan or script under review was executed by reviewer.')
with (E/'closure-reviewer-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
text='''# Independent documentation-closure correction review

Accepted for documentation-only closure: 0 critical, 0 important, 0 minor. This accepts the prospective source correction, not a successful host survey, staging, commit, push or numerical admission. The accepted amended design remains unchanged.

The preserved closure.json has exactly one false check, fresh_host; its other twelve checks pass. host-closure.json records no matched historical groups/sessions or recognized Julia process, 246 historical identifiers and 28 permission-denied executable links. Those records do not establish that every unreadable executable belongs to a harmless root/system process, nor prove universal absence of Julia. I do not make either claim.

The correction is reasonable for publishing documentation and review evidence. closure-supplement.py starts a new scan and writes new exclusive output names; it does not rewrite the failed closure or host record. It checks both PGID and SID against all246 historical identifiers and reads stat, comm and command. Permission failures on these necessary inputs fail the new gate. When executable links are available it also checks their names; when permission denies access, it records the process PID, start ticks, PGID/SID, comm and command and expressly disclaims executable-identity verification. Recognized Julia names from comm, available exe or argv0 cause failure. Process-exit races can be skipped; the scan is a bounded observation rather than an atomic or omniscient process census. A renamed/otherwise concealed executable is not excluded by these signals. These limits must remain visible in the final handoff and must not be treated as numerical-run admission.

The initial no-unread-executable condition was stricter than needed to publish these docs; its failure remains a real preserved gate failure. The supplemental policy is explicit about its narrower claim, retains failclosed stat/command and historical-group/session checks, and rechecks boot/ref/index/no-candidate conditions. It verifies every original failed-closure content binding, the current accepted review and this correction review. Its exact-set check limits publication to the two specified documents and files actually inside this evidence directory. publication-final.py requires successful supplemental closure and unchanged closure hashes, then enforces initially untracked names, an empty index, exact staged names/blobs and whitespace checks. Both prospective scripts were read and bound but not executed by this reviewer. The final manifest, supplemental host/result and publication outputs do not yet exist and are not certified here.

The new offline closure-reviewer-check.py was saved before execution. It independently rehashed all22 failed-closure bindings and all41 accepted-review readtime bindings plus17 accepted-review evidence bindings, then checked the source correction and publication requirements. It does not import or execute any previous checker, closure, publication script or Julia code, and does not poll the host. The failed attempt and initial/revised design reviews remain byte-preserved.

Computational work and memory: no production-code change is involved, and no new numerical work, solver allocation or retained solver state is introduced. The new cold diagnostic scan and file hashing are bounded closure overhead; another set of saved JSON/review records is intentional audit evidence. No benchmark is needed. The earlier amended-design work/memory acceptance and its future implementation/measurement limitations remain unchanged.
'''
with (E/'closure-review.md').open('x') as f:f.write(text)
result['evidence_sha256'][str(E/'closure-reviewer-check.json')]=hashlib.sha256((E/'closure-reviewer-check.json').read_bytes()).hexdigest()
result['evidence_sha256'][str(E/'closure-review.md')]=hashlib.sha256((E/'closure-review.md').read_bytes()).hexdigest()
with (E/'closure-review.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(accepted=result['accepted'],checks=len(checks),bindings=len(bindings),failed=[k for k,v in checks.items() if not v])))
if not all(checks.values()):raise SystemExit(1)
