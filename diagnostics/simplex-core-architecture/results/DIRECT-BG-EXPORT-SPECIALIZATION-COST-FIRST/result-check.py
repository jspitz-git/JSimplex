"""Fresh independent saved-result recomputation. No operational auditor or Julia execution.
Only pure record-schema/cache/counter/preflight/control predicates are reused.
Residuals, complete schedule, statistics, bindings, inverses and host scan are independent.
"""
from pathlib import Path
import sys,json,hashlib,tomllib,struct,math,statistics,subprocess,time,re
from fractions import Fraction
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
P=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-SPECIALIZATION-COST';Q=P.with_name(P.name+'-FIRST');RUN=P/'runs/cost1-300';OUT=RUN/'output';O=P/'outers/cost1-300';C=R/'diagnostics/direct-bg-export-specialized/reproduce'
G=P.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-GC-DRIVER');GR=G/'runs/greengc300'
sys.path.insert(0,str(P));import record_schema as schema;import evidence as predicates
checks=[];used=set();hash_counts={};residual_count=0

def ck(v,label):
 checks.append(dict(check=label,passed=bool(v)))
 if not v:raise AssertionError(label)
def path(p):
 p=Path(p);return p if p.is_absolute() else R/p
def read(p):
 p=path(p);used.add(str(p));return json.loads(p.read_text())
def txt(p):
 p=path(p);used.add(str(p));return p.read_text()
def toml(p):return tomllib.loads(txt(p))
def sha(p):
 p=path(p);return hashlib.sha256(p.read_bytes()).hexdigest()
def bind(d,label):
 hash_counts[label]=len(d)
 for n,h in d.items():ck(sha(n)==h,label+' '+n)
def invcheck(v,label):
 ck(set(v['files'])==set(v['inventory']),label+' exact inventory membership')
 for n,h in v['inventory'].items():
  ck(h==dict(resolved=str(path(n).resolve()),sha256=sha(n)),label+' '+n)
 for tree in v['trees']:
  ck(not path(tree).is_symlink() and not any(p.is_symlink() for p in path(tree).rglob('*')),label+' tree no symlinks '+tree)
  ck({str(p) for p in path(tree).rglob('*') if p.is_file()}<=set(v['files']),label+' complete tree '+tree)
 hash_counts[label]=len(v['inventory'])
def git(*args,cwd=R):return subprocess.check_output(['git',*args],cwd=cwd,text=True).strip()
def stats(values):
 m=statistics.median(values);return dict(median=m,mad=statistics.median([abs(x-m) for x in values]),minimum=min(values),maximum=max(values),values=values)
def decode(tokens):
 ck(type(tokens) is list and all(type(t) is str and re.fullmatch('[0-9a-f]{16}',t) for t in tokens),'exact Float64 tokens')
 values=[struct.unpack('>d',bytes.fromhex(t))[0] for t in tokens]
 ck(all(math.isfinite(x) for x in values),'finite decoded bits')
 ratios=[x.as_integer_ratio() for x in values];exponent=max([d.bit_length()-1 for n,d in ratios],default=0)
 return [n*2**(exponent-(d.bit_length()-1)) for n,d in ratios],exponent

def matrix(m,transpose=False):
 n=m['n'];vals,e=decode(m['nzval']);rows=[[] for _ in range(n)]
 ck(len(m['colptr'])==n+1 and m['colptr'][0]==1 and m['colptr'][-1]==len(vals)+1 and len(vals)==len(m['rowval']),'CSC shape')
 for j in range(n):
  ix=range(m['colptr'][j]-1,m['colptr'][j+1]-1);inds=[m['rowval'][k] for k in ix]
  ck(inds==sorted(set(inds)) and all(1<=i<=n for i in inds),'canonical CSC rows')
  for k in ix:
   i=m['rowval'][k]-1;row,col=(j,i) if transpose else (i,j);rows[row].append((col,vals[k]))
 return rows,e,max(sum(abs(v) for _,v in row) for row in rows)

