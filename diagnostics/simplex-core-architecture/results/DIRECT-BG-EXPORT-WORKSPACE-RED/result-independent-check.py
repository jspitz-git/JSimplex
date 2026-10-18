"""Independent saved-result and fresh host closure verification; no old scripts imported/run."""
from pathlib import Path
import hashlib,json,os,re,subprocess,time,tomllib,math
E=Path(__file__).resolve().parent;D=E.with_name('DIRECT-BG-EXPORT-WORKSPACE-DRIVER-PREPARATION');R=D.parents[3];run=D/'runs/red300';out=run/'output';checks={};hashes={};bytes_read=0
def rd(p):return json.loads(Path(p).read_text())
def sha(p):
 global bytes_read
 p=str(p)
 if p not in hashes:
  h=hashlib.sha256()
  with Path(p).open('rb') as f:
   for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk);bytes_read+=len(chunk)
  hashes[p]=h.hexdigest()
 return hashes[p]
def ck(n,v):checks[n]=bool(v)
def bindings(v):return all(sha(n)==h for n,h in v.items())
def save(p,v):
 with Path(p).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True).strip()
s=rd(run/'sealed.json');ad=rd(run/'admission.json');cfg=rd(run/'config.json');pins=rd(run/'launch-pins.json');a=rd(run/'audit.json');p=rd(out/'process.json');cur=rd(out/'current.json');inv=rd(run/'invocation.json');sup=inv['supervisor'];res=rd(run/'reservation.json');post=rd(run/'posthost.json');pre=rd(run/'prehost.json');host=rd(run/'host.json')
files={str(z) for z in run.rglob('*') if z.is_file()};names={str(z.relative_to(run)) for z in run.rglob('*') if z.is_file()}
expected={'host.json','config.json','sealed.json','admission.json','prehost.json','launch-pins.json','reservation.json','launcher.log','invocation.json','posthost.json','audit.json','output/pins.json','output/current.json','output/process.json','output/resources.jsonl','output/run.log','output/raw.toml'}
ck('exact17_run_files',names==expected and not any(z.is_symlink() for z in run.rglob('*')))
ck('one_requested_phase_only',{z.name for z in (D/'runs').iterdir()}=={'red300'} and rd(E/'authorization.json')['one_attempt'] is True and rd(E/'authorization.json')['no_green'] is True)
ck('admission_scope_accepted',ad['accepted'] is True and ad['findings']==[] and ad['scope']=='BG export workspace exact-stage admission' and ad['phase']=='red300')
ck('admission_exact_binding_membership',set(ad['sha256'])==set(s['files'])|{str(run/'sealed.json')} and ad['pins_sha256']==sha(run/'sealed.json'))
ck('all_admission_and_evidence_hashes',bindings(ad['sha256']) and bindings(ad['evidence_sha256']))
for label,v in [('sealed',s),('launch',pins)]:
 actual=set(v['files'])
 for tree in v['trees']:
  root=Path(tree);paths=list(root.rglob('*'));ck(label+'_tree_'+root.name,root.is_dir() and not root.is_symlink() and not any(z.is_symlink() and (z.is_dir() or not z.exists()) for z in paths));actual.update(str(z) for z in paths if z.is_file())
 ck(label+'_exact_inventory',actual==set(v['inventory']))
 ck(label+'_all_resolved_paths_hashes',all(str(Path(n).resolve(strict=True))==q['resolved'] and sha(n)==q['sha256'] for n,q in v['inventory'].items()))
