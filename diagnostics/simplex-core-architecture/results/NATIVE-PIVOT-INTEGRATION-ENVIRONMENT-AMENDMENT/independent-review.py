"""Independent offline amendment review. New definitions only; no Julia or stage commands."""
from pathlib import Path
import ast,copy,hashlib,json,os,subprocess,sys
D=Path(__file__).resolve().parent;R=D.parents[3];P=D.parent/'NATIVE-PIVOT-INTEGRATION-DRIVER-PREPARATION'
sys.dont_write_bytecode=True
import control as c
checks={};details={};findings=[]
def rd(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def path(n):return Path(n) if Path(n).is_absolute() else R/n
def check(n,v):
 checks[n]=bool(v)
 if not v:findings.append(n)
def bind(z):return all(sha(path(n))==v for n,v in z.items())
def funcs(p):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_text()).body if isinstance(n,ast.FunctionDef)}
def refuses(f):
 try:f()
 except RuntimeError:return True
 return False
m=rd(D/'preparation-pins.json');required=rd(D/'required-paths.json')['paths'];pm=rd(P/'preparation-pins.json');pr=rd(P/'review-final.json')
check('manifest_1561_absolute',len(m['sha256'])==1561 and all(Path(n).is_absolute() for n in m['sha256']))
check('all_1561_current_hashes',bind(m['sha256']))
check('required_exact_unique',len(required)==len(set(required))==1561 and set(required)==set(m['sha256']))
check('prior_1503_manifest',len(pm['sha256'])==1503 and bind(pm['sha256']))
check('prior_1504_review',pr['accepted'] is True and pr['findings']==[] and pr['scope']=='offline preparation' and pr['pins_sha256']==sha(P/'preparation-pins.json') and set(pr['sha256'])==set(pm['sha256'])|{str(P/'preparation-pins.json')} and len(pr['sha256'])==1504 and bind(pr['sha256']))
check('prior_18_supplemental_bindings',len(pr['evidence_sha256'])==18 and bind(pr['evidence_sha256']))
files={P/'preparation-pins.json',P/'review-final.json'}|{path(n) for n in pm['sha256']}|{path(n) for n in pr['evidence_sha256']}
remap={str(c.STATUS):D/'STATUS.md.before-environment',str(c.ROAD):D/'roadmap.md.before-environment'}
expected_maps=[]
for name in ['closure.json','publication.json']:
 z=rd(P/name);check('prior_'+name+'_pass',z['all_passed'] is True);files.add(P/name)
 for n,h in z['sha256'].items():
  p=path(n);p=remap.get(str(p),p)
  check('prior_'+name+'_binding_'+n,sha(p)==h);files.add(p)
 for key,p in remap.items():expected_maps.append(dict(record=str((P/name).relative_to(R)),pointer=['sha256',str(Path(key).relative_to(R))],preserved_path=str(p.relative_to(R)),sha256=sha(p)))
