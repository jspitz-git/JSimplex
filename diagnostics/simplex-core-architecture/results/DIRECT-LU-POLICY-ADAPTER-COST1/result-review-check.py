"""Independent saved-output review. Standard library only; no author code imports/reruns."""
from pathlib import Path
import json,tomllib,hashlib,math,subprocess,os,time,traceback
E=Path(__file__).resolve().parent;R=E.parents[3];D=E.parent/'DIRECT-LU-POLICY-ADAPTER-COST-PREPARATION';P=D/'runs/cost1-300';O=P/'output'
checks=[];facts={};hashed={}
def rd(p):return json.loads(Path(p).read_text())
def tom(p):return tomllib.loads(Path(p).read_text())
def sha(p):
 p=Path(p);s=p.stat();key=(str(p),s.st_size,s.st_mtime_ns)
 if key not in hashed:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):h.update(b)
  hashed[key]=h.hexdigest()
 return hashed[key]
def ck(n,v):
 checks.append(dict(name=n,passed=bool(v)))
 if not v:raise AssertionError(n)
def binds(n,m):ck(n,all(sha(Path(p) if Path(p).is_absolute() else R/p)==v for p,v in m.items()))
def invcheck(n,j):
 paths=set(j['files'])
 for t in j['trees']:
  root=Path(t);ck(n+' tree valid '+t,root.is_dir() and not root.is_symlink())
  ck(n+' no directory symlink '+t,not any(p.is_symlink() and (p.is_dir() or not p.exists()) for p in root.rglob('*')))
  paths|={str(p) for p in root.rglob('*') if p.is_file()}
 ck(n+' exact inventory',paths==set(j['inventory']))
 ck(n+' all current resolved hashes',all(sha(p)==v['sha256'] and str(Path(p).resolve(strict=True))==v['resolved'] for p,v in j['inventory'].items()))
def integer_tokens(tokens):
 values=[]
 for token in tokens:
  if not isinstance(token,str) or len(token)!=16 or any(c not in '0123456789abcdef' for c in token):raise ValueError('bad token')
  bits=int(token,16);exp=(bits>>52)&2047;mant=bits&((1<<52)-1)
  if exp==2047:raise ValueError('nonfinite token')
  if exp:mant+=1<<52;power=exp-1023-52
  else:power=-1074
  if bits>>63:mant=-mant
  if not mant:power=0
  values.append((mant,power))
 denominator=max([0]+[-power for mant,power in values])
 return [mant<<(power+denominator) for mant,power in values],denominator

def matrix(m,transposed):
 n=m['n'];v,e=integer_tokens(m['nzval']);rows=[[] for i in range(n)]
 for col in range(n):
  for k in range(m['colptr'][col]-1,m['colptr'][col+1]-1):
   row=m['rowval'][k]-1;i,j=(col,row) if transposed else (row,col);rows[i].append((j,v[k]))
 return rows,e,max(sum(abs(z) for j,z in row) for row in rows)
def exact_residual(m,xx,bb):
 rows,em,nm=m;x,ex=integer_tokens(xx);b,eb=integer_tokens(bb)
 if len(x)!=len(rows) or len(b)!=len(rows):return False
 e=max(em+ex,eb,0);sx=e-em-ex;sb=e-eb
 r=max(abs((sum(a*x[j] for j,a in row)<<sx)-(b[i]<<sb)) for i,row in enumerate(rows))
 scale=max(1<<e,(nm*max(map(abs,x)))<<sx,max(map(abs,b))<<sb)
 return (r<<52)<=128*len(rows)*scale

