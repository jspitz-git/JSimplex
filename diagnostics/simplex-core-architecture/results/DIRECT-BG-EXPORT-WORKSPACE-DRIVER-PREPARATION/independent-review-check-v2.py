"""Independent offline review only. No Julia, prior checker, seal or launcher."""
from pathlib import Path
import hashlib,json,sys,copy,tempfile,tomllib,ast,re
D=Path(__file__).resolve().parent;R=D.parents[3];C=R/'diagnostics/direct-bg-export-workspace/reproduce'
sys.dont_write_bytecode=True
sys.path.insert(0,str(D))
# New package definitions only: never call run/main/seal/audit or author scripts.
import guard,oracle,control
checks={};readtime={}
def sha(p):
 p=Path(p);h=hashlib.sha256()
 with p.open('rb') as f:
  for x in iter(lambda:f.read(1048576),b''):h.update(x)
 v=h.hexdigest();readtime[str(p)]=v;return v
def rd(p):return json.loads(Path(p).read_text())
def ck(n,v):
 checks[n]=bool(v)
 if not v:raise AssertionError(n)
def rejects(n,f):
 try:f()
 except (ValueError,RuntimeError,KeyError,TypeError,OSError):ck(n,True)
 else:ck(n,False)
pinfile=D/'preparation-pins.json';pins=rd(pinfile)['sha256'];pinsha=sha(pinfile)
ck('all_1858_pins_rehashed',len(pins)==1858 and all(sha(p)==h for p,h in pins.items()))
ck('exact_required_path_set',set(pins)==set(rd(D/'required-paths.json')['paths']))
for f in D.glob('*.py'):ast.parse(f.read_text(),filename=str(f))
ck('Python_source_parse_only',True)
entry=rd(D/'entry.json');ck('entry_bindings',all(sha(p)==v for p,v in entry['sha256'].items()))
for task in ['TASK1','TASK2']:
 t=D.with_name('DIRECT-BG-EXPORT-WORKSPACE-'+task);v=rd(t/'final-review.json')
 # Verify current directly accepted candidate bindings without replaying older amendment checkers.
 ck(task+'_accepted',v.get('accepted') is True)
 current={p:h for p,h in v.get('readtime_sha256',{}).items() if Path(p).parent==C}
 ck(task+'_candidate_bindings',bool(current) and all(sha(p)==h for p,h in current.items()))
for label,root in [('diagnostic',R),('production',control.W)]:
 b=rd(D/'baseline.json')[label]
 ck(label+'_baseline_hashes',all(sha(root/p)==h for p,h in b.items()))
 ck(label+'_baseline_membership',set(control.git('ls-files','src','test','.github','Project.toml',cwd=root).splitlines())==set(b))