ck('launch_retains_exact_seal',set(pins['files'])==set(s['files'])|{str(run/n) for n in ['sealed.json','admission.json','prehost.json']} and pins['trees']==s['trees'] and all(pins['inventory'][n]==q for n,q in s['inventory'].items()) and rd(out/'pins.json')==pins)
ck('audit_exact_saved_bindings',set(a['sha256'])==files-{str(run/'audit.json')} and bindings(a['sha256']))
ck('audit_accepted_structural_scope',a['all_passed'] is True and a['pure_timeout'] is False and a['error']=='' and a['phase']=='red300' and a['result']==dict(assertions=6,groups=[['Missing BG export workspace contracts (six expected failures)',0,6,0,0]],scope='Expected missing-contract RED'))
ck('config_seal_and_all_commands',cfg==s['config'] and cfg['phase']=='red300' and cfg['mode']=='red' and cfg['seconds']==300 and cfg['expected_exit']==1 and all(q['command']==cfg['command'] for q in [p,cur,inv,res]))
ck('reservation_exact',res==dict(one_attempt=True,phase='red300',command=cfg['command'],pins_sha256=sha(run/'launch-pins.json'),review_sha256=sha(run/'admission.json'),max_seconds=300))
ck('invocation_hash_linkage',inv['pins_sha256']==p['pins_sha256']==cur['pins_sha256']==sha(run/'launch-pins.json') and inv['review_sha256']==sha(run/'admission.json') and inv['reservation_sha256']==sha(run/'reservation.json'))
guard_cmd=[inv['python'],'-B',str(D/'guard.py'),'run',str(run/'launch-pins.json'),str(out),'--seconds','292','--deadline',str(inv['monotonic_start']+292),'--expected-exit','1','--',*cfg['command']]
ck('exact_guard_command_and_deadline',inv['guard_command']==guard_cmd and Path(inv['python']).resolve()==Path('/usr/bin/python3').resolve())
ck('process_identity_linkage',p['runner']==cur['runner']==sup['guard_identity'] and p['child']==cur['child'])
ck('owned_session_and_start_identity',all(q['pid']==q['pgid']==q['sid'] and q['start_ticks']>0 and q['boot_id']==s['boot_id'] and q['command'] for q in [p['runner'],p['child']]) and p['runner']['pid']!=p['child']['pid'] and p['runner']['start_ticks']<=p['child']['start_ticks'])
ck('recorded_identity_exact_commands',p['runner']['command']==' '.join(guard_cmd)+' ' and p['child']['command']==' '.join(cfg['command'])+' ' and p['cwd']==cur['cwd']==str(R))
ck('exact_exit1_guard0_no_timeout_cleanup',p['reason']=='exit1' and p['returncode']==1 and p['pins_unchanged'] is True and sup['accepted'] is True and sup['returncode']==0 and all(sup[k] is False for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']) and 'cleanup_error' not in sup and 'error' not in p)
ck('finite_inclusive_limits',all(type(x) in (int,float) and math.isfinite(x) and 0<x<=300 for x in [inv['elapsed_seconds'],sup['elapsed_seconds']]) and 0<p['elapsed_including_launch']<=292 and sup['elapsed_seconds']<=inv['elapsed_seconds'])
raw=tomllib.loads((out/'raw.toml').read_text());root=raw['tests'];child=root['children'][0]
ck('raw_exact_schema_phase_complete',set(raw)=={'fatal','complete','threads','blas_threads','phase','tests','loaded'} and raw['phase']=='red300' and raw['complete'] is True and raw['fatal']=='')
ck('raw_one_zero_root',set(root)=={'name','pass','fail','error','broken','failures','children'} and root['name']=='root' and all(type(root[k]) is int and root[k]==0 for k in ['pass','fail','error','broken']) and root['failures']==[] and len(root['children'])==1)
ck('raw_exact_six_failed_leaves',set(child)==set(root) and child['name']=='Missing BG export workspace contracts (six expected failures)' and type(child['fail']) is int and child['fail']==6 and all(type(child[k]) is int and child[k]==0 for k in ['pass','error','broken']) and child['children']==[] and len(child['failures'])==6)
symbols=['BGExportWorkspace','_bgx_scratch!','_bgx_scale_mode','_bgx_import_upper','BGExportFactor','_bgx_refactor_with!']
failures=[f'Test Failed at {D}/red.jl:{i}\n  Expression: isdefined(JSimplex, :{n})\n   Evaluated: isdefined(JSimplex, {n})' for i,n in enumerate(symbols,4)]
ck('exact_six_failure_expressions_paths_lines',child['failures']==failures)
ck('source_assertions_exact_correspondence',re.findall(r'@test isdefined\(JSimplex, :([^\)]+)\)',(D/'red.jl').read_text())==symbols)
loaded=dict(rd(D/'loaded-paths.json'),JSimplex=str(Path(cfg['stage'])/'src/JSimplex.jl'))
ck('runtime_exact_loaded_paths_threads',raw['loaded']==loaded and type(raw['threads']) is int and type(raw['blas_threads']) is int and raw['threads']==raw['blas_threads']==1 and all(z in s['files'] for z in loaded.values()))
runlog=(out/'run.log').read_text();launcher=(run/'launcher.log').read_text()
ck('exact_run_log',runlog=='BEGIN BG export workspace driver red300\n'+''.join('TEST FAILURE: '+f+'\n' for f in failures))
ck('exact_launcher_terminal_record',json.loads(launcher)==p)
ck('no_warning_worldage_fatal',re.search(r'(?i)\bwarning\b|world[ -]age|FATAL DRIVER:|GROUP/COUNT MISMATCH|BROKEN TEST:|LoadError|OutOfMemoryError',runlog+'\n'+launcher) is None)
samples=[json.loads(z) for z in (out/'resources.jsonl').read_text().splitlines()]
ck('five_ordered_resource_samples',len(samples)==5 and [q['elapsed'] for q in samples]==sorted(q['elapsed'] for q in samples) and all(0<=q['elapsed']<=p['elapsed_including_launch'] for q in samples))
ck('all_samples_terminal_RAM_swap',all(q['available_kib']>=6*1024**2 and q['swap_used_kib']<=1024**2 for q in samples+[p['terminal_memory']]))
ck('valid_maxrss',type(p['child_maxrss_kib']) is int and 0<p['child_maxrss_kib']<=8*1024**2)
for label,h in [('sealhost',host),('prehost',pre),('posthost',post),('authorpost',rd(E/'postcheck-host.json'))]:
 ck(label+'_closure_identity',h['matches']==[] and h['unreadable_identity_pids']==[] and all(h[k]==s[k] for k in ['head','master','boot_id']))
newgroups={p[role][k] for role in ['runner','child'] for k in ['pgid','sid']};groups=set(post['groups'])
ck('full248_groups_AND_sessions',len(groups)==248 and groups==set(s['groups'])|newgroups and set(pre['groups'])==set(s['groups']) and groups==set(rd(E/'postcheck-host.json')['groups']))
postcheck=rd(E/'postcheck.json');ck('author13check_saved_evidence',postcheck['all_passed'] is True and len(postcheck['checks'])==13 and all(postcheck['checks'].values()) and bindings(postcheck['sha256']))
ck('environment_unchanged',all(os.environ.get(k)==v for k,v in rd(D/'environment.json').items()))
# Fresh independent host closure; no control import.
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[];unreadable_exe=[];unreadable_identity=[]
for z in Path('/proc').glob('[0-9]*'):
 try:
  stat=(z/'stat').read_text();v=stat[stat.rindex(')')+2:].split();comm=(z/'comm').read_text().strip();command=(z/'cmdline').read_bytes();argv0=command.split(b'\0',1)[0].decode(errors='replace');exe=''
  try:exe=str((z/'exe').resolve(strict=True))
  except PermissionError:unreadable_exe.append(int(z.name))
  except FileNotFoundError:pass
  if int(v[2]) in groups or int(v[3]) in groups or any(Path(q).name.lower().startswith('julia') for q in [comm,argv0,exe]):matches.append(dict(pid=int(z.name),pgid=int(v[2]),sid=int(v[3]),start_ticks=int(v[19]),boot_id=boot,command=command.replace(b'\0',b' ').decode(errors='replace'),comm=comm,argv0=argv0,exe=exe))
 except (FileNotFoundError,ProcessLookupError):pass
 except PermissionError:unreadable_identity.append(int(z.name))
h=dict(time=time.time(),groups=sorted(groups),matches=matches,unreadable_exe_pids=unreadable_exe,unreadable_identity_pids=unreadable_identity,boot_id=boot,head=git('rev-parse','HEAD'),master=git('rev-parse','master'),remote=git('ls-remote','origin','refs/heads/codex/simplex-core-architecture','refs/heads/master'),scope='All248 historical and current PGIDs AND SIDs/stat/comm/argv0/readable exe; inaccessible executable links limit universal executable visibility')
ck('fresh_independent_full_host_closure',not matches and not unreadable_identity and all(h[k]==s[k] for k in ['head','master','boot_id']))
ck('fresh_refs_remote_and_clean',h['remote']==s['head']+'\trefs/heads/codex/simplex-core-architecture\n'+s['master']+'\trefs/heads/master' and not git('diff','--name-only') and not git('diff','--cached','--name-only'))
save(E/'result-independent-host.json',h)
result=dict(all_passed=all(checks.values()),checks=checks,failed=[n for n,v in checks.items() if not v],phase='red300',scope='Saved exact structural missing-contract RED result only; no GREEN/candidate/performance/production qualification',sha256=hashes,run_sha256={n:sha(n) for n in sorted(files)},bytes_hashed=bytes_read,resources=dict(inclusive_seconds=inv['elapsed_seconds'],guard_seconds=p['elapsed_including_launch'],samples=len(samples),min_available_kib=min(q['available_kib'] for q in samples),max_swap_used_kib=max(q['swap_used_kib'] for q in samples),child_maxrss_kib=p['child_maxrss_kib']))
save(E/'result-independent-check.json',result)
print(json.dumps(dict(all_passed=result['all_passed'],checks=len(checks),failed=result['failed'],resources=result['resources'],groups=len(groups),unreadable_exe=len(unreadable_exe))))
raise SystemExit(0 if result['all_passed'] else 1)
