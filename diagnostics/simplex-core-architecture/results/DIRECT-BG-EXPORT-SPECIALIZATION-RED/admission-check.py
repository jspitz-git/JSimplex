"""Independent exact RED300 admission check. No launcher, seal, auditor or Julia execution."""
from pathlib import Path
import ast,json,hashlib,sys,os,time,subprocess
Q=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-SPECIALIZATION-RED')
D=Q.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-DRIVER');R=D.parents[3];RUN=D/'runs/red300'
sys.path.insert(0,str(D));import control as c
checks={};evidence={};hashes={}
def ck(n,v):
 checks[n]=bool(v)
 if not v:raise AssertionError(n)
def rd(p):return json.loads(Path(p).read_text())
def sha(p):
 p=str(p)
 if p not in hashes:
  h=hashlib.sha256()
  with open(p,'rb') as f:
   for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
  hashes[p]=h.hexdigest()
 return hashes[p]
def bindings(m):return all(sha(c.path(p))==h for p,h in m.items())
def git(*args,root=R):return subprocess.check_output(['git',*args],cwd=root,text=True).strip()
try:
 s=rd(RUN/'sealed.json');cfg=s['config'];ready=rd(Q/'outer-ready.json');outer=ready['identity']
 ck('phase_config',s['phase']=='red300' and cfg==c.config('red300')==rd(RUN/'config.json') and cfg['seconds']==300 and cfg['expected_exit']==1)
 ck('no_release_invocation_outcome',all(not (Q/n).exists() for n in ['release.json','outer-invocation.json','outer-outcome.json']))
 ck('no_numerical_attempt',set(p.name for p in RUN.iterdir())=={'host.json','config.json','sealed.json'})
 ck('live_outer_identity',c.guard.process_identity(outer['pid'])==outer==s['outer_identity'] and outer['pid']==outer['pgid']==outer['sid'] and outer['start_ticks']>0)
 ck('outer_binding',ready['phase']=='red300' and ready['waiting_only'] is True and ready['script_sha256']==sha(Q/'outer.py') and ready['expected_launcher']==str(D/'launch.py'))
 source=(Q/'outer.py').read_text();tree=ast.parse(source)
 f=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='valid_release');ns={'PHASE':'red300'}
 exec(compile(ast.Module(body=[f],type_ignores=[]),'pure-release-function','exec'),ns)
 v=dict(phase='red300',sealed_sha256='s',admission_sha256='a',outer_ready_sha256='i',one_attempt=True)
 ck('release_exact',ns['valid_release'](v,'s','a','i'))
 for k in v:
  z=dict(v);z[k]='invalid';ck('reject_release_'+k,not ns['valid_release'](z,'s','a','i'))
 ck('reject_release_extra',not ns['valid_release'](dict(v,extra=True),'s','a','i'))
 ck('reject_release_missing',all(not ns['valid_release']({a:b for a,b in v.items() if a!=k},'s','a','i') for k in v))
 ck('reject_release_type',not ns['valid_release']([],'s','a','i'))
 invocation='runpy.run_path(str(D/\'launch.py\'),run_name=\'__main__\')'
 ck('one_sameprocess_invocation',source.count(invocation)==1 and "sys.argv=[str(D/'launch.py'),PHASE]" in source)
 ck('gates_before_invocation',all(source.index(t)<source.index(invocation) for t in ['c.require(valid_release(', 'c.verify_review(', "s['outer_identity']==identity", 'c.guard.pins_match(s)']))
 ck('bounded_wait', 'deadline=time.monotonic()+1200' in source and 'while not (Q/\'release.json\').exists():' in source)
 # Exact reverse of the three explicit additions and relocated import; no original seal execution.
 supplemented=(Q/'seal-outer.py').read_text()
 supplemented=supplemented.replace("from pathlib import Path\nimport sys\nQ=Path(__file__).resolve().parent\nD=Q.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-DRIVER')\nsys.path.insert(0,str(D))\nfrom control import *",'from control import *')
 supplemented=supplemented.replace("require(phase=='red300','Only authorized RED300');ready=rd(Q/'outer-ready.json');outer=ready['identity']\n require(guard.process_identity(outer['pid'])==outer and outer['pid']==outer['pgid']==outer['sid'],'Outer not alive/isolated')\n require(ready['script_sha256']==sha(Q/'outer.py') and ready['phase']==phase and ready['waiting_only'] is True,'Outer ready linkage')\n cfg=config(phase);validate_environment();",'cfg=config(phase);validate_environment();')
 supplemented=supplemented.replace("extra_paths=rd(Q/'outer-required.json')['paths']\n require(all(Path(p).is_file() for p in extra_paths),'Outer inputs missing')\n files=sorted(set(files+extra_paths))\n # All production tracked bytes and immutable outer wrapper inputs pinned.",'# All production tracked bytes individually pinned; no .git tree/cache snapshot.')
 supplemented=supplemented.replace("dict(phase=phase,outer_identity=outer,head=h['head']","dict(phase=phase,head=h['head']")
 ck('seal_original_exact_inverse',supplemented==(D/'seal.py').read_text())
 old=rd(Q/'outer-offline-check.json')
 ck('author_offline14',old['all_passed'] is True and len(old['checks'])==14 and all(old['checks'].values()) and bindings(old['sha256']))
 prep=rd(D/'preparation-pins.json');review=rd(D/'review.json')
 ck('preparation2097',len(prep['sha256'])==2097 and set(prep['sha256'])==set(rd(D/'required-paths.json')['paths']) and bindings(prep['sha256']))
 ck('accepted_preparation_exact',review['accepted'] is True and review['findings']==[] and review['scope']=='BG specialization driver preparation' and review['red_expectation_supported'] is True and review['pins_sha256']==sha(D/'preparation-pins.json') and set(review['sha256'])==set(prep['sha256'])|{str(D/'preparation-pins.json')} and bindings(review['sha256']) and bindings(review['evidence_sha256']))
 actual=set(s['files'])
 for root in s['trees']:
  root=Path(root);ck('tree_no_symlink_'+root.name,not root.is_symlink() and not any(p.is_symlink() for p in root.rglob('*')))
  actual|={str(p) for p in root.rglob('*') if p.is_file()}
 ck('sealed_inventory_membership',actual==set(s['inventory']))
 ck('sealed_inventory_full_rehash',all(str(Path(p).resolve(strict=True))==z['resolved'] and sha(p)==z['sha256'] for p,z in s['inventory'].items()))
 required=set(prep['sha256'])|{str(D/'preparation-pins.json'),str(D/'review.json')}|set(rd(D/'runtime-inputs-complete.json')['inventory'])|set(rd(Q/'outer-required.json')['paths'])|{str(RUN/'host.json'),str(RUN/'config.json')}
 for label,root in [('diagnostic',R),('production',c.W)]:
  b=rd(D/'baseline.json')[label];required|={str(root/n) for n in b}
  ck('baseline_membership_'+label,set(git('ls-files','src','test','.github','Project.toml',root=root).splitlines())==set(b))
  ck('baseline_bytes_'+label,all(sha(root/n)==h for n,h in b.items()))
 st=rd(D/'stages.json')['red'];required|={str(Path(st['path'])/n) for n in st['sha256']}
 ck('exact_sealed_files',set(s['files'])==required and len(s['files'])==2111)
 ck('stage83',len(st['sha256'])==83 and set(str(p.relative_to(st['path'])) for p in Path(st['path']).rglob('*') if p.is_file())==set(st['sha256']) and all(sha(Path(st['path'])/n)==h for n,h in st['sha256'].items()))
 rt=rd(D/'runtime-inputs-complete.json')['inventory'];ck('runtime609',len(rt)==609 and all(s['inventory'][p]==z for p,z in rt.items()))
 ck('environment', {k:os.environ.get(k) for k in rd(D/'environment.json')}==rd(D/'environment.json'))
 ck('refs',git('rev-parse','HEAD')==s['head']=='e780e6158ea5365adf5cde36dceaa8032a34fe9c' and git('rev-parse','master')==s['master']==c.MASTER and git('rev-parse','HEAD',root=c.W)==c.MASTER and c.MASTER+'\trefs/heads/master' in git('ls-remote','origin','refs/heads/master'))
 ck('ancestor',subprocess.run(['git','merge-base','--is-ancestor',c.ENTRY,'HEAD'],cwd=R).returncode==0)
 ck('tracked_clean',not git('diff','--name-only') and not git('diff','--cached','--name-only'))
 h=c.full_host(s['groups']);evidence['actual_host']=h;mem=c.guard.memory();evidence['memory']=mem
 ck('historical256_group_session_closed',len(s['groups'])==256 and h['groups']==s['groups'] and c.host_safe(h))
 ck('current_host_identity',all(h[k]==s[k] for k in ['head','master','boot_id']))
 ck('resources',not c.guard.pressure(mem))
 ho=c.full_host(s['groups']+[outer['pgid'],outer['sid']]);evidence['host_including_live_outer']=ho
 ck('outer_live_not_claimed_closed',len(ho['matches'])==1 and all(ho['matches'][0][k]==outer[k] for k in outer) and not ho['unreadable_identity_pids'])
 ck('guard292',c.guard_command(cfg,RUN/'synthetic-pins',100.)[6:10]==['--seconds','292','--deadline','392.0'])
 exp=rd(D/'expected-tests.json')['red'];ck('exact_three_expected',exp=={'groups':[['allocation_nonincrease_sparse32',0,1,0,0],['allocation_nonincrease_dense32',0,1,0,0],['allocation_nonincrease_sparse96',0,1,0,0]],'assertions':3})
 historical=(D.parent/'DIRECT-BG-EXPORT-WORKSPACE-COST-PREPARATION/cost.jl').read_text();body=historical[historical.index('token(x::Float64)'):historical.index('# Untimed bounded controls')].replace('function save(name,data)','function save_window(name,data)')
 ck('red_original_kernel', (D/'red-kernel.jl').read_text()=='# UNEXECUTED. Exact old lifecycle/window body except save name and candidate namespace.\n'+body)
 audit=(D/'audit.py').read_text();launch=(D/'launch.py').read_text();driver=(D/'driver.jl').read_text();oracle=(D/'allocation_oracle.py').read_text()
 ck('expected_exit_only_all_gates',"require(audit(phase)['all_passed']" in launch and "p['returncode']==cfg['expected_exit']" in audit and "log.count('TEST FAILURE:')==(3 if cfg['mode']=='red' else 0)" in audit and 'allocation_results(rows,' in audit and 'test_results(raw,' in audit)
 ck('all60_windows_and_residual_route','for c in range(1,4) for w in range(1,21)' in oracle and 'window_ok(r,f,1,pair,order,matrices)' in oracle and 'for pair in range(1,11)' in oracle and 'for order in (1,2)' in oracle)
 ck('unchanged_allocation_gate','median7(cands_events)<=median7(refs_events) && median7(cands_bytes)<=median7(refs_bytes)' in driver)
 ck('no_green_red_suite', 'if MODE=="green"' in driver and "PHASE='red300'" in source)
 ck('no_auto_retry',source.count(invocation)==1 and "supervisor.run(cmd,log,cfg['output'],started,cfg['seconds'])" in launch)
 ck('external_outer_closure_requirement',all(t in (Q/'EXECUTION.md').read_text() for t in ['After the outer returns','PGID AND SID','verify fullgroup/session absence','future GREEN must explicitly']))
 ck('outer_still_waiting',c.guard.process_identity(outer['pid'])==outer and not (Q/'release.json').exists())
except Exception as e:
 evidence['error']=repr(e)
finally:
 result=dict(all_passed=bool(checks) and all(checks.values()) and 'error' not in evidence,checks=checks,evidence=evidence,sealed_sha256=sha(RUN/'sealed.json'),sha256={str(Path(__file__)):sha(__file__)},scope='Independent offline exact RED300 admission; actual host read-only; no numerical execution')
 with (Q/'admission-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({'all_passed':result['all_passed'],'checks':len(checks),'error':evidence.get('error'),'rehash_paths':len(hashes),'outer':outer,'memory':evidence.get('memory')}))
 if not result['all_passed']:sys.exit(1)
