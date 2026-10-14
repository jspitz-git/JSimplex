"""Independent MA-X offline review. No Julia, old script execution, or launch main.
Reads all prospective pins once, inspects Python AST/source, exercises only new
pure auditor definitions with synthetic values, and writes one exclusive report.
"""
from pathlib import Path
import ast,copy,hashlib,json,statistics,subprocess,time,tomllib
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-X';B=D.parent
checks={};hashes={}
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 p=Path(p);h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 hashes[str(p)]=h.hexdigest();return h.hexdigest()
def ck(k,v):checks[k]=v is True
def git(*args):return subprocess.check_output(['git',*args],text=True).strip()
def fn(path,name):return next(n for n in ast.parse(Path(path).read_text()).body if isinstance(n,ast.FunctionDef) and n.name==name)
pins=read(D/'pins.json');required=read(D/'required-paths.json');inv=pins['inventory'];start=time.monotonic()
ck('4375_manifest_hashes',len(inv)==4375 and all(sha(p)==v['sha256'] for p,v in inv.items()))
ck('4375_resolved_paths',all(str(Path(p).resolve(strict=True))==v['resolved'] for p,v in inv.items()))
ck('unique_exact_required_inventory_files',len(set(required))==len(required) and len(set(pins['files']))==len(pins['files']) and set(required)==set(inv)==set(pins['files']))
walked=set(pins['files']);bad=[]
for root in pins['trees']:
 q=Path(root)
 if not q.is_dir() or q.is_symlink():bad.append(str(q))
 for p in q.rglob('*'):
  if p.is_symlink() and (p.is_dir() or not p.exists()):bad.append(str(p))
  if p.is_file():walked.add(str(p))
ck('73_tree_membership_and_no_directory_dangling_symlinks',len(pins['trees'])==73 and not bad and walked==set(inv))
manifest_seconds=time.monotonic()-start
m=read(D/'source-map.json');driver=(D/'driver.jl').read_text();restored=driver
for i,e in enumerate(reversed(m['driver_edits'])):
 ck('driver_inverse_unique_'+str(i),restored.count(e['new'])==1);restored=restored.replace(e['new'],e['old'])
ck('driver_exact_inverse',restored==Path(m['driver_source']).read_text() and sha(m['driver_source'])==m['driver_source_sha256'])
for name in ('validate_raw','expected_correctness','aggregate'):
 ck('original_AST_'+name,ast.dump(fn(D/'audit.py',name))==ast.dump(fn(B/'MA-S-2/audit.py',name)))
for name,v in m['byte_exact_copies'].items():ck('byte_exact_'+name,sha(D/name)==sha(v['source'])==v['sha256'])
u=Path(m['candidate']).read_text();inst=Path(m['instrumented']).read_text()
ck('candidate_fixed_hash',sha(m['candidate'])==m['candidate_sha256']=='50b1421e06eabed34cbc0b9fd50bb1a0977aada3fe9159a4e005513cbefca98b')
ck('instrumented_fixed_hash',sha(m['instrumented'])==m['instrumented_sha256']==sha(B/'MA-R/instrumented.jl'))
ck('candidate_guard_only_inverse',u[u.index('# UNEXECUTED.'):].replace('return _dense_ma_rounding_matches()','return Base.MPFR.rounding_raw(BigFloat) == Base.MPFR.ROUNDING_MODE[]')==(B/'MA-R/candidate.jl').read_text())
for direction in ('forward','transpose'):
 start=inst.index('function instrumented_'+direction+'!');end=inst.index('\nend',start)+4
 clean=inst[start:end].replace('instrumented_'+direction+'!','candidate_'+direction+'!').replace('    _route_entries[] += 1\n','').replace('    _route_scratches[] += 1\n','')
 clean=clean.replace('    if !_dense_ma_eligible(dest, backend, rhs)\n        _route_fallbacks[] += 1\n        return reference_'+direction+'!(dest, backend, rhs)\n    end','    _dense_ma_eligible(dest, backend, rhs) || return reference_'+direction+'!(dest, backend, rhs)')
 start=u.index('function candidate_'+direction+'!');end=u.index('\nend',start)+4
 ck('instrumentation_inverse_'+direction,clean==u[start:end])