def stats(xs):
 med=sorted(xs)[len(xs)//2]
 return dict(median=med,mad=sorted(abs(x-med) for x in xs)[len(xs)//2],minimum=min(xs),maximum=max(xs),values=xs)
def statistics_of(rows):
 pairs=[{r['side']:r for r in rows if r['pair']==p} for p in range(4,11)];a=[p['reference'] for p in pairs];b=[p['candidate'] for p in pairs];s={}
 for metric in ['seconds','bytes','events','retained_bytes','gc_seconds','compile_seconds','recompile_seconds']:
  av=[x[metric] for x in a];bv=[x[metric] for x in b];s[metric]=dict(reference=stats(av),candidate=stats(bv))
  if all(v!=0 for v in av):s[metric]['paired_ratio']=stats([y/x for x,y in zip(av,bv)])
 s['nested_seconds']=[dict(reference=stats([x['nested_seconds'][i] for x in a]),candidate=stats([x['nested_seconds'][i] for x in b])) for i in range(6)]
 s.update(faster_pairs=sum(y['seconds']<x['seconds'] for x,y in zip(a,b)),time_median_gate=s['seconds']['paired_ratio']['median']<=0.95,allocation_gate=all(s[m]['candidate']['median']<=s[m]['reference']['median'] for m in ['bytes','events']),memory_gate=all(10*y['retained_bytes']<=11*x['retained_bytes'] for x,y in zip(a,b)))
 return s
try:
 seal=rd(P/'sealed.json');pins=rd(P/'launch-pins.json');ad=rd(P/'admission.json');audit=rd(P/'audit.json');cfg=rd(P/'config.json');pr=rd(O/'process.json');cur=rd(O/'current.json');invoke=rd(P/'invocation.json');sup=invoke['supervisor'];res=rd(P/'reservation.json')
 ck('admission accepted exact membership',ad['accepted'] is True and ad['findings']==[] and ad['phase']=='cost1-300' and ad['scope']=='direct adapter matched cost admission' and set(ad['sha256'])==set(seal['files'])|{str(P/'sealed.json')} and ad['pins_sha256']==sha(P/'sealed.json'))
 binds('admission hashes',ad['sha256']);binds('admission evidence',ad['evidence_sha256']);invcheck('sealed',seal);invcheck('launch',pins)
 ck('launch exact files',set(pins['files'])==set(seal['files'])|{str(P/n) for n in ['sealed.json','admission.json','prehost.json']} and pins['trees']==seal['trees'] and len(pins['inventory'])==1812)
 ck('output identical launch pins',rd(O/'pins.json')==pins)
 ck('config canonical',cfg==seal['config']==rd(D/'config.json')['cost1-300'])
 ck('full command linkage',pr['command']==cur['command']==invoke['command']==cfg['command'] and pr['cwd']==str(R))
 cmd=['/usr/bin/python3','-B',str(D/'guard.py'),'run',str(P/'launch-pins.json'),str(O),'--seconds','292','--deadline',str(invoke['monotonic_start']+292),'--expected-exit','0','--']+cfg['command']
 ck('exact inner292 command',invoke['guard_command']==cmd and invoke['python']=='/usr/bin/python3')
 ck('reservation exact one attempt',res==dict(one_attempt=True,phase='cost1-300',command=cfg['command'],pins_sha256=sha(P/'launch-pins.json'),review_sha256=sha(P/'admission.json'),max_seconds=300))
 ck('hash identities',invoke['reservation_sha256']==sha(P/'reservation.json') and invoke['review_sha256']==sha(P/'admission.json') and pr['pins_sha256']==cur['pins_sha256']==invoke['pins_sha256']==sha(P/'launch-pins.json'))
 ck('process identity linkage',pr['runner']==cur['runner']==sup['guard_identity'] and pr['child']==cur['child'])
 for role in ['runner','child']:
  z=pr[role];ck(role+' session identity',z['pid']==z['pgid']==z['sid'] and z['start_ticks']>0 and z['boot_id']==seal['boot_id'])
 ck('recorded commands',pr['runner']['command'].strip()==' '.join(cmd) and pr['child']['command'].strip()==' '.join(cfg['command']))
 ck('exit accepted no interventions',pr['reason']=='exit0' and pr['returncode']==sup['returncode']==0 and sup['accepted'] is True and not any(sup[k] for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']) and 'cleanup_error' not in sup and pr['pins_unchanged'] is True)
 ck('inclusive and inner elapsed',0<pr['elapsed_including_launch']<=292 and 0<sup['elapsed_seconds']<=invoke['elapsed_seconds']<=300)
 for n in ['host.json','prehost.json','posthost.json']:
  h=rd(P/n);ck(n+' host refs',all(h[k]==seal[k] for k in ['head','master','boot_id']) and not h['matches'])
 post=rd(P/'posthost.json');ck('group session closure coverage',set(seal['groups'])<=set(rd(P/'prehost.json')['groups'])<=set(post['groups']) and all(pr[role][k] in post['groups'] for role in ['runner','child'] for k in ['pgid','sid']))
 ck('no second or retry',set(p.name for p in (D/'runs').iterdir())=={'cost1-300'})
 samples=[json.loads(x) for x in (O/'resources.jsonl').read_text().splitlines()];ck('all sampled and terminal resources',len(samples)==12 and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in samples+[pr['terminal_memory']]))
 ck('sampling chronological',all(a['elapsed']<=b['elapsed'] for a,b in zip(samples,samples[1:])) and samples[-1]['elapsed']<=pr['elapsed_including_launch'])
 ck('logs exact', (O/'run.log').read_text()=='BEGIN matched policy cost cost1-300\n' and json.loads((P/'launcher.log').read_text())==pr)
 wanted={'pins.json','current.json','process.json','resources.jsonl','run.log','raw.toml'}|{f'{prefix}-{c}.toml' for c in range(1,25) for prefix in ['started','preflight','cell']}|{f'window-{c}-{w}.toml' for c in range(1,25) for w in range(1,21)}
 ck('558 exact outputs',len(wanted)==558 and {x.name for x in O.iterdir()}==wanted and all(x.is_file() and not x.is_symlink() for x in O.iterdir()))
 loaded=rd(D/'loaded-paths.json')|{'JSimplex':str(Path(cfg['stage'])/'src/JSimplex.jl')}
 ck('complete raw exact',tom(O/'raw.toml')==dict(phase='cost1-300',loaded=loaded,completed=True,fatal='',cells=24,windows=480,threads=1,blas_threads=1))
 ck('audit accepted first only',audit['all_passed'] is True and audit['pure_timeout'] is False and audit['counts']==dict(cells=24,windows=480,exact_residuals=11520) and audit['selection']==audit['manager_backend']==[] and len(audit['cells'])==24)
 ck('audit hashes exact preaudit membership',set(audit['sha256'])=={str(x) for x in P.rglob('*') if x.is_file() and x.name!='audit.json'})
 binds('audit full hashes',audit['sha256'])
 schema=set('pair order side measured policy correct inputs_unchanged modes seconds bytes events gc_seconds compile_seconds recompile_seconds retained_bytes nested_seconds outputs'.split())
 count=0;cell=0;allcells=[];gcs=[];modes=0;report=(E/'REPORT.md').read_text();table=[];nested=[]
 for fixture in rd(D/'inputs.json')['fixtures']:
  matrices=[(matrix(m,False),matrix(m,True)) for m in fixture['matrices']]
  for manager in ['FT','SS','BG']:
   for backend in ['native','markowitz']:
    cell+=1;ident=dict(fixture=fixture['name'],manager=manager,backend=backend,policy='threshold_one' if backend=='native' else 'default');label=str(cell)
    ck(label+' identity and completion',tom(O/f'started-{cell}.toml')==ident and tom(O/f'cell-{cell}.toml')==ident|{'windows':20})
    pf=tom(O/f'preflight-{cell}.toml');ck(label+' preflight schema',set(pf)==set('reference candidate modes inputs_unchanged constructions refactors explicit_solves'.split()) and pf['inputs_unchanged'] is True and [pf[k] for k in ['constructions','refactors','explicit_solves']]==[2,4,0] and all(type(pf[k]) is int for k in ['constructions','refactors','explicit_solves']) and len(pf['reference'])==len(pf['candidate'])==3 and pf['modes']==['normalized']*3)
    for j,x in enumerate(pf['reference']+pf['candidate']):
     ck(label+' preflight item '+str(j),set(x)==set('kind policy control expected_control strategy'.split()) and x['kind']==backend and x['policy']==ident['policy'])
     if backend=='native':
      ck(label+' actual controls '+str(j),len(x['control'])==20 and x['control']==x['expected_control'] and x['control'][3]=='3ff0000000000000' and x['control'][7]=='0000000000000000');integer_tokens(x['control']+[x['strategy']])
     else:ck(label+' Markowitz fields '+str(j),x['control']==x['expected_control']==[] and x['strategy']=='')
    rows=[]
    for w in range(1,21):
     r=tom(O/f'window-{cell}-{w}.toml');pair=(w+1)//2;order=(w-1)%2+1;side='reference' if (pair%2==1)==(order==1) else 'candidate';l=f'{cell}/{w}'
     ck(l+' schema schedule',set(r)==schema and type(r['pair']) is int and type(r['order']) is int and type(r['measured']) is bool and r['pair']==pair and r['order']==order and r['side']==side and r['measured']==(pair>3) and r['policy']==ident['policy'])
     ck(l+' mode unchanged correct',r['correct'] is True and r['inputs_unchanged'] is True and r['modes']==(['normalized'] if side=='candidate' else ['ordinary'])*3)
     ck(l+' valid counters times',all(type(r[k]) is int and r[k]>=0 for k in ['bytes','events','retained_bytes']) and all(type(r[k]) in (float,int) and math.isfinite(r[k]) and r[k]>=0 for k in ['seconds','gc_seconds','compile_seconds','recompile_seconds']) and r['seconds']>0 and len(r['nested_seconds'])==6 and all(math.isfinite(v) and v>=0 for v in r['nested_seconds']) and sum(r['nested_seconds'])<=r['seconds']+1e-9)
     ck(l+' measured compile zero',pair<=3 or r['compile_seconds']==r['recompile_seconds']==0)
     ck(l+' output shape',len(r['outputs'])==24 and all(len(x)==fixture['n'] for x in r['outputs']))
     for k,s in enumerate(fixture['steps']):
      for offset,mat,rhs in [(0,matrices[k][0],s['a']),(1,matrices[k][0],s['dse']),(2,matrices[k+1][1],s['unit'])]:ck(l+' exact residual '+str(3*k+offset),exact_residual(mat,r['outputs'][3*k+offset],rhs));count+=1
     if side=='candidate':modes+=3
     if pair>3 and r['gc_seconds']>0:gcs.append(dict(cell=cell,pair=pair,side=side,seconds=r['gc_seconds']))
     rows.append(r)
    st=statistics_of(rows);entry=ident|dict(preflight=pf,modes=[r['modes'] for r in rows],statistics=st)
    ck(label+' independently reconstructed entire audit cell',entry==audit['cells'][cell-1]);allcells.append(entry)
    ck(label+' negative time allocations positive memory',st['time_median_gate'] is False and st['allocation_gate'] is False and st['memory_gate'] is True and st['seconds']['paired_ratio']['median']>1 and all(st[m]['candidate']['median']>st[m]['reference']['median'] for m in ['bytes','events']) and st['retained_bytes']['candidate']['median']<st['retained_bytes']['reference']['median'])
    q=st['seconds']['paired_ratio'];txt=f"| {fixture['name']} | {manager} | {backend} | {q['median']:.6f} / {q['mad']:.6f} / {q['minimum']:.6f}–{q['maximum']:.6f} | {st['faster_pairs']} | "+' | '.join(f"{st[m]['reference']['median']} / {st[m]['candidate']['median']}" for m in ['bytes','events','retained_bytes'])+' |';table.append(txt);ck(label+' report full cost row',txt in report)
    values=[st['seconds']]+st['nested_seconds'];nt=f"| {fixture['name']} | {manager} | {backend} | "+' | '.join(f"{z['reference']['median']*1e6:.3f} / {z['candidate']['median']*1e6:.3f}" for z in values)+' |';nested.append(nt);ck(label+' report nested row',nt in report)
 ck('11520 independent exact residuals',count==11520)
 ck('normalized observations and GC',modes==720 and len(gcs)==19 and sum(x['side']=='reference' for x in gcs)==7)
 ck('report has exactly 48 data rows',sum(l.startswith(('| sparse32 |','| sparse96 |','| dense32 |','| dense96 |')) for l in report.splitlines())==48)
 ck('nested header ordering', '| Whole ref / candidate us | Construct | FTRAN | BTRAN | Updates | Refactor4 | Refactor8 |' in report)
 ck('negative and one process scopes','first process only' in report and 'not the complete two-process comparison' in report and 'not recommended for performance promotion' in report and 'not native live/peak/free accounting' in report)
 for n,countchecks in [('postcheck.json',9),('summary-check.json',8)]:
  j=rd(E/n);ck(n+' accepted exact checks',j['all_passed'] is True and len(j['checks'])==countchecks and all(j['checks'].values()))
 binds('postcheck hashes',rd(E/'postcheck.json')['sha256'])
 for live,before in [(R/'diagnostics/simplex-core-architecture/STATUS.md',E/'STATUS.md.before-cost1'),(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',E/'roadmap.md.before-cost1')]:
  for n in ['closure.json','publication.json']:ck('pending continuation mapping '+n+live.name,sha(live)==sha(before)==rd(D/n)['sha256'][str(live.relative_to(R))])
 def git(*a):return subprocess.check_output(['git',*a],cwd=R).decode().strip()
 ck('exact refs current',git('rev-parse','HEAD')==seal['head'] and git('rev-parse','master')==seal['master'] and git('ls-remote','origin','refs/heads/master')==seal['master']+'\trefs/heads/master')
 ck('index tracked clean',not git('diff','--name-only') and not git('diff','--cached','--name-only'))
 matches=[];unreadable=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   fields=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip();exe=''
   try:exe=str((p/'exe').resolve(strict=True))
   except PermissionError:unreadable.append(int(p.name))
   except FileNotFoundError:pass
   if int(fields[2]) in post['groups'] or int(fields[3]) in post['groups'] or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):matches.append(dict(pid=int(p.name),comm=comm,exe=exe))
  except (FileNotFoundError,ProcessLookupError):pass
 ck('fresh full groups sessions no Julia',not matches and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==seal['boot_id'])
 facts=dict(exact_residuals=count,cells=cell,windows=480,normalized_observations=modes,measured_gc=gcs,elapsed=invoke['elapsed_seconds'],resources=dict(samples=len(samples),min_available_kib=min(x['available_kib'] for x in samples),max_swap_kib=max(x['swap_used_kib'] for x in samples),child_maxrss_kib=pr['child_maxrss_kib'],terminal=pr['terminal_memory']),host=dict(time=time.time(),matches=matches,groups=post['groups'],unreadable_exe_pids=unreadable),all_cell_statistics=allcells,report_cost_rows=table,report_nested_rows=nested)
except Exception:facts['error']=traceback.format_exc()
finally:
 result=dict(all_passed=all(x['passed'] for x in checks) and 'error' not in facts,count=len(checks),checks=checks,facts=facts)
 with (E/'result-review-checks.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps(dict(all_passed=result['all_passed'],checks=result['count'],error=facts.get('error'),exact_residuals=facts.get('exact_residuals'),cells=facts.get('cells'))))
