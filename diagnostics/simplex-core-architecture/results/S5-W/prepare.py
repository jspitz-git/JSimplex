"""Exclusive S5-W offline evidence preparation; saved before execution. No Julia."""
from pathlib import Path
import hashlib,json,re,subprocess,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';H=Path(__file__).resolve().parent;V=H.parent/'S5-V';U=H.parent/'S5-U';M=Path('/home/jspitz/JSimplex.jl');cache={}
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
def git(*args):return subprocess.check_output(['git',*args],text=True)
def bindings(x):return all(sha(k)==v for k,v in x.items())
ve=read(V/'evidence.json');vi=read(V/'independent.json');vc=read(V/'closure.json');vp=read(V/'publication-check.json');vs=read(V/'staged-files.json')['sha256']
entry=dict(V166=len(ve['sha256'])==166 and bindings(ve['sha256']),V21=len(ve['checks'])==21 and ve['all_passed'] is True and all(ve['checks'].values()),V9_7=len(vi['checks'])==9 and vi['all_passed'] is True and len(vi['sha256'])==7 and bindings(vi['sha256']),V12_24=len(vc['checks'])==12 and vc['all_passed'] is True and len(vc['sha256'])==24 and bindings(vc['sha256']),Vpublication7=len(vp['checks'])==7 and vp['all_passed'] is True,V27=len(vs)==26 and bindings({str(R/k):v for k,v in vs.items()}) and set(git('diff-tree','--no-commit-id','--name-only','-r','48771ac').splitlines())==set(vs)|{str((V/'staged-files.json').relative_to(R))} and all(hashlib.sha256(subprocess.check_output(['git','show','48771ac:'+k])).hexdigest()==v for k,v in vs.items()),Vreview='Unresolved findings: []' in (V/'review.md').read_text())
entry['blocks24_rows48']=len(ve['blocks'])==24 and len(ve['rows'])==48 and all(b['text'] in (R/b['file']).read_text() and hashlib.sha256(b['text'].encode()).hexdigest()==b['sha256'] for b in ve['blocks']) and all((R/f".superpowers/simplex-core-architecture/S6-A/ci-inventory-1/{x['run']}-failed.log").read_text().splitlines()[x['line']-1]==x['raw'] for x in ve['rows'])
entry['comparisons32']=len(ve['comparisons'])==32 and all(hashlib.sha256(subprocess.check_output(['git','show',read(D/f"results/S6-A/ci-inventory-1-{x['run']}-metadata.json")['headSha']+':'+x['file']])).hexdigest()==sha(R/x['file'])==x['historical_sha256'] for x in ve['comparisons'])
entry['failed511each']=all(sum(x['passed'] for x in ve['rows'] if x['run']==run)==511 and all(x['conclusion']=='failure' for x in ve['rows'] if x['run']==run) for run in ['38142752357','38149970679'])
def old(k,v):
 if k in [str(r/'test/simplex_precision_tests.jl') for r in (R,M)] and v=='b864b39bde32ee9a1c2b85ef57fdc6efd6d69a59c3a56571cdf62d8659bf4ba5':return U/'original-test.jl'
 if k==str(D/'STATUS.md'):return U/'STATUS.md.before-U'
 if k==str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'):return U/'2026-10-11-simplex-core-architecture.md.before-U'
 return Path(k)
for stage,n in [('master',1512),('green',1489)]:
 inv=read(U/stage/'pins.json')['inventory'];entry[stage+'_pins']=len(inv)==n and all(sha(old(k,v['sha256']))==v['sha256'] for k,v in inv.items())
