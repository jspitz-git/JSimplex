"""Fresh OFFLINE RED2 review. No Julia or launch/outer/seal/guard execution.
Only definitions modules and pure synthetic data generation are imported.
Writes a new reviewer evidence file named by argv[1]; never author evidence.
"""
from pathlib import Path
from unittest.mock import patch
from contextlib import ExitStack
import ast, copy, hashlib, importlib.util, json, os, subprocess, sys, tempfile
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
D=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-RED2-HARNESS'
H=D.with_name('DIRECT-BG-BLOCKED-UPDATE-HARNESS'); S=D.with_name('DIRECT-BG-BLOCKED-UPDATE-STAGE-REPAIR')
sys.dont_write_bytecode=True;sys.path.insert(0,str(D))
import control as c
import audit as a
import oracle as o
checks={}
def ck(n,v):
 if not v: raise AssertionError(n)
 checks[n]=True
def reject(n,f):
 try:f()
 except (ValueError,RuntimeError,KeyError,TypeError,FileNotFoundError):ck(n,True)
 else:raise AssertionError('Accepted invalid '+n)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True).strip()
pins=rd(D/'preparation-pins.json');required=rd(D/'required-paths.json')['paths']
ck('347_exact_membership',len(pins['sha256'])==len(required)==len(set(required))==347 and set(required)==set(pins['sha256']))
for p,h in pins['sha256'].items():ck('preparation_hash:'+p,sha(p)==h)
local_names='ADMISSION.md MEMORY-WORK.md REPORT.md adaptations.json assertion-sites.json audit.py auditor-tests.json auditor-tests.py baseline.json control.py copied-files.json driver.jl entry.json environment.json finish-preparation.py guard.py host-entry.json launch.py lifecycle-tests.jl loaded-paths.json numerical-tests.jl oracle.py outer.py panel-tests.jl post-return.py prepare.py progress.md.after-red2 progress.md.before-red2 recorder.jl required-paths.json routing-source-red.json routing-tests.json routing-tests.py runtime-inputs-complete.json schedule.json seal.py source-check.json stages.json supervisor.py synthetic-data.py test-transform.json'.split()
expected=set(rd(H/'preparation-pins-reviewed.json')['sha256'])|set(rd(H/'review.json')['sha256'])|set(rd(H/'review.json').get('evidence_sha256',{}))|{str(H/'review.json')}
expected |=set(rd(S/'publication.json')['sha256'])|{str(S/'publication.json')}|set(rd(S/'review.json')['sha256'])|set(rd(S/'review.json').get('evidence_sha256',{}))|set(rd(S/'stage.json')['sha256'])|{str(D/n) for n in local_names}
ck('independent_transitive_membership',expected==set(required))
ck('HEAD',git('rev-parse','HEAD')==c.ENTRY);ck('master',git('rev-parse','master')==c.MASTER)
ck('clean_tracked',not git('diff','--name-only') and not git('diff','--cached','--name-only'))
for label,root in [('diagnostic',R),('production',c.W)]:
 b=rd(D/'baseline.json')[label]
 members=subprocess.check_output(['git','ls-files','src','test','.github','Project.toml'],cwd=root,text=True).splitlines()
 ck('baseline_membership:'+label,set(members)==set(b))
 for n,h in b.items():ck('baseline:'+label+':'+n,sha(root/n)==h)
for n,item in rd(D/'copied-files.json').items():ck('frozen_copy:'+n,sha(D/n)==sha(item['source'])==item['sha256'])
for n in ['launch.py','outer.py','audit.py']:ck('scope_only:'+n,(D/n).read_text().replace('BG blocked U RED2 exact-stage admission','BG blocked U exact-stage admission')==(H/n).read_text())
def funcs(p):return {n.name:ast.dump(n) for n in ast.parse(p.read_text()).body if isinstance(n,ast.FunctionDef)}
f,g=funcs(D/'control.py'),funcs(H/'control.py')
ck('five_control_function_changes',{n for n in set(f)|set(g) if f.get(n)!=g.get(n)}=={'config','validate_sources','validate_stage_binding','preparation','predecessor'})
for p in D.glob('*.py'):ast.parse(p.read_text());ck('Python_syntax:'+p.name,True)
m=rd(S/'stage.json');stage=Path(m['stage'])
ck('75_stage_members',len(m['stage_files'])==75 and {str(p.relative_to(stage)) for p in stage.rglob('*') if p.is_file()}==set(m['stage_files']))
ck('no_stage_symlinks',not stage.is_symlink() and not any(p.is_symlink() for p in stage.rglob('*')))
for n,h in m['stage_files'].items():ck('stage:'+n,sha(stage/n)==h)
for n in m['master_files']:
 blob=subprocess.check_output(['git','show',c.MASTER+':'+n],cwd=R)
 data=(stage/n).read_bytes()
 if n=='src/JSimplex.jl':data=data.replace(m['root_insertion'].encode(),b'')
 ck('committed_master:'+n,data==blob)
