"""Exclusive S5-V source/evidence collector. No prior scripts or Julia executed."""
from pathlib import Path
import hashlib,json,re,subprocess,time,tomllib
R=Path.cwd();M=Path('/home/jspitz/JSimplex.jl');D=R/'diagnostics/simplex-core-architecture';H=Path(__file__).resolve().parent;U=H.parent/'S5-U';T=H.parent/'S5-T'
cache={}
def sha(p):
 p=Path(p)
 if p not in cache:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):h.update(b)
  cache[p]=h.hexdigest()
 return cache[p]
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def git(*args,cwd=R):return subprocess.check_output(['git','-C',str(cwd),*args],text=True)
def oldpath(k,v):
 if k in [str(r/'test/simplex_precision_tests.jl') for r in (R,M)] and v=='b864b39bde32ee9a1c2b85ef57fdc6efd6d69a59c3a56571cdf62d8659bf4ba5':return U/'original-test.jl'
 if k==str(D/'STATUS.md'):return U/'STATUS.md.before-U'
 if k==str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'):return U/'2026-10-11-simplex-core-architecture.md.before-U'
 return Path(k)
entry={}
for stage,n in [('master',1512),('green',1489)]:
 inv=read(U/stage/'pins.json')['inventory'];entry[stage+'_fullpins']=len(inv)==n and all(sha(oldpath(k,v['sha256']))==v['sha256'] for k,v in inv.items())
 a=read(U/stage/'audit.json');p=read(U/stage/'postcheck.json');entry[stage+'_audit_post']=len(a['checks'])==25 and a['all_passed'] is True and all(v is True for v in a['checks'].values()) and len(p['checks'])==9 and p['all_passed'] is True and all(v is True for v in p['checks'].values())
 entry[stage+'_raw8_inv3']=len(a['raw_sha256'])==8 and all(sha(R/'.superpowers/simplex-core-architecture/S5-U'/f'{stage}-1'/k)==sha(U/stage/'portable'/k)==v for k,v in a['raw_sha256'].items()) and len(a['invocation_sha256'])==3 and all(sha(k)==v for k,v in a['invocation_sha256'].items())
