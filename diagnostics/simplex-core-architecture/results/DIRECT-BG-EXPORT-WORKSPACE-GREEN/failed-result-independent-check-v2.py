"""Independent saved GREEN300 rejection review; no Julia or historical checker imports."""
from pathlib import Path
import json,hashlib,os,time,subprocess,tomllib,re,math
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');D=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-WORKSPACE-DRIVER-PREPARATION';E=D.with_name('DIRECT-BG-EXPORT-WORKSPACE-GREEN');run=D/'runs/green300';out=run/'output';checks=[]
def rd(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def ck(v,n):checks.append(dict(name=n,passed=bool(v)))
def bind(j,k='sha256'):return all(sha(Path(n) if Path(n).is_absolute() else R/n)==h for n,h in j[k].items())
def inv(s):
 names=set(s['files'])
 for root in s['trees']:
  root=Path(root);ck(not root.is_symlink() and not any(p.is_symlink() and (p.is_dir() or not p.exists()) for p in root.rglob('*')),'safe tree '+str(root));names.update(str(p) for p in root.rglob('*') if p.is_file())
 return {n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=sha(n)) for n in sorted(names)}
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
s=rd(run/'sealed.json');cfg=rd(run/'config.json');a=rd(run/'admission.json');pins=rd(run/'launch-pins.json');audit=rd(run/'audit.json');i=rd(run/'invocation.json');p=rd(out/'process.json');cur=rd(out/'current.json');sup=i['supervisor'];res=rd(run/'reservation.json');post=rd(run/'posthost.json')
ck(s['inventory']==inv(s),'all1892 sealed inputs full streaming hashes and trees');ck(pins['inventory']==inv(pins),'all launch inputs full streaming hashes and trees');ck(rd(out/'pins.json')==pins,'output launch pins identical')
ck(a['accepted'] is True and a['findings']==[] and a['scope']=='BG export workspace exact-stage admission' and a['phase']=='green300' and a['pins_sha256']==sha(run/'sealed.json') and bind(a) and bind(a,'evidence_sha256'),'admission and nine evidence hashes')
ck(set(a['sha256'])==set(s['files'])|{str(run/'sealed.json')},'admission exact membership');ck(set(pins['files'])==set(s['files'])|{str(run/'sealed.json'),str(run/'admission.json'),str(run/'prehost.json')} and pins['trees']==s['trees'],'launch exact membership')
ck(all(pins['inventory'][n]==v for n,v in s['inventory'].items()),'seal launch continuity');ck(audit['all_passed'] is False and audit['pure_timeout'] is False and audit['error']=="RuntimeError('Exact exit')" and audit['phase']=='green300','saved audit rejects non-timeout')
ck(bind(audit) and set(audit['sha256'])=={str(q) for q in run.rglob('*') if q.is_file() and q!=run/'audit.json'},'audit exact pre-audit17-minus1 files')
ck(set(q.name for q in out.iterdir())=={'pins.json','current.json','process.json','resources.jsonl','run.log','raw.toml'} and all(q.is_file() and not q.is_symlink() for q in out.iterdir()),'exact output membership')
ck(s['config']==cfg and cfg['phase']=='green300' and cfg['seconds']==300 and cfg['expected_exit']==0,'config phase unchanged');ck(res==dict(one_attempt=True,phase='green300',command=cfg['command'],pins_sha256=sha(run/'launch-pins.json'),review_sha256=sha(run/'admission.json'),max_seconds=300),'exclusive reservation')
ck(i['pins_sha256']==cur['pins_sha256']==p['pins_sha256']==sha(run/'launch-pins.json') and i['review_sha256']==sha(run/'admission.json') and i['reservation_sha256']==sha(run/'reservation.json'),'invocation hashes')
ck(i['command']==cur['command']==p['command']==cfg['command'] and p['pins_unchanged'] is True and p['cwd']==str(R),'exact invocation command and unchanged pins')
ck(i['guard_command']==[i['python'],'-B',str(D/'guard.py'),'run',str(run/'launch-pins.json'),str(out),'--seconds','292','--deadline',str(i['monotonic_start']+292),'--expected-exit','0','--',*cfg['command']],'exact inner guard command')
ck(cur['runner']==p['runner']==sup['guard_identity'] and cur['child']==p['child'],'runner child identity linkage');ck(all(p[r]['boot_id']==s['boot_id'] and p[r]['start_ticks']>0 and p[r]['command'] for r in ['runner','child']),'boot ticks and commands')
ck(p['reason']=='exit2' and p['returncode']==2 and sup['returncode']==1 and sup['accepted'] is False,'observed rejection exit2 guard1');ck(all(sup[k] is False for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']) and 'cleanup_error' not in sup and 'error' not in p,'not timeout interruption or launch error')
ck(all(type(v) in (int,float) and math.isfinite(v) and 0<=v<300 for v in [i['elapsed_seconds'],sup['elapsed_seconds'],p['elapsed_including_launch']]),'inclusive timing bounds')
for n in ['host.json','prehost.json','posthost.json']:
 h=rd(run/n);ck(h['matches']==[] and h['unreadable_identity_pids']==[] and all(h[k]==s[k] for k in ['head','master','boot_id']),'saved host '+n)
ck(set(s['groups'])<=set(rd(run/'prehost.json')['groups'])<=set(post['groups']) and all(p[r][k] in post['groups'] for r in ['runner','child'] for k in ['pgid','sid']),'all historical plus runner child PGID SID coverage')
samples=[json.loads(x) for x in (out/'resources.jsonl').read_text().splitlines()];ck(bool(samples) and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in samples+[p['terminal_memory']]),'every resource and terminal sample');ck(p['child_maxrss_kib']==895440,'reported child RSS')
raw=tomllib.loads((out/'raw.toml').read_text());loaded=dict(rd(D/'loaded-paths.json'),JSimplex=cfg['stage']+'/src/JSimplex.jl');ck(set(raw)=={'phase','complete','fatal','loaded','threads','blas_threads','tests'} and raw['phase']=='green300' and raw['complete'] is True and raw['fatal']=='' and raw['threads']==raw['blas_threads']==1 and raw['loaded']==loaded,'complete raw schema threads paths')
root=raw['tests'];ex=rd(D/'expected-tests.json')['green']['groups'];children=root['children'];ck(root['name']=='root' and all(root[k]==0 for k in ['pass','fail','error','broken']) and not root['failures'] and len(children)==11,'root11 groups')
for idx,(t,e) in enumerate(zip(children,ex)):
 want=e.copy()
 if idx==3:want[1]=55;want[3]=1
 ck([t['name'],t['pass'],t['fail'],t['error'],t['broken']]==want and t['children']==[] and len(t['failures'])==t['fail']+t['error'],'exact observed group '+str(idx+1))
totals={k:sum(t[k] for t in children) for k in ['pass','fail','error','broken']};ck(totals=={'pass':7934,'fail':0,'error':1,'broken':0},'7934pass oneerror zero fail broken')
error=children[3]['failures'][0];ck('import-tests.jl:28' in error and 'reducing over an empty collection is not allowed' in error and 'check_import(U::SparseMatrixCSC{Float64, Int64}, normalize::Bool)' in error,'sole error source location and reducer')
log=(out/'run.log').read_text()+'\n'+(run/'launcher.log').read_text();ck(not re.search(r'(?i)\bwarning\b|world[ -]age',log),'no warning world-age');ck(log.count('TEST FAILURE:')==1 and 'GROUP/COUNT MISMATCH OR FATAL' in log and 'END all BG export workspace tests' in log and 'FATAL DRIVER:' not in log and 'BROKEN TEST:' not in log,'complete log and exact rejection diagnostics')
C=R/'diagnostics/direct-bg-export-workspace/reproduce';test=(C/'import-tests.jl').read_text();candidate=(C/'import.jl').read_text();allocator=(C/'workspace-tests.jl').read_text();base=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/base/reduce.jl')
ck(test.splitlines()[27].strip()=='@test sum(n for (T,n) in a.requests if T===Float64)==nnz(U)+(normalize ? size(U,1) : 0)','frozen exact failing assertion');ck('inputs=(spzeros(0,0),' in test and 'for U in inputs, normalize in (false,true);check_import(U,normalize);end' in test and 'requests::Vector{Tuple{Any,Int}}' in allocator,'empty false case and request type')
ck('if normalize\n        D=allocate(Float64,n)' in candidate and 'for col in 1:n' in candidate and 'order_ids=allocate(Int,n)' in candidate and 'positions=allocate(Int,n)' in candidate,'n0 false no Float64 request by source');ck('mapreduce_empty(f, op, T) = _empty_reduce_error()' in ' '.join(base.read_text().split()) and 'reduce_empty(op::MappingRF, ::Type{T}) where {T} = mapreduce_empty(op.f, op.rf, T)' in ' '.join(base.read_text().split()),'installed Base explains observed empty mapped reduction')
# Fresh read-only host closure.
groups=sorted(set(post['groups']));boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[];ue=[];ui=[]
for q in Path('/proc').glob('[0-9]*'):
 try:
  f=(q/'stat').read_text().rsplit(')',1)[1].split();comm=(q/'comm').read_text().strip();cmd=(q/'cmdline').read_bytes();argv=cmd.split(b'\0',1)[0].decode(errors='replace');exe=''
  try:exe=str((q/'exe').resolve(strict=True))
  except PermissionError:ue.append(int(q.name))
  except FileNotFoundError:pass
  if int(f[2]) in groups or int(f[3]) in groups or any(Path(v).name.lower().startswith('julia') for v in [comm,argv,exe]):matches.append(dict(pid=int(q.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),command=cmd.replace(b'\0',b' ').decode(errors='replace'),comm=comm,argv0=argv,exe=exe))
 except (FileNotFoundError,ProcessLookupError):pass
 except PermissionError:ui.append(int(q.name))
m={x.split(':')[0]:int(x.split()[1]) for x in Path('/proc/meminfo').read_text().splitlines()};host=dict(time=time.time(),groups=groups,boot_id=boot,matches=matches,unreadable_exe_pids=ue,unreadable_identity_pids=ui,head=git('rev-parse','HEAD'),master=git('rev-parse','master'),remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'),available_kib=m['MemAvailable'],swap_used_kib=m['SwapTotal']-m['SwapFree'])
ck(not matches and not ui and len(groups)==250,'fresh250group and session closure');ck(all(host[k]==s[k] for k in ['boot_id','head','master']) and set(host['remote'].splitlines())=={s['head']+'\trefs/heads/codex/simplex-core-architecture',s['master']+'\trefs/heads/master'},'fresh refs boot');ck(host['available_kib']>=6*1024**2 and host['swap_used_kib']<=1024**2,'fresh memory')
ck(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'tracked files unchanged')
result=dict(all_passed=all(x['passed'] for x in checks),findings=[x['name'] for x in checks if not x['passed']],checks=checks,host=host,observed=totals|dict(groups=11,inclusive_seconds=i['elapsed_seconds'],child_maxrss_kib=p['child_maxrss_kib']),correctness_accepted=False,pure_timeout=False,classification='Diagnostic test assertion errors on empty filtered reduction; original GREEN rejected',sha256={str(q):sha(q) for q in sorted(run.rglob('*')) if q.is_file()},root_cause_sources_sha256={str(q):sha(q) for q in [C/'import-tests.jl',C/'workspace-tests.jl',C/'import.jl',base]},scope='Independent saved failed GREEN300 result integrity and root cause; no launch or retry')
with (E/'failed-result-independent-check-v2.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({k:result[k] for k in ['all_passed','findings','observed','classification']}));print('checks',len(checks),'runfiles',len(result['sha256']),'exe_gaps',len(ue))
