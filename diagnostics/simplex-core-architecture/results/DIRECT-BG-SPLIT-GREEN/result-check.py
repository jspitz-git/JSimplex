"""Independent saved-result review. Standard-library text/hash/raw arithmetic and host reads only."""
from pathlib import Path
import hashlib,json,tomllib,re,math,os,subprocess,time
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');D=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-SPLIT-DRIVER-PREPARATION';E=D.parent/'DIRECT-BG-SPLIT-GREEN';run=D/'runs/green300';out=run/'output';red=D/'runs/red300';N=R/'diagnostics/direct-bg-split-upper/reproduce';O=R/'diagnostics/direct-bg-block-upper/reproduce';A=D.parent/'DIRECT-BG-SPLIT-ADAPTER-PREPARATION';U=D.parent/'DIRECT-BG-SPLIT-U-PREPARATION'
checks={}
def rd(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def ck(n,v):checks[n]=bool(v)
def bind(j,k='sha256'):return all(sha(Path(n) if Path(n).is_absolute() else R/n)==h for n,h in j[k].items())
def inv(j):
 paths=set(map(Path,j['files']))
 for t in map(Path,j['trees']):
  assert t.is_dir() and not t.is_symlink()
  for p in t.rglob('*'):
   assert not (p.is_symlink() and (p.is_dir() or not p.exists()))
   if p.is_file():paths.add(p)
 return {str(p):dict(resolved=str(p.resolve(strict=True)),sha256=sha(p)) for p in sorted(paths)}
def git(*args,cwd=R):return subprocess.check_output(['git',*args],cwd=cwd,text=True).strip()
s=rd(run/'sealed.json');lp=rd(run/'launch-pins.json');ad=rd(run/'admission.json');cfg=rd(run/'config.json');p=rd(out/'process.json');cur=rd(out/'current.json');i=rd(run/'invocation.json');sup=i['supervisor'];audit=rd(run/'audit.json');post=rd(run/'posthost.json');pre=rd(run/'prehost.json');hs=rd(run/'host.json');rr=rd(red/'result-review.json');res=rd(run/'reservation.json');pc=rd(E/'postcheck.json')
allrun={str(x) for x in run.rglob('*') if x.is_file()}
ck('run_output_exact', {x.name for x in run.iterdir()}=={'host.json','config.json','sealed.json','admission.json','prehost.json','launch-pins.json','reservation.json','launcher.log','invocation.json','posthost.json','audit.json','output'} and {x.name for x in out.iterdir()}=={'pins.json','current.json','process.json','resources.jsonl','run.log','raw.toml'} and all(not x.is_symlink() for x in run.rglob('*')))
ck('seal_exact_inventory',len(s['files'])==1893 and inv(s)==s['inventory'])
ck('launch_exact_inventory',set(lp['files'])==set(s['files'])|{str(run/'sealed.json'),str(run/'admission.json'),str(run/'prehost.json')} and lp['trees']==s['trees'] and lp['inputs']==[] and inv(lp)==lp['inventory'] and rd(out/'pins.json')==lp and all(lp['inventory'][n]==v for n,v in s['inventory'].items()))
ck('admission_exact',ad['accepted'] is True and ad['findings']==[] and ad['scope']=='split BG exact-stage admission' and ad['phase']=='green300' and ad['pins_sha256']==sha(run/'sealed.json') and set(ad['sha256'])==set(s['files'])|{str(run/'sealed.json')} and bind(ad) and bind(ad,'evidence_sha256'))
ck('audit_exact',audit['all_passed'] is True and audit['pure_timeout'] is False and audit['phase']=='green300' and set(audit['sha256'])==allrun-{str(run/'audit.json')} and bind(audit))
ck('supplement_exact',pc['all_passed'] is True and len(pc['checks'])==17 and all(pc['checks'].values()) and bind(pc) and set(pc['sha256'])==allrun|{str(E/n) for n in ['postcheck.py','posthost.json','allowance.json','preflight.json']})
ck('red_result_exact',rr['accepted'] is True and rr['findings']==[] and rr['scope']=='split BG RED result' and rr['phase']=='red300' and set(rr['sha256'])=={str(x) for x in red.rglob('*') if x.is_file() and x!=red/'result-review.json'} and bind(rr) and bind(rr,'evidence_sha256') and inv(rd(red/'sealed.json'))==rd(red/'sealed.json')['inventory'])
prep=rd(D/'preparation-pins.json');prev=rd(D/'review.json');ck('preparation_exact',bind(prep) and set(prep['sha256'])==set(rd(D/'required-paths.json')['paths']) and prev['accepted'] is True and prev['findings']==[] and prev['pins_sha256']==sha(D/'preparation-pins.json') and bind(prev) and bind(rd(D/'entry.json')))
st=rd(D/'stages.json')
for name,z in st.items():
 root=Path(z['path']);ck(name+'_stage_source_exact',len(z['sha256'])==(81 if name=='green' else 75) and {str(x.relative_to(root)) for x in root.rglob('*') if x.is_file()}==set(z['sha256']) and all(sha(root/k)==v==sha(Path(z['source'])/k) for k,v in z['sha256'].items()) and not any(x.is_symlink() for x in root.rglob('*')))
bs=rd(N/'source-bindings.json');cand=(N/'split-upper.jl').read_text();replacement=(U/'replacement-reserve.jl.txt').read_text();old=(U/'original-reserve-renamed.jl.txt').read_text();back=cand.replace(replacement,old)
for orig,new in reversed(list(bs['renames'].items())):back=back.replace(new,orig)
ck('upper_source_inverse',bind(bs) and cand.count(replacement)==1 and back==(O/'block-upper.jl').read_text())
ai=rd(A/'adapter-inverse.json');back=(N/'split-bg.jl').read_text()
for orig,new in reversed(ai['renames']):back=back.replace(new,orig)
ck('adapter_source_inverse',back==Path(ai['reference']).read_text() and sha(N/'split-bg.jl')==ai['candidate_sha256'] and sha(ai['reference'])==ai['reference_sha256'])
pa=rd(D.parent/'DIRECT-BG-BLOCK-ADAPTER-PREPARATION/adapter-inverse-reviewed.json');back=(O/'block-bg.jl').read_text();selectors=True
for edit in reversed(pa['edits']):
 selectors=selectors and back.count(edit['after'])==edit.get('count',1);back=back.replace(edit['after'],edit['before'])
for orig,new in reversed(pa['renames']):back=back.replace(new,orig)
ck('parent_source_inverse',selectors and back==Path(pa['reference']).read_text() and sha(O/'block-bg.jl')==pa['candidate_sha256'] and sha(pa['reference'])==pa['reference_sha256'])
tf=rd(A/'tests-first.json');back=(N/'split-bg-tests.jl').read_text();unique=back.count(tf['extra'])==back.count(tf['call'])==1;back=back.replace(tf['extra'],'').replace(tf['call'],'')
for orig,new in reversed(tf['renames']):back=back.replace(new,orig)
ck('tests_inverse_fixed_fixtures',unique and back==(O/'block-bg-tests.jl').read_text() and bind(tf) and (N/'fixtures.jl').read_bytes()==(O/'fixtures.jl').read_bytes())
raw=tomllib.loads((out/'raw.toml').read_text());root=raw['tests'];leaves=root['children'];ex=rd(D/'expected-tests.json')['green'];actual=[[x['name'],x['pass'],x['fail'],x['error'],x['broken']] for x in leaves]
ck('raw_complete_exact_tree',raw['phase']=='green300' and raw['complete'] is True and raw['fatal']=='' and root['name']=='root' and all(root[k]==0 for k in ['pass','fail','error','broken']) and root['failures']==[] and actual==ex['groups'] and len(leaves)==34 and all(x['children']==[] and x['failures']==[] for x in leaves))
ck('raw15929_all_passed',sum(x['pass'] for x in leaves)==15929 and all(x[k]==0 for x in leaves for k in ['fail','error','broken']) and audit['result']['assertions']==15929 and audit['result']['groups']==actual)
tx=tomllib.loads((D/'expected-tests.toml').read_text())['green'];ck('expected_toml_exact',[[x[k] for k in ['name','pass','fail','error','broken']] for x in tx['groups']]==actual)
loaded=dict(rd(D/'loaded-paths.json'),JSimplex=str(Path(cfg['stage'])/'src/JSimplex.jl'));ck('loaded_six_paths_threads',raw['loaded']==loaded and len(loaded)==6 and raw['threads']==raw['blas_threads']==1 and all(str(Path(v).resolve(strict=True))==v for v in loaded.values()))
log=(out/'run.log').read_text();ll=(run/'launcher.log').read_text();names=['split storage','lifecycles','rejection_and_aliases','export_modes','focused_updates','block_boundaries','storage_failure_boundaries','new_scratch_aliases','split_allocator_differentials'];expectedlog=['BEGIN split BG driver green300']+[f'{end} {n}' for n in names for end in ['BEGIN','END']]
ck('exact_begin_end_log',log.splitlines()==expectedlog)
ck('no_error_warning_log',re.search(r'(?i)\bwarning\b|world[ -]age|TEST FAILURE:|BROKEN TEST:|FATAL DRIVER:|GROUP/COUNT MISMATCH',log+'\n'+ll) is None and json.loads(ll)==p)
driver=(D/'driver.jl').read_text();ck('raw_before_aggregate_source',driver.index('TOML.print(io,raw)')<driver.index('expected=TOML.parsefile') and driver.rfind('include(')<driver.index('function main()'))
ck('command_config_identity',cfg==s['config'] and cfg['phase']=='green300' and cfg['mode']=='green' and cfg['seconds']==300 and cfg['expected_exit']==0 and p['command']==cur['command']==i['command']==cfg['command'] and p['cwd']==str(R) and p['pins_unchanged'] is True and p['pins_sha256']==cur['pins_sha256']==i['pins_sha256']==sha(run/'launch-pins.json'))
ck('reservation_linkage',res==dict(one_attempt=True,phase='green300',command=cfg['command'],pins_sha256=sha(run/'launch-pins.json'),review_sha256=sha(run/'admission.json'),max_seconds=300) and i['reservation_sha256']==sha(run/'reservation.json') and i['review_sha256']==sha(run/'admission.json'))
expectedguard=[i['python'],'-B',str(D/'guard.py'),'run',str(run/'launch-pins.json'),str(out),'--seconds','292','--deadline',str(i['monotonic_start']+292),'--expected-exit','0','--',*cfg['command']]
ck('guard_deadline_command',i['guard_command']==expectedguard and Path(i['python']).resolve()==Path('/usr/bin/python3').resolve())
ck('process_identity_linkage',p['runner']==cur['runner']==sup['guard_identity'] and p['child']==cur['child'] and all(p[role]['pid']==p[role]['pgid']==p[role]['sid']==pid and p[role]['start_ticks']==start and p[role]['boot_id']==s['boot_id'] for role,pid,start in [('runner',22695,1195082),('child',22696,1195134)]) and p['runner']['command']==' '.join(expectedguard)+' ' and p['child']['command']==' '.join(cfg['command'])+' ')
ck('no_timeout_cleanup_error',p['returncode']==0 and p['reason']=='exit0' and sup['returncode']==0 and sup['accepted'] is True and all(sup[k] is False for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']) and 'error' not in p and 'cleanup_error' not in sup)
ck('inclusive_time_limits',0<p['elapsed_including_launch']<=sup['elapsed_seconds']<=i['elapsed_seconds']<=300 and p['elapsed_including_launch']<=292 and all(math.isfinite(v) for v in [p['elapsed_including_launch'],sup['elapsed_seconds'],i['elapsed_seconds']]))
resources=[json.loads(x) for x in (out/'resources.jsonl').read_text().splitlines()];ck('all_resources_terminal',len(resources)==22 and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in resources+[p['terminal_memory']]) and all(0<=x['elapsed']<=292 for x in resources) and [x['elapsed'] for x in resources]==sorted(x['elapsed'] for x in resources))
ck('reported_resource_numbers',min(x['available_kib'] for x in resources)==22513844 and max(x['swap_used_kib'] for x in resources)==0 and p['terminal_memory']==dict(available_kib=23223760,swap_used_kib=0) and p['child_maxrss_kib']==807556)
ck('saved_host_closure',all(not h['matches'] and all(h[k]==s[k] for k in ['head','master','boot_id']) for h in [hs,pre,post,rd(E/'posthost.json')]) and set(s['groups'])<=set(pre['groups']) and set(post['groups'])==set(rd(E/'posthost.json')['groups'])==set(s['groups'])|{22695,22696} and len(post['groups'])==244)
W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl')
for label,r in [('diagnostic',R),('production',W)]:
 b=rd(D/'baseline.json')[label];ck(label+'_source_unchanged',set(git('ls-files','src','test','.github','Project.toml',cwd=r).splitlines())==set(b) and all(sha(r/n)==h for n,h in b.items()))
remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture');ck('fresh_refs_clean',git('rev-parse','HEAD')==s['head'] and git('rev-parse','master')==git('rev-parse','HEAD',cwd=W)==s['master'] and s['head']+'\trefs/heads/codex/simplex-core-architecture' in remote and s['master']+'\trefs/heads/master' in remote and not git('diff','--name-only') and not git('diff','--cached','--name-only'))
groups=set(post['groups']);matches=[];unreadable=[]
for z in Path('/proc').glob('[0-9]*'):
 try:
  f=(z/'stat').read_text().rsplit(')',1)[1].split();comm=(z/'comm').read_text().strip();exe=''
  try:exe=os.readlink(z/'exe')
  except PermissionError:unreadable.append(int(z.name))
  except FileNotFoundError:pass
  if int(f[2]) in groups or int(f[3]) in groups or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):matches.append(dict(pid=int(z.name),pgid=int(f[2]),sid=int(f[3]),comm=comm,exe=exe))
 except (FileNotFoundError,ProcessLookupError):pass
mem={x.split(':')[0]:int(x.split()[1]) for x in Path('/proc/meminfo').read_text().splitlines()};freshmem=dict(available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree']);boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
ck('fresh244_host_clear',not matches and boot==s['boot_id']);ck('fresh_resources',freshmem['available_kib']>=6*1024**2 and freshmem['swap_used_kib']<=1024**2)
files=sorted(allrun|{str(E/n) for n in ['REPORT.md','postcheck.py','postcheck.json','posthost.json','allowance.json','preflight.json','result-check.py']})
record=dict(all_passed=all(checks.values()),checks=checks,scope='Independent saved GREEN result review; no Julia or old checker reruns',checked_at=time.time(),sha256={n:sha(n) for n in files},details=dict(groups=sorted(groups),matches=matches,unreadable_exe_pids=unreadable,visibility_limit='Unreadable executable links remain a visibility limit',boot_id=boot,memory=freshmem,remote_refs=remote,assertions=15929,leaf_groups=34,launcher_seconds=i['elapsed_seconds'],supervisor_seconds=sup['elapsed_seconds'],guard_seconds=p['elapsed_including_launch'],resource_samples=len(resources),minimum_available_kib=min(x['available_kib'] for x in resources),maxrss_kib=p['child_maxrss_kib'],run_files=len(allrun)))
with (E/'result-check.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=record['all_passed'],checks=len(checks),failed=[k for k,v in checks.items() if not v],assertions=15929,groups=244,run_files=len(allrun),memory=freshmem)))