c.validate_stage_binding();ck('stage_binding',True)
for n,h in rd(S/'verification.json')['candidate_sha256'].items():ck('candidate14:'+n,sha(n)==h)
c.validate_environment();ck('environment_exact',True)
runtime=rd(D/'runtime-inputs-complete.json')['inventory']
for n,v in runtime.items():ck('runtime:'+n,str(Path(n).resolve(strict=True))==v['resolved'] and sha(n)==v['sha256'])
ck('runtime_count',len(runtime)==609)
cfg=c.config('red300');ck('private_roots',cfg['run']==str(D/'runs/red300') and cfg['output']==str(D/'runs/red300/output') and c.outer_dir('red300')==D/'outers/red300')
ck('exact_stage_mode_budget',cfg['stage']==str(stage) and cfg['mode']=='red' and cfg['seconds']==300 and cfg['expected_exit']==1)
cmd=c.guard_command(cfg,D/'dummy-pins',100.)
ck('inner_absolute_deadline',cmd[cmd.index('--seconds')+1]=='292' and cmd[cmd.index('--deadline')+1]=='392.0')
ck('fixed_Julia_flags',all(x in cfg['command'] for x in ['--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G']))
ck('actual_stage_loaded_path',c.loaded_for(cfg)['JSimplex']==str(stage/'src/JSimplex.jl'))
for phase in ['green300','red600','green600','red','RED300','../red300','',None,1]:
 reject('phase_refusal:'+repr(phase),lambda phase=phase:c.config(phase))
 reject('outer_phase_refusal:'+repr(phase),lambda phase=phase:c.outer_dir(phase))
ck('no_old_qualification_dependency',c.predecessor('red300')==([],[]))
ck('271_historic_groups',len(rd(D/'host-entry.json')['groups'])==271 and len(set(rd(D/'host-entry.json')['groups']))==271)
ck('both_group_and_session_source',"int(a[2]) in groups or int(a[3]) in groups" in (D/'control.py').read_text())
ck('old_RED_unaccepted',rd(H/'runs/red300/audit.json')['all_passed'] is False and not (H/'runs/red300/result-review.json').exists())
real_rd=c.rd
for name,mut in [('old_stage',lambda x:x['red'].update(path=m['failed_stage'])),('changed_stage_hash',lambda x:x['red']['sha256'].update({'src/JSimplex.jl':'0'*64})),('green_stage',lambda x:x.update(green=x['red']))]:
 bad=copy.deepcopy(rd(D/'stages.json'));mut(bad)
 with patch.object(c,'rd',lambda p:bad if Path(p)==D/'stages.json' else real_rd(p)):reject('stage_refusal:'+name,c.validate_stage_binding)
# A synthetic review exists only in memory; it is not launch admission.
receipt=dict(accepted=True,findings=[],scope='BG blocked U RED2 preparation',launch_admitted=False,pins_sha256=sha(D/'preparation-pins.json'),sha256={**pins['sha256'],str(D/'preparation-pins.json'):sha(D/'preparation-pins.json')})
c.verify_review(receipt,D/'preparation-pins.json',list(receipt['sha256']),receipt['scope']);ck('348_receipt_positive',len(receipt['sha256'])==348)
for name,changes in [('old_scope',dict(scope='BG blocked U driver preparation')),('old_exact_scope',dict(scope='BG blocked U exact-stage admission')),('accepted_number',dict(accepted=1)),('findings',dict(findings=['x'])),('pins_hash',dict(pins_sha256='0'*64)),('missing_input',dict(sha256={})),('extra_input',dict(sha256={**receipt['sha256'],'/tmp/unrequested':'0'*64}))]:
 bad={**receipt,**changes};reject('receipt_refusal:'+name,lambda bad=bad:c.verify_review(bad,D/'preparation-pins.json',list(receipt['sha256']),receipt['scope']))
