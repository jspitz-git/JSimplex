"""Independent saved-result verification; never imports or executes historical tooling or Julia."""
from pathlib import Path
import json,tomllib,hashlib,struct,math,statistics,os,time,subprocess
from fractions import Fraction
Q=Path(__file__).resolve().parent;E=Q.parent/'DIRECT-BG-BLOCK-COST-PREPARATION';R=E.parents[3];U=E/'runs/cost1-300';O=U/'output';checks={};hashes={};residuals=0

def check(v,n):
 checks[n]=bool(v)
 if not v:raise AssertionError(n)
def rd(p):return json.loads(Path(p).read_text())
def tom(n):return tomllib.loads((O/n).read_text())
def sha(p):
 p=Path(p);s=p.stat();key=(str(p),s.st_size,s.st_mtime_ns)
 if key not in hashes:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):h.update(b)
  hashes[key]=h.hexdigest()
 return hashes[key]
def binding(m,label):check(all(sha(n)==h for n,h in m.items()),label)
def inventory(j,label):
 expected=set(j['files'])
 for n in j['trees']:
  root=Path(n);check(root.is_dir() and not root.is_symlink(),label+'_tree_'+root.name)
  for p in root.rglob('*'):
   if p.is_symlink():check(p.is_file() and p.exists(),label+'_symlink_'+str(p))
   if p.is_file():expected.add(str(p))
 check(expected==set(j['inventory']),label+'_membership');check(all(str(Path(n).resolve(strict=True))==v['resolved'] and sha(n)==v['sha256'] for n,v in j['inventory'].items()),label+'_hashes_paths')
def decode(t):
 assert isinstance(t,str) and len(t)==16 and all(c in '0123456789abcdef' for c in t)
 v=struct.unpack('>d',bytes.fromhex(t))[0];assert math.isfinite(v);return v

def ints(tokens):
 ratios=[decode(t).as_integer_ratio() for t in tokens];e=max((d.bit_length()-1 for _,d in ratios),default=0)
 return [a*(1<<(e-(d.bit_length()-1))) for a,d in ratios],e

def matrix(m,tr):
 v,e=ints(m['nzval']);rows=[[] for _ in range(m['n'])]
 for c in range(m['n']):
  for k in range(m['colptr'][c]-1,m['colptr'][c+1]-1):
   r=m['rowval'][k]-1
   if tr:rows[c].append((r,v[k]))
   else:rows[r].append((c,v[k]))
 return rows,e,max((sum(abs(x) for _,x in row) for row in rows),default=0)

def residual(m,xt,bt):
 global residuals
 rows,em,nm=m;x,ex=ints(xt);b,eb=ints(bt);assert len(x)==len(b)==len(rows)
 e=max(em+ex,eb);err=max((abs(sum(a*x[c] for c,a in row)*(1<<(e-em-ex))-b[r]*(1<<(e-eb))) for r,row in enumerate(rows)),default=0)
 bound=Fraction(128*len(rows),1<<52)*max(Fraction(1),Fraction(nm*max(map(abs,x),default=0),1<<(em+ex)),Fraction(max(map(abs,b),default=0),1<<eb))
 assert Fraction(err,1<<e)<=bound;residuals+=1

def outputs(out,f,mats):
 assert len(out)==24
 for k,s in enumerate(f['steps']):
  residual(mats[k][0],out[3*k],s['a']);residual(mats[k][0],out[3*k+1],s['dse']);residual(mats[k+1][1],out[3*k+2],s['unit'])

def counter(c):
 assert set(c)==set(rd(E/'probe-inverse.json')['counts']) and all(type(v) is int and 0<=v<2**63 for v in c.values())
 assert c['tuple_writes']==c['row_handle_repairs'] and c['split_stage_reads']==32*c['splits'] and c['split_stage_writes']==c['split_final_writes']==33*c['splits'] and c['merge_stage_reads']==c['merge_stage_writes']==c['merge_tuple_moves']

