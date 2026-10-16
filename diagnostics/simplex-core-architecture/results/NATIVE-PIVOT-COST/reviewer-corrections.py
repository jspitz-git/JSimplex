"""Independent offline result checks. No imports or execution of historical tools.
Reads saved JSON/TOML, source, hashes and /proc only. Writes exclusive new evidence.
"""
from pathlib import Path
from fractions import Fraction
import json, tomllib, hashlib, struct, math, statistics, os, time, traceback
D=Path(__file__).resolve().parent;R=D.parents[3];Q=D.parent/'NATIVE-PIVOT-COST-PREPARATION';RUN=Q/'runs/cost'
checks={};details={};failures=[]
def path(n):
 p=Path(n);return p if p.is_absolute() else R/p
def sha(n):
 h=hashlib.sha256()
 with path(n).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(path(p).read_text())
def tt(p):return tomllib.loads(path(p).read_text())
def check(name,ok):
 checks[name]=bool(ok)
 if not ok:failures.append(name)
def bind(label,z,field='sha256',count=None):
 v=z[field];bad=[n for n,h in v.items() if sha(n)!=h];check(label,not bad and (count is None or len(v)==count));details[label]={'count':len(v),'mismatches':bad}
def num(s):
 assert isinstance(s,str) and len(s)==16 and all(c in '0123456789abcdef' for c in s)
 x=struct.unpack('>d',bytes.fromhex(s))[0];assert math.isfinite(x);return x
def rat(s):
 # Decode the IEEE-754 bit fields directly, independently of the saved oracle.
 z=int(s,16);sgn=-1 if z>>63 else 1;e=(z>>52)&2047;m=z&((1<<52)-1)
 assert len(s)==16 and e!=2047
 if e:m+=1<<52;power=e-1023-52
 else:power=-1074
 return Fraction(sgn*m*(1<<max(power,0)),1<<max(-power,0))
def token(x):return struct.pack('>d',x).hex()
def stats(v):
 m=statistics.median(v);return dict(median=m,minimum=min(v),maximum=max(v),mad=statistics.median(abs(x-m) for x in v))
def save(n,z):
 with (D/n).open('x') as f:json.dump(z,f,indent=2);f.write('\n')