with patch.object(c,'rd',lambda p:receipt if Path(p)==D/'review.json' else real_rd(p)):
 prepared=c.preparation();ck('preparation_returns_exact_closure',set(prepared)==set(receipt['sha256'])|{str(D/'review.json')})
 files=c.seal_files(cfg,prepared,[])
 ck('future_seal_runtime',set(runtime)<=set(files))
 ck('future_seal_stage',set(m['sha256'])<=set(files))
 ck('future_seal_roots',all(str(Path(cfg['run'])/n) in files for n in ['host.json','config.json']) and str(D/'outers/red300/outer-ready.json') in files)
 sealed=dict(files=files,trees=[cfg['stage'],str(c.C)],inputs=[],inventory={})
 with patch.object(c.guard,'inventory',lambda *args:{}):
  c.verify_seal(cfg,sealed);ck('future_exact_seal',True)
  for name,change in [('missing_file',dict(files=files[:-1])),('extra_file',dict(files=files+['/tmp/unrequested'])),('old_stage_tree',dict(trees=[m['failed_stage'],str(c.C)])),('extra_input',dict(inputs=['x'])),('inventory',dict(inventory={'x':1}))]:
   reject('seal_refusal:'+name,lambda change=change:c.verify_seal(cfg,{**sealed,**change}))
bad={**receipt,'launch_admitted':True}
with patch.object(c,'rd',lambda p:bad if Path(p)==D/'review.json' else real_rd(p)):reject('preparation_cannot_admit_launch',c.preparation)
for name in ['launch.py','outer.py','audit.py']:ck('new_exact_scope:'+name,'BG blocked U RED2 exact-stage admission' in (D/name).read_text())
# Fresh pure-oracle cases; no historical test runner is executed.
spec=importlib.util.spec_from_file_location('review_synthetic_data',D/'synthetic-data.py');sm=importlib.util.module_from_spec(spec);spec.loader.exec_module(sm)
raw,units=sm.mock('red');schedule=rd(D/'schedule.json')
ck('28_units_13_fixtures',len(schedule['units'])==28 and len(schedule['fixtures'])==13)
ck('512_replacements_begins_finishes',sum(f['updates'] for f in schedule['fixtures'])*4==512)
ck('six_named_N026',schedule['expected_red_units']==[f'{n}/{b}' for n in ['dense96','dense256','dense96-long32'] for b in ['native','markowitz']])
ck('complete_oracle_synthetic',o.test_results(raw,units,schedule,{},'red300')['expected_failures']==6)
for msg in ['Warning: test','WORLD AGE','method foo overwritten','method overwrite']:
 ck('warning_rejection:'+msg,o.warning_log(msg))
for name,mut in [('wrong_failure_site',lambda r,u:u['unit-9.toml']['records']['failures'][0].update(site='N005')),('missing_unit',lambda r,u:u.pop('unit-28.toml')),('extra_unit',lambda r,u:u.update({'unit-29.toml':u['unit-28.toml']})),('incomplete_raw',lambda r,u:r.update(complete=False)),('threads_bool',lambda r,u:r.update(threads=True)),('growth_nan',lambda r,u:u['unit-3.toml']['observations'][0].update(growth=float('nan'))),('wrong_loaded',lambda r,u:r.update(loaded={'JSimplex':'wrong'})),('missing_API',lambda r,u:u['unit-3.toml']['records']['apis'].pop('BTRAN')),('unknown_event',lambda r,u:u['unit-3.toml']['records']['events'].update(untracked=1)),('begin_mismatch',lambda r,u:u['unit-3.toml']['records']['events'].update(event_begin=15)),('assertion_missing',lambda r,u:u['unit-3.toml']['records']['sites'].pop('N005')),('hidden_error',lambda r,u:u['unit-3.toml']['tests'].update(error=1))]:
 r,u=copy.deepcopy((raw,units));mut(r,u);reject('oracle_refusal:'+name,lambda:o.test_results(r,u,schedule,{},'red300'))
