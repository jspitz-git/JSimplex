from pathlib import Path
import ast,copy,hashlib,json,math,os,re,stat,subprocess,sys,tomllib,types
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl')
P=W/'diagnostics/dual-recovery-devex-green2-admission/2026-10-30'
F=W/'diagnostics/dual-recovery-devex-green-fixture-preparation/2026-10-30'
O=W/'diagnostics/dual-recovery-devex-task4/2026-10-30'
R=W/'.superpowers/dual-recovery-devex-task4/green2-1'
RED=W/'diagnostics/dual-recovery-devex-task4-red/2026-10-30'
OLD=W/'diagnostics/dual-recovery-devex-task4-green/2026-10-30'
HEAD='4f5e6b9966830955637cfb7bba288b9339c9a494';MASTER='c0fa748ffa61ccb7c1caaf248c40324f60bc737b'
checks={};bindings={}
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def bind(p):
 p=str(p);bindings[p]=sha(p);return bindings[p]
def read(p):bind(p);return json.loads(Path(p).read_text())
def need(v,n):
 if not v:raise AssertionError(n)
 checks[n]=True

def git(*args):return subprocess.check_output(['git','-C',str(W),*args],text=True).strip()
def rejects(fn,n):
 try:fn()
 except (ValueError,KeyError,TypeError):need(True,n)
 else:need(False,n)
# Only new checker plus definitions-only safe helpers; no executable main/guard import.
sys.path.insert(0,str(P));import common as C;import binding_checks as B
seal=read(R/'seal.json');pins=read(R/'pins.json');contract=read(P/'contract.json')
need(bind(R/'seal.json')=='da0d0f2653da383f633825fff75a971c259d42932de835c2d97a5ee59c400daf','concrete_seal_sha')
need(bind(R/'pins.json')==seal['pins_sha256']=='4deb0e97c0a3acdca21c9fb8dbf5b4c4095873d462c95469ad93c19e7b786582','concrete_pins_sha')
need(sorted(p.name for p in R.iterdir())==['pins.json','seal.json'],'only_unconsumed_seal_and_pins')
need(seal['head']==HEAD and seal['master']==MASTER and seal['phase']=='green2','seal_scope_refs')
need(seal['command']==contract['command']==C.command(),'exact_julia_command')
need(seal['environment']==contract['environment']==C.environment(),'exact_julia_environment')
need(seal['expected_exit']==0 and seal['shared_total_seconds']==1800,'exit_and_total')
need(seal['guard_python']=='/usr/bin/python3'==sys.executable,'exact_interpreter')
B.interpreter(seal,pins,sys.executable);need(True,'interpreter_target_bytes_helper')
required=set()
counts=[]
for folder in (O,RED,OLD,F,P):
 pub=read(folder/'publication.json');need(pub['accepted'] is True,'publication_'+folder.parent.name)
 counts.append(len(pub['expected_names']))
 for rel in pub['expected_names']:
  p=W/rel;need(p.is_file() and not p.is_symlink(),'regular_'+rel)
  required.add(str(p));bind(p)
  blob=hashlib.sha1(b'blob '+str(p.stat().st_size).encode()+b'\0'+p.read_bytes()).hexdigest()
  need(blob==git('rev-parse','HEAD:'+rel),'committed_'+rel)
  if rel in pub.get('blobs_excluding_publication',{}):need(blob==pub['blobs_excluding_publication'][rel],'publication_blob_'+rel)
need(sum(counts[:4])==402 and counts[4]==51,'publication_counts_402_51')
runtime=Path(C.JULIA).parents[1]
runtime_paths={str(p) for p in [Path('/usr/bin/python3'),Path(C.JULIA),runtime/'lib/libjulia.so.1.13.0',runtime/'lib/julia/sys.so',runtime/'lib/julia/libjulia-internal.so.1.13.0',runtime/'share/julia/base/timing.jl']}
required.update(runtime_paths)
need(len(pins['files'])==len(set(pins['files']))==len(pins['inventory'])==459 and set(pins['inventory'])==set(pins['files'])==required,'full_459_inventory')
need(pins['trees']==[] and pins['inputs']==sorted(contract['fixture_inputs']),'explicit_both_inputs')
for path,item in pins['inventory'].items():
 need(str(Path(path).resolve(strict=True))==item['resolved'] and bind(path)==item['sha256'],'pin_'+path)