def storage(s,n):
 C,Rr,K,S,D=(s[k] for k in ('C','R','K','S','D'));assert s['live']<=C and s['live']+s['gap_reserve']==Rr and s['live_blocks']<=s['used']<=K and S<=D and K*32<=2**31-1
 assert s['core_payload']==16*C+4*Rr+28*K+32*n+656 and s['outer_pointer_payload']==8*n+24*D
 top='values row_ids row_backs slab start capacity count column prev next row_order row_position column_order column_position column_head column_tail rows gap_first gap_length bins scratch_value scratch_row scratch_back'.split();expected=top+[f'{key}[{i}]' for i in range(1,S+1) for key in ('values','row_ids','row_backs')]+[f'rows[{i}]' for i in range(1,n+1)]
 assert [a['name'] for a in s['arrays']]==expected
 for a in s['arrays']:assert all(type(a[k]) is int and 0<=a[k]<2**63 for k in a if k!='name') and a['backing_length']>=a['length'] and a['backing_bytes']==a['backing_length']*a['element_bytes'] and a['graph_bytes']>=a['backing_bytes']
 arrays={a['name']:a for a in s['arrays']};assert sum(arrays[f'values[{i}]']['length'] for i in range(1,S+1))==C and sum(arrays[f'rows[{i}]']['length'] for i in range(1,n+1))==Rr