def residual(mat,tokens,rhs):
 global residual_count
 rows,em,nm=mat;x,ex=decode(tokens);b,eb=decode(rhs);ck(len(x)==len(b)==len(rows),'output dimensions')
 exponent=max(em+ex,eb)
 error=max(abs(sum(v*x[j] for j,v in row)*2**(exponent-em-ex)-b[i]*2**(exponent-eb)) for i,row in enumerate(rows))
 scale=max(Fraction(1),Fraction(nm*max(map(abs,x)),2**(em+ex)),Fraction(max(map(abs,b)),2**eb))
 ck(Fraction(error,2**exponent)<=Fraction(128*len(rows),2**52)*scale,'exact rational residual '+str(residual_count));residual_count+=1

def outputs(outs,f,mats):
 ck(len(outs)==24,'24 outputs')
 for k,s in enumerate(f['steps']):
  residual(mats[k][0],outs[3*k],s['a']);residual(mats[k][0],outs[3*k+1],s['dse']);residual(mats[k+1][1],outs[3*k+2],s['unit'])

def fresh_host(groups):
 matches=[];unreadable=[];bad=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   z=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip();raw=(p/'cmdline').read_bytes();argv0=raw.split(b'\0')[0].decode(errors='replace');exe=''
   try:exe=str((p/'exe').resolve(strict=True))
   except PermissionError:unreadable.append(int(p.name))
   except FileNotFoundError:pass
   if int(z[2]) in groups or int(z[3]) in groups or any(Path(x).name.lower().startswith('julia') for x in [comm,argv0,exe]):
    matches.append(dict(pid=int(p.name),pgid=int(z[2]),sid=int(z[3]),start_ticks=int(z[19]),comm=comm,command=raw.replace(b'\0',b' ').decode(errors='replace'),exe=exe))
  except (FileNotFoundError,ProcessLookupError):pass
  except PermissionError:bad.append(int(p.name))
 return dict(time=time.time(),groups=sorted(groups),matches=matches,unreadable_exe_pids=unreadable,unreadable_identity_pids=bad,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),head=git('rev-parse','HEAD'),master=git('rev-parse','master'),remote=git('ls-remote','origin','refs/heads/codex/simplex-core-architecture','refs/heads/master'))