files.add(P/'closure-host.json');ph=rd(P/'closure-host.json')
check('prior_host_216',not ph['matches'] and len(ph['groups'])==len(set(ph['groups']))==216)
actual_files,groups=c.predecessor('integration')
check('predecessor_exact_1532',len(files)==1532 and set(actual_files)==files and groups==ph['groups'])
check('four_exact_continuation_mappings',rd(D/'continuation-mappings.json')['mappings']==expected_maps)
new_names={'prepare.py','offline-GREEN.json','required-paths.json','source-check.json','offline-RED.json','offline-tests-final.py','launch.py','guard.py','controls-baseline.json','config-preview.json','roadmap.md.before-environment','host.json','continuation-mappings.json','REPORT.md','source-check.py','environment.json','common.py','loaded-paths.json','freeze.py','seal.py','STATUS.md.before-environment','environment-delta.json','oracle.py','supervisor.py','control.py','test-selector-note.json','prepare-2.py','audit.py','offline-tests.py','prepare-failure.json','source-map.json'}
check('independent_manifest_membership',set(m['sha256'])=={str(p) for p in files}|{str(D/n) for n in new_names})
source=rd(D/'source-map.json');copy_names={'guard.py','supervisor.py','seal.py','launch.py','audit.py','oracle.py','loaded-paths.json','controls-baseline.json'}
check('eight_copy_membership',set(source['byte_identical'])==copy_names)
check('eight_copy_bytes',all((D/n).read_bytes()==(P/n).read_bytes() and source['byte_identical'][n]['source']==str(P/n) and source['byte_identical'][n]['sha256']==sha(P/n) for n in copy_names))
check('common_only_two_changes',(D/'common.py').read_text().replace("PREV=Q.parent/'NATIVE-PIVOT-INTEGRATION-DRIVER-PREPARATION'",'PREV=Q').replace('5fd40966abc84be5bb88a789853273b41f754717','86e0397c882ff6628193cfa4c1d24a7c71ed7c3e')==(P/'common.py').read_text())
a=funcs(P/'control.py');b=funcs(D/'control.py')
check('other_control_functions_identical',set(a)==set(b) and all(a[k]==b[k] for k in a if k not in {'config','predecessor'}))
check('new_definitions_resolve_locally',Path(c.__file__).resolve()==D/'control.py' and Path(sys.modules['common'].__file__).resolve()==D/'common.py' and c.D==D and c.PREV==c.DRIVER==P)
cfg=c.config('integration');old=rd(P/'config-preview.json');expected=copy.deepcopy(old)
expected.update(stage=str(R/'.superpowers/native-pivot-integration-env1/integration'),run=str(D/'runs/integration'),output=str(D/'runs/integration/output'))
expected['command']=[x.replace(old['stage'],expected['stage']).replace(old['output'],expected['output']) for x in old['command']]
check('config_exact_allowed_delta',cfg==expected==rd(D/'config-preview.json'))
check('command_only_indices_6_8_10_change',[i for i,(x,y) in enumerate(zip(old['command'],cfg['command'])) if x!=y]==[6,8,10] and len(old['command'])==len(cfg['command'])==11)
check('fixed_60_outer_52_inner',cfg['seconds']==60 and c.guard_command(cfg,D/'fictional-pins',100)[6:10]==['--seconds','52','--deadline','152'])
check('other_phase_refused',refuses(lambda:c.config('cost')))
check('stage_run_output_fresh',all(not Path(p).exists() and not Path(p).is_symlink() for p in [cfg['stage'],old['stage'],D/'runs',P/'runs']))
check('original_driver_pin',cfg['command'][7]==str(P/'driver.jl') and sha(P/'driver.jl')==source['driver_sha256'])
check('original_driver_relative_dependencies',all('include(joinpath(@__DIR__,"'+n+'"))' in (P/'driver.jl').read_text() and str(P/n) in m['sha256'] for n in ['probe.jl','recorder.jl','observed-tests.jl']))
overlay=rd(P/'overlay-manifest.json')['candidate']
check('overlay76_immutable_sources',len(overlay)==76 and all(sha(e['source'])==e['sha256'] and str(path(e['source'])) in m['sha256'] for e in overlay))
env=rd(D/'environment.json');prev=rd(P/'environment.json');keys={'HOME','PATH','JULIA_LOAD_PATH','JULIA_PROJECT','JULIA_DEPOT_PATH','JULIA_CPU_TARGET','JULIA_BINDIR','LD_LIBRARY_PATH','LD_PRELOAD'}
check('exact_nine_environment_keys',set(env)==set(prev)==keys)
check('only_first_path_component_changed',[k for k in env if env[k]!=prev[k]]==['PATH'] and env['PATH'].split(':')[1:]==prev['PATH'].split(':')[1:] and env['PATH'].split(':')[0]!=prev['PATH'].split(':')[0])
details['current_environment_delta']={k:{'expected':v,'actual':os.environ.get(k)} for k,v in env.items() if v!=os.environ.get(k)}
check('reviewer_environment_exact',not details['current_environment_delta']);check('new_environment_gate_accepts',c.validate_environment() is None)
saved=dict(os.environ)
try:
 for k in keys:
  os.environ[k]='__independent_review_drift__'
  check('refuse_env_drift_'+k,refuses(c.validate_environment));os.environ.clear();os.environ.update(saved)
 for k,v in prev.items():
  if v is None:os.environ.pop(k,None)
  else:os.environ[k]=v
 check('old_environment_refused',refuses(c.validate_environment))