def main():
 a=rd(RUN/'audit.json');seal=rd(RUN/'sealed.json');launch=rd(RUN/'launch-pins.json');ad=rd(RUN/'admission.json');summary=rd(D/'summary.json');post=rd(D/'postcheck.json')
 check('audit_outcome',a['phase']=='cost' and a['all_passed'] is True and a['error']=='')
 bind('audit156',a,count=156);bind('admission1002',ad,count=1002);bind('admission_supplement7',ad,'evidence_sha256',7)
 for label,z,c in [('seal1001',seal,1001),('launch1004',launch,1004)]:
  bad=[n for n,v in z['inventory'].items() if sha(n)!=v['sha256'] or str(path(n).resolve())!=v['resolved']]
  check(label,len(z['files'])==len(z['inventory'])==c and set(z['files'])==set(z['inventory']) and len(set(z['files']))==c and not bad);details[label]={'count':c,'mismatches':bad}
 check('seal_admission_membership',set(ad['sha256'])==set(seal['files'])|{str(RUN/'sealed.json')} and ad['pins_sha256']==sha(RUN/'sealed.json') and ad['accepted'] is True and ad['findings']==[] and ad['scope']=='exact-stage admission' and ad['phase']=='cost')
 # Explicit expression avoids any reliance on saved guard code.
 check('launch_membership_and_inventory',set(launch['files'])==set(seal['files'])|{str(RUN/n) for n in ['sealed.json','admission.json','prehost.json']} and launch['trees']==seal['trees'] and all(launch['inventory'][n]==v for n,v in seal['inventory'].items()) and rd(RUN/'output/pins.json')==launch)
 prep=rd(Q/'preparation-pins.json');pr=rd(Q/'review-final.json');bind('preparation920',prep,count=920);bind('preparation_review921',pr,count=921);bind('preparation_review_supplement',pr,'evidence_sha256',5)
 check('preparation_acceptance',pr['accepted'] is True and pr['findings']==[] and pr['pins_sha256']==sha(Q/'preparation-pins.json') and set(pr['sha256'])==set(prep['sha256'])|{str(Q/'preparation-pins.json')})
 bind('postcheck10',post,count=10);check('postcheck17',post['all_passed'] is True and len(post['checks'])==17 and all(post['checks'].values()))
 cfg=rd(RUN/'config.json');stage=Path(cfg['stage']);manifest=rd(D.parent/'NATIVE-PIVOT-PREPARATION/overlay-manifest.json')['candidate']
 check('stage75',len(manifest)==75 and {str(p.relative_to(stage)) for p in stage.rglob('*') if p.is_file()}=={v['destination'] for v in manifest} and all(not (stage/v['destination']).is_symlink() and sha(stage/v['destination'])==v['sha256']==sha(v['source']) for v in manifest))
 check('environment',all(os.environ.get(k)==v for k,v in rd(Q/'environment.json').items()))
 check('source_copy_identity',all(sha(Q/n)==sha(v) for n,v in rd(Q/'source-map.json')['byte_identical'].items()))
 actual=[p for root in ['src','test','.github','diagnostics/direct-lu-markowitz/reproduce'] for p in (R/root).rglob('*') if p.is_file()]+[R/'Project.toml']
 unbound=[str(p) for p in actual if str(p) not in prep['sha256'] and str(p) not in seal['inventory']]
 details['actual_file_coverage']={'files':len(actual),'unbound':unbound};check('actual_production_source_bound',all(str(p) in prep['sha256'] or str(p) in seal['inventory'] for p in (R/'src').rglob('*') if p.is_file()))
 inv=rd(RUN/'invocation.json');proc=rd(RUN/'output/process.json');cur=rd(RUN/'output/current.json');sup=inv['supervisor'];res=rd(RUN/'reservation.json')
 command=['/bin/bash','/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh','--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+str(stage),str(Q/'cost-driver.jl'),str(RUN/'output'),str(stage),str(Q/'inputs.toml')]
 check('command_config',cfg==seal['config'] and cfg['phase']=='cost' and cfg['seconds']==45 and cfg['expected_exit']==0 and cfg['arm']=='candidate' and cfg['command']==inv['command']==proc['command']==cur['command']==command and proc['cwd']==str(R))
 guard=[inv['python'],'-B',str(Q/'guard.py'),'run',str(RUN/'launch-pins.json'),str(RUN/'output'),'--seconds','37','--deadline',str(inv['monotonic_start']+37),'--expected-exit','0','--',*command]
 check('guard_deadline',inv['guard_command']==guard and str(Path(inv['python']).resolve())==str(Path('/usr/bin/python3').resolve()))
 check('reservation',res==dict(one_attempt=True,phase='cost',command=command,pins_sha256=sha(RUN/'launch-pins.json'),review_sha256=sha(RUN/'admission.json'),max_seconds=45) and inv['reservation_sha256']==sha(RUN/'reservation.json') and inv['review_sha256']==sha(RUN/'admission.json'))
 check('process_pins',proc['pins_sha256']==cur['pins_sha256']==inv['pins_sha256']==sha(RUN/'launch-pins.json') and proc['pins_unchanged'] is True)
 check('exit_and_limit',proc['returncode']==sup['returncode']==0 and proc['reason']=='exit0' and sup['accepted'] is True and not any(sup[k] for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']) and 'cleanup_error' not in sup and 0<proc['elapsed_including_launch']<=sup['elapsed_seconds']<=inv['elapsed_seconds']<=45)
 check('linked_identities',cur['runner']==proc['runner']==sup['guard_identity'] and cur['child']==proc['child'] and proc['runner']['command'].strip()==' '.join(guard) and proc['child']['command'].strip()==' '.join(command))
 check('exact_identities',all(proc[role]['pid']==proc[role]['pgid']==proc[role]['sid']==pid and proc[role]['start_ticks']==tick and proc[role]['boot_id']==seal['boot_id'] for role,pid,tick in [('runner',254592,14997081),('child',254593,14997132)]))
 hs=[rd(RUN/n) for n in ['host.json','prehost.json','posthost.json']]+[rd(D/'posthost.json')]
 check('saved_hosts',all(not h['matches'] and all(h[k]==seal[k] for k in ['head','master','boot_id']) for h in hs) and len(hs[0]['groups'])==len(hs[1]['groups'])==214 and len(hs[2]['groups'])==len(hs[3]['groups'])==216 and set(hs[2]['groups'])==set(seal['groups'])|{254592,254593})
 resources=[json.loads(l) for l in (RUN/'output/resources.jsonl').read_text().splitlines()];check('resources',len(resources)==6 and all(z['available_kib']>=6*1024**2 and z['swap_used_kib']<=1024**2 for z in resources+[proc['terminal_memory']]) and proc['child_maxrss_kib']==533368 and a['result']['resources']==resources and a['result']['resident_highwater_kib']==533368)
 check('guard_source_limits','resource.RLIMIT_AS' in (Q/'guard.py').read_text() and '8*1024**3' in (Q/'guard.py').read_text().replace(' ',''))
 raw=tt(RUN/'output/raw.toml');inputs=rd(Q/'inputs.json');windows=[tt(RUN/f'output/window-{i:03d}.toml') for i in range(1,89)]
 check('exact_output_membership',{p.name for p in (RUN/'output').iterdir()}=={'pins.json','current.json','process.json','resources.jsonl','run.log','raw.toml'}|{f'window-{i:03d}.toml' for i in range(1,89)})
 check('input_JSON_TOML',tt(Q/'inputs.toml')['fixtures']==inputs['fixtures'])
 expected_schedule=[]
 for f in inputs['fixtures']:
  for r in range(1,12):
   for arm in (['C','P'] if r%2 else ['P','C']):expected_schedule.append(dict(id=len(expected_schedule)+1,fixture=f['name'],arm=arm,round=r,warm=r<=3))
 check('schedule88',inputs['schedule']==expected_schedule==[w['schedule'] for w in windows] and sum(w['schedule']['warm'] for w in windows)==24)
 check('raw_completed_counts',raw['complete'] is True and raw['fatal']=='' and raw['inputs_unchanged'] is True and raw['counts']==dict(construction=88,refactor=176,forward=2816,transpose=1408) and raw['windows']==88 and raw['threads']==raw['blas_threads']==1)
 check('loaded_paths',raw['loaded']==dict(rd(Q/'loaded-paths.json'),JSimplex=str(stage/'src/JSimplex.jl')))
 check('diagnostic_payload',raw['output_payload_bytes']==2162688 and raw['info_payload_bytes']==135168 and raw['diagnostic_graph_bytes']==2510224)
 fixtures={f['name']:f for f in inputs['fixtures']};saved=rd(Q/'saved-C.json');eq_cache={};rows_cache={};records=[];accuracy={};matches=[];factor={};strategies={};timings={};gc=[]
 for name,v in saved.items():
  for z in v:assert sha(z['path'])==z['sha256'] and tt(z['path'])['outputs']==z['outputs']
 check('saved_C_sources44',sum(map(len,saved.values()))==44)
 base=raw['default_control'];assert len(base)==20 and base[3]==token(.1) and base[7]==token(0.)
 for w in windows:
  s=w['schedule'];name=s['fixture'];arm=s['arm'];n=fixtures[name]['matrix']['n'];key=name+':'+arm
  ctrl=base.copy();ctrl[3]=token(1. if arm=='P' else .1)
  assert w['control']==w['spare_control']==ctrl and w['policy']==('_NATIVE_PIVOT_ONE' if arm=='P' else '_NATIVE_PIVOT_DEFAULT')
  assert w['fresh'] is w['reused'] is w['no_spare'] is True
  own=w['owners'];assert len(own)==6 and own[:3]==own[3:] and own[0]!=own[1] and w['Wi']==w['W']==n
  assert len(w['info'])==90 and len(w['outputs'])==len(w['solve_info'])==48
  strategy=num(w['info'][18]);assert strategy in (1,3);strategies.setdefault(key,set()).add(strategy)
  for k,(x,info) in enumerate(zip(w['outputs'],w['solve_info'])):
   rhs=['a','dse','unit'][k%3];b=fixtures[name]['rhs'][rhs];trans=rhs=='unit';ck=(name,rhs,tuple(x))
   assert len(x)==len(b)==n and len(info)==4
   st,taken,attempt,flops=map(num,info);assert st==taken==attempt==0 and flops>=0
   if ck not in eq_cache:
    mk=(name,trans)
    if mk not in rows_cache:
     m=fixtures[name]['matrix'];cp=m['colptr'];ri=m['rowval'];val=m['nzval'];assert len(cp)==n+1 and cp[0]==1 and cp[-1]==len(val)+1 and len(ri)==len(val)
     rows=[[] for _ in range(n)]
     for j in range(n):
      assert cp[j]<=cp[j+1];indices=ri[cp[j]-1:cp[j+1]-1];assert indices==sorted(set(indices))
      for t in range(cp[j]-1,cp[j+1]-1):
       i=ri[t]-1;assert 0<=i<n;u,v=(j,i) if trans else (i,j);rows[u].append((v,rat(val[t])))
     rows_cache[mk]=rows
    rows=rows_cache[mk];xx=list(map(rat,x));bb=list(map(rat,b))
    error=max(abs(sum((v*xx[j] for j,v in row),Fraction())-bb[i]) for i,row in enumerate(rows))
    norm=max(sum((abs(v) for _,v in row),Fraction()) for row in rows)
    bound=Fraction(128*n,2**52)*max(Fraction(1),norm*max(map(abs,xx)),max(map(abs,bb)))
    eq_cache[ck]=dict(passed=error<=bound,max_residual=str(error),bound=str(bound),ratio=float(error/bound))
   z=eq_cache[ck];records.append(dict(window=s['id'],solve=k+1,**z));ac=accuracy.setdefault(key,dict(total=0,passed=0,nonzero=0,max_ratio=0.));ac['total']+=1;ac['passed']+=int(z['passed']);ac['nonzero']+=int(z['max_residual']!='0');ac['max_ratio']=max(ac['max_ratio'],z['ratio'])
   if not z['passed'] and not (name=='sparse96' and arm=='C' and rhs=='unit'):raise AssertionError(dict(window=s['id'],fixture=name,arm=arm,rhs=rhs,computed=z,expected=a['result']['residuals'][len(records)-1]))
  if arm=='C':matches.append(dict(window=s['id'],fixture=name,matches_all_saved=all(w['outputs']==z['outputs'] for z in saved[name]),saved_hashes=[z['sha256'] for z in saved[name]]))
  for region in ['construction','refactor_fresh','refactor_spare','solve','total']:
   v=w[region];assert set(v)=={'seconds','bytes','events','gctime','compile_time','recompile_time'} and all(type(x) in (int,float) and math.isfinite(x) and x>=0 for x in v.values()) and all(type(v[k]) is int for k in ['bytes','events'])
   if not s['warm']:
    assert v['compile_time']==v['recompile_time']==0
    timings.setdefault(name+':'+region,{'C':{},'P':{}})[arm][str(s['round'])]=v
    if v['gctime']:gc.append(dict(schedule=s,region=region,metrics=v))
    if region=='solve':assert v['bytes']==v['events']==0
  if s['round']==11:
   f=w['factor'];assert f['m']==f['n']==f['nzd']==n and f['spare_W']==f['spare_Wi']==n and n<=f['lnz']<=n*(n+1)//2 and n<=f['unz']<=n*(n+1)//2
   factor[key]=dict(**f,info=w['info'],control=w['control'],strategy=strategy)
  else:assert 'factor' not in w
 check('all4224_exact_residual_records',records==a['result']['residuals'] and len(records)==4224);details['residuals']={'reconciled':len(records),'distinct_equations':len(eq_cache),'C_passed':sum(z['passed'] for k,z in accuracy.items() if k.endswith(':C')),'P_passed':sum(z['passed'] for k,z in accuracy.items() if k.endswith(':P'))}
 check('accuracy_summary',accuracy==summary['accuracy'] and details['residuals']['C_passed']==1936 and details['residuals']['P_passed']==2112 and a['result']['accuracy']=={'C':False,'P':True})
 check('saved_C_matches',matches==a['result']['saved_C_comparison'] and all(z['matches_all_saved'] for z in matches) and a['result']['unexplained_C_mismatch'] is False)
 check('controls_owners_workspace_refinement88',len(windows)==88)
 check('factor_and_strategy',factor==a['result']['factors'] and {k:sorted(v) for k,v in strategies.items()}==a['result']['strategies'])
 comparisons={};flags=[]
 for key,z in timings.items():
  C=z['C'];P=z['P'];assert set(C)==set(P)==set(map(str,range(4,12)))
  ratios=[P[str(i)]['seconds']/C[str(i)]['seconds'] for i in range(4,12)];st=stats(ratios)
  assert a['result']['paired_cost'][key]==dict(**z,ratios=ratios,summary=st)
  out=dict(summary=st,ratios=ratios,Cmedian_us=statistics.median(v['seconds'] for v in C.values())*1e6,Pmedian_us=statistics.median(v['seconds'] for v in P.values())*1e6)
  for metric in ['bytes','events']:
   dif=[P[str(i)][metric]-C[str(i)][metric] for i in range(4,12)];out[metric]=dict(Cmedian=statistics.median(v[metric] for v in C.values()),Pmedian=statistics.median(v[metric] for v in P.values()),paired_differences=dif,minimum_delta=min(dif),maximum_delta=max(dif))
  comparisons[key]=out
  for i,v in zip(range(4,12),ratios):
   if v>2 or v<.5:flags.append(dict(series=key,round=i,ratio=v,C=C[str(i)],P=P[str(i)],scope='Descriptive ratio flag only, never exclusion'))
 check('20_series_160_ratios_stats_allocations',len(comparisons)==20 and comparisons==summary['comparisons']);check('11_flags_preserved',flags==summary['ratio_flags'] and len(flags)==11)
 check('320_regions_compile_and_solves',summary['measured_regions']==sum(len(v) for z in timings.values() for v in z.values())==320)
 check('two_GC_windows_four_nested_records',gc==summary['measured_gc_nonzero'] and len(gc)==4 and {v['schedule']['id'] for v in gc}=={73,85})
 fac={k:{**{n:v[n] for n in ['lnz','unz','graph_bytes','strategy','spare_W','spare_Wi']},'unit_bytes':num(v['info'][3]),'numeric_units':num(v['info'][40]),'peak_units':num(v['info'][41])} for k,v in factor.items()}
 check('factor_memory_summary',fac==summary['factors'] and fac['sparse96:P']['unz']-fac['sparse96:C']['unz']==15 and (fac['sparse96:P']['numeric_units']-fac['sparse96:C']['numeric_units'])*16==48 and all(fac[n+':C']['graph_bytes']==fac[n+':P']['graph_bytes'] and fac[n+':C']['peak_units']==fac[n+':P']['peak_units'] for n in fixtures))
 check('summary_run_metadata',summary['inclusive_seconds']==inv['elapsed_seconds'] and summary['resources']==dict(samples=6,min_available_kib=min(v['available_kib'] for v in resources),max_swap_kib=max(v['swap_used_kib'] for v in resources),terminal=proc['terminal_memory'],child_maxrss_kib=proc['child_maxrss_kib']) and summary['pins']==dict(seal=1001,launch=1004,audit=156) and summary['diagnostic_graph_bytes']==raw['diagnostic_graph_bytes'])
 check('old_failures_and_single_run',rd(D.parent/'NATIVE-PIVOT-QUALIFICATION/runs/green/audit.json')['all_passed'] is False and rd(D.parent/'DIRECT-LU-COST-PREPARATION/cost1-audit.json')['all_passed'] is False and {p.name for p in (Q/'runs').iterdir()}=={'cost'})
 # Review canonical closure as inert text and independently enumerate its mappings.
 bind('unexecuted_draft_note',rd(D/'closure-draft-note.json'))
 draft=(D/'finalize.py').read_text();final=(D/'finalize-final.py').read_text()
 check('canonical_only_label_fix',draft.replace('before-GREEN2','before-cost-result')==final and not any((D/n).exists() for n in ['closure.json','closure-host.json','publication.json','continuation-mappings.json']))
 preserved={str(R/'diagnostics/simplex-core-architecture/STATUS.md'):D/'STATUS.md.before-cost-result',str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'):D/'roadmap.md.before-cost-result'}
 check('new_continuation_preimages',all(sha(n)==sha(p) for n,p in preserved.items()))
 mappings=[]
 def walk(rec,obj,loc=()):
  if isinstance(obj,dict):
   for k,v in obj.items():
    target=str(path(k));h=v if isinstance(v,str) else v.get('sha256') if isinstance(v,dict) else None
    if target in preserved and h==sha(preserved[target]):mappings.append(dict(record=str(rec.relative_to(R)),pointer=list(loc)+([k] if isinstance(v,str) else [k,'sha256']),key=k,sha256=h,preserved_path=str(preserved[target].relative_to(R))))
    walk(rec,v,loc+(k,))
  elif isinstance(obj,list):
   for i,v in enumerate(obj):walk(rec,v,loc+(i,))
 for p in sorted(list(Q.rglob('*.json'))+list(D.glob('*.json'))):walk(p,rd(p))
 check('new_mappings_relative_absolute',len(mappings)>=12 and any(Path(v['key']).is_absolute() for v in mappings) and any(not Path(v['key']).is_absolute() for v in mappings) and all('NATIVE-PIVOT-COST/' in v['preserved_path'] and v['preserved_path'].endswith('before-cost-result') for v in mappings))
 details['prospective_continuation_mappings']=mappings
 oldmaps=[]
 for p in D.parent.rglob('continuation-mappings.json'):
  if p.parent==D:continue
  obj=rd(p)
  for m in obj.get('mappings',[]):
   if not all(k in m for k in ['record','pointer','sha256','preserved_path']):continue
   v=rd(m['record'])
   for k in m['pointer']:v=v[k]
   assert v==m['sha256']==sha(m['preserved_path'])
   oldmaps.append((str(p),m['record']))
 check('older_mapping_values_preserved',len(oldmaps)>0);details['old_mapping_entries']=len(oldmaps)
 # Fresh independent read-only host observation; no process signaling or launch.
 gd=Path((R/'.git').read_text().strip().split(': ',1)[1]);common=(gd/(gd/'commondir').read_text().strip()).resolve()
 def ref(name):
  p=common/name
  if p.exists():return p.read_text().strip()
  return next(l.split()[0] for l in (common/'packed-refs').read_text().splitlines() if l.endswith(' '+name))
 head=(gd/'HEAD').read_text().strip();head=ref(head[5:]) if head.startswith('ref: ') else head
 boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();groups=hs[2]['groups'];present=[];unreadable=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   st=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip();exe=''
   try:exe=str((p/'exe').resolve(strict=True))
   except PermissionError:unreadable.append(int(p.name))
   except FileNotFoundError:pass
   if int(st[2]) in groups or int(st[3]) in groups or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):
    present.append(dict(pid=int(p.name),pgid=int(st[2]),sid=int(st[3]),start_ticks=int(st[19]),comm=comm,exe=exe,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'),boot_id=boot))
  except (FileNotFoundError,ProcessLookupError):pass
 host=dict(time=time.time(),head=head,master=ref('refs/heads/master'),boot_id=boot,groups=groups,matches=present,unreadable_exe_pids=unreadable,scope='Independent read-only PGID OR SID and Julia comm/readable exe inspection; inaccessible executable links remain a visibility limit')
 save('reviewer-host-corrections.json',host)
 check('fresh216_groups_AND_sessions',not present and len(groups)==216 and head==seal['head']=='1dd0bc58a124e365a53c926770c13bd7c494959f' and host['master']==seal['master']=='6f68e24e8ddac42b948da8fcc2d636c010751194' and boot==seal['boot_id'])
try:main()
except Exception as e:
 failures.append(repr(e));details['exception']=traceback.format_exc()
result=dict(all_passed=not failures,checks=checks,failures=failures,details=details,checker_sha256=sha(Path(__file__)),scope='Independent offline saved-data result checks only; no historical checker or numerical rerun')
save('reviewer-corrections.json',result)
print(json.dumps(dict(all_passed=result['all_passed'],checks=len(checks),failures=failures,details={k:v for k,v in details.items() if k in ['residuals','actual_file_coverage','exception','old_mapping_entries']}),indent=2))
