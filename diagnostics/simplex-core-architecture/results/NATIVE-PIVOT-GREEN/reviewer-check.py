"""New independent offline failed-GREEN review, human-approved 2026-10-16.
Only saved evidence/source/hash/Git/proc reads; exclusive creation of new review
artifacts. No old checker import/run, Julia, finalization, or publication execution.
"""
from pathlib import Path
import ast,collections,hashlib,json,os,subprocess,time,tomllib
D=Path(__file__).resolve().parent;Q=D.parent/'NATIVE-PIVOT-QUALIFICATION';R=D.parents[3];RUN=Q/'runs/green'
def rd(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()
def path(n):return Path(n) if Path(n).is_absolute() else R/n
def bound(z):return all(sha(path(n))==v for n,v in z['sha256'].items())
def save(p,z):
 with p.open('x') as f:json.dump(z,f,indent=2);f.write('\n')
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
checks={}
def check(n,x):
 checks[n]=bool(x)
 if not x:raise RuntimeError('Independent review failed: '+n)
a=rd(RUN/'audit.json');s=rd(RUN/'sealed.json');ad=rd(RUN/'admission.json');lp=rd(RUN/'launch-pins.json');cfg=rd(RUN/'config.json');iv=rd(RUN/'invocation.json');p=rd(RUN/'output/process.json');cur=rd(RUN/'output/current.json');sup=iv['supervisor'];b=rd(Q/'budget.json');post=rd(D/'postcheck.json');raw=tomllib.loads((RUN/'output/raw.toml').read_text());gs=raw['tests']['children'];res=[json.loads(z) for z in (RUN/'output/resources.jsonl').read_text().splitlines()]
check('original_failed_audit_98',len(a['sha256'])==98 and bound(a) and a['all_passed'] is False and a['phase']=='green' and a['error']=="RuntimeError('Inclusive limit/cleanup')" and sha(RUN/'audit.json')=='e5d0e88c3fa5e677cc4d0cd8185c887e9ed372e4cebe2e00fa285c4a621733bc')
for label,z,n in [('sealed',s,981),('launch',lp,984)]:check(label+'_inventory',len(z['files'])==len(z['inventory'])==n and set(z['files'])==set(z['inventory']) and all(sha(k)==v['sha256'] and str(Path(k).resolve())==v['resolved'] for k,v in z['inventory'].items()))
check('launch_membership',set(lp['files'])==set(s['files'])|{str(RUN/n) for n in ['sealed.json','admission.json','prehost.json']} and lp['trees']==s['trees'] and all(lp['inventory'][n]==v for n,v in s['inventory'].items()))
check('admission_982',len(ad['sha256'])==982 and ad['accepted'] is True and ad['findings']==[] and ad['phase']=='green' and ad['scope']=='exact-stage admission' and ad['pins_sha256']==sha(RUN/'sealed.json') and set(ad['sha256'])==set(s['files'])|{str(RUN/'sealed.json')} and bound(ad))
manifest=rd(Q.parent/'NATIVE-PIVOT-PREPARATION/overlay-manifest.json')['candidate'];stage=Path(cfg['stage'])
check('stage_75',len(manifest)==75 and {str(f.relative_to(stage)) for f in stage.rglob('*') if f.is_file()}=={e['destination'] for e in manifest} and all(not(stage/e['destination']).is_symlink() and (stage/e['destination']).stat().st_nlink==1 and sha(stage/e['destination'])==e['sha256']==sha(e['source']) for e in manifest))
check('preparation_review',bound(rd(Q/'preparation-pins-reviewed.json')) and bound(rd(Q/'review-final.json')))
check('environment',all(os.environ.get(k)==v for k,v in rd(Q/'environment.json').items()))
check('commands_pins',cfg==s['config'] and cfg['seconds']==60 and cfg['expected_exit']==0 and cfg['command']==p['command']==cur['command']==iv['command'] and p['pins_sha256']==cur['pins_sha256']==iv['pins_sha256']==sha(RUN/'launch-pins.json')==sha(RUN/'output/pins.json') and iv['review_sha256']==sha(RUN/'admission.json') and iv['reservation_sha256']==sha(RUN/'reservation.json') and p['pins_unchanged'] is True)
check('loading',raw['loaded']==dict(rd(Q/'loaded-paths.json'),JSimplex=str(stage/'src/JSimplex.jl')) and raw['threads']==raw['blas_threads']==1)
check('postcheck_17_13',post['all_passed'] is True and post['qualification_accepted'] is False and len(post['checks'])==17 and all(post['checks'].values()) and len(post['sha256'])==13 and bound(post))
check('raw_totals',raw['complete'] is True and raw['fatal']=='' and len(gs)==9 and [sum(z[k] for z in gs) for k in ['pass','fail','error','broken']]==[5352,0,1,0])
check('fixed_groups',b['green_assertions']==6858 and gs[2]['name']=='private_spare_copy_and_failure' and gs[2]['pass']==62 and b['test_groups'][gs[2]['name']]==1568 and all(z['pass']==b['test_groups'][z['name']] for z in gs if z is not gs[2]))
check('partial_work',len(raw['events'])==sum(raw['counts'].values())==289 and dict(collections.Counter(e['call'] for e in raw['events']))==raw['counts'] and sum(b['main'].values())+sum(b['neighbors'].values())==792 and len(raw['equations'])==34)
err=[e for e in raw['events'] if e['exception']=='MethodError'];support=(Q/'test-support.jl').read_text();rt=Path(raw['loaded']['SparseArrays']).parent
check('post_return_failure',len(err)==1 and err[0]['call']=='forward_solve' and err[0]['number']==8 and err[0]['after']=={'kind':'Vector{Float64}'} and err[0]['output']==['3ff0000000000000','3fcfffffffffffff'] and 'rhs' not in err[0] and err[0]['before']==err[0]['after_failure'] and all(t in gs[2]['failures'][0] for t in ['zero(::String)','test-support.jl:35','SparseVector{Float64, Int64}','_map_zeropres!']))
check('source_cause',support.index('value=f(args...;kwargs...)')<support.index('e["after"]=state(value)')<support.index('e["output"]=scalar.(value)')<support.index('e["rhs"]=scalar.(args[2])')<support.index('catch error') and 'column = matrix[:,1] + matrix[:,2]/4' in (Q/'tests-observed.jl').read_text() and 'if isfixed || _isnotzero(Cx)' in (rt/'higherorderfns.jl').read_text() and '_isnotzero(x) = iszero(x) !== true' in (rt/'SparseArrays.jl').read_text())
check('exit_no_timeout',p['returncode']==sup['returncode']==1 and p['reason']=='exit1' and sup['accepted'] is False and 0<iv['elapsed_seconds']<60 and not any(sup[k] for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']) and 'cleanup_error' not in sup)
check('audit_predicate',"sup['accepted'] is True" in (Q/'audit_reviewed.py').read_text() and "record['accepted']=record['returncode']==0" in (Q/'supervisor.py').read_text())
check('resources',len(res)==28 and min(z['available_kib'] for z in res)==21871576 and all(z['swap_used_kib']==0 and z['available_kib']>=6*1024**2 for z in res+[p['terminal_memory']]) and p['child_maxrss_kib']==783296)
check('identity',p['runner']==cur['runner']==sup['guard_identity'] and p['child']==cur['child'] and (p['runner']['pid'],p['runner']['pgid'],p['runner']['sid'],p['runner']['start_ticks'])==(238457,238457,238457,14328901) and (p['child']['pid'],p['child']['pgid'],p['child']['sid'],p['child']['start_ticks'])==(238458,238458,238458,14328949) and all(z['boot_id']==s['boot_id'] and z['command'] for z in [p['runner'],p['child']]))
check('no_cost_clean_tracked',{z.name for z in (Q/'runs').iterdir()}=={'red','green'} and not git('diff','--name-only') and not git('diff','--cached','--name-only'))
draft_hashes={'REPORT.md':'4259ead12019c6af98bf8947de5aa1374f557e29cd85bf01c0386342c367bdc7','finalize.py':'ed314a45e657f660d0de26827b91fc67d3c7398330a32bce6456a6335c78a2b5','publication.py':'e2da898fbabfbcb9bfea557e325fd665046748efe9bf103dce16a4120475ee4f','continuation-text.md':'349fa64cd328eacebc541f237367b3e30cf15f99c891e527445150e47a863999'}
check('read_only_reviewed_drafts_unchanged',all(sha(D/n)==v for n,v in draft_hashes.items()))
for n in ['finalize.py','publication.py']:ast.parse((D/n).read_text())
STATUS=R/'diagnostics/simplex-core-architecture/STATUS.md';ROAD=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md';preserved={str(STATUS):D/'STATUS.md.before-GREEN',str(ROAD):D/'roadmap.md.before-GREEN'};maps=[]
def walk(rec,obj):
 if isinstance(obj,dict):
  for k,v in obj.items():
   full=str(path(k))
   if full in preserved:
    value=v if isinstance(v,str) else v.get('sha256') if isinstance(v,dict) else None
    if value==sha(preserved[full]):maps.append(dict(record=str(rec.relative_to(R)),key=k,sha256=value))
   walk(rec,v)
 elif isinstance(obj,list):
  for v in obj:walk(rec,v)
for f in sorted(list(Q.rglob('*.json'))+list((D.parent/'NATIVE-PIVOT-RED').glob('*.json'))+list(D.glob('*.json'))):walk(f,rd(f))
check('synthetic_continuation_mapping',len(maps)==12 and all(sha(n)==sha(v) for n,v in preserved.items()))
ids=set(rd(RUN/'posthost.json')['groups']);matches=[];unreadable=[];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
for f in Path('/proc').glob('[0-9]*'):
 try:
  z=(f/'stat').read_text().rsplit(')',1)[1].split();comm=(f/'comm').read_text().strip();exe=''
  try:exe=str((f/'exe').resolve(strict=True))
  except PermissionError:unreadable.append(int(f.name))
  except FileNotFoundError:pass
  if int(z[2]) in ids or int(z[3]) in ids or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):matches.append(dict(pid=int(f.name),pgid=int(z[2]),sid=int(z[3]),start_ticks=int(z[19]),comm=comm,exe=exe,command=(f/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,ProcessLookupError):pass
h=dict(time=time.time(),boot_id=boot,groups=sorted(ids),matches=matches,unreadable_exe_pids=unreadable,head=git('rev-parse','HEAD'),master=git('rev-parse','master'),reviewer_pid=os.getpid(),scope='All /proc stat groups AND sessions; Julia names/readable executable paths; inaccessible executable symlinks remain a visibility limit')
check('fresh_host_212',len(ids)==212 and {238457,238458}<=ids and not matches and h['boot_id']==s['boot_id'] and h['head']==s['head'] and h['master']==s['master'])
save(D/'reviewer-host.json',h)
paths=[Path(__file__),D/'reviewer-host.json',D/'REPORT.md',D/'postcheck.json',D/'postcheck.py',D/'postcheck-host.json',D/'finalize.py',D/'publication.py',D/'continuation-text.md',rt/'higherorderfns.jl',rt/'SparseArrays.jl',RUN/'audit.json',R/'docs/superpowers/plans/2026-10-15-native-pivot-policy.md']
save(D/'reviewer-check.json',dict(all_passed=True,diagnostic_accepted=True,qualification_accepted=False,checks=checks,sha256={str(f):sha(f) for f in paths},synthetic_continuation_mappings=maps,scope='Independent failed-stage diagnostic preservation checks only; no numerical execution'))
finding='Unresolved observer serialization failure: test-support.jl:35 broadcasts scalar over a SparseVector RHS after the real forward_solve has returned a dense Vector. Sparse broadcast calls iszero on String tokens and throws zero(::String), aborting private_spare_copy_and_failure after 62/1568 assertions. Required GREEN counts remain unmet (5352/6858 passes, 289/792 calls, 34/324 equations); candidate qualification, cost and Task3 remain blocked.'
record=dict(accepted=False,diagnostic_accepted=True,qualification_accepted=False,scope='failed-stage diagnostic',phase='green',findings=[finding],pins_sha256=sha(RUN/'audit.json'),sha256=dict(a['sha256'],**{str(RUN/'audit.json'):sha(RUN/'audit.json')}))
check('result_exact_99',len(record['sha256'])==99 and set(record['sha256'])==set(a['sha256'])|{str(RUN/'audit.json')} and bound(record))
save(RUN/'result-review.json',record)
text='''# Independent failed GREEN diagnostic review

Diagnostic preservation and causal interpretation are ACCEPTED. GREEN qualification
is NOT ACCEPTED; the only admitted attempt is CONSUMED. The original audit FALSE,
raw error, failed exit and all frozen source/run evidence are preserved unchanged.

## Unresolved finding

The observer fails at test-support.jl:35 while applying scalar.(args[2]) to the
SparseVector RHS from tests-observed.jl:59-60. The eighth forward_solve event has
already recorded after.kind=Vector{Float64} and two output tokens, but no rhs.
Source order and the saved stack show the real solve returned before diagnostic
sparse broadcast called iszero on String tokens and raised zero(::String). The
observer catch also covers its recording work; exception/after_failure therefore
do not establish a backend throw. Full solver correctness and observer neutrality
remain unqualified.

Raw: 5352 passes, 0 failures, 1 error, 0 broken. private_spare_copy_and_failure
completed 62 of 1568 required assertions; 1506 are unfulfilled. All eight other
groups meet their fixed assertion counts. Only 289 of 792 selected calls and 34
of 324 helper equations exist. complete=true records driver serialization, not
successful qualification. No assertion, equation, safeguard or count is waived.

## Evidence and process interpretation

Independently rehashed all 981 sealed entries, 984 launch entries, exact 982
admission bindings, 98 original audit bindings, and 75 candidate-stage files with
source/digest identity. Offline preparation/review, loading environment, command,
actual loaded paths and the author's 17 checks/13 bindings match. The result JSON
contains precisely the 98 audit keys plus audit.json (99), with pins_sha256 equal
to the original audit hash. Supplementary bindings are separate.

Child exit1 and guard return1 reject supervisor.accepted. The original auditor's
Inclusive limit/cleanup message is a combined predicate; no timeout, kill flag or
cleanup error occurred. Inclusive elapsed 28.980952097976115 seconds is below 60
and includes import/compilation/output; it is not a performance measurement.
28 samples have minimum available RAM 21871576 KiB and zero swap; terminal RAM
22455520 KiB, child resident high-water 783296 KiB. Partial events are not a full
native work or allocation ledger.

Fresh independent process closure is recorded in reviewer-host.json: all 212
historical groups AND sessions, Julia names/readable executable paths, matching
HEAD ec3b19f and master 6f68e24 and boot identity. Runner 238457/start14328901 and
child 238458/start14328949 are linked by the original current/process/supervisor
records. Inaccessible system executable links are explicitly retained as a
visibility limit. A saved host snapshot never replaces a future launch preflight.

## Draft continuation and AGENTS review

Read-only assessment of REPORT.md, finalize.py, publication.py and continuation-text.md
found no additional actionable issue beyond the known observer failure. The
finalizer requires diagnostic acceptance with accepted=false and qualification=false;
its acceptance cannot turn this run into a GREEN PASS. Synthetic inspection finds
12 exact current STATUS/roadmap bindings mapping to preserved before-GREEN copies.
Older mappings remain. Exact publication-name membership must still be checked by
the later closure; finalization and publication scripts were not executed here.

No production changes were introduced and no unnecessary new production work,
allocations or retained memory were found in this diagnostic-only step. The faulty
diagnostic broadcast allocates text tokens/containers and can throw after numerical
work; this is avoidable instrumentation work with incomplete sparse handling.
A future explicit dense token capture must account for O(n) conversion and storage,
preserve values/order and numerical inputs, and review all similar sites including
equations. It remains UNIMPLEMENTED and UNQUALIFIED. No warmup, benchmark, tolerance
change or speedup claim is justified by this failed run.

Next is a separate OFFLINE observer/serialization correction, focused sparse/dense
regression coverage and independent review, followed by a newly labelled exact
admission before another GREEN. Existing stage/reservation/output cannot be reused.
No automatic retry, cost run, Task3 or production promotion is authorized by this
review. Broader plan stays open and all earlier failures remain.

Only a NEW Python source/hash/raw/proc checker ran, after the explicit human approval
“Schvaluji offline kontrolu a uložení review”. No Julia, numerical reproducer, old
checker/auditor/launcher, finalizer or publication script was executed. Previously
rejected write attempts created no files; this approval allowed the new review
artifacts only.
'''
with (RUN/'result-review.md').open('x') as f:f.write(text)
supp=paths+[D/'reviewer-check.json',RUN/'result-review.json',RUN/'result-review.md']
save(D/'reviewer-supplementary-bindings.json',dict(scope='Supplementary diagnostic review bindings; does not extend or alter exact audit+1 result-review membership',diagnostic_accepted=True,qualification_accepted=False,sha256={str(f):sha(f) for f in supp}))
assert bound(rd(D/'reviewer-supplementary-bindings.json')) and bound(rd(RUN/'result-review.json'))
print(json.dumps(dict(all_passed=True,checks=len(checks),host_groups=len(ids),host_time=h['time'],inaccessible_exe=len(unreadable),result_bindings=len(record['sha256']),supplementary_bindings=len(supp),diagnostic_accepted=True,qualification_accepted=False)))