# New full auditor exercise uses temporary JSON as TOML transport. Real oracle
# runs, but host/hash/review/process execution is not evidence from these mocks.
with tempfile.TemporaryDirectory(prefix='review-red2-') as tmp:
 root=Path(tmp);run=root/'run';out=run/'output';outer=root/'outer';out.mkdir(parents=True);outer.mkdir()
 cc=dict(phase='red300',mode='red',seconds=300,expected_exit=1,stage='synthetic',run=str(run),output=str(out),command=['synthetic'])
 ident=dict(pid=99,pgid=99,sid=99,start_ticks=1,boot_id='b',command='synthetic')
 host=dict(head='h',master=c.MASTER,boot_id='b',groups=[99],matches=[],unreadable_identity_pids=[],remote='h\trefs/heads/codex/simplex-core-architecture\n'+c.MASTER+'\trefs/heads/master')
 s=dict(phase='red300',config=cc,head='h',master=c.MASTER,boot_id='b',groups=[99],files=[str(outer/'outer-ready.json')],trees=[],inventory={})
 pp=dict(files=s['files']+[str(run/n) for n in ['sealed.json','admission.json','prehost.json']]+[str(outer/n) for n in ['release.json','outer-invocation.json']],trees=[],inventory={})
 mem=dict(available_kib=7*1024**2,swap_used_kib=0)
 process=dict(runner=ident,child=ident,pins_unchanged=True,command=cc['command'],pins_sha256='hash',terminal_memory=mem,child_maxrss_kib=100,returncode=1,reason='exit1')
 inv=dict(supervisor=dict(guard_identity=ident,returncode=0,accepted=True,elapsed_seconds=2.),elapsed_seconds=2.,command=cc['command'],pins_sha256='hash',guard_command=['synthetic_guard'],monotonic_start=1.,python=sys.executable,reservation_sha256='hash',review_sha256='hash')
 docs={'sealed.json':s,'config.json':cc,'admission.json':{},'launch-pins.json':pp,'invocation.json':inv,'host.json':host,'prehost.json':host,'posthost.json':host,'reservation.json':dict(one_attempt=True,phase='red300',command=cc['command'],pins_sha256='hash',review_sha256='hash',max_seconds=300)}
 log='BEGIN BG blocked U driver red300\n'+''.join(f'UNIT BEGIN {i} {n}\nUNIT END {i} {n}\n' for i,n in enumerate(schedule['units'],1))+'TEST FAILURE:\n'*6
 def reset():
  for p in out.iterdir():p.unlink()
  for n,v in docs.items():(run/n).write_text(json.dumps(v))
  for n,v in {**units,'raw.toml':raw,'pins.json':pp,'current.json':dict(runner=ident,child=ident,command=cc['command'],pins_sha256='hash'),'process.json':process}.items():(out/n).write_text(json.dumps(v))
  (out/'resources.jsonl').write_text(json.dumps(mem)+'\n');(out/'run.log').write_text(log);(run/'launcher.log').write_text('')
 def change(n,fn,parent=out):
  p=parent/n;j=rd(p);fn(j);p.write_text(json.dumps(j))
 with ExitStack() as stack:
  for name,fn in dict(config=lambda p:cc,validate_environment=lambda:None,preparation=lambda:[],validate_sources=lambda:None,predecessor=lambda p:([],[]),verify_seal=lambda *x:None,verify_outer_invocation=lambda *x:None,verify_review=lambda *x:None,sha=lambda p:'hash',outer_dir=lambda p:outer,guard_command=lambda *x:['synthetic_guard'],loaded_for=lambda cfg:{}).items():stack.enter_context(patch.object(a,name,fn))
  stack.enter_context(patch.object(a.guard,'pins_match',lambda p:True));stack.enter_context(patch.object(a.tomllib,'loads',json.loads))
  reset();ck('full_auditor_synthetic_positive',a.checks_for('red300')['all_passed'])
  mutations={
   'unit_missing':lambda:(out/'unit-28.toml').unlink(),
   'raw_missing':lambda:(out/'raw.toml').unlink(),
   'warning':lambda:(out/'run.log').write_text(log+'Warning: test'),
   'world_age_launcher':lambda:(run/'launcher.log').write_text('world-age warning'),
   'extra_output':lambda:(out/'extra').write_text('x'),
   'elapsed_nan':lambda:change('invocation.json',lambda j:j.update(elapsed_seconds=float('nan')),run),
   'elapsed_301':lambda:change('invocation.json',lambda j:j.update(elapsed_seconds=301),run),
   'cleanup_failure':lambda:change('invocation.json',lambda j:j['supervisor'].update(cleanup_error='failed'),run),
   'bad_exit':lambda:change('process.json',lambda j:j.update(returncode=0)),
   'remaining_process':lambda:change('posthost.json',lambda j:j.update(matches=[99]),run),
   'unreadable_identity':lambda:change('posthost.json',lambda j:j.update(unreadable_identity_pids=[99]),run),
   'missing_session_coverage':lambda:change('posthost.json',lambda j:j.update(groups=[]),run),
   'changed_start_ticks':lambda:change('current.json',lambda j:j['child'].update(start_ticks=2)),
   'low_RAM':lambda:change('process.json',lambda j:j['terminal_memory'].update(available_kib=1)),
   'missing_samples':lambda:(out/'resources.jsonl').write_text(''),
   'nonboolean_reservation':lambda:change('reservation.json',lambda j:j.update(one_attempt=1),run),
   'missing_log_end':lambda:(out/'run.log').write_text(log.replace('UNIT END 28','OTHER 28')),
   'failure_site':lambda:change('unit-9.toml',lambda j:j['records']['failures'][0].update(site='N025'))}
  for name,fn in mutations.items():reset();fn();reject('full_auditor_refusal:'+name,lambda:a.checks_for('red300'))
  reset()
  for p in list(out.iterdir()):
   if p.name=='raw.toml' or p.name.startswith('unit-'):p.unlink()
  change('process.json',lambda j:j.update(returncode=-15,reason='wall_time'))
  change('invocation.json',lambda j:j['supervisor'].update(returncode=1,accepted=False,hard_timeout=False),run)
  (out/'run.log').write_text('BEGIN BG blocked U driver red300\n')
  t=a.checks_for('red300');ck('pure_timeout_remains_failure',t['pure_timeout'] and not t['all_passed'])
  (out/'unit-1.toml').write_text('{');reject('malformed_prefix_refusal',lambda:a.checks_for('red300'))
  reset();change('raw.toml',lambda j:j.update(complete=False));result=a.audit('red300');ck('full_audit_saved_failclosed',result['all_passed'] is False and rd(run/'audit.json')['all_passed'] is False)
for name,count in [('routing-tests.json',25),('auditor-tests.json',31),('source-check.json',44)]:
 j=rd(D/name);ck('author_receipt:'+name,j['all_passed'] is True and len(j['checks'])==count and all(j['checks'].values()))
ck('no_run_artifacts',not any((D/n).exists() for n in ['runs','outers','sealed.json','reservation.json']))
# All immutable inputs remain identical after reviewer checks.
ck('preparation_unchanged_after',all(sha(p)==h for p,h in pins['sha256'].items()))
evidence=dict(all_passed=True,scope='Independent OFFLINE RED2 preparation checks; not runtime acceptance',check_count=len(checks),checks=checks,preparation_inputs=347,review_inputs=348,stage_files=75,runtime_files=609,runtime_bytes=sum(Path(n).stat().st_size for n in runtime),launch_admitted=False,runtime_acceptance=False,numerical_acceptance=False,performance_acceptance=False,mock_boundaries='Full auditor uses mocked host/ref/hash/admission and JSON transport for TOML; pure oracle, schema/count/resource/failure checks remain real. No actual process execution.',pins_sha256=sha(D/'preparation-pins.json'))
with Path(sys.argv[1]).open('x') as f:json.dump(evidence,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in evidence.items() if k!='checks'}))
