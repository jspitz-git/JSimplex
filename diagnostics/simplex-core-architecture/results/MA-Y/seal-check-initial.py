"""Independent MA-Y prelaunch checker: read-only evidence/host review, exclusive report.
No imported project module, Julia invocation, previous checker, or launcher main.
"""
from pathlib import Path
import ast,hashlib,json,subprocess,time,tomllib
R=Path.cwd();X=R/'diagnostics/simplex-core-architecture/results/MA-X';Y=X.with_name('MA-Y');B=X.parent
checks={};bindings={}
def rd(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def ck(k,v):checks[k]=v is True
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def fn(p,n):return next(v for v in ast.parse(Path(p).read_text()).body if isinstance(v,ast.FunctionDef) and v.name==n)
pins=rd(X/'pins.json');inv=pins['inventory'];required=rd(X/'required-paths.json');context=rd(X/'launch-context.json');prep=rd(X/'admission-review.json');entry=rd(Y/'entry.json');host=rd(Y/'host.json');m=rd(X/'source-map.json')
started=time.monotonic();bad=[];total_bytes=0
for p,v in inv.items():
 q=Path(p);total_bytes+=q.stat().st_size
 if sha(q)!=v['sha256'] or str(q.resolve(strict=True))!=v['resolved']:bad.append(p)
ck('fresh4375_hashes_and_realpaths',len(inv)==4375 and not bad)
ck('unique_exact_manifest',len(set(required))==len(required) and len(set(pins['files']))==len(pins['files']) and set(required)==set(inv)==set(pins['files']))
walked=set(pins['files']);badtrees=[]
for root in pins['trees']:
 q=Path(root)
 if not q.is_dir() or q.is_symlink():badtrees.append(str(q))
 for p in q.rglob('*'):
  if p.is_symlink() and (p.is_dir() or not p.exists()):badtrees.append(str(p))
  if p.is_file():walked.add(str(p))
ck('fresh73_trees_membership_symlinks',len(pins['trees'])==73 and walked==set(inv) and not badtrees)
manifest_seconds=time.monotonic()-started
ck('preparation_acceptance',prep['accepted'] is True and prep['findings']==[] and prep['pins_sha256']==sha(X/'pins.json') and len(prep['computed_checks'])==85 and all(v is True for v in prep['computed_checks'].values()))
for name in ('admission-review.json','review-check.json','closure.json','publication.json','continuation.json'):
 o=rd(X/name);ck('fresh_bindings_'+name,all(sha(p)==v for p,v in o['sha256'].items()))
ck('fresh_entry19_bindings',entry['all_passed'] is True and len(entry['checks'])==19 and all(v is True for v in entry['checks'].values()) and all(sha(p)==v for p,v in entry['sha256'].items()))
ck('context_limits_permission',context['standing_short_run_permission'] is True and type(context['maximum_processes']) is int and context['maximum_processes']==3 and type(context['maximum_seconds_per_process']) is int and context['maximum_seconds_per_process']==90 and context['total_cap_seconds']==270 and context['no_retry'] is True)
ck('context_hashlinks',context['host_sha256']==sha(Y/'host.json') and context['pins_sha256']==sha(X/'pins.json') and context['preparation_review_sha256']==sha(X/'admission-review.json'))
refs={k:git(*a) for k,a in {'head':['rev-parse','HEAD'],'master':['rev-parse','master'],'branch':['branch','--show-current'],'remote':['ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture']}.items()}
ck('fresh_exact_published_refs',refs==context['refs']==host['refs'] and refs['head']=='aac5075afcf45f527996edf1a77972ccb48b6cea' and refs['master']=='6f68e24e8ddac42b948da8fcc2d636c010751194' and refs['branch']=='codex/simplex-core-architecture' and set(refs['remote'].splitlines())=={refs['head']+'\trefs/heads/'+refs['branch'],refs['master']+'\trefs/heads/master'})
ck('tracked_and_stage_clean',not git('diff','--name-only','HEAD') and not git('diff','--cached','--name-only'))
pub=rd(X/'publication.json');ck('published_exact45_blobs',len(pub['exact_names'])==45 and set(git('diff-tree','--no-commit-id','--name-only','-r','HEAD').splitlines())==set(pub['exact_names']) and all(git('rev-parse','HEAD:'+n)==git('hash-object','--',n) for n in pub['exact_names']))
ck('source514_and_protected6',len(host['master_identity'])==514 and len(host['protected'])==6 and all(sha(R/p)==v for p,v in host['master_identity'].items()) and all(sha(p)==v for p,v in host['protected'].items()))
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();groups=context['groups'];matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  f=(p/'stat').read_text().rsplit(')',1)[1].split();exe=(p/'exe').resolve().name
  if int(f[2]) in groups or int(f[3]) in groups or exe.startswith('julia'):
   matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'),boot_id=boot))
 except (FileNotFoundError,ProcessLookupError):pass
ck('fresh_boot170groups_ORsessions_noJulia',boot==context['boot_id']==host['boot_id'] and len(groups)==len(set(groups))==170 and groups==host['groups']==rd(X/'host.json')['groups'] and not matches)
mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()};memory=dict(available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree'])
ck('fresh_memory',memory['available_kib']>=6*1024**2 and 0<=memory['swap_used_kib']<=1024**2)
ck('no_reservation_or_output',not any((X/n).exists() for n in ['sequence-reservation.json','aggregate.json','numerical-review.json','numerical-review.md',*[f'{prefix}-{i}{suffix}' for i in (1,2,3) for prefix,suffix in [('run',''),('reservation','.json'),('invocation','.json'),('prelaunch','.json'),('posthost','.json'),('audit','.json'),('launcher','.log')]]))
maps=rd(Y/'continuation-map.json')['old_bindings'];ck('six_beforecopy_maps',len(maps)==6 and all(sha(z['preserved'])==z['sha256']==rd(z['source'])['sha256'][z['path']] for z in maps))
driver=(X/'driver.jl').read_text();restore=driver
for i,e in enumerate(reversed(m['driver_edits'])):
 ck('driver_inverse_unique_'+str(i),restore.count(e['new'])==1);restore=restore.replace(e['new'],e['old'])
ck('driver_exact_inverse',restore==Path(m['driver_source']).read_text() and sha(m['driver_source'])==m['driver_source_sha256'])
for name in m['unchanged_functions']:ck('original_auditor_AST_'+name,ast.dump(fn(X/'audit.py',name))==ast.dump(fn(m['original_validator'],name)))
for n,v in m['byte_exact_copies'].items():ck('MA_V_byte_exact_'+n,sha(X/n)==sha(v['source'])==v['sha256'])
ck('candidate_instrumented_fixed',sha(m['candidate'])==m['candidate_sha256']=='50b1421e06eabed34cbc0b9fd50bb1a0977aada3fe9159a4e005513cbefca98b' and sha(m['instrumented'])==m['instrumented_sha256'])
fixtures=tomllib.loads(Path(m['fixtures']).read_text());cases=fixtures['cost_cases'];schedule=rd(X/'schedule.json')
ck('exact52_original_costs',schedule['costs']==cases and len(cases)==52 and sum(c['eligible'] for c in cases)==36 and len([c for c in cases if c['scalar']=='Rational{BigInt}'])==2)
commands=rd(X/'commands.json');wrapper='/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh'
ck('exact3_commands',set(commands)=={'1','2','3'} and all(commands[str(i)]==['/bin/bash',wrapper,'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+str(B/'MA-R/environment'),str(X/'driver.jl'),str(i),str(X/f'run-{i}')] for i in (1,2,3)))
ck('wrapper_and_runtime_pinned',wrapper in inv and '/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/bin/julia' in inv and '--startup-file=no' in Path(wrapper).read_text())
ck('failclosed_no_asserts',not any(isinstance(n,ast.Assert) for name in ('launcher.py','audit.py','supervisor.py','guard.py') for n in ast.walk(ast.parse((X/name).read_text()))))
critical=[X/n for n in ('pins.json','required-paths.json','launch-context.json','admission.md','admission-review.md','admission-review.json','review-check.py','review-check.json','source-map.json','schedule.json','commands.json','driver.jl','audit.py','launcher.py','supervisor.py','guard.py','offline-tests.json','source-check.json','supervisor-tests-final.json')]+[Y/n for n in ('entry.py','entry.json','host.json','continuation-map.json','STATUS.md.before-MA-Y','roadmap.md.before-MA-Y','seal-check.py')]+[Path(m[n]) for n in ('candidate','instrumented','reference','tests','fixtures','driver_source','original_validator')]+[Path(wrapper),R/'AGENTS.md',R/'docs/superpowers/plans/2026-10-14-ma-denselu-complete-qualification.md']
bindings={str(p):sha(p) for p in critical}
report=dict(all_passed=all(checks.values()),checks=checks,refs=refs,boot_id=boot,groups=groups,matches=matches,memory=memory,manifest_files=len(inv),manifest_trees=len(pins['trees']),manifest_bytes=total_bytes,manifest_seconds=manifest_seconds,sha256=bindings,scope='Independent prelaunch read-only seal checks; no Julia or old checker execution')
with (Y/'seal-check.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=report['all_passed'],checks=len(checks),failed=[k for k,v in checks.items() if not v],bindings=len(bindings),manifest_seconds=manifest_seconds,memory=memory)))
if not report['all_passed']:raise SystemExit(1)