finally:os.environ.clear();os.environ.update(saved)
check('environment_restored_exactly',dict(os.environ)==saved)
small=D/'environment.json';v=dict(accepted=True,findings=[],scope='offline preparation',pins_sha256=sha(small),sha256={str(small):sha(small)})
check('review_gate_good_shape',c.verify_review(v,small,[str(small)],'offline preparation') is None)
for field,value in [('accepted',False),('findings',['finding']),('scope','exact-stage admission'),('pins_sha256','0'*64),('sha256',{}),('sha256',{str(small):'0'*64}),('sha256',{str(small):sha(small),str(D/'common.py'):sha(D/'common.py')})]:
 bad=copy.deepcopy(v);bad[field]=value
 check('refuse_review_'+field+'_'+str(len(checks)),refuses(lambda:c.verify_review(bad,small,[str(small)],'offline preparation')))
check('admission_phase_refused',refuses(lambda:c.verify_review(v,small,[str(small)],'offline preparation','integration')))
for n in ['seal.py','launch.py','audit.py']:
 t=(D/n).read_text();check(n+'_new_control_import','from control import *' in t and 'validate_environment()' in t and 'predecessor(phase)' in t)
check('oracle_new_baseline','from common import rd,require,Q' in (D/'oracle.py').read_text() and "rd(Q/'controls-baseline.json')" in (D/'oracle.py').read_text())
check('seal_exact_preparation_and_review_membership',"list(z['sha256'])+[str(pins)]" in (D/'seal.py').read_text() and "set(z['sha256'])==set(rd(D/'required-paths.json')['paths'])" in (D/'seal.py').read_text())
check('exclusive_single_attempt_and_admission',"reservation.json" in (D/'launch.py').read_text() and "one_attempt=True" in (D/'launch.py').read_text() and "sealed['files']+[str(sp)],'exact-stage admission',phase" in (D/'launch.py').read_text() and "Path(p).open('x')" in (D/'common.py').read_text())
check('offline_17_evidence',rd(D/'offline-GREEN.json')['all_passed'] is True and len(rd(D/'offline-GREEN.json')['checks'])==17 and all(rd(D/'offline-GREEN.json')['checks'].values()))
sc=rd(D/'source-check.json');check('source_17_and_bindings',sc['all_passed'] is True and len(sc['checks'])==17 and all(sc['checks'].values()) and bind(sc['sha256']))
check('preserved_initial_red',rd(D/'offline-RED.json')['all_passed'] is False)
check('test_selector_only_correction',(D/'offline-tests.py').read_text().replace("[5]=='--seconds' and c.guard_command(cfg,Path('/tmp/pins'),10)[6]=='52'","[6:8]==['--seconds','52']")== (D/'offline-tests-final.py').read_text())
try:ast.parse((D/'prepare.py').read_text());invalid=False
except SyntaxError:invalid=True
check('preserved_author_syntax_failure',invalid and rd(D/'prepare-failure.json')['outputs_created_by_failed_script'] is False)
check('no_new_julia_text',not list(D.glob('*.jl')))
base=rd(P/'actual-baseline.json');check('baseline520_current',len(base['sha256'])==520 and bind(base['sha256']) and (D/'actual-baseline.json').read_bytes()==(P/'actual-baseline.json').read_bytes())
head=subprocess.check_output(['git','rev-parse','HEAD','master'],cwd=R,text=True).splitlines()
check('refs_exact',head==['5fd40966abc84be5bb88a789853273b41f754717','6f68e24e8ddac42b948da8fcc2d636c010751194'])
check('tracked_and_index_clean',not subprocess.check_output(['git','diff','--name-only'],cwd=R) and not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=R))
h=c.host();check('fresh_host216_no_julia_or_prior_groups_sessions',len(h['groups'])==216 and not h['matches'] and h['boot_id']==rd(D/'host.json')['boot_id']);details['host']=h
check('continuation_preimages_current',all(sha(path(k))==sha(v) for k,v in remap.items()))
check('all_pins_still_match_at_finish',bind(m['sha256']))
details.update(pins=1561,required=1561,expected_review_bindings=1562,prior_pins=1503,prior_review_bindings=1504,prior_supplemental=18,predecessor_files=len(files),baseline_files=520,overlay_files=76,runtime='UNEXECUTED')
with (D/'independent-review-checks.json').open('x') as f:json.dump(dict(all_passed=not findings,checks=checks,findings=findings,details=details,scope='offline preparation; no stage, seal, launcher, guard, supervisor or auditor execution'),f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=not findings,checks=len(checks),findings=findings,environment_delta=details['current_environment_delta'])))
sys.exit(1 if findings else 0)
