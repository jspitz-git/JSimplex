"""Independent saved-result review using stdlib read/hash checks only."""
from pathlib import Path
import hashlib,json,subprocess,os,time,tomllib,math
E=Path(__file__).resolve().parent;D=E.parent/'DIRECT-LU-POLICY-ADAPTER-DRIVER-PREPARATION';R=D.parents[3];G=D/'runs/green300';O=G/'output';W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl')
checks=[]
def ck(n,v,detail=None):
 checks.append(dict(name=n,passed=bool(v),detail=detail))
 if not v:raise RuntimeError(n)
def rd(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def hashes(m):return all(sha(Path(n) if Path(n).is_absolute() else R/n)==h for n,h in m.items())
def git(*a,cwd=R):return subprocess.check_output(['git',*a],cwd=cwd).decode().strip()
def verify_inventory(x,label):
 paths=set(x['files'])
 ck(label+' unique sorted files',x['files']==sorted(paths))
 for tree in x['trees']:
  root=Path(tree);ck(label+' root '+root.name,root.is_dir() and not root.is_symlink())
  descendants=list(root.rglob('*'));ck(label+' no tree symlink',not any(p.is_symlink() for p in descendants))
  paths.update(str(p) for p in descendants if p.is_file())
 ck(label+' inventory exact membership',paths==set(x['inventory']))
 ck(label+' hashes/resolved paths',all(sha(p)==v['sha256'] and str(Path(p).resolve(strict=True))==v['resolved'] for p,v in x['inventory'].items()),len(paths))
s=rd(G/'sealed.json');lp=rd(G/'launch-pins.json');ad=rd(G/'admission.json');cfg=rd(G/'config.json');audit=rd(G/'audit.json')
old_names={'admission-independent-check.py','posthost.json','audit.json','sealed.json','config.json','admission-independent-checks.json','host.json','launch-pins.json','launcher.log','admission.json','admission-independent-first-check-note.json','admission-independent-check-v2.py','admission.md','invocation.json','reservation.json','prehost.json','output/process.json','output/raw.toml','output/pins.json','output/run.log','output/resources.jsonl','output/current.json'}
ck('exact run before result review',{str(p.relative_to(G)) for p in G.rglob('*') if p.is_file()}==old_names)
ck('no symlink result artifacts',not any(p.is_symlink() for p in G.rglob('*')))
ck('exact six output files',{p.name for p in O.iterdir()}=={'process.json','raw.toml','pins.json','run.log','resources.jsonl','current.json'} and all(p.is_file() for p in O.iterdir()))
ck('audit exact21 preaudit membership',set(audit['sha256'])=={str(G/n) for n in old_names-{'audit.json'}} and hashes(audit['sha256']))
ck('audit accepted non-timeout',audit['all_passed'] is True and audit['pure_timeout'] is False and audit['phase']=='green300' and audit['error']=='')
verify_inventory(s,'seal');verify_inventory(lp,'launch')
ck('launch membership and seal agreement',set(lp['files'])==set(s['files'])|{str(G/n) for n in ['sealed.json','admission.json','prehost.json']} and lp['trees']==s['trees'] and all(lp['inventory'][n]==v for n,v in s['inventory'].items()) and len(lp['inventory'])==1823)
ck('output launch pins exact',rd(O/'pins.json')==lp and sha(O/'pins.json')==sha(G/'launch-pins.json'))
ck('admission required hashes',ad['accepted'] is True and ad['findings']==[] and ad['scope']=='direct adapter exact-stage admission' and ad['phase']=='green300' and ad['pins_sha256']==sha(G/'sealed.json') and set(ad['sha256'])==set(s['files'])|{str(G/'sealed.json')} and hashes(ad['sha256']) and hashes(ad['evidence_sha256']))
ck('exact phase config',s['config']==cfg and cfg['phase']==s['phase']=='green300' and cfg['seconds']==300 and cfg['expected_exit']==0 and cfg['mode']=='green' and cfg['output']==str(O))
ck('no other attempt',set(p.name for p in (D/'runs').iterdir())=={'red300','green300'})
red=D/'runs/red300';rr=rd(red/'result-review.json');ck('RED predecessor full membership',rr['accepted'] is True and rr['scope']=='direct adapter RED result' and rr['findings']==[] and set(rr['sha256'])=={str(p) for p in red.rglob('*') if p.is_file() and p!=red/'result-review.json'} and hashes(rr['sha256']) and hashes(rr['evidence_sha256']))
p=rd(O/'process.json');cur=rd(O/'current.json');inv=rd(G/'invocation.json');sup=inv['supervisor'];res=rd(G/'reservation.json')
ck('child and guard successful exits',p['returncode']==0 and p['reason']=='exit0' and sup['returncode']==0 and sup['accepted'] is True and p['pins_unchanged'] is True and 'error' not in p)
ck('no timeout or cleanup signals',all(sup[k] is False for k in ('soft_timeout','hard_timeout','child_kill','guard_term','guard_kill')) and 'cleanup_error' not in sup and 'remaining_group' not in p and 'remaining_session' not in p)
ck('inclusive and inner deadlines',all(type(t) in (int,float) and math.isfinite(t) and 0<t<=300 for t in [inv['elapsed_seconds'],sup['elapsed_seconds']]) and 0<p['elapsed_including_launch']<=292 and p['elapsed_including_launch']<=sup['elapsed_seconds']<=inv['elapsed_seconds'],dict(invocation=inv['elapsed_seconds'],supervisor=sup['elapsed_seconds'],child=p['elapsed_including_launch']))
ck('commands and pins linkage',p['command']==cur['command']==inv['command']==cfg['command'] and p['pins_sha256']==cur['pins_sha256']==inv['pins_sha256']==sha(G/'launch-pins.json'))
command=['/usr/bin/python3','-B',str(D/'guard.py'),'run',str(G/'launch-pins.json'),str(O),'--seconds','292','--deadline',str(inv['monotonic_start']+292),'--expected-exit','0','--',*cfg['command']]
ck('guard command absolute deadline',inv['guard_command']==command and inv['python']=='/usr/bin/python3')
ck('reservation exact',res==dict(one_attempt=True,phase='green300',command=cfg['command'],pins_sha256=sha(G/'launch-pins.json'),review_sha256=sha(G/'admission.json'),max_seconds=300) and inv['review_sha256']==sha(G/'admission.json') and inv['reservation_sha256']==sha(G/'reservation.json'))
ck('runner/child identity linkage',p['runner']==cur['runner']==sup['guard_identity'] and p['child']==cur['child'])
ck('identity boot/start/session/commands',all(v['boot_id']==s['boot_id'] and v['pid']==v['pgid']==v['sid'] and v['start_ticks']>0 and v['command']==' '.join(command if role=='runner' else cfg['command'])+' ' for role,v in [('runner',p['runner']),('child',p['child'])]))
ck('launch log exact process record',json.loads((G/'launcher.log').read_text())==p)
hosts=[rd(G/n) for n in ['host.json','prehost.json','posthost.json']];post=hosts[-1]
ck('saved host/ref consistency',all(h['matches']==[] and all(h[k]==s[k] for k in ['head','master','boot_id']) for h in hosts))
ck('posthost complete group/session coverage',set(hosts[0]['groups'])==set(hosts[1]['groups'])==set(s['groups']) and set(post['groups'])==set(s['groups'])|{p[role][k] for role in ['runner','child'] for k in ['pgid','sid']} and len(post['groups'])==226)
samples=[json.loads(x) for x in (O/'resources.jsonl').read_text().splitlines()];ck('36 resource samples',len(samples)==36 and all(type(v['elapsed']) in (int,float) and 0<=v['elapsed']<=p['elapsed_including_launch'] for v in samples) and [v['elapsed'] for v in samples]==sorted(v['elapsed'] for v in samples))
resources=samples+[p['terminal_memory']];stats=dict(min_available_kib=min(v['available_kib'] for v in resources),max_swap_used_kib=max(v['swap_used_kib'] for v in resources),child_maxrss_kib=p['child_maxrss_kib'])
ck('all sampled and terminal resources',all(type(v['available_kib']) is int and v['available_kib']>=6*1024**2 and type(v['swap_used_kib']) is int and 0<=v['swap_used_kib']<=1024**2 for v in resources) and type(p['child_maxrss_kib']) is int and p['child_maxrss_kib']>0,stats)
raw=tomllib.loads((O/'raw.toml').read_text());expected=rd(D/'expected-tests.json')['green'];loaded=rd(D/'loaded-paths.json');loaded['JSimplex']=str(Path(cfg['stage'])/'src/JSimplex.jl')
ck('raw schema and flags',set(raw)=={'phase','complete','fatal','loaded','threads','blas_threads','tests'} and raw['phase']=='green300' and raw['complete'] is True and raw['fatal']=='' and type(raw['threads']) is int and type(raw['blas_threads']) is int and raw['threads']==raw['blas_threads']==1 and raw['loaded']==loaded)
root=raw['tests'];nodes=[root]+root['children'];ck('raw exact node schema',all(set(t)=={'name','pass','fail','error','broken','failures','children'} and type(t['name']) is str and all(type(t[k]) is int and t[k]>=0 for k in ['pass','fail','error','broken']) and t['fail']==t['error']==t['broken']==0 and t['failures']==[] for t in nodes))
ck('root and exact nine leaf tree',root['name']=='root' and root['pass']==0 and len(root['children'])==9 and all(t['children']==[] for t in root['children']) and [[t[k] for k in ['name','pass','fail','error','broken']] for t in root['children']]==expected['groups'] and sum(t['pass'] for t in root['children'])==expected['assertions']==30455)
ck('audit matches independent raw',audit['result']['groups']==expected['groups'] and audit['result']['assertions']==30455)
names=['test_exports','test_export_rejections','test_scale_selection','test_normalization_and_scaling','test_lifecycles','test_fallback_transitions','test_policy_transitions','test_policy_rejections_and_forwarders','test_generic_policy_forwarding'];log=(O/'run.log').read_text()
warning=lambda n:('WARNING: Detected access to binding `Main.'+n+'` in a world prior to its definition world.\n  Julia 1.12 has introduced more strict world age semantics for global bindings.\n  !!! This code may malfunction under Revise.\n  !!! This code will error in future versions of Julia.\nHint: Add an appropriate `invokelatest` around the access to this binding.\nTo make this warning an error, and hence obtain a stack trace, use `julia --depwarn=error`.\n')
ck('exact nine warnings and completed groups log',log=='BEGIN adapter driver green300\n'+''.join('BEGIN '+n+'\n'+warning(n)+'END '+n+'\n' for n in names))
for label,where in [('diagnostic',R),('production',W)]:
 b=rd(D/'baseline.json')[label];ck(label+' baseline full names/hashes',set(git('ls-files','src','test','.github','Project.toml',cwd=where).splitlines())==set(b) and all(sha(where/n)==h for n,h in b.items()),len(b))
for label,t in rd(D/'stages.json').items():
 where=Path(t['path']);ck(label+' stage full75 names/hashes',{str(p.relative_to(where)) for p in where.rglob('*') if p.is_file()}==set(t['sha256']) and len(t['sha256'])==75 and all(sha(where/n)==h for n,h in t['sha256'].items()))
rt=rd(D/'runtime-inputs-complete.json')['inventory'];ck('runtime609 exact current',len(rt)==609 and all(lp['inventory'][n]==v for n,v in rt.items()))
ck('refs unchanged',git('rev-parse','HEAD')==s['head']=='bbee8f5cb680e981eae878c77f2110ed36c9d029' and git('rev-parse','master')==git('rev-parse','HEAD',cwd=W)==s['master']=='26e2291745999f485a74f643298ca997d65c7205' and git('ls-remote','origin','refs/heads/master')==s['master']+'\trefs/heads/master')
ck('clean tracked/index',not git('diff','--name-only') and not git('diff','--cached','--name-only'))
ck('current loading environment',all(os.environ.get(k)==v for k,v in rd(D/'environment.json').items()))
ck('same boot',Path('/proc/sys/kernel/random/boot_id').read_text().strip()==s['boot_id'])
matches=[];unreadable=[]
for q in Path('/proc').glob('[0-9]*'):
 try:
  fields=(q/'stat').read_text().rsplit(')',1)[1].split();comm=(q/'comm').read_text().strip();exe=''
  try:exe=str((q/'exe').resolve(strict=True))
  except PermissionError:unreadable.append(int(q.name))
  except FileNotFoundError:pass
  if int(fields[2]) in post['groups'] or int(fields[3]) in post['groups'] or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):matches.append(dict(pid=int(q.name),pgid=int(fields[2]),sid=int(fields[3]),start_ticks=int(fields[19]),comm=comm,exe=exe,command=(q/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,ProcessLookupError):pass
ck('fresh all226 groups/sessions and Julia absent',not matches,dict(matches=matches,unreadable_exe_pids=unreadable))
mem={a.split(':')[0]:int(a.split()[1]) for a in Path('/proc/meminfo').read_text().splitlines()};ck('fresh memory gate',mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2,dict(available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree']))
original=(E/'postcheck.py').read_text();fixed=(E/'postcheck-2.py').read_text();inverse=fixed.replace('postcheck-2-host.json','postcheck-host.json').replace("E/'postcheck-2.json'","E/'postcheck.json'").replace('==tuple(e)','==(e[\'name\'],e[\'pass\'],0,0,0)')
ck('reporting-only correction exact inverse',inverse==original and original.count("(e['name'],e['pass'],0,0,0)")==1)
fix=rd(E/'postcheck-fix.json');ck('supplement fix saved hashes',fix['original_sha256']==sha(E/'postcheck.py') and fix['corrected_sha256']==sha(E/'postcheck-2.py') and fix['all_passed'] is True and len(fix['checks'])==3 and all(fix['checks'].values()))
failure=rd(E/'postcheck-failure.json');ck('supplement original failure preserved',failure['returncode']==1 and failure['numerical_rerun'] is False and failure['auditor_rerun'] is False and (E/'postcheck-host.json').exists() and not (E/'postcheck.json').exists())
supp=rd(E/'postcheck-2.json');ck('supplement saved exact memberships/hashes',set(supp['sha256'])=={str(G/n) for n in old_names}|{str(E/'postcheck-2.py')} and hashes(supp['sha256']) and supp['all_passed'] is True and len(supp['checks'])==10 and all(supp['checks'].values()))
ck('supplement agrees with raw',supp['result']['groups']==[{k:t[k] for k in ['name','pass','fail','error','broken']} for t in root['children']] and supp['warnings']==[x for x in log.splitlines() if x.startswith('WARNING:')])
for filename in ['postcheck-host.json','postcheck-2-host.json']:
 h=rd(E/filename);ck(filename+' host closure',h['matches']==[] and h['groups']==post['groups'] and all(h[k]==s[k] for k in ['head','master','boot_id']))
result=dict(all_passed=True,scope='Independent GREEN saved-result verification; no candidate/auditor/helper rerun',time=time.time(),checks=checks,resource_summary=stats,assertions=30455,group_counts=[t['pass'] for t in root['children']],run_input_sha256={str(G/n):sha(G/n) for n in sorted(old_names)},julia_executed=False)
with (E/'result-review-checks.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=True,checks=len(checks),assertions=30455,resources=stats)))