s=rd(U/'sealed.json');a=rd(U/'admission.json');lp=rd(U/'launch-pins.json');cfg=rd(U/'config.json');audit=rd(U/'audit.json')
check(a['accepted'] is True and a['findings']==[] and a['scope']=='block BG matched cost admission' and a['phase']=='cost1-300' and a['pins_sha256']==sha(U/'sealed.json') and set(a['sha256'])==set(s['files'])|{str(U/'sealed.json')},'exact_admission');binding(a['sha256'],'admission_files');binding(a['evidence_sha256'],'frozen_admission_evidence');inventory(s,'sealed');inventory(lp,'launch');check(set(lp['files'])==set(s['files'])|{str(U/n) for n in ('sealed.json','admission.json','prehost.json')} and lp['trees']==s['trees'],'launch_exact');check(rd(O/'pins.json')==lp,'output_pins');check(s['config']==cfg and cfg==rd(E/'commands.json')['cost1-300'],'config')
base={'pins.json','current.json','process.json','resources.jsonl','run.log','raw.toml','growth.toml'};expected=base|{f'{p}-{c}.toml' for c in range(1,9) for p in ('started','preflight','probe','cell')}|{f'window-{c}-{w}.toml' for c in range(1,9) for w in range(1,21)};check({p.name for p in O.iterdir()}==expected and all(p.is_file() and not p.is_symlink() for p in O.iterdir()),'exact199outputs')
check(audit['all_passed'] is True and audit['pure_timeout'] is False and audit['counts']=={'cells':8,'windows':160,'exact_residuals':4416},'original_integrity_audit');binding(audit['sha256'],'audit_preserved_inputs');check(set(audit['sha256'])=={str(p) for p in U.rglob('*') if p.is_file() and p.name!='audit.json'},'audit_exact_input_membership')
raw=tom('raw.toml');loaded=dict(rd(E/'loaded-paths.json'),JSimplex=str(Path(cfg['stage'])/'src/JSimplex.jl'));check(raw==dict(phase='cost1-300',loaded=loaded,completed=True,fatal='',cells=8,windows=160,threads=1,blas_threads=1),'raw_complete_loaded5')
fixtures=rd(E/'inputs.json')['fixtures'];cells=[];all_rows=[]
for fi,f in enumerate(fixtures):
 mats=[(matrix(m,False),matrix(m,True)) for m in f['matrices']]
 for bi,backend in enumerate(('native','markowitz')):
  c=fi*2+bi+1;identity=dict(fixture=f['name'],manager='BG',backend=backend,policy='threshold_one' if bi==0 else 'default');check(tom(f'started-{c}.toml')==identity and tom(f'cell-{c}.toml')==dict(identity,windows=20),f'cell{c}_identity')
  pre=tom(f'preflight-{c}.toml');assert pre['inputs_unchanged'] is True and [pre[k] for k in ('constructions','refactors','explicit_solves')]==[2,4,0] and len(pre['reference'])==len(pre['candidate'])==3
  for z in pre['reference']+pre['candidate']:
   assert z['kind']==backend and z['policy']==identity['policy']
   if bi==0:assert len(z['control'])==20 and z['control']==z['expected_control'] and decode(z['control'][3])==1 and decode(z['control'][7])==0 and math.isfinite(decode(z['strategy']))
   else:assert z['control']==z['expected_control']==[] and z['strategy']==''
  pr=tom(f'probe-{c}.toml');assert pr['inputs_unchanged'] is True and [pr[k] for k in ('constructions','refactors','updates','ftran','btran','copies')]==[3,6,24,48,24,0] and len(pr['outputs'])==3 and pr['outputs'][0]==pr['outputs'][1]==pr['outputs'][2]
  for out in pr['outputs']:outputs(out,f,mats)
  sequence=[(0,False)]+[(k,r) for k in range(1,9) for r in ([False,True] if k in (4,8) else [False])];assert len(pr['states'])==11;prev=None;cp=[]
  for state,(k,ref) in zip(pr['states'],sequence):
   assert state['step']==k and state['refactored'] is ref and state['equal'] is True and state['history_length']==(0 if ref or k==0 else (k-1)%4+1);storage(state['storage'],f['n']);counter(state['counts']);assert prev is None or all(state['counts'][key]>=v for key,v in prev.items());prev=state['counts'];assert len(state['graphs'])==3 and state['storage']['graph_bytes']<=state['graphs'][1]
   cp.append({'step':k,'refactored':ref,'reference_bytes':state['graphs'][0],'candidate_bytes':state['graphs'][1],'ratio':state['graphs'][1]/state['graphs'][0],'pass':10*state['graphs'][1]<=11*state['graphs'][0],'C':state['storage']['C'],'R':state['storage']['R'],'K':state['storage']['K'],'S':state['storage']['S'],'live':state['storage']['live']})
  assert pr['counts']==prev
  rows=[tom(f'window-{c}-{w}.toml') for w in range(1,21)];all_rows+=rows
  for w,row in enumerate(rows,1):
   pair=(w+1)//2;order=1+(w-1)%2;side=('reference' if (pair%2==1)==(order==1) else 'candidate');assert row['pair']==pair and row['order']==order and row['side']==side and row['measured'] is (pair>3) and row['policy']==identity['policy'] and row['correct'] is True and row['inputs_unchanged'] is True and len(row['modes'])==3 and all(m in ('normalized','direct','fallback') for m in row['modes']);assert all(type(row[k]) in (int,float) and math.isfinite(row[k]) and row[k]>=0 for k in ('seconds','bytes','events','retained_bytes','gc_seconds','compile_seconds','recompile_seconds'));assert row['seconds']>0 and len(row['nested_seconds'])==6 and all(v>=0 and math.isfinite(v) for v in row['nested_seconds']) and sum(row['nested_seconds'])<=row['seconds']+1e-9;assert pair<=3 or row['compile_seconds']==row['recompile_seconds']==0;outputs(row['outputs'],f,mats)
  pairs=[]
  for i in range(0,20,2):
   assert rows[i]['outputs']==rows[i+1]['outputs'] and rows[i]['modes']==rows[i+1]['modes']
   if i>=6:pairs.append({r['side']:r for r in rows[i:i+2]})
  stats={}
  for metric in ('seconds','bytes','events','retained_bytes','gc_seconds'):
   x=[p['reference'][metric] for p in pairs];y=[p['candidate'][metric] for p in pairs];rat=[b/a for a,b in zip(x,y)] if all(x) else None;stats[metric]={'reference_median':statistics.median(x),'candidate_median':statistics.median(y),'reference_values':x,'candidate_values':y,'paired_ratios':rat,'paired_ratio_median':statistics.median(rat) if rat else None}
  faster=sum(p['candidate']['seconds']<p['reference']['seconds'] for p in pairs);gates={'time':stats['seconds']['paired_ratio_median']<=.95,'allocation':all(stats[m]['candidate_median']<=stats[m]['reference_median'] for m in ('bytes','events')),'final_graph':all(10*p['candidate']['retained_bytes']<=11*p['reference']['retained_bytes'] for p in pairs),'checkpoint_graph':all(v['pass'] for v in cp),'faster_pairs':faster>=3}
  ast=audit['cells'][c-1]['statistics'];assert ast['time_median_gate']==gates['time'] and ast['allocation_gate']==gates['allocation'] and ast['probe_memory_gate']==gates['checkpoint_graph'] and ast['memory_gate']==(gates['final_graph'] and gates['checkpoint_graph']) and ast['faster_pairs']==faster
  for metric in ('seconds','bytes','events','retained_bytes','gc_seconds'):assert ast[metric]['reference']['median']==stats[metric]['reference_median'] and ast[metric]['candidate']['median']==stats[metric]['candidate_median']
  cells.append(dict(identity,statistics=stats,faster_pairs=faster,gates=gates,all_cost_gates=all(gates.values()),checkpoints=cp,probe_counts=pr['counts'],nested_medians=[{'reference':statistics.median(p['reference']['nested_seconds'][k] for p in pairs),'candidate':statistics.median(p['candidate']['nested_seconds'][k] for p in pairs)} for k in range(6)]));check(True,f'cell{c}_numerical_schema_policy_memory_statistics')