ck('one_helper_twelve_products',u.count('function _dense_ma_eligible(')==1 and '_dense_ma_eligible' not in inst.split('function instrumented_forward!')[0] and u.count('_dense_ma_mul!(product,')==12)
v=read(B/'MA-V/pins.json')['inventory'];reached=[p for p in v if '/src/' in p or '/share/julia/base/' in p or '/share/julia/stdlib/' in p]
ck('V_1912_reached_source_identities',len(reached)==1912 and all(p in hashes and hashes[p]==v[p]['sha256'] and str(Path(p).resolve())==v[p]['resolved'] for p in reached))
ck('V_candidate_instrumented_reference_identity',all(str(Path(m[k])) in v and hashes[str(Path(m[k]))]==v[str(Path(m[k]))]['sha256'] for k in ('candidate','instrumented','reference')))
f=tomllib.loads(Path(m['fixtures']).read_text());s=read(D/'schedule.json');cases=f['cost_cases'];dirs=len(f['directions'])
correctness=len(f['bits'])*len(f['sizes'])*len(f['layouts'])*dirs+(len(f['specials'])+len(f['mixed_stored_ambient'])+len(f['matching_rounding'])+len(f['scoped_mismatch'])+2)*dirs
per_arm=correctness+sum(x=='retained_outputs' for x in f['specials'])*dirs
ledger=dict(correctness_cases=correctness,correctness_entries=per_arm*3+dirs,correctness_setup_factorizations=correctness+dirs,cost_setups=3*len(cases),cost_entries=3*len(cases)*10*2*4,windows=3*len(cases)*10*2,warm_windows=3*len(cases)*3*2,measured_windows=3*len(cases)*7*2,pfi_copies=sum(x=='copied_pfi' for x in f['specials'])*dirs)
ledger['setup_factorizations']=ledger['correctness_setup_factorizations']+ledger['cost_setups'];ledger['total_entries']=ledger['correctness_entries']+ledger['cost_entries']
ck('exact_52_schedule',s['costs']==cases and len(cases)==52 and sum(c['eligible'] for c in cases)==36 and sum(c['scalar']=='Rational{BigInt}' for c in cases)==2)
ck('source_budget_ledger',all(s[k]==v for k,v in ledger.items()) and correctness==160 and per_arm==162 and ledger['total_entries']==12968)
ck('fixed_schedule_constants',all(s[k]==v for k,v in dict(processes=3,pairs=10,warm_pairs=3,measured_pairs=7,calls_per_window=4,seconds_per_process=90,total_seconds=270,no_retry=True).items()))
old=Path(m['driver_source']).read_text()
ck('batch_window_unchanged',driver[driver.index('@noinline function batch'):driver.index('const JOURNAL')]==old[old.index('@noinline function batch'):old.index('function costs')])
ck('cold_boundary_and_RED_order',driver.count('Base.invokelatest')==2 and 'Base.invokelatest(TST.qualification)' in driver and 'Base.invokelatest(costs,index,raw["costs"])' in driver and driver.index('raw["red"]=red()')<driver.index('Base.include(P,joinpath(UD,"candidate.jl"))'))
ck('journal_before_conversion_then_assertions',driver.index('"whole-metrics"')<driver.index('output=serialtokens(y.dest)')<driver.index('"whole-complete"')<driver.index('output==expected || error') and 'TOML.print(io,Dict("records"=>[record]));flush(io)' in driver)
ck('source_refusal_before_candidate',driver.index('VERSION == v"1.13.0"')<driver.index('Base.include(P,joinpath(UD,"candidate.jl"))') and driver.index('error("wrong MA")')<driver.index('Base.include(P,joinpath(UD,"candidate.jl"))'))
cmds=read(D/'commands.json')
ck('exact_three_commands',set(cmds)=={'1','2','3'} and all(c[-3:]==[str(D/'driver.jl'),i,str(D/f'run-{i}')] and c[:2]==['/bin/bash','/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh'] and c[2:7]==['--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+str(B/'MA-R/environment')] for i,c in cmds.items()))
# Load only new auditor definitions, not any main, stage, process, or old script.
tree=ast.parse((D/'audit.py').read_text());names={'require','finite','spec','expected_correctness','validate_raw','passed','process_costs','journal_expected','journal_valid','aggregate'}
selected=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[])
import math
ns=dict(Path=Path,D=D,tomllib=tomllib,math=math,statistics=statistics)
exec(compile(ast.fix_missing_locations(selected),str(D/'audit.py')+':pure-definitions','exec'),ns)
def raw(index):
 r=dict(index=index,errors=[],ambient_restored=True,load_seconds=.1,candidate_definition_seconds=.1,loaded_paths={'fake':'/tmp/mock.jl'},red={},counts={},correctness=[],costs=[])
 if index==1:
  r['red']=dict(pass_=0);r['red']={'pass':0,'fail':2,'error':0,'broken':0,'missing_route_only':True,'failure_expressions':['isdefined(P, :_dense_ma_eligible)','isdefined(P, :candidate_forward!) && isdefined(P, :candidate_transpose!)']}
  r['counts']={k:{'pass':1,'fail':0,'error':0,'broken':0} for k in ('smoke','qualification')}
  r['correctness']=[dict(id=i,direction=dr,eligible=e,calls_per_side=c,output=['synthetic']*n,exception=[] if exc is None else [exc,'synthetic']) for i,dr,e,c,n,exc in ns['expected_correctness']()]
 for ci,c in enumerate(cases,1):
  row=dict(id=c['id'],eligible=c['eligible'],expected=['synthetic']*c['n'],windows=[])
  for pair in range(1,11):
   order=['reference','candidate'] if (index+ci+pair)%2==0 else ['candidate','reference']
   for oi,side in enumerate(order,1):
    target=side=='candidate' and c['eligible'];row['windows'].append(dict(side=side,pair=pair,order=oi,phase='warm' if pair<=3 else 'measured',calls=4,seconds=.00036 if target else .0004,bytes=9 if target else 10,events=1 if target else 2,gc_seconds=0.,compile_seconds=0.,recompile_seconds=0.,output=row['expected'],preserved=True))
  r['costs'].append(row)
 return r
rs=[raw(i) for i in (1,2,3)]
ck('new_synthetic_raws_valid',all(ns['passed'](ns['validate_raw'](r,i)) for i,r in enumerate(rs,1)))
ck('new_synthetic_complete_aggregate',all(x['accepted'] for x in ns['aggregate'](rs)))
ck('process_reducer_exact_old_process_rows',all(all({k:v for k,v in row.items() if k!='id'}==agg['processes'][i] for row,agg in zip(ns['process_costs'](r),ns['aggregate'](rs))) for i,r in enumerate(rs)))
for ci in (50,51):
 for metric in ('bytes','events'):
  r=copy.deepcopy(rs[0])
  for w in r['costs'][ci]['windows']:
   if w['side']=='candidate' and w['phase']=='measured':w[metric]+=1
  ck('strict_Rational_'+str(ci)+'_'+metric,ns['process_costs'](r)[ci]['pass'] is False)
for i,r in enumerate(rs,1):
 journal=ns['journal_expected'](r);ck('full_2080_journal_'+str(i),len(journal)==2080 and ns['journal_valid'](journal,r))
 for cutoff in (0,1,2,3,2079):
  try:ns['journal_valid'](journal[:cutoff],r);refused=False
  except ValueError:refused=True
  ck('journal_refuses_prefix_'+str(i)+'_'+str(cutoff),refused)
# Structural launch gate ordering: per-process audit and require dominate next loop.
main=fn(D/'launcher.py','main');loop=next(n for n in main.body if isinstance(n,ast.For))
ck('per_process_terminal_require_is_last',isinstance(loop.body[-1],ast.Expr) and isinstance(loop.body[-1].value,ast.Call) and ast.unparse(loop.body[-1].value.func)=='require' and "result['all_passed']" in ast.unparse(loop.body[-1]) and any(isinstance(n,ast.Assign) and 'audit.stage(i)' in ast.unparse(n) for n in loop.body))
for name in ('audit.py','launcher.py','guard.py','supervisor.py'):ck('nonremovable_gates_'+name,not any(isinstance(n,ast.Assert) for n in ast.walk(ast.parse((D/name).read_text()))))
for name,count in [('offline-tests.json',115),('supervisor-tests-final.json',10),('source-check.json',37)]:
 o=read(D/name);ck('record_'+name,len(o['checks'])==count and o['all_passed'] is True and all(v is True for v in o['checks'].values()) and all(sha(p)==h for p,h in o['sha256'].items()))
for name in ('entry.json','freeze.json'):
 o=read(D/name);ck('record_'+name,o['all_passed'] is True and all(sha(p)==h for p,h in o['sha256'].items()))
h=read(D/'host.json');maps=read(D/'continuation-map.json')['old_bindings']
ck('six_continuation_maps',len(maps)==6 and all(sha(x['preserved'])==x['sha256']==read(x['source'])['sha256'][x['path']] for x in maps))
ck('source514',len(h['master_identity'])==514 and all(sha(R/p)==v for p,v in h['master_identity'].items()))
ck('protected6',len(h['protected'])==6 and all(sha(p)==v for p,v in h['protected'].items()))
ck('refs',git('rev-parse','HEAD')==h['refs']['head']=='bb705c15c16480225df86bf803d71835f322ed18' and git('rev-parse','master')==h['refs']['master']=='6f68e24e8ddac42b948da8fcc2d636c010751194' and git('branch','--show-current')==h['refs']['branch'])
ck('remote_refs',set(git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture').splitlines())==set(h['refs']['remote'].splitlines()))
ck('tracked_staged_clean',not git('diff','--name-only','HEAD') and not git('diff','--cached','--name-only'))
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  parts=(p/'stat').read_text().rsplit(')',1)[1].split()
  if int(parts[2]) in h['groups'] or int(parts[3]) in h['groups'] or (p/'exe').resolve().name.startswith('julia'):
   matches.append(dict(pid=int(p.name),pgid=int(parts[2]),sid=int(parts[3]),start_ticks=int(parts[19]),boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,ProcessLookupError):pass
ck('170_groups_or_sessions_no_Julia',len(set(h['groups']))==170 and not matches and boot==h['boot_id'])
ck('no_numerical_context_seal_reservations_runs',not any((D/n).exists() for n in ('launch-context.json','numerical-review.json','sequence-reservation.json','run-1','run-2','run-3','reservation-1.json','reservation-2.json','reservation-3.json','invocation-1.json','invocation-2.json','invocation-3.json')))
ck('live_continuations_excluded',str(R/'diagnostics/simplex-core-architecture/STATUS.md') not in inv and str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md') not in inv)
critical=[D/n for n in ('pins.json','required-paths.json','driver.jl','source-map.json','launcher.py','guard.py','supervisor.py','audit.py','schedule.json','commands.json','admission.md','work-ledger.md','source-check.py','source-check.json','offline-tests.py','offline-tests.json','supervisor-tests.py','supervisor-tests-final.json','entry.py','entry.json','host.json','continuation-map.json','STATUS.md.before-MA-X','roadmap.md.before-MA-X','freeze.py','freeze.json','build.py','build-tests.py','build-tests-2.py','build-tests-failure.txt','preparation-red.py','preparation-red.json','review-check.py')]
critical += [Path(m[k]) for k in ('driver_source','original_validator','candidate','instrumented','reference','tests','fixtures')]
critical += [R/'docs/superpowers/plans/2026-10-14-ma-denselu-complete-qualification.md',R/'docs/superpowers/specs/2026-10-14-ma-denselu-bigfloat-design.md',R/'docs/superpowers/specs/2026-10-14-ma-rounding-guard-design.md']
critical += [B/'MA-V'/n for n in ('admission-review.json','numerical-review.json','aggregate.json','pins.json','source-check.json')]+[B/'MA-W'/n for n in ('review.json','review.md','evidence.json','closure.json','publication.json')]
critical_hashes={str(p):sha(p) for p in critical}
o=dict(all_computed_checks_passed=all(checks.values()),computed_checks=checks,manifest=dict(files=len(inv),trees=len(pins['trees']),listed_bytes=sum(Path(p).stat().st_size for p in inv),hash_and_membership_seconds=manifest_seconds),source_ledger=ledger,host=dict(time=time.time(),boot_id=boot,groups=h['groups'],matches=matches),pins_sha256=sha(D/'pins.json'),sha256=critical_hashes,scope='Independent source/hash/AST checks and new pure-definition synthetic checks only; no Julia or old script/main executed. Timing is read-only manifest review overhead, not numerical or performance evidence.')
with (D/'review-check.json').open('x') as out:json.dump(o,out,indent=2);out.write('\n')
print(json.dumps(dict(all_passed=o['all_computed_checks_passed'],count=len(checks),failed=[k for k,v in checks.items() if not v],manifest=o['manifest'],bindings=len(critical_hashes))))
if not o['all_computed_checks_passed']:raise SystemExit(1)