C.check_inventory(pins,C.required_paths(),C.expected_inputs());need(True,'inventory_helper')
for exe in ('/usr/bin/python3',C.JULIA):
 mode=Path(exe).resolve().stat().st_mode
 need(not mode&(stat.S_ISUID|stat.S_ISGID),'nonprivileged_exec_'+exe)
 need('security.capability' not in os.listxattr(Path(exe).resolve()),'no_exec_capabilities_'+exe)
for depot in contract['environment']['JULIA_DEPOT_PATH'].split(':'):need(Path(depot).is_dir(),'depot_'+depot)
need(not os.environ.get('LD_PRELOAD') and not os.environ.get('LD_AUDIT'),'no_loader_injection')
# Published final review and every bound original source/evidence byte remain exact.
review=read(P/'review-final.json')
need(review['accepted'] is True and review['scope']=='offline_preparation' and review['numerical_admission'] is False,'prior_review_scope')
need(len(review['checks'])==1356 and all(v is True for v in review['checks'].values()) and len(review['bindings'])==455,'prior_review_1356_455')
for path,h in review['bindings'].items():need(bind(path)==h,'review_binding_'+path)
for path,h in read(P/'preservation.json')['frozen_publications'].items():need(bind(path)==h,'frozen_'+path)
# All corrected prepared files equal their original exact source; no waiver for fixture.
staging=read(F/'staging.json');prepared=sorted(p for p in (F/'prepared').rglob('*') if p.is_file())
need(len(prepared)==91 and all(not p.is_symlink() for p in prepared),'prepared_91_regular')
for p in prepared:
 q=staging['copies'][str(p)];need(bind(p)==bind(q['source'])==q['sha256'] and p.stat().st_size==q['bytes'],'prepared_source_'+str(p))
need(sum(p.is_file() for p in (F/'prepared/overlays/candidate').rglob('*'))==74,'candidate_74_files')
oldstage=read(O/'staging.json')
for p,q in oldstage['bindings'].items():need(bind(p)==bind(q['source'])==q['sha256'],'original_stage_'+p)
changed=[]
for p in (F/'prepared/overlays/candidate/src').rglob('*.jl'):
 rel=p.relative_to(F/'prepared/overlays/candidate/src');r=O/'overlays/reference/src'/rel
 if sha(p)!=sha(r):changed.append(str(rel))
need(sorted(changed)==['simplex_numerics.jl','simplex_pivot.jl','simplex_recovery.jl'],'exact_three_canonical_candidate_changes')
fixture=C.fixtures();need(fixture==seal['fixture_audit'],'sealed_fixture_graph_unchanged')
need((fixture['program_count'],fixture['include_edges'],fixture['fixture_count'])==(15,14,2),'fixture_graph_counts')
for p,h in contract['fixture_hashes'].items():need(bind(p)==h,'fixture_'+p)
need((F/'prepared/tests/fixtures/solver/netlib/adlittle.mps').stat().st_size==16500,'adlittle_16500_bytes')
for name in ('guard_reviewed.py','supervisor_reviewed.py','entry_gate.py'):
 need(bind(P/'guard'/name)==bind(O/'guard'/name),'unchanged_guard_'+name)
need(bind(P/'fixture_check.py')==bind(F/'fixture_check.py') and bind(P/'fixture-manifest.json')==bind(F/'fixture-manifest.json'),'unchanged_fixture_helpers')
# Historical raw and portable records remain separate immutable byte-exact evidence.
for folder in (RED,OLD):
 closure=read(folder/'closure.json')
 for src,dst in closure['explicit_exact_copy_maps'].items():need(bind(src)==bind(dst),'raw_portable_'+src)