check(residuals==4416,'all4416_independent_exact_residuals');check(not all(c['all_cost_gates'] for c in cells),'first_cost_rejected_stop')
growth=tom('growth.toml');assert growth['complete'] is True and [growth[k] for k in ('n','insertions','factorizations','solves')]==[64,64,0,0] and len(growth['states'])==64;cap=0;copied=0;ng=0
for i,z in enumerate(growth['states'],1):
 if i>cap:copied+=4*(i-1);cap=i+min(8,max(1,cap//8));ng+=1
 assert z['insertions']==i and z['row_capacity']==cap and z['counts']['row_growths']==ng and z['counts']['row_copied_bytes']==copied;counter(z['counts'])
storage(growth['storage'],64);assert growth['counts']==growth['states'][-1]['counts'];check(True,'growth64_capacity_counters')
inv=rd(U/'invocation.json');sup=inv['supervisor'];proc=rd(O/'process.json');cur=rd(O/'current.json');pre=rd(U/'prehost.json');post=rd(U/'posthost.json');host=rd(U/'host.json');res=rd(U/'reservation.json')
check(inv['command']==proc['command']==cur['command']==cfg['command'] and inv['pins_sha256']==proc['pins_sha256']==cur['pins_sha256']==sha(U/'launch-pins.json') and inv['review_sha256']==sha(U/'admission.json') and inv['reservation_sha256']==sha(U/'reservation.json'),'invocation_bindings')
check(res==dict(one_attempt=True,phase='cost1-300',command=cfg['command'],pins_sha256=sha(U/'launch-pins.json'),review_sha256=sha(U/'admission.json'),max_seconds=300),'exclusive_reservation')
check(proc['returncode']==sup['returncode']==0 and proc['reason']=='exit0' and proc['pins_unchanged'] is True and sup['accepted'] is True and all(sup[k] is False for k in ('soft_timeout','hard_timeout','child_kill','guard_term','guard_kill')) and 'cleanup_error' not in sup and 0<=sup['elapsed_seconds']<=inv['elapsed_seconds']<=300,'exit_limits_no_cleanup')
check(cur['runner']==proc['runner']==sup['guard_identity'] and cur['child']==proc['child'],'identity_linkage');check(all(not h['matches'] and all(h[k]==s[k] for k in ('head','master','boot_id')) for h in (host,pre,post)) and set(s['groups'])<=set(pre['groups'])<=set(post['groups']) and all(proc[role][k] in post['groups'] for role in ('runner','child') for k in ('pgid','sid')),'saved_host_identity_closure')
expectedguard=['/usr/bin/python3','-B',str(E/'guard.py'),'run',str(U/'launch-pins.json'),str(O),'--seconds','292','--deadline',str(inv['monotonic_start']+292),'--expected-exit','0','--',*cfg['command']];check(inv['guard_command']==expectedguard,'guard_absolute_deadline')
log=(O/'run.log').read_text()+(U/'launcher.log').read_text();check('BEGIN matched policy cost cost1-300' in log and not any(z in log for z in ('FATAL COST:','ERROR:','Traceback','WARNING:','Warning:','world age')),'no_warning_error')
resources=[json.loads(x) for x in (O/'resources.jsonl').read_text().splitlines()];check(bool(resources) and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in resources+[proc['terminal_memory']]),'all_resource_samples');check(proc['child_maxrss_kib']>0,'rss_positive')
groups=set(post['groups']);matches=[];unreadable=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  fields=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip();exe=''
  try:exe=str((p/'exe').resolve(strict=True))
  except PermissionError:unreadable.append(int(p.name))
  except FileNotFoundError:pass
  if int(fields[2]) in groups or int(fields[3]) in groups or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):matches.append({'pid':int(p.name),'pgid':int(fields[2]),'sid':int(fields[3]),'comm':comm,'exe':exe,'start_ticks':int(fields[19])})
 except (FileNotFoundError,ProcessLookupError):pass