ck('refs_unchanged',control.git('rev-parse','HEAD')==control.ENTRY and control.git('rev-parse','master')==control.MASTER and control.git('rev-parse','HEAD',cwd=control.W)==control.MASTER)
ck('historical_group_set',rd(D/'host.json')['groups']==rd(D.with_name('DIRECT-BG-EXPORT-WORKSPACE-TASK2')/'host-closure.json')['groups'])
stages=rd(D/'stages.json');overlay=rd(C/'overlay-manifest.json')
for mode,count in [('red',75),('green',79)]:
 root=Path(stages[mode]['path']);entries=stages[mode]['sha256'];files={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
 ck(mode+'_stage_membership_and_hashes',len(entries)==count and set(entries)==files and all(sha(root/p)==h for p,h in entries.items()))
 ck(mode+'_stage_no_symlinks',not root.is_symlink() and not any(p.is_symlink() for p in root.rglob('*')))
red=Path(stages['red']['path']);green=Path(stages['green']['path']);origin=Path(stages['red']['source'])
ck('red_original_exact',all((red/p).read_bytes()==(origin/p).read_bytes() for p in stages['red']['sha256']))
adds=overlay['root_additions'];addition=''.join(x['include_literal']+'\n' for x in adds).encode()
groot=(green/'src/JSimplex.jl').read_bytes();rroot=(red/'src/JSimplex.jl').read_bytes()
ck('green_root_exact_inverse',groot.count(addition)==1 and groot.replace(addition,b'',1)==rroot)
ck('green_nonroot_original_exact',all((green/p).read_bytes()==(red/p).read_bytes() for p in stages['red']['sha256'] if p!='src/JSimplex.jl'))
ck('green_candidate_copies',len(adds)==4 and all(sha(green/x['staged_relative'])==sha(x['source'])==x['source_sha256'] for x in adds))
runtime=rd(D/'runtime-inputs-complete.json')['inventory']
ck('runtime_complete_entries',len(runtime)==609 and guard.inventory(list(runtime),[])==runtime)
lineage=rd(D/'control-lineage.json')
ck('prior_control_bindings',all(sha(v['source'])==v['source_sha256'] for v in lineage.values()))
ck('three_helpers_byte_exact',all(sha(D/n)==lineage[n]['source_sha256'] for n in ['guard.py','supervisor.py','recorder.jl']))
expected=rd(D/'expected-tests.json');toml=tomllib.loads((D/'expected-tests.toml').read_text())
counts=[42,6,35,56,108,53,303,6236,378,108,610]
ck('independent_counts',sum(counts)==7935 and [x[1] for x in expected['green']['groups']]==counts)
ck('source_group_order',sum([re.findall(r'@testset "([^"]+)"',(C/n).read_text()) for n in ['workspace-tests.jl','import-tests.jl','lifecycle-tests.jl']],[])==[x[0] for x in expected['green']['groups']])
for mode in ['red','green']:
 ck(mode+'_JSON_TOML_agreement',expected[mode]['assertions']==toml[mode]['assertions'] and expected[mode]['groups']==[[z[k] for k in ['name','pass','fail','error','broken']] for z in toml[mode]['groups']])
 cfg=control.config(mode+'300');loaded=control.loaded_for(cfg)
 def node(name,p=0,f=0,e=0,b=0):return dict(name=name,**{'pass':p,'fail':f,'error':e,'broken':b},failures=['synthetic']*(f+e),children=[])
 root=node('root');root['children']=[node(*z) for z in expected[mode]['groups']]
 raw=dict(phase=cfg['phase'],complete=True,fatal='',loaded=loaded,threads=1,blas_threads=1,tests=root)
 ck(mode+'_synthetic_valid',oracle.test_results(raw,expected[mode],loaded,cfg['phase'])['assertions']==expected[mode]['assertions'])
 mutations=[('phase',lambda x:x.update(phase='other')),('boolean_threads',lambda x:x.update(threads=True)),('extra_key',lambda x:x.update(extra=True)),('wrong_source',lambda x:x['loaded'].update(JSimplex='/wrong')),('group_nesting',lambda x:x['tests']['children'][0]['children'].append(node('extra'))),('missing_group',lambda x:x['tests']['children'].pop()),('broken',lambda x:x['tests']['children'][0].update(broken=1)),('fatal',lambda x:x.update(fatal='failure'))]
 if mode=='green':mutations.append(('compensating_group_counts',lambda x:(x['tests']['children'][0].update({'pass':41}),x['tests']['children'][1].update({'pass':7}))))
 for name,mut in mutations:
  x=copy.deepcopy(raw);mut(x);rejects(mode+'_reject_'+name,lambda:oracle.test_results(x,expected[mode],loaded,cfg['phase']))
 process=dict(reason='wall_time',returncode=-15,pins_unchanged=True);supervisor=dict(returncode=1,hard_timeout=False);log='BEGIN BG export workspace driver '+cfg['phase']
 ck(mode+'_timeout_checkpoint',oracle.timeout_only(process,supervisor,None,log,299,300,loaded,cfg['phase']))
 for name,p,s,r,l,e in [('no_checkpoint',process,supervisor,None,'',299),('error_output',process,supervisor,None,log+'\nERROR:',299),('completed',process,supervisor,raw,log,299),('pressure',dict(process,reason='memory_guard'),supervisor,None,log,299),('hard_kill',process,dict(supervisor,hard_timeout=True),None,log,299),('nan',process,supervisor,None,log,float('nan')),('warning',process,supervisor,None,log+'\nWarning:',299)]:
  ck(mode+'_timeout_reject_'+name,not oracle.timeout_only(p,s,r,l,e,300,loaded,cfg['phase']))
with tempfile.TemporaryDirectory(prefix='bgx-independent-review-') as tmp:
 t=Path(tmp);tree=t/'stage';tree.mkdir();f=tree/'root';f.write_bytes(b'original');q=t/'pins'
 inv=guard.inventory([], [str(tree)]);p=dict(files=[],trees=[str(tree)],inventory=inv)
 ck('synthetic_stage_pins_match',guard.pins_match(p))
 f.write_bytes(b'changed');ck('wrong_content_refused',not guard.pins_match(p));f.write_bytes(b'original')
 extra=tree/'extra';extra.write_bytes(b'x');ck('extra_stage_file_refused',not guard.pins_match(p));extra.unlink()
 f.unlink();ck('missing_stage_file_refused',not guard.pins_match(p))
 other=t/'other';other.write_bytes(b'original');f.symlink_to(other);ck('same_bytes_resolved_path_drift_refused',not guard.pins_match(p));f.unlink();f.write_bytes(b'original')
 q.write_text('pin');v=dict(accepted=True,findings=[],scope='review',phase='red300',pins_sha256=sha(q),sha256={str(q):sha(q)})
 control.verify_review(v,q,[str(q)],'review','red300');ck('synthetic_exact_review',True)
 for key,value in [('phase','green300'),('scope','other'),('accepted',False),('findings',['x']),('pins_sha256','wrong'),('sha256',{})]:
  x=dict(v);x[key]=value;rejects('review_refuses_'+key,lambda:control.verify_review(x,q,[str(q)],'review','red300'))
 reservation=t/'reservation.json';control.save(reservation,dict(attempt=1));rejects('exclusive_reservation_reuse',lambda:control.save(reservation,dict(attempt=1)))
for phase in ['red300','green300','red600','green600']:
 cfg=control.config(phase);cmd=control.guard_command(cfg,D/'synthetic-unused',123.0)
 ck(phase+'_time_bounds',cfg['seconds']==(300 if phase.endswith('300') else 600) and float(cmd[cmd.index('--seconds')+1])==cfg['seconds']-8 and float(cmd[cmd.index('--deadline')+1])==123+cfg['seconds']-8)
ck('no_phase_artifacts',not (D/'runs').exists())
fixture=(C/'../../direct-lu-policy-adapters/reproduce/fixtures.jl').resolve();sha(fixture)
ck('confirmed_missing_transitive_fixture',str(fixture) not in pins and not any(fixture.is_relative_to(Path(t)) for t in [str(C),stages['red']['path'],stages['green']['path']]))
readtime={k:v for k,v in readtime.items() if Path(k).exists()}
result=dict(all_checks_passed=all(checks.values()),checks=checks,pinned_files_verified=len(pins),pins_sha256=pinsha,sha256=readtime,findings=[dict(id='R1',severity='important',path=str(D/'freeze-preparation.py'),summary='Transitive fixture source is omitted from preparation pins and future seal trees',missing=str(fixture))],scope='Independent offline evidence only; no Julia or launch')
with (D/'independent-review-check-v2.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(checks=len(checks),passed=result['all_checks_passed'],pins_verified=len(pins),findings=result['findings'])))
