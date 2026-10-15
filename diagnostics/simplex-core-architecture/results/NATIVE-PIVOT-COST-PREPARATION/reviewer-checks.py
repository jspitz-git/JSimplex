"""Independent offline review only. No historical script or numerical workflow execution."""
from pathlib import Path
import json,hashlib,subprocess,sys,time,tomllib,copy,tempfile
D=Path(__file__).resolve().parent;R=D.parents[3];B=D.parent
checks={};details={}
def rd(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def path(p):return Path(p) if Path(p).is_absolute() else R/p
def ck(n,v):
 checks[n]=bool(v)
 if not v:print('FAILED',n,flush=True)
def bound(z,mapping={}):return all(sha(mapping.get(str(path(p)),path(p)))==v for p,v in z.items())
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
def save(p,z):
 with Path(p).open('x') as f:json.dump(z,f,indent=2);f.write('\n')
pins=rd(D/'preparation-pins.json')['sha256'];required=rd(D/'required-paths.json')['paths']
ck('exact_920_manifest_members',len(pins)==len(required)==len(set(required))==920 and set(pins)==set(required))
ck('all_920_current_hashes',bound(pins));details['pins_sha256']=sha(D/'preparation-pins.json')
sc=rd(D/'source-check.json');ck('source_18_checks_219_bindings',sc['all_passed'] is True and len(sc['checks'])==18 and all(sc['checks'].values()) and len(sc['sha256'])==219 and bound(sc['sha256']))
red=rd(D/'offline-RED.json');green=rd(D/'offline-GREEN.json');ck('synthetic_red_retained',red['all_passed'] is False and 'No module named' in red['error']);ck('synthetic_green_27',green['all_passed'] is True and len(green['checks'])==27 and all(green['checks'].values()))
sm=rd(D/'source-map.json');ck('12_identical_files',len(sm['byte_identical'])==12 and all((D/n).read_bytes()==Path(p).read_bytes() for n,p in sm['byte_identical'].items()))
for n,z in sm['changed'].items():
 s=(D/n).read_text();unique=True
 for e in reversed(z['edits']):unique &= s.count(e['after'])==1;s=s.replace(e['after'],e['before'],1)
 ck('exact_inverse_'+n,unique and s==Path(z['source']).read_text())
ck('exact_three_changed_files',set(sm['changed'])=={'common.py','control.py','audit.py'})
overlay=rd(B/'NATIVE-PIVOT-PREPARATION/overlay-manifest.json')
for arm,count in [('candidate',75),('reference',73)]:
 a=overlay[arm];ck(arm+'_overlay_'+str(count),len(a)==count==len({e['destination'] for e in a}) and all(sha(e['source'])==e['sha256'] for e in a))
ck('overlay_sources_pinned',all(e['source'] in pins for arm in ['candidate','reference'] for e in overlay[arm]))
ck('no_tracked_changes',git('diff','--name-only')=='' and git('diff','--cached','--name-only')=='')
ck('refs',git('rev-parse','HEAD')=='294d4435e888577d90533b50c3c44da6702976e6' and git('rev-parse','master')=='6f68e24e8ddac42b948da8fcc2d636c010751194')
G=B/'NATIVE-PIVOT-GREEN2-PREPARATION/runs/green2';O=B/'NATIVE-PIVOT-QUALIFICATION';RES=B/'NATIVE-PIVOT-GREEN2'
a=rd(G/'audit.json');rr=rd(G/'result-review.json');old=rd(O/'runs/green/audit.json')
ck('accepted_green2_audit',a['all_passed'] is True and a['phase']=='green2' and bound(a['sha256']))
ck('exact_canonical75_review',rr['accepted'] is True and rr['findings']==[] and rr['scope']=='stage result' and rr['phase']=='green2' and rr['pins_sha256']==sha(G/'audit.json') and len(rr['sha256'])==75 and set(rr['sha256'])==set(a['sha256'])|{str(G/'audit.json')} and bound(rr['sha256']))
ck('exact_16_review_evidence',len(rr['evidence_sha256'])==16 and bound(rr['evidence_sha256']))
ck('original_failed_green_retained',old['all_passed'] is False and old['phase']=='green' and bound(old['sha256']))
ck('old_direct_cost_failed',rd(B/'DIRECT-LU-COST-PREPARATION/cost1-audit.json')['all_passed'] is False)
status=R/'diagnostics/simplex-core-architecture/STATUS.md';road=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md';mapping={str(status):D/'STATUS.md.before-cost',str(road):D/'roadmap.md.before-cost'}
ck('exact_before_cost_preimages',all(sha(p)==sha(n) for n,p in mapping.items()))
for fn in ['closure.json','publication.json']:
 z=rd(RES/fn);ck('predecessor_mapped_'+fn,z['all_passed'] is True and bound(z['sha256'],mapping));ck('both_continuations_'+fn,all(str(p.relative_to(R)) in z['sha256'] for p in [status,road]))
closure=rd(RES/'closure.json');pub=rd(RES/'publication.json');ck('predecessor_complete_publication',set(pub['sha256'])==set(pub['staged_names'])-{str((RES/'publication.json').relative_to(R))} and set(pub['other_blobs'])==set(pub['sha256']) and set(closure['sha256'])==set(pub['sha256'])-{str((RES/'closure.json').relative_to(R))})
inputs=rd(D/'inputs.json');fs=inputs['fixtures'];schedule=inputs['schedule'];expected=[]
for f in fs:
 for r in range(1,12):
  for arm in (('C','P') if r%2 else ('P','C')):expected.append(dict(id=len(expected)+1,fixture=f['name'],arm=arm,round=r,warm=r<=3))
ck('same_json_toml_fixtures',tomllib.loads((D/'inputs.toml').read_text())['fixtures']==fs)
ck('four_original_dimensions',len(fs)==4 and sorted(f['matrix']['n'] for f in fs)==[32,32,96,96])
ck('exact_88_alternating_schedule',len(schedule)==88 and schedule==expected)
ck('24_warm_64_measured',sum(s['warm'] for s in schedule)==24 and sum(not s['warm'] for s in schedule)==64)
ck('payload_2297856',sum(f['matrix']['n']*22*48*8 for f in fs)==2162688 and 88*4*48*8==135168)
ck('selected_counts',88*2==176 and 88*32==2816 and 88*16==1408 and 88*48==4224)
# Only new definition-only helpers are imported; no guard/auditor or workflow execution.
sys.path.insert(0,str(D));import control as c
from exact import validate_controls,validate_info,validate_timing,token,residual
cfg=c.config('cost');ck('cost_config',cfg['phase']=='cost' and cfg['seconds']==45 and cfg['arm']=='candidate' and cfg['expected_exit']==0 and cfg['stage']==str(R/'.superpowers/native-pivot-cost/cost') and cfg['run']==str(D/'runs/cost'))
ck('exact_command',cfg['command']==['/bin/bash',c.WRAPPER,'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+cfg['stage'],str(D/'cost-driver.jl'),str(D/'runs/cost/output'),cfg['stage'],str(D/'inputs.toml')])
gc=c.guard_command(cfg,D/'fake',100.);ck('inner37_absolute137',gc[gc.index('--seconds')+1]=='37' and gc[gc.index('--deadline')+1]=='137.0')
def rejects(f):
 try:f();return False
 except (ValueError,RuntimeError,KeyError,TypeError,FileNotFoundError):return True
ck('reject_other_routes',all(rejects(lambda p=p:c.config(p)) for p in ['red','green','green2','cost2','../cost','']))
ck('reject_failed_new_predecessor',rejects(lambda:c.validate_prerequisites({'all_passed':False,'phase':'green2'},old)))
ck('reject_relabelled_original_failure',rejects(lambda:c.validate_prerequisites(a,dict(old,all_passed=True))))
pf,pg=c.predecessor('cost');ck('new_predecessor_complete_pinned',len(set(pg))==len(pg)==214 and all(str(p) in pins for p in pf))
with tempfile.TemporaryDirectory(prefix='native-cost-review-') as td:
 p=Path(td)/'pins.json';p.write_text('{}');v=dict(accepted=True,findings=[],scope='exact-stage admission',phase='cost',pins_sha256=sha(p),sha256={str(p):sha(p)})
 c.verify_review(v,p,[str(p)],'exact-stage admission','cost');ck('pure_valid_review',True)
 for key,value in [('accepted',False),('findings',['x']),('scope','offline preparation'),('phase','green2'),('pins_sha256','x'),('sha256',{})]:
  w=copy.deepcopy(v);w[key]=value;ck('review_refuses_'+key,rejects(lambda:c.verify_review(w,p,[str(p)],'exact-stage admission','cost')))
 p.write_text('changed');ck('review_refuses_changed_file',rejects(lambda:c.verify_review(v,p,[str(p)],'exact-stage admission','cost')))
base=[token(0.)]*20;base[3]=token(.1);policy=list(base);policy[3]=token(1.);validate_controls('P',policy,base);ck('pure_threshold_controls',True)
for i in range(20):
 bad=policy.copy();bad[i]=token(9.);ck('reject_control_slot_'+str(i),rejects(lambda:validate_controls('P',bad,base)))
validate_info('P',[token(0.)]*4);ck('pure_zero_refinement',True)
ck('reject_refinement',rejects(lambda:validate_info('P',[token(0.),token(1.),token(1.),token(0.)])))
t=dict(seconds=1.,bytes=0,events=0,gctime=0.,compile_time=0.,recompile_time=0.);validate_timing(t);ck('pure_timing',True)
for k,v in [('seconds',float('nan')),('bytes',-1),('events',.5),('gctime',float('inf'))]:ck('reject_timing_'+k,rejects(lambda:validate_timing(dict(t,**{k:v}))))
ck('reject_timing_extra',rejects(lambda:validate_timing(dict(t,extra=0))))
# Tiny pure-helper examples are neither saved-experiment recomputation nor native numerical execution.
m=dict(n=1,colptr=[1,2],rowval=[1],nzval=[token(1.)]);ck('pure_exact_bound',residual(m,[token(1.)],[token(1.)])['passed'] and not residual(m,[token(2.)],[token(1.)])['passed'])
ck('no_new_stage_or_runs',not Path(cfg['stage']).exists() and not (D/'runs').exists());ck('old_cost_unexecuted',not (O/'runs/cost').exists())
historical=rd(D/'host.json');groups=historical['groups'];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[];unreadable=[];scanned=0
for p in Path('/proc').glob('[0-9]*'):
 try:
  z=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip();exe='';scanned+=1
  try:exe=str((p/'exe').resolve(strict=True))
  except PermissionError:unreadable.append(int(p.name))
  except FileNotFoundError:pass
  if int(z[2]) in groups or int(z[3]) in groups or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):
   matches.append(dict(pid=int(p.name),pgid=int(z[2]),sid=int(z[3]),start_ticks=int(z[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'),comm=comm,exe=exe,boot_id=boot))
 except (FileNotFoundError,ProcessLookupError):pass
h=dict(time=time.time(),boot_id=boot,groups=groups,matches=matches,unreadable_exe_pids=unreadable,processes_scanned=scanned,head=git('rev-parse','HEAD'),master=git('rev-parse','master'),scope='Independent full process stat/comm and readable exe scan; inaccessible system exe visibility limit; PGID and SID independently checked')
save(D/'reviewer-host.json',h);ck('fresh_214_groups_and_sessions_no_julia',len(set(groups))==len(groups)==214 and set(pg)==set(groups) and not matches and boot==historical['boot_id'])
final=(D/'finalize.py').read_text();publication=(D/'publication.py').read_text()
ck('closure_requires_exact_review_before_mutation',final.index('verify_review(')<final.index('STATUS.write_text(') and "'offline preparation'" in final)
ck('closure_requires_preimages_and_records_mappings',"require(all(sha(n)==sha(p) for n,p in preserved.items()),'Continuation preimages')" in final and "save(D/'continuation-mappings.json'" in final and 'pointer=list(loc)' in final and 'require(len(maps)>=4' in final)
ck('closure_exact_complete_publication_names',"set(names)==actual and len(names)==len(set(names))" in final and "D.rglob('*')" in final and "D/'closure.json',D/'publication.json'" in final)
ck('publication_checks_all_closure_bindings',"all(sha(R/n)==v for n,v in c['sha256'].items())" in publication)
ck('publication_checks_names_blobs_and_complete_stage',"==set(other)" in publication and "==set(names)" in publication and "git('hash-object','--',n)==v" in publication and "open('x')" in publication)
# Derive planned mapping records independently, without writing continuation or running finalizer.
maps=[]
def walk(rec,obj,loc=()):
 if isinstance(obj,dict):
  for k,v in obj.items():
   full=str(path(k));value=v if isinstance(v,str) else v.get('sha256') if isinstance(v,dict) else None
   if full in mapping and value==sha(mapping[full]):maps.append(dict(record=str(rec.relative_to(R)),pointer=list(loc)+([k] if isinstance(v,str) else [k,'sha256']),sha256=value,preserved_path=str(mapping[full].relative_to(R))))
   walk(rec,v,loc+(k,))
 elif isinstance(obj,list):
  for i,v in enumerate(obj):walk(rec,v,loc+(i,))
for rec in sorted(list(RES.glob('*.json'))+list(D.glob('*.json'))):walk(rec,rd(rec))
ck('derived_exact_predecessor_four_current_mappings',sum(m['record'] in [str((RES/n).relative_to(R)) for n in ['closure.json','publication.json']] for m in maps)==4)
details.update(planned_continuation_mappings=maps,predecessor_files=len(pf),manifest_count=len(pins),source_bindings=len(sc['sha256']),canonical_predecessor_review_bindings=len(rr['sha256']),supplemental_predecessor_bindings=len(rr['evidence_sha256']))
save(D/'reviewer-checks.json',dict(all_passed=all(checks.values()),checks=checks,details=details,scope='Independent offline preparation checks; no numerical workflow, historical auditor, finalizer, publication, stage or reservation executed'))
print(json.dumps(dict(all_passed=all(checks.values()),checks=len(checks),failed=[k for k,v in checks.items() if not v],manifest=len(pins),mappings=len(maps))))
if not all(checks.values()):sys.exit(1)