try:
 seal=read(RUN/'sealed.json');cfg=read(RUN/'config.json');admission=read(RUN/'admission.json');launch=read(RUN/'launch-pins.json');audit=read(RUN/'audit.json');postcheck=read(Q/'postcheck.json')
 ck(admission['accepted'] is True and admission['findings']==[] and admission['scope']=='BG specialized export cost admission' and admission['phase']=='cost1-300','admission identity')
 ck(admission['pins_sha256']==sha(RUN/'sealed.json') and set(admission['sha256'])==set(seal['files'])|{str(RUN/'sealed.json')},'exact admission membership')
 bind(admission['sha256'],'admission primary');bind(admission['evidence_sha256'],'admission evidence');invcheck(seal,'seal');invcheck(launch,'launch')
 prep=read(P/'preparation-pins-final.json');review=read(P/'review-final.json')
 ck(set(prep['sha256'])==set(read(P/'required-paths-final.json')['paths']) and len(prep['sha256'])==2609,'canonical preparation exact2609')
 bind(prep['sha256'],'preparation');bind(review['sha256'],'preparation review');bind(review['evidence_sha256'],'preparation evidence')
 ck(review['accepted'] is True and review['findings']==[] and review['launch_admitted'] is False and review['pins_sha256']==sha(P/'preparation-pins-final.json'),'accepted preparation binding')
 ck(set(review['sha256'])==set(prep['sha256'])|{str(P/'preparation-pins-final.json')},'exact2610 preparation review membership')
 green=read(GR/'result-review.json');gcclose=read(GR/'outer-closure.json');gcaudit=read(GR/'audit.json');gcout=read(G/'outers/greengc300/outer-outcome.json')
 ck(green['accepted'] is True and green['findings']==[] and green['scope']=='BG specialization GC GREEN result' and gcaudit['all_passed'] is True,'accepted GREEN predecessor')
 ck(set(green['sha256'])=={str(p) for p in GR.rglob('*') if p.is_file() and p!=GR/'result-review.json'},'exact GREEN RUN membership')
 bind(green['sha256'],'GREEN RUN');bind(green['evidence_sha256'],'GREEN evidence');bind(gcclose['sha256'],'GREEN closure')
 ck(len(green['sha256'])==81 and len(green['evidence_sha256'])==24 and len(gcclose['sha256'])==8,'GREEN81+24+8')
 ck(gcout['identity']==gcclose['outer_identity'] and gcout['launched'] is True and gcout['returncode']==0 and gcout['error']=='','GREEN outcome identity')
 invcheck(read(GR/'sealed.json'),'GREEN seal')
 expected=set(prep['sha256'])|{str(P/n) for n in ['preparation-pins-final.json','review-final.json']}|set(review['evidence_sha256'])|set(green['sha256'])|set(green['evidence_sha256'])|set(gcclose['sha256'])|{str(GR/'result-review.json'),str(RUN/'host.json'),str(RUN/'config.json'),str(O/'outer-ready.json')}
 ck(set(seal['files'])==expected and len(expected)==2617,'independently derived exact seal2617')
 ck(set(seal['groups'])==set(read(P/'host-entry.json')['groups'])|set(read(GR/'posthost.json')['groups'])|set(gcclose['host']['groups']),'complete prior265groups')
 ck(set(launch['files'])==expected|{str(RUN/n) for n in ['sealed.json','admission.json','prehost.json']}|{str(O/n) for n in ['release.json','outer-invocation.json']} and launch['trees']==seal['trees'],'exact launch2622')
 ck(read(OUT/'pins.json')==launch,'output pins equal launch')
 stage=read(P/'stages.json')['cost'];stagepath=Path(stage['path']);ck(len(stage['sha256'])==87 and {str(p.relative_to(stagepath)) for p in stagepath.rglob('*') if p.is_file()}==set(stage['sha256']),'87 exact stage')
 bind({str(stagepath/n):h for n,h in stage['sha256'].items()},'stage');rt=read(P/'runtime-inputs-complete.json')
 for n,v in rt['inventory'].items():ck(v==dict(resolved=str(path(n).resolve()),sha256=sha(n)),'runtime '+n)
 for label,root in [('diagnostic',R),('production',Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl'))]:
  base=read(P/'baseline.json')[label];ck(set(git('ls-files','src','test','.github','Project.toml',cwd=root).splitlines())==set(base),'baseline membership '+label);bind({str(root/n):h for n,h in base.items()},'baseline '+label)
 sourceinv=read(C/'source-inverse.json');probeinv=read(P/'probe-inverse.json');seed=Path(probeinv['seed'])
 for name,record in sourceinv['files'].items():
  original=txt(C/(name+'.jl'));restored=original;ck(sha(C/(name+'.jl'))==record['candidate_sha256'],'candidate '+name)
  for edit in reversed(record['edits']):ck(restored.count(edit['after'])==1,'unique facade '+name);restored=restored.replace(edit['after'],edit['before'])
  for old,new in sourceinv['rename'].items():restored=restored.replace(new,old)
  ck(restored==txt(record['source']),'full original source inverse '+name)
  source=txt(P/('probe-'+name+'.jl'));ck(source==txt(stagepath/'src'/('_bgxsp_'+name+'.jl')),'probe stage '+name)
  if name=='workspace':ck(source.startswith(probeinv['header']),'probe header');source=source[len(probeinv['header']):]
  for old,new,count in reversed(probeinv['edits'][name]):ck(source.count(new)==count,'counter inverse '+name);source=source.replace(new,old)
  for old,new in probeinv['rename']:source=source.replace(new,old)
  ck(source==original,'full probe inverse '+name)
 ck(len([p for p in seed.rglob('*') if p.is_file()])==83,'83 GREEN stage files')
 for p in seed.rglob('*'):
  if p.is_file():
   actual=txt(stagepath/p.relative_to(seed));actual=actual.replace(probeinv['stage_addition'],'') if p==seed/'src/JSimplex.jl' else actual;ck(actual==txt(p),'preserved GREEN stage '+str(p.relative_to(seed)))
 for n,v in read(P/'reused-files.json').items():ck(sha(P/n)==sha(v['path'])==v['sha256'],'reused exact '+n)
 frozen=read(P/'reviewer-final-check.json');ck(frozen['all_passed'] is True and not frozen['failures'] and len(frozen['checks'])==13235 and frozen['original_reproductions']==21 and frozen['final_counter_reproductions']==23,'44 malformed rejected evidence preserved, not rerun')
 bind(read(P/'publication.json')['sha256'],'preparation publication');bind(postcheck['sha256'],'author postcheck');ck(postcheck['all_passed'] is True and all(postcheck['checks'].values()),'author8postchecks')
 command=['/bin/bash','/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh','--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--history-file=no','--project='+str(stagepath),str(P/'cost.jl'),'cost1-300',str(OUT),str(stagepath)]
 ck(cfg==dict(phase='cost1-300',mode='cost',process=1,seconds=300,expected_exit=0,stage=str(stagepath),run=str(RUN),output=str(OUT),command=command)==seal['config'],'exact actual command/config')
 ready=read(O/'outer-ready.json');outerinv=read(O/'outer-invocation.json');outcome=read(O/'outer-outcome.json');closure=read(RUN/'outer-closure.json');oid=seal['outer_identity']
 ck(ready['identity']==outerinv['identity']==outcome['identity']==closure['outer_identity']==oid and oid['pid']==oid['pgid']==oid['sid']==140961 and oid['start_ticks']==11823805,'outer exact identity')
 ck(ready['waiting_only'] is True and ready['script_sha256']==sha(P/'outer.py') and ready['expected_launcher']==str(P/'launch.py'),'ready script')
 ck(read(O/'release.json')==dict(phase='cost1-300',sealed_sha256=sha(RUN/'sealed.json'),admission_sha256=sha(RUN/'admission.json'),outer_ready_sha256=sha(O/'outer-ready.json'),one_attempt=True) and read(O/'release.json')['one_attempt'] is True,'exact one release')
 ck(outerinv==dict(identity=oid,phase='cost1-300',seal_sha256=sha(RUN/'sealed.json'),review_sha256=sha(RUN/'admission.json'),release_sha256=sha(O/'release.json'),launcher_sha256=sha(P/'launch.py'),method='runpy.run_path launch.py as __main__ in this outer process'),'outer invocation exact')
 ck(outcome['launched'] is True and type(outcome['returncode']) is int and outcome['returncode']==0 and outcome['error']=='','outer successful return')
 closurefiles={str(O/n) for n in ['outer-ready.json','release.json','outer-invocation.json','outer-outcome.json']}|{str(RUN/n) for n in ['sealed.json','admission.json','posthost.json','audit.json']}
 ck(set(closure['sha256'])==closurefiles and closure['all_passed'] is True,'external closure exact8');bind(closure['sha256'],'external closure')
 bind(audit['sha256'],'saved once-only audit');ck(set(audit['sha256'])=={str(p) for p in RUN.rglob('*') if p.is_file()}-{str(RUN/'audit.json'),str(RUN/'outer-closure.json')},'audit exact preclosure RUN membership')
 proc=read(OUT/'process.json');current=read(OUT/'current.json');inv=read(RUN/'invocation.json');sup=inv['supervisor'];resources=[json.loads(s) for s in txt(OUT/'resources.jsonl').splitlines()];hosts=[read(RUN/n) for n in ['host.json','prehost.json','posthost.json']]
 schema.runtime(proc,current,inv,resources,hosts,300);ck(True,'strict complete runtime schemas')
 ck(schema.success(proc,sup) and proc['pins_unchanged'] is True,'success flags no timeout/intervention')
 ck(current['runner']==proc['runner']==sup['guard_identity'] and current['child']==proc['child'],'runner child identities linked')
 ck(proc['runner']['pid']==proc['runner']['pgid']==proc['runner']['sid']==141585 and proc['runner']['start_ticks']==11858135 and proc['child']['pid']==proc['child']['pgid']==proc['child']['sid']==141586 and proc['child']['start_ticks']==11858210,'exact runner child starts')
 ck(proc['command']==current['command']==inv['command']==command and proc['cwd']==current['cwd']==str(R),'runtime exact command cwd')
 ck(proc['pins_sha256']==current['pins_sha256']==inv['pins_sha256']==sha(RUN/'launch-pins.json'),'runtime pin identity')
 guardcmd=[inv['python'],'-B',str(P/'guard.py'),'run',str(RUN/'launch-pins.json'),str(OUT),'--seconds','292','--deadline',str(inv['monotonic_start']+292),'--expected-exit','0','--',*command]
 ck(inv['guard_command']==guardcmd and Path(inv['python']).resolve()==Path(sys.executable).resolve(),'exact 292 guard command')
 reservation=read(RUN/'reservation.json');ck(reservation==dict(one_attempt=True,phase='cost1-300',command=command,pins_sha256=sha(RUN/'launch-pins.json'),review_sha256=sha(RUN/'admission.json'),max_seconds=300) and reservation['one_attempt'] is True,'one exact reservation')
 ck(inv['reservation_sha256']==sha(RUN/'reservation.json') and inv['review_sha256']==sha(RUN/'admission.json'),'reservation review linkage')
 ck(all(s['available_kib']>=6*1024**2 and s['swap_used_kib']<=1024**2 for s in resources+[proc['terminal_memory']]),'RAM/swap all samples and terminal')
 ck(all(h[k]==seal[k] for h in hosts for k in ['head','master','boot_id']) and all(proc[role]['boot_id']==seal['boot_id'] for role in ['runner','child']),'host refs boot')
 ck(set(seal['groups'])<=set(hosts[1]['groups'])<=set(hosts[2]['groups']),'runtime groups coverage')
 groups=set(seal['groups'])|set(hosts[2]['groups'])|{oid[k] for k in ['pgid','sid']}|{proc[r][k] for r in ['runner','child'] for k in ['pgid','sid']}
 ck(groups==set(closure['host']['groups']) and len(groups)==268 and closure['host']['matches']==[] and closure['host']['unreadable_identity_pids']==[],'external full268group AND session closure')
 ck(closure['host']['time']>proc['ended'] and all(closure['host'][k]==seal[k] for k in ['head','master','boot_id']),'external post-return closure timing refs')
 log=txt(OUT/'run.log')+'\n'+txt(RUN/'launcher.log');ck('BEGIN BG export workspace cost cost1-300' in log and not re.search(r'warning|world[ -]age|FATAL COST:|ERROR:|Traceback|TEST FAILURE:',log,re.I),'run log clean')
 ck('GC.gc' not in txt(P/'cost.jl') and 'GC.gc' not in txt(P/'probe.jl'),'Task3 no explicit GC')
 ck('resource.RLIMIT_AS, (8 * 1024**3, 8 * 1024**3)' in txt(P/'guard.py'),'VM8GiB source guard')
 ck({p.name for p in P.joinpath('runs').iterdir()}=={'cost1-300'} and {p.name for p in P.joinpath('outers').iterdir()}=={'cost1-300'},'one phase only')
 expectedoutputs={'pins.json','current.json','process.json','resources.jsonl','run.log','raw.toml','controls.toml'}|{f'{prefix}-{i}.toml' for i in range(1,9) for prefix in ['started','preflight','probe','cell']}|{f'window-{i}-{j}.toml' for i in range(1,9) for j in range(1,21)}
 ck({p.name for p in OUT.iterdir()}==expectedoutputs and len(expectedoutputs)==199 and all(p.is_file() and not p.is_symlink() for p in OUT.iterdir()),'199 exact output files')
 fixtures=read(P/'inputs.json')['fixtures'];ck(toml(P/'inputs.toml')==read(P/'inputs.json'),'exact JSON TOML input bits')
 ck([f['name'] for f in fixtures]==['sparse32','dense32','sparse96','dense96'],'fixed fixtures')
 controls=toml(OUT/'controls.toml');predicates.control_ok(controls);ck(True,'all synthetic importer orientation and transition controls')
 loaded=read(P/'loaded-paths.json');loaded['JSimplex']=str(stagepath/'src/JSimplex.jl');raw=toml(OUT/'raw.toml');schema.raw(raw);ck(raw==dict(phase='cost1-300',loaded=loaded,completed=True,fatal='',cells=8,windows=160,threads=1,blas_threads=1),'exact loaded paths complete raw')
 cells=[];rows_all=[];gc_positive=[];totals=dict(constructions=0,refactors=0,updates=0,ftran=0,btran=0,copies=0);probe_totals={};idx=0
 for f in fixtures:
  mats=[(matrix(m),matrix(m,True)) for m in f['matrices']]
  for backend in ['native','markowitz']:
   idx+=1;identity=dict(fixture=f['name'],manager='BG',backend=backend,policy='threshold_one' if backend=='native' else 'default')
   ck(toml(OUT/f'started-{idx}.toml')==identity,'started identity');end=toml(OUT/f'cell-{idx}.toml');schema.cell(end);ck(end==dict(identity,windows=20),'ended cell identity')
   pre=toml(OUT/f'preflight-{idx}.toml');predicates.preflight_ok(pre,backend,identity['policy']);ck(True,'actual preflight policy controls')
   probe=toml(OUT/f'probe-{idx}.toml');schema.probe(probe);predicates.counters(probe['counts']);ck(probe['inputs_unchanged'] is True,'probe inputs unchanged')
   for k,n in dict(constructions=3,refactors=6,updates=24,ftran=48,btran=24,copies=0).items():ck(probe[k]==n,'probe API '+k);totals[k]+=probe[k]
   checkpoints=[(0,False)]+[(k,b) for k in range(1,9) for b in ([False,True] if k in [4,8] else [False])];ck(len(probe['states'])==11,'11 checkpoints');previous=None
   for state,(step,refactored) in zip(probe['states'],checkpoints):
    ck((state['step'],state['refactored'],state['equal'])==(step,refactored,True),'exact probe checkpoint')
    ck(len(state['graphs'])==3 and all(type(x) is int and x>0 for x in state['graphs']),'graph integers');predicates.cache(state['cache']);predicates.cache(state['probe_cache']);predicates.counters(state['counts'])
    ck(state['cache']==state['probe_cache'],'cache inverse')
    if previous:ck(all(state['counts'][k]>=previous['counts'][k] for k in state['counts']) and state['coexistence_graph_peak']>=previous['coexistence_graph_peak'],'monotone counters graph peak')
    previous=state
   ck(probe['counts']==previous['counts'] and probe['coexistence_graph_peak']==previous['coexistence_graph_peak'],'strict final counters equality')
   pc=probe['counts'];ck(pc['factorizations']==pc['extractions']==3 and pc['refactor_entries']==2 and pc['orientation_solves']<=3 and (backend!='markowitz' or pc['orientation_solves']==0),'probe entry counters')
   for k,v in pc.items():probe_totals[k]=probe_totals.get(k,0)+v
   ck(probe['cache_charge_sum']==sum(s['cache']['charge'] for s in probe['states']) and probe['cache_charge_peak']==max(s['cache']['charge'] for s in probe['states']),'cache charge aggregate')
   ck(len(probe['outputs'])==3 and probe['outputs'][0]==probe['outputs'][1]==probe['outputs'][2],'three exact bitwise probe sides')
   for outs in probe['outputs']:outputs(outs,f,mats)
   memory=all(10*s['graphs'][i]<=11*s['graphs'][0] for s in probe['states'] for i in [1,2]);rows=[]
   for w in range(1,21):
    row=toml(OUT/f'window-{idx}-{w}.toml');pair=(w+1)//2;order=1+(w-1)%2;side=(['reference','candidate'] if pair%2 else ['candidate','reference'])[order-1]
    ck(set(row)==set('pair order side measured policy correct inputs_unchanged modes seconds bytes events gc_seconds compile_seconds recompile_seconds retained_bytes nested_seconds outputs'.split()),'exact window schema')
    ck(type(row['pair']) is int and type(row['order']) is int and type(row['measured']) is bool and row['pair']==pair and row['order']==order and row['side']==side and row['measured']==(pair>3),'all warm/measured order')
    ck(row['policy']==identity['policy'] and row['correct'] is True and row['inputs_unchanged'] is True and row['modes']==pre['modes'],'policy modes inputs correctness')
    ck(all(type(row[k]) in [float,int] and math.isfinite(row[k]) and row[k]>=0 for k in ['seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds','retained_bytes']) and row['seconds']>0 and all(type(row[k]) is int for k in ['bytes','events','retained_bytes']),'strict metrics')
    ck(len(row['nested_seconds'])==6 and all(type(x) in [int,float] and math.isfinite(x) and x>=0 for x in row['nested_seconds']) and sum(row['nested_seconds'])<=row['seconds']+1e-9,'six nested subsets')
    ck(pair<=3 or row['compile_seconds']==row['recompile_seconds']==0,'measured compile zero')
    outputs(row['outputs'],f,mats);rows.append(row);rows_all.append(row)
    if pair>3 and row['gc_seconds']>0:gc_positive.append(dict(cell=idx,window=w,pair=pair,side=side,seconds=row['seconds'],gc_seconds=row['gc_seconds'],bytes=row['bytes'],events=row['events'],nested_seconds=row['nested_seconds']))
   for pair in range(1,11):
    a,b=rows[2*pair-2:2*pair];ck(a['outputs']==b['outputs'] and a['modes']==b['modes'],'all paired bitwise outputs modes')
   pairs=[{r['side']:r for r in rows if r['pair']==pair} for pair in range(4,11)];st={}
   for metric in ['seconds','bytes','events','retained_bytes','gc_seconds','compile_seconds','recompile_seconds']:
    a=[p['reference'][metric] for p in pairs];b=[p['candidate'][metric] for p in pairs];st[metric]=dict(reference=stats(a),candidate=stats(b))
    if all(a):st[metric]['paired_ratio']=stats([y/x for x,y in zip(a,b)])
   st['nested_seconds']=[{side:stats([p[side]['nested_seconds'][i] for p in pairs]) for side in ['reference','candidate']} for i in range(6)]
   st['faster_pairs']=sum(p['candidate']['seconds']<p['reference']['seconds'] for p in pairs);st['time_median_gate']=st['seconds']['paired_ratio']['median']<=.95;st['allocation_gate']=all(st[k]['candidate']['median']<=st[k]['reference']['median'] for k in ['bytes','events']);st['probe_memory_gate']=memory
   st['memory_gate']=memory and all(10*{r['side']:r for r in rows if r['pair']==pair}['candidate']['retained_bytes']<=11*{r['side']:r for r in rows if r['pair']==pair}['reference']['retained_bytes'] for pair in range(1,11))
   result=dict(identity,statistics=st,probe_counts=pc,cache_charge_sum=probe['cache_charge_sum'],cache_charge_peak=probe['cache_charge_peak'],coexistence_graph_peak=probe['coexistence_graph_peak']);ck(result==audit['cells'][idx-1],'all independently recomputed stats exact cell'+str(idx));cells.append(result)
   reportcell=postcheck['cells'][idx-1];ck(reportcell['time_ratio']==st['seconds']['paired_ratio']['median'] and reportcell['bytes']==[st['bytes'][s]['median'] for s in ['reference','candidate']] and reportcell['events']==[st['events'][s]['median'] for s in ['reference','candidate']] and reportcell['retained_bytes']==[st['retained_bytes'][s]['median'] for s in ['reference','candidate']],'author summary agreement')
 for k,v in dict(constructions=160+16+4,refactors=320+32+12,updates=1280,ftran=2560,btran=1280,copies=4).items():totals[k]+=v
 ck(totals==dict(constructions=204,refactors=412,updates=1472,ftran=2944,btran=1472,copies=4),'complete source/API entry schedule')
 ck(residual_count==4416 and len(rows_all)==160 and sum(r['measured'] for r in rows_all)==112,'all4416 outputs160windows112measured')
 ck(audit['counts']==dict(cells=8,windows=160,window_outputs=3840,probe_outputs=576) and audit['all_passed'] is True and audit['pure_timeout'] is False and audit['error']=='' and audit['selection']==[] and audit['manager_backend']==[],'saved auditor result matches independent acceptance')
 viable=all(all(z['statistics'][k] for k in ['time_median_gate','allocation_gate','memory_gate','probe_memory_gate']) and z['statistics']['faster_pairs']>=3 for z in cells)
 ck(viable is False and postcheck['first_process_viable'] is False and sum(z['statistics']['time_median_gate'] for z in cells)==2 and all(z['statistics']['allocation_gate'] and z['statistics']['memory_gate'] for z in cells),'separate cost rejection2of8time8of8allocation/memory')
 host=fresh_host(groups);ck(not host['matches'] and not host['unreadable_identity_pids'],'fresh all268groups AND sessions absent/noJulia')
 ck(all(host[k]==seal[k] for k in ['head','master','boot_id']) and host['head']=='e149671cd2c9560ae2a91b80614d36799b845240' and host['master']=='26e2291745999f485a74f643298ca997d65c7205','fresh exact HEAD master boot')
 ck(host['head']+'\trefs/heads/codex/simplex-core-architecture' in host['remote'] and host['master']+'\trefs/heads/master' in host['remote'],'fresh remote refs')
 ck(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'clean tracked worktree/index')
 ck(git('rev-parse','HEAD',cwd=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl'))==host['master'],'production HEAD unchanged')
 result=dict(accepted=True,findings=[],scope='BG specialized export cost result',phase='cost1-300',diagnostic_review_accepted=True,first_process_viable=False,qualification_accepted=False,checks=checks,count=len(checks),binding_counts=hash_counts,host=host,cells=cells,counts=audit['counts'],residual_checks=residual_count,api_totals=totals,probe_counter_totals=probe_totals,gc_positive_measured=gc_positive,warm_compile_seconds=sum(r['compile_seconds'] for r in rows_all if not r['measured']),warm_recompile_seconds=sum(r['recompile_seconds'] for r in rows_all if not r['measured']),guard_elapsed=proc['elapsed_including_launch'],supervisor_elapsed=sup['elapsed_seconds'],outer_elapsed=outcome['elapsed_with_checks_seconds'],resource_samples=len(resources),min_available_kib=min(r['available_kib'] for r in resources),max_swap_kib=max(r['swap_used_kib'] for r in resources),child_maxrss_kib=proc['child_maxrss_kib'],used_files=sorted(used),executed_old_checkers=False,rerun_malformed_tests=False,executed_numerics=False)
except BaseException as e:
 result=dict(accepted=False,findings=[repr(e)],checks=checks,count=len(checks),used_files=sorted(used))
with (Q/'result-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['checks','used_files','cells','host']},indent=2))
if not result['accepted']:sys.exit(1)