check(len(groups)==240 and not matches,'fresh240_group_session_noJulia');check(Path('/proc/sys/kernel/random/boot_id').read_text().strip()==s['boot_id'],'same_boot');git=lambda *x:subprocess.check_output(['/usr/bin/git',*x],cwd=R,text=True).strip();check(git('rev-parse','HEAD')==s['head'] and git('rev-parse','master')==s['master'] and not git('diff','--name-only') and not git('diff','--cached','--name-only'),'fresh_refs_tracked_clean')
runfiles={str(p):sha(p) for p in U.rglob('*') if p.is_file()};out={'all_passed':True,'integrity_accepted':True,'performance_accepted':False,'next_process_permitted':False,'checks':checks,'cells':cells,'exact_residuals':residuals,'windows':160,'growth':{'growths':ng,'copied_bytes':copied,'final_capacity':cap,'counts':growth['counts']},'execution':{'elapsed_seconds':inv['elapsed_seconds'],'child_maxrss_kib':proc['child_maxrss_kib'],'resource_samples':len(resources),'min_available_kib':min(x['available_kib'] for x in resources),'max_swap_used_kib':max(x['swap_used_kib'] for x in resources),'warm_compile_seconds':sum(x['compile_seconds'] for x in all_rows if not x['measured']),'measured_compile_seconds':sum(x['compile_seconds'] for x in all_rows if x['measured'])},'host':{'time':time.time(),'groups':sorted(groups),'matches':matches,'unreadable_exe_pids':unreadable},'sha256':runfiles,'checker_sha256':sha(__file__),'scope':'Independent saved first-result verification; no old tooling or Julia execution'}
with (Q/'result-check.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({'all_passed':True,'checks':len(checks),'residuals':residuals,'cells':[dict(fixture=c['fixture'],backend=c['backend'],time_ratio=c['statistics']['seconds']['paired_ratio_median'],bytes=[c['statistics']['bytes'][k] for k in ('reference_median','candidate_median')],events=[c['statistics']['events'][k] for k in ('reference_median','candidate_median')],faster=c['faster_pairs'],gates=c['gates']) for c in cells],'execution':out['execution']}))
