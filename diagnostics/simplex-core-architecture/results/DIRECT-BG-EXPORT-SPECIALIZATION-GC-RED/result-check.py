"""Fresh independent saved-result verifier. No Julia, operational entrypoint or frozen checker invocation."""
from pathlib import Path
import json, hashlib, math, struct, statistics, tomllib, subprocess, time, traceback, sys, re, os
from fractions import Fraction as F
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
P=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-SPECIALIZATION-GC-DRIVER'
Q=P.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-GC-RED');RUN=P/'runs/redgc300';OUT=RUN/'output';O=P/'outers/redgc300'
result={'scope':'Independent fixed-GC RED saved-result verification','started':time.time(),'checks':[],'findings':[]};cache={}
def ck(v,n):
 if not v:raise AssertionError(n)
 result['checks'].append(n)
def rd(p):return json.loads(Path(p).read_text())
def digest(p):
 p=Path(p);h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def sha(p):
 p=str(Path(p))
 if p not in cache:cache[p]=digest(p)
 return cache[p]
def binds(v,key='sha256'):
 for n,h in v[key].items():ck(sha(n)==h,'binding '+key+' '+n)
def git(*a,cwd=R):return subprocess.check_output(['git',*a],cwd=cwd,text=True).strip()
def tokens(t):
 z=[]
 for s in t:
  if not (type(s) is str and re.fullmatch('[0-9a-f]{16}',s)):raise ValueError('bad bit token')
  x=struct.unpack('>d',bytes.fromhex(s))[0]
  if not math.isfinite(x):raise ValueError('nonfinite bit token')
  z.append(F(x))
 return z
def mat(m,transpose=False):
 n=m['n'];rows=[[] for _ in range(n)];v=tokens(m['nzval'])
 ck(len(m['colptr'])==n+1 and m['colptr'][0]==1 and m['colptr'][-1]==len(v)+1 and len(v)==len(m['rowval']),'CSC shape')
 for j in range(n):
  idx=m['rowval'][m['colptr'][j]-1:m['colptr'][j+1]-1]
  ck(idx==sorted(set(idx)) and all(1<=i<=n for i in idx),'CSC canonical rows')
  for k in range(m['colptr'][j]-1,m['colptr'][j+1]-1):
   i=m['rowval'][k]-1;r,c=(j,i) if transpose else (i,j);rows[r].append((c,v[k]))
 return rows,max(sum(abs(v) for _,v in row) for row in rows)
def residual(m,xt,bt):
 rows,norm=m;x=tokens(xt);b=tokens(bt);n=len(rows)
 if not len(x)==len(b)==n:return False
 res=max(abs(sum(v*x[j] for j,v in row)-b[i]) for i,row in enumerate(rows))
 bound=F(128*n,2**52)*max(F(1),norm*max(map(abs,x)),max(map(abs,b)))
 return res<=bound