entry['T891']=len(read(T/'pins.json')['sha256'])==891 and all(sha(oldpath(k,v))==v for k,v in read(T/'pins.json')['sha256'].items())
cl=read(U/'closure.json');entry['U_closure24_123']=len(cl['checks'])==24 and cl['all_passed'] is True and all(v is True for v in cl['checks'].values()) and len(cl['sha256'])==123 and all(sha(k)==v for k,v in cl['sha256'].items())
pub=read(U/'publication-check.json');entry['U_publication6']=len(pub['checks'])==6 and pub['all_passed'] is True
st=read(U/'staged-files.json')['sha256'];entry['U_complete126']=len(st)==125 and all(sha(R/k)==v and hashlib.sha256(subprocess.check_output(['git','show','a4f4cca:'+k])).hexdigest()==v for k,v in st.items()) and set(git('diff-tree','--no-commit-id','--name-only','-r','a4f4cca').splitlines())==set(st)|{str((U/'staged-files.json').relative_to(R))}
assert all(entry.values());dump(H/'entry.json',dict(checks=entry,all_passed=True))
groups={23249,23257,49081,49084,52772,52774,53479,53481,60706,60708,63808,63815,64420,64422,71824,71826,75902,75907,76742,76746};matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();v=s[s.rindex(')')+2:].split()
  if int(v[2]) in groups or (p/'comm').read_text().strip()=='julia':matches.append(dict(pid=int(p.name),pgid=int(v[2]),start_ticks=int(v[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except FileNotFoundError:pass
users=read(U/'host-before.json')['user_hashes'];assert all(sha(k)==v for k,v in users.items()) and not matches
host=dict(groups=sorted(groups),matches=matches,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),refs={str(p):git('rev-parse','HEAD',cwd=p).strip() for p in (R,M)},remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'),user_hashes=users,time_ns=time.time_ns());dump(H/'host.json',host)
tests=['test/simplex_start_tests.jl','test/simplex_start_state_tests.jl','test/simplex_start_guard_tests.jl','test/simplex_start_exact_tests.jl','test/simplex_phase_one_completion_tests.jl']
sources=['src/simplex_start.jl','src/simplex.jl','src/simplex_diagnostics.jl','src/simplex_recovery.jl','src/simplex_driver.jl','src/simplex_numerics.jl','src/dual_simplex.jl','src/primal_simplex.jl','src/simplex_phase_one.jl','src/refactorization_policy.jl','src/hypersparse_pipeline.jl']
paths={Path(__file__).resolve(),H/'entry.json',H/'host.json',R/'AGENTS.md',R/'docs/superpowers/plans/2026-10-13-crash-fallback-ownership-contract.md'}|{R/x for x in tests+sources}|set(map(Path,users))
rows=[];comparisons=[];blocks=[]
for file in tests:
 text=(R/file).read_text();starts=list(re.finditer(r'@testset "([^"]+)" begin',text))
 for i,x in enumerate(starts):
  end=starts[i+1].start() if i+1<len(starts) else len(text);value=text[x.start():end]
  blocks.append(dict(file=file,name=x.group(1),start_line=text[:x.start()].count('\n')+1,end_offset=end,sha256=hashlib.sha256(value.encode()).hexdigest(),text=value,scope='Exact lexical slice through before next testset; may include intervening module/helper syntax.'))
for run in ['38142752357','38149970679']:
 meta=D/f'results/S6-A/ci-inventory-1-{run}-metadata.json';md=read(meta);log=R/f'.superpowers/simplex-core-architecture/S6-A/ci-inventory-1/{run}-failed.log';lines=log.read_text().splitlines();paths|={meta,log}
 for b in blocks:
  found=[(i+1,l) for i,l in enumerate(lines) if b['name'] in l and '|' in l];assert len(found)==1,b['name']
  no,raw=found[0];clean=re.sub(r'(?:\x1b|\^\[)\[[0-9;]*m','',raw);nums=clean.split('|',1)[1].split();assert len(nums)==3 and nums[0]==nums[1] and nums[0].isdigit(),clean
  rows.append(dict(run=run,head=md['headSha'],conclusion=md['conclusion'],file=b['file'],name=b['name'],line=no,raw=raw,normalized=clean,passed=int(nums[0]),total=int(nums[1])))
 for file in tests+sources:
  old=subprocess.check_output(['git','show',md['headSha']+':'+file]);comparisons.append(dict(run=run,file=file,equal=old==(R/file).read_bytes(),historical_sha256=hashlib.sha256(old).hexdigest(),current_sha256=sha(R/file)))
s=(R/'src/simplex_start.jl').read_text();j=(R/'src/simplex.jl').read_text();d=(R/'src/simplex_diagnostics.jl').read_text();du=(R/'src/dual_simplex.jl').read_text()
f=s[s.index('function _crash_fallback'):s.index('function _crash_refactor!')];impl=s[s.index('function _crash_workspace_impl'):s.index('function _crash_workspace(initial')];event=d[d.index('function _diagnostic_event!(d::'):]
hits=[]
for p in sorted((R/'test').rglob('*.jl')):
 for i,line in enumerate(p.read_text().splitlines()):
  if ':crash_fallback' in line:hits.append(dict(file=str(p.relative_to(R)),line=i+1,text=line))
checks={
 'all24_testset_slices':len(blocks)==24,
 'all48_historical_rows':len(rows)==48,
 'historical_runs_failed':all(x['conclusion']=='failure' for x in rows),
 'all32_source_test_comparisons_equal':len(comparisons)==32 and all(x['equal'] for x in comparisons),
 'fallback_merges_before_event':f.index('initial.iterations = max')<f.index('initial.refactorizations = max')<f.index('_simplex_event!')<f.index('return initial,expired'),
 'fresh_trial_shared_progress':'trial = initialize_workspace(initial.problem,initial.options;progress=initial.progress)' in impl,
 'trial_attempt_charged_before_factory':impl.index('initial.refactorizations += 1')<impl.index('trial = initialize_workspace'),
 'trial_recovery_active_after_initialization':impl.index('trial = initialize_workspace')<impl.index('trial.scratch.recovery_active = true'),
 'default_basis_owned':'Basis(collect(column_count + 1:variable_count), states, Val(:owned))' in j,
 'default_factor_fresh':'factorization = _basis_factorization(initial_basis, typed_options)' in j,
 'bounds_owned_costs_copied':'lower = vcat(problem.column_lower, problem.row_lower)' in j and 'copyto!(costs, 1, problem.objective, 1, column_count)' in j,
 'event_record_before_observer':event.index('record_event!')<event.index('d.observer(reason, state)')<event.index('throw(DiagnosticObserverFailure(exception))'),
 'stop_original_cause': 'stop.exception = exception\n        rethrow()' in du and 'stop isa _StopCallback && (stop.exception=exception)' in impl,
 'refactor_finally_attempt_count':'ws.refactorizations = max(ws.refactorizations,before+1)' in s,
 'final_acceptance_order':impl.index('_invalidate_basis_checkpoints!(trial)')<impl.index('final_violation = primal_infeasibility(trial)')<impl.index('reset_devex!(trial)')<impl.index('_simplex_event!(trial,:crash_accepted)')<impl.index('return trial,false'),
 'accepted_partial_not_always_feasible':'accepted &= policy.phase_one || trial.options.algorithm != :primal || iszero(final_violation)' in impl,
 'public_basis_copy':'return Basis(workspace.basis.basic_indices,workspace.basis.states)' in s and 'new(Int.(basic_indices), collect(states))' in j,
 'four_literal_fallback_tests_are_counts':len(hits)==4 and all('event_count(d,:crash_fallback) == 1' in x['text'] for x in hits),
 'observer_throw_events_exclude_fallback':'for event in (:phase_crash,:crash_pivot,:crash_accepted)' in (R/tests[2]).read_text(),
 'final_refactor_interruption_already_covered':'Crash interruption after final factorization uses no fresh budget' in (R/tests[1]).read_text(),
 'no_production_test_diff_from_master':not git('diff','master','--','src','test','.github','Project.toml'),
}
excerpts=[];(H/'excerpts').mkdir()
for name,file,value in [('start','src/simplex_start.jl',s),('initialization','src/simplex.jl',j[j.index('function _initialize_workspace_state'):j.index('function primal_infeasibility_summary')]),('events','src/simplex_diagnostics.jl',d[d.index('function record_event!'):]),('stop','src/dual_simplex.jl',du[:du.index('_numerical_failure()')])]:
 p=H/'excerpts'/f'{name}.txt'
 with p.open('x') as out:out.write(value)
 paths.add(p);excerpts.append(dict(path=str(p),source=file,start_line=(R/file).read_text()[:(R/file).read_text().index(value)].count('\n')+1,sha256=sha(p)))
for n in ['S5-ENTRY.md','S5-RESTORATION.md','S5-INVENTORY-NOTES.md','S5-BASIS-INITIALIZATION-STOP-TEST-INTEGRATION.md','S5-BASIS-INITIALIZATION-STOP-TEST-INTEGRATION-REVIEW.md']:paths.add(D/n)
for p in U.rglob('*'):
 if p.is_file() and p.suffix in ('.json','.md'):paths.add(p)
for k in read(U/'master/pins.json')['inventory']:
 if k.endswith('.so') or '/bin/julia' in k:paths.add(Path(k))
result=dict(checks=checks,all_passed=all(checks.values()),blocks=blocks,rows=rows,comparisons=comparisons,fallback_test_hits=hits,excerpts=excerpts,sha256={str(p):sha(p) for p in sorted(paths)},time_ns=time.time_ns(),scope='Source/evidence only. Existing covered boundaries reused; one post-work fallback-observer exception composition unqualified, not defect or runtime claim.')
dump(H/'evidence.json',result);print(json.dumps(dict(checks=checks,pins=len(paths),rows=len(rows),pass_per_run={run:sum(x['passed'] for x in rows if x['run']==run) for run in ['38142752357','38149970679']})));assert result['all_passed']