used,facts=C.prior();need(used==527.9604928489425==seal['used_seconds'] and facts==seal['previous']==contract['previous'],'prior_facts_exact')
need(1800-used==1272.0395071510575==seal['remaining_seconds'] and seal['remaining_seconds']-12==1260.0395071510575 and seal['remaining_seconds']-4==1268.0395071510575,'shared_budget_no_reset')
for bad in ([True],[float('nan')],[-1],[0],['1'],[]):rejects(lambda bad=bad:C.accumulate(bad),'bad_prior_'+repr(bad))
# Evaluate selected pure auditor definitions only, never its evaluate/main.
audit_source=(P/'audit_reviewed.py').read_text();ns=dict(C=C,math=math,re=re)
names={'integer','number','stats','summary','ordinary','endpoint','process','resource'}
mod=ast.parse(audit_source);pure=ast.Module(body=[n for n in mod.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[])
exec(compile(pure,str(P/'audit_reviewed.py'),'exec'),ns)
inc=''.join('TASK4_INCLUDED '+n+'\n' for n in contract['green_includes'])
log='Test Summary: | Pass Total Time\nTASK4_GREEN | 100 100 1s\n'+inc+'TASK4_GREEN_COMPLETED\n'
need(ns['ordinary'](log)==dict(Pass=100,Total=100),'synthetic_nonverbose_parent')
verbose=log+'Test Summary: | Pass Total Time\nTASK4_POST_FALLBACK | 46 46 1s\n'
need(ns['ordinary'](verbose)==dict(Pass=100,Total=100),'synthetic_optional_46_row')
mutants=[verbose.replace('46 46','45 45'),verbose+verbose[verbose.index('Test Summary:',30):],log.replace('100 100','0 0'),log.replace('100 100','99 100'),log.replace('TASK4_GREEN_COMPLETED',''),log+'TASK4_GREEN_COMPLETED\n',log.replace('TASK4_INCLUDED tests/refinement_outcome_tests.jl\n',''),log+inc,log+'ERROR: failure\n',log+'world age\n',log.replace('TASK4_GREEN |','TASK4_OTHER |'),(OLD/'green/guard/run.log').read_text()]
for i,bad in enumerate(mutants):rejects(lambda bad=bad:ns['ordinary'](bad),'ordinary_mutant_'+str(i))
records=tomllib.loads((OLD/'green/result.toml').read_text())['cases'];need(ns['endpoint'](records) is True,'historical_endpoint_only_not_green_acceptance')
for key in ('iterations','factorizations','attempted_weight_rows','avoided_weight_rows','core_and_weight_ftran','core_and_weight_btran','final_ftran','final_btran'):
 q=copy.deepcopy(records);q[0][key]=True;rejects(lambda q=q:ns['endpoint'](q),'endpoint_boolean_work_'+key)
for key in ('original_primal_certified','original_optimality_certified','invalid_witness_rejected','invalid_row_rejected','trajectory_changed'):
 q=copy.deepcopy(records);q[0][key]=False;rejects(lambda q=q:ns['endpoint'](q),'endpoint_boolean_oracle_'+key)
for key in ('point','witness'):
 for value in ([True,False],[1,1]):
  q=copy.deepcopy(records);q[0][key]=value;rejects(lambda q=q:ns['endpoint'](q),'endpoint_vector_'+key+repr(value))
for key in ('preparation','whole_fallback','component_preparation','component_revalidation','component_reset'):
 q=copy.deepcopy(records);q[0][key]['bytes']=-1;rejects(lambda q=q:ns['endpoint'](q),'endpoint_profile_'+key)
endpoint=(F/'prepared/endpoint.jl').read_text()
need(len(re.findall(r'^\s*@test(?:_throws)?\b',endpoint,re.M))==23 and 'for T in (Float32,Float64)' in endpoint,'endpoint_source_23_times_2')
# Full fresh host view: every prior PGID AND SID, no Julia, exact old identity absence.
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();hostrec=read(P/'host.json')
need(boot==seal['preflight']['boot_id']==hostrec['host']['boot_id']=='781795f4-f7af-4c3b-9ce9-45c7cae76ecb','same_boot')
groups=set(hostrec['host']['checked_groups']);need(len(groups)==733 and groups==set(seal['preflight']['checked_groups']),'733_prior_groups_sessions')
def identity(pid):
 p=Path('/proc')/str(pid);s=(p/'stat').read_text();a=s[s.rfind(')')+2:].split()
 return dict(pid=int(pid),pgid=int(a[2]),sid=int(a[3]),start_ticks=int(a[19]),boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'))
conflicts=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  a=identity(p.name);comm=(p/'comm').read_text().strip()
  if comm.lower().startswith('julia') or a['pgid'] in groups or a['sid'] in groups:conflicts.append(a)
 except (FileNotFoundError,ProcessLookupError):pass
need(not conflicts,'full_host_no_julia_groups_sessions')
identities=[]
for a in hostrec['prior_owners']:
 try:now=identity(a['pid'])
 except (FileNotFoundError,ProcessLookupError):now=None
 need(now is None or (now['boot_id'],now['start_ticks'])!=(a['boot_id'],a['start_ticks']),'old_identity_absent_'+str(a['pid']))
 identities.append(dict(original=a,current=now))
m={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()};memory=dict(available_kib=m['MemAvailable'],swap_used_kib=m['SwapTotal']-m['SwapFree'])
need(memory['available_kib']>=6*1024**2 and memory['swap_used_kib']<=1024**2,'fresh_memory_guard')
refs={n:git('rev-parse',n) for n in ('HEAD','master','origin/master')}
need(refs==dict(HEAD=HEAD,master=MASTER,**{'origin/master':MASTER}),'fresh_local_refs')
need(git('branch','--show-current')=='codex/native-quality-finite','expected_branch')
remote=dict((s.split()[1],s.split()[0]) for s in git('ls-remote','origin','refs/heads/master','refs/heads/codex/native-quality-finite').splitlines())
need(remote=={'refs/heads/master':MASTER,'refs/heads/codex/native-quality-finite':HEAD},'fresh_remote_refs')
need(not git('diff','HEAD','--name-only') and not git('diff','--cached','--name-only'),'tracked_tree_index_clean')
need(not git('diff','master','HEAD','--','src','test','Project.toml','.github'),'production_test_env_CI_equal_master')
for p in ('AGENTS.md','Manifest.toml','LocalPreferences.toml'):bind(W/p)
for p in Path('/tmp/devex-green2-run-20261030').iterdir():
 if p.is_file() and p.name in ('preflight.py','preflight.json','admission-check.py','postcheck.py'):bind(p)
need(sorted(p.name for p in R.iterdir())==['pins.json','seal.json'],'attempt_absent_after_review')
result=dict(accepted=True,scope='new read-only concrete GREEN2 admission checks; no numerical execution',checks=checks,counts=dict(assertions=len(checks),inventory=459,old_published=402,new_published=51,prepared=91,candidate_files=74,programs=15,edges=14,fixtures=2),host=dict(boot_id=boot,checked_groups=sorted(groups),conflicts=conflicts,memory=memory,refs=refs,remote_refs=remote,old_identities=identities),bindings=bindings,seal_sha256=sha(R/'seal.json'),pins_sha256=sha(R/'pins.json'))
with Path('/tmp/devex-green2-numerical-check-result.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(accepted=True,counts=result['counts'],bindings=len(bindings),memory=memory,seal_sha256=result['seal_sha256'],pins_sha256=result['pins_sha256'])))