try:
 s=rd(RUN/'sealed.json');pins=rd(RUN/'launch-pins.json');cfg=rd(RUN/'config.json');adm=rd(RUN/'admission.json');a=rd(RUN/'audit.json');cl=rd(RUN/'outer-closure.json');inv=rd(RUN/'invocation.json');p=rd(OUT/'process.json');cur=rd(OUT/'current.json');sup=inv['supervisor'];outcome=rd(O/'outer-outcome.json');ready=rd(O/'outer-ready.json')
 ck(cfg==s['config'] and cfg['phase']=='redgc300' and cfg['mode']=='red' and cfg['seconds']==300 and cfg['expected_exit']==1,'exact RED configuration')
 prep=rd(P/'preparation-pins-final.json');pr=rd(P/'review.json');binds(prep);binds(pr);binds(pr,'evidence_sha256')
 ck(len(prep['sha256'])==2325 and set(prep['sha256'])==set(rd(P/'required-paths-final.json')['paths']),'2325 final preparation members')
 ck(pr['accepted'] is True and pr['findings']==[] and pr['scope']=='BG specialization GC driver preparation' and pr['pins_sha256']==sha(P/'preparation-pins-final.json') and set(pr['sha256'])==set(prep['sha256'])|{str(P/'preparation-pins-final.json')},'canonical preparation review exact')
 prepared=set(prep['sha256'])|{str(P/'preparation-pins-final.json'),str(P/'review.json')}|set(pr['evidence_sha256'])
 expected=prepared|set(rd(P/'runtime-inputs-complete.json')['inventory'])|{str(RUN/'host.json'),str(RUN/'config.json'),str(O/'outer-ready.json')}
 W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl')
 for label,root in [('diagnostic',R),('production',W)]:
  b=rd(P/'baseline.json')[label];ck(set(git('ls-files','src','test','.github','Project.toml',cwd=root).splitlines())==set(b),'tracked baseline membership '+label)
  for n,h in b.items():ck(sha(root/n)==h,'baseline '+label+' '+n);expected.add(str(root/n))
 for mode,st in rd(P/'stages.json').items():
  root=Path(st['path']);members={str(f.relative_to(root)) for f in root.rglob('*') if f.is_file()}
  ck(members==set(st['sha256']) and len(members)==83,'83 stage members '+mode)
  for n,h in st['sha256'].items():ck(sha(root/n)==h,'stage '+mode+' '+n)
  if mode=='red':expected.update(str(root/n) for n in st['sha256'])
 ck(len(prepared)==2330 and s['files']==sorted(expected) and len(expected)==2333,'exact recomputed 2333 seal members')
 ck(s['trees']==[cfg['stage'],str(R/'diagnostics/direct-bg-export-specialized/reproduce')] and s['inputs']==[],'exact sealed roots and no input aliases')
 for label,v in [('sealed',s),('launch',pins)]:
  paths=set(v['files']);ck(v['files']==sorted(paths),'sorted unique '+label)
  for t in v['trees']:
   ck(Path(t).is_dir() and not Path(t).is_symlink(),'real tree '+t)
   for f in Path(t).rglob('*'):
    ck(not f.is_symlink(),'no tree symlink '+str(f))
    if f.is_file():paths.add(str(f))
  ck(paths==set(v['inventory']),'exact '+label+' inventory membership')
  for n,item in v['inventory'].items():
   ck(set(item)=={'resolved','sha256'} and str(Path(n).resolve(strict=True))==item['resolved'],'resolved '+label+' '+n)
   ck(sha(n)==item['sha256'],'fresh inventory '+label+' '+n)
 ck(set(pins['files'])==set(s['files'])|{str(RUN/n) for n in ['sealed.json','admission.json','prehost.json']}|{str(O/n) for n in ['release.json','outer-invocation.json']} and pins['trees']==s['trees'] and pins['inputs']==[],'exact launch additions')
 ck(rd(OUT/'pins.json')==pins and all(pins['inventory'][n]==v for n,v in s['inventory'].items()),'launch and guard seal identity')
 runtime=rd(P/'runtime-inputs-complete.json')['inventory'];ck(len(runtime)==609,'609 runtime entries')
 for n,v in runtime.items():ck(sha(n)==v['sha256'] and str(Path(n).resolve(strict=True))==v['resolved'],'runtime '+n)
 for name,v in rd(P/'copied-files.json').items():ck(sha(P/name)==sha(v['source'])==v['sha256'],'copied source '+name)
 gp=P.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-GC-PREPARATION');gpm=rd(gp/'preparation-pins-reviewed.json');gpr=rd(gp/'review.json');binds(gpm);binds(gpr);binds(gpr,'evidence_sha256')
 ck(gpr['accepted'] is True and gpr['findings']==[] and gpr['pins_sha256']==sha(gp/'preparation-pins-reviewed.json'),'accepted fixed GC amendment')
 binds(adm);binds(adm,'evidence_sha256');binds(rd(Q/'entry.json'));binds(rd(Q/'postcheck.json'));binds(a);binds(cl);binds(rd(P/'publication.json'))
 ck(adm['accepted'] is True and adm['findings']==[] and adm['scope']=='BG specialization GC exact-stage admission' and adm['phase']=='redgc300' and adm['pins_sha256']==sha(RUN/'sealed.json') and set(adm['sha256'])==set(s['files'])|{str(RUN/'sealed.json')},'exact 2334 admission bindings')
 ac=rd(Q/'admission-check.json');ck(ac['all_passed'] is True and ac['findings']==[] and ac['checks_passed']==7135,'saved independent admission 7135')
 ck(ac['inventory_sha256']=={n:v['sha256'] for n,v in s['inventory'].items()},'admission fresh inventory matches seal')
 ck(rd(Q/'postcheck.json')['all_passed'] is True and len(rd(Q/'postcheck.json')['checks'])==12 and all(rd(Q/'postcheck.json')['checks'].values()),'saved postcheck12')
 identity=s['outer_identity'];ck(identity==ready['identity']==cl['outer_identity']==outcome['identity']==ac['outer_identity'],'one exact outer identity')
 ck(identity['pid']==identity['pgid']==identity['sid']==129983 and identity['start_ticks']==11286240,'outer PID and start ticks')
 ck(ready['script_sha256']==sha(P/'outer.py') and ready['phase']=='redgc300' and ready['waiting_only'] is True and ready['expected_launcher']==str(P/'launch.py'),'ready binds actual scripts')
 ck(rd(O/'release.json')==dict(phase='redgc300',sealed_sha256=sha(RUN/'sealed.json'),admission_sha256=sha(RUN/'admission.json'),outer_ready_sha256=sha(O/'outer-ready.json'),one_attempt=True) and rd(O/'release.json')['one_attempt'] is True,'exact one-attempt release')
 ck(rd(O/'outer-invocation.json')==dict(identity=identity,phase='redgc300',seal_sha256=sha(RUN/'sealed.json'),review_sha256=sha(RUN/'admission.json'),release_sha256=sha(O/'release.json'),launcher_sha256=sha(P/'launch.py'),method='runpy.run_path launch.py as __main__ in this outer process'),'exact outer invocation')
 ck(rd(RUN/'reservation.json')==dict(one_attempt=True,phase='redgc300',command=cfg['command'],pins_sha256=sha(RUN/'launch-pins.json'),review_sha256=sha(RUN/'admission.json'),max_seconds=300) and rd(RUN/'reservation.json')['one_attempt'] is True,'exclusive one-attempt reservation')
 ck(inv['reservation_sha256']==sha(RUN/'reservation.json') and inv['review_sha256']==sha(RUN/'admission.json'),'reservation invocation linkage')
 ck(p['command']==cur['command']==inv['command']==cfg['command'] and p['cwd']==str(R),'exact measured command cwd')
 ck(p['pins_sha256']==cur['pins_sha256']==inv['pins_sha256']==sha(RUN/'launch-pins.json') and p['pins_unchanged'] is True,'measured pins unchanged')
 ck(inv['guard_command']==[inv['python'],'-B',str(P/'guard.py'),'run',str(RUN/'launch-pins.json'),str(OUT),'--seconds','292','--deadline',str(inv['monotonic_start']+292),'--expected-exit','1','--',*cfg['command']],'292 guard and absolute deadline')
 ck(Path(inv['python']).resolve()==Path(sys.executable).resolve(),'actual Python runtime')
 ck(cfg['command'][2:7]==['--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--history-file=no'],'exact Julia thread heap flags')
 wrapper=Path(cfg['command'][1]).read_text();ck('ulimit -v 8388608' in wrapper and '--startup-file=no "$@"' in wrapper,'VM8GiB startup wrapper')
 ck(cur['runner']==p['runner']==sup['guard_identity'] and cur['child']==p['child'],'runner and child identity chain')
 for role,pid,ticks in [('runner',130504,11318386),('child',130505,11318452)]:
  v=p[role];ck(v['pid']==v['pgid']==v['sid']==pid and v['start_ticks']==ticks and v['boot_id']==s['boot_id'],'actual '+role+' boot identity')
 ck(sup['returncode']==0 and sup['accepted'] is True and all(sup[k] is False for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']) and 'cleanup_error' not in sup,'successful guard without timeout cleanup')
 ck(p['returncode']==1 and p['reason']=='exit1' and 'error' not in p and outcome['launched'] is True and outcome['returncode']==0 and outcome['error']=='','Julia exit1 outer success')
 ck(0<p['elapsed_including_launch']<=sup['elapsed_seconds']<=inv['elapsed_seconds']<=300 and outcome['elapsed_with_checks_seconds']>=inv['elapsed_seconds'],'distinct inclusive clock scopes')
 ck(p['child_maxrss_kib']>0,'positive child RSS')
 for n in ['host.json','prehost.json','posthost.json']:
  h=rd(RUN/n);ck(h['matches']==[] and h['unreadable_identity_pids']==[] and all(h[k]==s[k] for k in ['head','master','boot_id']),'saved host safety '+n)
 ck(set(s['groups'])==set(rd(P/'host-entry.json')['groups']) and len(s['groups'])==259,'complete 259 prior groups')
 ck(set(cl['sha256'])=={str(O/n) for n in ['outer-ready.json','release.json','outer-invocation.json','outer-outcome.json']}|{str(RUN/n) for n in ['sealed.json','admission.json','posthost.json','audit.json']},'exact eight closure bindings')
 groups=set(s['groups'])|{identity['pgid'],identity['sid']}|{p[r][k] for r in ['runner','child'] for k in ['pgid','sid']};h=cl['host']
 ck(cl['all_passed'] is True and set(h['groups'])==groups and len(groups)==262 and h['matches']==[] and h['unreadable_identity_pids']==[],'saved full262 PGID AND SID closure')
 ck(all(h[k]==s[k] for k in ['head','master','boot_id']) and h['time']>p['ended'],'post-return closure refs boot time')
 resources=[json.loads(l) for l in (OUT/'resources.jsonl').read_text().splitlines()]
 ck(len(resources)==9 and all(z['available_kib']>=6*1024**2 and z['swap_used_kib']<=1024**2 for z in resources+[p['terminal_memory']]),'all resource samples and terminal limits')
 ck([z['elapsed'] for z in resources]==sorted(z['elapsed'] for z in resources) and resources[-1]['elapsed']<=p['elapsed_including_launch'],'resource clock ordering')
 ck(a['all_passed'] is True and a['pure_timeout'] is False and a['error']=='' and a['phase']=='redgc300','saved audit success not pure timeout')
 expectedout={'pins.json','current.json','process.json','resources.jsonl','run.log','raw.toml'}|{f'window-{c}-{w}.toml' for c in range(1,4) for w in range(1,21)}|{f'preparation-{c}.toml' for c in range(1,4)}
 ck({f.name for f in OUT.iterdir()}==expectedout and all(f.is_file() and not f.is_symlink() for f in OUT.iterdir()),'exact69 complete output files')
 ck({f.name for f in RUN.iterdir()}=={'admission.json','audit.json','config.json','host.json','invocation.json','launch-pins.json','launcher.log','outer-closure.json','output','posthost.json','prehost.json','reservation.json','sealed.json'},'exact run membership before review')
 ck({f.name for f in O.iterdir()}=={'outer-invocation.json','outer-outcome.json','outer-ready.json','release.json'},'exact outer membership')
 ck(set(a['sha256'])=={str(f) for f in RUN.rglob('*') if f.is_file()}-{str(RUN/'audit.json'),str(RUN/'outer-closure.json')},'saved audit exact then-current file membership')
 raw=tomllib.loads((OUT/'raw.toml').read_text());ck(set(raw)==set('fatal preparation_calls complete preparations_completed threads blas_threads phase tests loaded'.split()),'raw exact schema')
 ck(raw['complete'] is True and raw['fatal']=='' and raw['phase']=='redgc300' and all(type(raw[k]) is int and raw[k]==v for k,v in [('threads',1),('blas_threads',1),('preparation_calls',3),('preparations_completed',3)]),'raw complete1thread3calls3done')
 ck(raw['loaded']==dict(rd(P/'loaded-paths.json'),JSimplex=str(Path(cfg['stage'])/'src/JSimplex.jl')),'actual loaded module paths')
 root=raw['tests'];ck(set(root)==set('pass name fail broken failures error children'.split()) and root['name']=='root' and all(type(root[k]) is int and root[k]==0 for k in ['pass','fail','broken','error']) and root['failures']==[] and len(root['children'])==3,'exact root test tree')
 fixtures=[f for f in rd(P/'inputs.json')['fixtures'] if f['name'] in ['sparse32','dense32','sparse96']]
 ck(tomllib.loads((P/'inputs.toml').read_text())['fixtures']==rd(P/'inputs.json')['fixtures'],'JSON and Julia TOML fixtures identical')
 result['allocation']=[];result['residual_checks']=0;result['paired_bit_checks']=0;result['observed_windows']=0;result['observed_gc_nonzero']=0;allrows={}
 for cell,f in enumerate(fixtures,1):
  leaf=root['children'][cell-1]
  ck(set(leaf)==set(root) and leaf['name']=='allocation_nonincrease_'+f['name'] and all(type(leaf[k]) is int and leaf[k]==v for k,v in [('pass',0),('fail',1),('error',0),('broken',0)]) and leaf['children']==[] and len(leaf['failures'])==1 and 'median7(cands_events)' in leaf['failures'][0],'exact expected allocation leaf '+f['name'])
  matrices=[(mat(m),mat(m,True)) for m in f['matrices']];rows=[]
  for w in range(1,21):
   name=f'window-{cell}-{w}.toml';row=tomllib.loads((OUT/name).read_text());allrows[name]=row;rows.append(row);pair=(w+1)//2;order=(w-1)%2+1;side=['reference','candidate'][(order-1) if pair%2 else 2-order]
   ck(set(row)==set('pair order side measured policy correct inputs_unchanged modes seconds bytes events gc_seconds compile_seconds recompile_seconds retained_bytes nested_seconds outputs'.split()),'exact window schema '+name)
   ck(type(row['pair']) is int and row['pair']==pair and type(row['order']) is int and row['order']==order and row['side']==side and row['measured'] is (pair>3),'exact alternating window '+name)
   ck(row['correct'] is True and row['inputs_unchanged'] is True and row['policy']=='threshold_one' and len(row['modes'])==3 and all(v in ['normalized','direct','fallback'] for v in row['modes']),'correct input policy mode '+name)
   ck(all(type(row[k]) in (int,float) and math.isfinite(row[k]) and row[k]>=0 for k in ['seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds','retained_bytes']) and row['seconds']>0 and all(type(row[k]) is int for k in ['bytes','events','retained_bytes']),'valid window metrics '+name)
   ck(len(row['nested_seconds'])==6 and all(type(v) in (int,float) and math.isfinite(v) and v>=0 for v in row['nested_seconds']) and sum(row['nested_seconds'])<=row['seconds']+1e-9,'nested clocks '+name)
   if pair>3:
    ck(row['compile_seconds']==row['recompile_seconds']==0,'observed compile zero '+name);result['observed_windows']+=1;result['observed_gc_nonzero']+=int(row['gc_seconds']!=0)
   ck(len(row['outputs'])==24,'24 outputs '+name)
   for k,step in enumerate(f['steps']):
    for offset,m,b in [(0,matrices[k][0],step['a']),(1,matrices[k][0],step['dse']),(2,matrices[k+1][1],step['unit'])]:
     ck(residual(m,row['outputs'][3*k+offset],b),'independent rational residual '+name+' '+str(3*k+offset));result['residual_checks']+=1
   if order==2:
    prev=rows[-2];ck(row['outputs']==prev['outputs'] and row['modes']==prev['modes'],'exact paired bits and modes '+name);result['paired_bit_checks']+=1
  st={k:{side:statistics.median(r[k] for r in rows if r['side']==side and r['measured']) for side in ['reference','candidate']} for k in ['events','bytes','retained_bytes','seconds']}
  ck(st['events']['candidate']>st['events']['reference'] and st['bytes']['candidate']<st['bytes']['reference'],'RED allocation false despite lower bytes '+f['name'])
  ast=a['allocation'][cell-1];ck(ast['fixture']==f['name'] and ast['statistics']['allocation_gate'] is False,'audit RED predicate '+f['name'])
  for k,med in st.items():
   for side,v in med.items():ck(ast['statistics'][k][side]['median']==v,'audit median '+f['name']+' '+k+' '+side)
  result['allocation'].append(dict(fixture=f['name'],medians=st))
 ck(result['residual_checks']==1440 and result['paired_bit_checks']==30 and result['observed_windows']==42 and result['observed_gc_nonzero']==0,'all1440 residuals30pairs42observed noGC')
 preps={};keys=set('phase fixture cell after_pair before_pair requested_full_gc calls cumulative_calls returned seconds bytes events gc_seconds compile_seconds recompile_seconds gc_pauses full_collections'.split())
 for cell,f in enumerate(fixtures,1):
  row=tomllib.loads((OUT/f'preparation-{cell}.toml').read_text());preps[f'preparation-{cell}.toml']=row
  ck(set(row)==keys and row['phase']=='redgc300' and row['fixture']==f['name'],'preparation exact17 identity '+f['name'])
  ck(all(type(row[k]) is int and row[k]==v for k,v in [('cell',cell),('after_pair',3),('before_pair',4),('calls',1),('cumulative_calls',cell)]) and row['requested_full_gc'] is True and row['returned'] is True,'preparation strict schedule '+f['name'])
  ck(all(type(row[k]) is int and row[k]>=0 for k in ['bytes','events','gc_pauses','full_collections']) and all(type(row[k]) is float and math.isfinite(row[k]) and row[k]>=0 for k in ['seconds','gc_seconds','compile_seconds','recompile_seconds']),'preparation strict metrics '+f['name'])
  ck(row['seconds']<=p['elapsed_including_launch']+1e-9,'GC individual inner wall bound '+f['name'])
 ck(a['preparation']['records']==list(preps.values()) and a['preparation']['saved_preparations']==3 and a['preparation']['saved_windows']==60 and a['preparation']['raw_counters_available'] is True,'audit exact preparations')
 # Definitions-only pure oracle import; independently enumerate all prefix/boundary possibilities.
 sys.path.insert(0,str(P));from preparation_oracle import preparation_results
 schedule=[f'window-{c}-{w}.toml' for c in range(1,4) for w in range(1,21)];pc=0
 for n in range(61):
  for done in range(4):
   wr={k:allrows[k] for k in schedule[:n]};pr={k:preps[k] for k in list(preps)[:done]}
   valid=all((n>=(c-1)*20+6 if c<=done else n<=(c-1)*20+6) for c in range(1,4))
   for calls in range(4):
    rr=dict(raw,complete=False,preparation_calls=calls,preparations_completed=done)
    expected=valid and done<=calls<=done+1 and (calls==done or n==done*20+6)
    try:preparation_results(pr,wr,rr,'redgc300',False);accepted=True
    except (ValueError,KeyError,TypeError):accepted=False
    ck(accepted==expected,f'partial prefix n{n} done{done} calls{calls}');pc+=1
   try:preparation_results(pr,wr,None,'redgc300',False);accepted=True
   except (ValueError,KeyError,TypeError):accepted=False
   ck(accepted==valid,f'partial no raw n{n} done{done}');pc+=1
 result['partial_prefix_cases']=pc
 log=(OUT/'run.log').read_text()+'\n'+(RUN/'launcher.log').read_text()
 ck(not re.search(r'(?i)\bwarning\b|world[ -]age',log) and log.count('TEST FAILURE:')==3 and all(v not in log for v in ['BROKEN TEST:','FATAL DRIVER:','GROUP/COUNT MISMATCH','OutOfMemoryError','LoadError']),'exact3failure clean diagnostic logs')
 ck(rd(P.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-DRIVER')/'runs/red300/audit.json')['all_passed'] is False,'original RED stays failed')
 ck(not (P/'runs/greengc300').exists() and not (P/'outers/greengc300').exists(),'no GREEN attempt')
 expectedhead='18ab2a17b16508833d16b83cdcfb832a7c422c18';master='26e2291745999f485a74f643298ca997d65c7205'
 ck(git('rev-parse','HEAD')==git('rev-parse','origin/codex/simplex-core-architecture')==s['head']==expectedhead and git('rev-parse','master')==git('rev-parse','HEAD',cwd=W)==s['master']==master,'fresh unchanged local refs')
 remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture');ck(remote==h['remote']==expectedhead+'\trefs/heads/codex/simplex-core-architecture\n'+master+'\trefs/heads/master','fresh remote refs')
 ck(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'fresh clean tracked staged')
 env=rd(P/'environment.json');ck({k:os.environ.get(k) for k in env}==env,'current exact loading environment')
 fresh={'groups':sorted(groups),'matches':[],'unreadable_exe_pids':[],'unreadable_identity_pids':[]}
 for proc in Path('/proc').glob('[0-9]*'):
  try:
   fields=(proc/'stat').read_text().rsplit(')',1)[1].split();comm=(proc/'comm').read_text().strip();argv0=(proc/'cmdline').read_bytes().split(b'\0')[0].decode(errors='replace');exe=''
   try:exe=str((proc/'exe').resolve(strict=True))
   except PermissionError:fresh['unreadable_exe_pids'].append(int(proc.name))
   except FileNotFoundError:pass
   if int(fields[2]) in groups or int(fields[3]) in groups or any(Path(z).name.lower().startswith('julia') for z in [comm,argv0,exe]):fresh['matches'].append(dict(pid=int(proc.name),pgid=int(fields[2]),sid=int(fields[3]),comm=comm,argv0=argv0,exe=exe))
  except (FileNotFoundError,ProcessLookupError):pass
  except PermissionError:fresh['unreadable_identity_pids'].append(int(proc.name))
 ck(fresh['matches']==[] and fresh['unreadable_identity_pids']==[],'fresh all262 groups ANDsessions closed noJulia')
 ck(Path('/proc/sys/kernel/random/boot_id').read_text().strip()==s['boot_id']=='1ecae454-f1f5-4e2e-a95c-7b5474243126','fresh same boot')
 result['fresh_host']=fresh;result['preparation']=list(preps.values());result['clocks']={'guard':p['elapsed_including_launch'],'supervisor':sup['elapsed_seconds'],'invocation':inv['elapsed_seconds'],'outer_including_checks':outcome['elapsed_with_checks_seconds']};result['resources']={'samples':len(resources),'min_available_kib':min(z['available_kib'] for z in resources),'max_swap_kib':max(z['swap_used_kib'] for z in resources),'child_maxrss_kib':p['child_maxrss_kib']}
 summary=rd(Q/'summary.json');ck(summary['measured_windows']==42 and summary['measured_gc_nonzero']==0 and summary['resource_samples']==9 and summary['min_available_kib']==result['resources']['min_available_kib'] and summary['max_swap_kib']==result['resources']['max_swap_kib'] and summary['runner']==p['runner'] and summary['child']==p['child'],'report summary metrics identities')
 for v,st in zip(summary['allocations'],result['allocation']):ck(v==dict(fixture=st['fixture'],reference_events=st['medians']['events']['reference'],old_workspace_events=st['medians']['events']['candidate'],reference_bytes=st['medians']['bytes']['reference'],old_workspace_bytes=st['medians']['bytes']['candidate']),'report allocation summary '+st['fixture'])
 result['run_sha256']={str(f):digest(f) for f in sorted(RUN.rglob('*')) if f.is_file()};result['outer_sha256']={str(f):digest(f) for f in sorted(O.iterdir())};result['fresh_hashed_paths']=len(cache);result['seal_paths']=len(s['inventory']);result['launch_paths']=len(pins['inventory']);result['listed_seal_bytes']=sum(Path(n).stat().st_size for n in s['inventory']);result['all_passed']=True
except Exception as e:
 result['all_passed']=False;result['findings'].append(repr(e));result['traceback']=traceback.format_exc()
result['completed']=time.time();result['checks_passed']=len(result['checks'])
with (Q/'result-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['checks','run_sha256','outer_sha256','fresh_host']}))
if not result['all_passed']:sys.exit(1)