t=read(H.parent/'S5-T/pins.json')['sha256'];entry['T891']=len(t)==891 and all(sha(old(k,v))==v for k,v in t.items())
umaps={str(D/'STATUS.md'):V/'STATUS.md.before-V',str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'):V/'2026-10-11-simplex-core-architecture.md.before-V'}
entry['Uclosure123']=all(sha(umaps.get(k,k))==v for k,v in read(U/'closure.json')['sha256'].items())
dump(H/'entry.json',dict(checks=entry,all_passed=all(entry.values())));assert all(entry.values())
groups=set(read(V/'host.json')['groups']);matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();v=s[s.rindex(')')+2:].split()
  if int(v[2]) in groups or (p/'comm').read_text().strip()=='julia':matches.append(dict(pid=int(p.name),pgid=int(v[2]),start_ticks=int(v[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except FileNotFoundError:pass
users=read(V/'host.json')['user_hashes'];assert not matches and bindings(users)
host=dict(groups=sorted(groups),matches=matches,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),refs=git('rev-parse','HEAD','master').splitlines(),remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'),user_hashes=users,time_ns=time.time_ns());assert host['refs']==['48771ac4318ada0bff6fef35157ba03b95d99d07','2b546e946ddb7fdb6c0092df9cc19f566e301aa2'];dump(H/'host.json',host)
s=(R/'src/simplex_start.jl').read_text();j=(R/'src/simplex.jl').read_text();d=(R/'src/simplex_diagnostics.jl').read_text();n=(R/'src/simplex_numerics.jl').read_text();q=(R/'src/simplex_recovery.jl').read_text();o=(R/'src/options.jl').read_text();du=(R/'src/dual_simplex.jl').read_text()
b=next(b for b in ve['blocks'] if b['name']=='Crash interruption after final factorization uses no fresh budget');fixture=b['text'];assert fixture.count('@test ')==6
with (H/'original-testset.txt').open('x') as f:f.write(fixture)
fallback=s[s.index('function _crash_fallback'):s.index('function _crash_refactor!')];final=s[s.index('        _invalidate_basis_checkpoints!(trial)'):s.index('        final_violation =')];event=d[d.index('function _diagnostic_event!(d::'):]
checks=dict(existing_six_assertions=fixture.count('@test ')==6,exact_existing_construction='p = LinearProblem(spdiagm(0=>[2.0,3.0]),ones(2);row_lower=[2.0,3.0])' in fixture,unchanged_default_options='initial = JSimplex.initialize_workspace(p,SolverOptions(verbose=false);progress)' in fixture,unchanged_policy='policy = JSimplex.NumericalPolicy(Float64;crash=true)' in fixture,existing_stop='JSimplex._crash_workspace(initial,()->done[])' in fixture,refactor_latch='reason == :refactor_other && (done[]=true)' in fixture,final_guard_after_refactor=final.index('_crash_refactor!(trial,guard)')<final.index('guard() && return _crash_fallback(initial,trial,true)'),guard_latched='stopped[] = stopped[] ||' in s,record_before_observer=event.index('record_event!')<event.index('d.observer(reason, state)'),wrapped_cause='throw(DiagnosticObserverFailure(exception))' in event,wrapper_not_numerical='DiagnosticObserverFailure' not in du[:du.index('# Internal deadline')],merge_before_fallback=fallback.index('initial.iterations = max')<fallback.index('initial.refactorizations = max')<fallback.index('_simplex_event!(initial,:crash_fallback)')<fallback.index('return initial,expired'),event_before_reconstruction=j.index('_simplex_event!(workspace, diagnostic_reason)')<j.index('basic_primal = _checked_basis_solve!'),native_refinement_off='solve_refinement::Bool=(numerical_profile == :checked)' in n and 'numerical_profile::Symbol=:native' in n and 'policy.solve_refinement || return true' in q,native_recovery_off='recovery::Bool=(numerical_profile == :checked)' in n,default_timing_off='kernel_timing::Bool=false' in d,default_budget='iteration_limit::Integer=100_000, time_limit::Real=Inf' in o,default_pfi_dual='algorithm::Symbol=:dual' in o and 'basis_update::Symbol=:pfi' in o,no_production_test_change=not git('diff','master','--','src','test','.github','Project.toml'))
paths=set(map(Path,ve['sha256']))|{Path(__file__).resolve(),H/'entry.json',H/'host.json',H/'original-testset.txt',R/'src/options.jl',D/'S5-CRASH-FALLBACK-OWNERSHIP.md',D/'S5-CRASH-FALLBACK-OWNERSHIP-REVIEW.md',R/'docs/superpowers/plans/2026-10-13-crash-fallback-observer-oracle.md'}|{p for p in V.rglob('*') if p.is_file()}
x=dict(checks=checks,all_passed=all(checks.values()),sha256={str(p):sha(p) for p in sorted(paths)},fixture=dict(source=b['file'],name=b['name'],sha256=sha(H/'original-testset.txt'),start_line=b['start_line']),scope='Offline source oracle only. All proposed runtime outcomes unqualified; no executable candidate or numerical admission.',time_ns=time.time_ns());dump(H/'evidence.json',x);print(json.dumps(dict(entry=len(entry),checks=checks,pins=len(paths))));assert x['all_passed']
