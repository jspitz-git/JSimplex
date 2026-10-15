"""Read-only fail-closed diagnostic validation; never executes historical scripts."""
from control import *
from analysis import analyze
import guard,math
SUFFIXES=('seal-host.json','sealed-pins.json','admission.json','prehost.json','launch-pins.json','reservation.json','launcher.log','invocation.json','posthost.json')
def output_names():return ['pins.json','current.json','process.json','resources.jsonl','run.log','raw.toml']+['lifecycle-'+a+'.toml' for a in 'CPR']+[f'window-{i:03d}.toml' for i in range(1,133)]
def phase_paths(phase,cfg):return [Q/(phase+'-'+n) for n in SUFFIXES]+[Path(cfg['output'])/n for n in output_names()]
def validate_predecessor(phase):
 req(phase=='accuracy','One diagnostic only');binding=rd(D/'predecessor-bindings.json')
 req(all(sha(n)==h for n,h in binding['sha256'].items()),'Predecessor changed')
 G=D.parent/'NATIVE-ACCURACY-POLICY-PLAN';A=D.parent/'DIRECT-LU-COST-PREPARATION'
 req(rd(G/'review.json')['accepted'] is True and rd(G/'review.json')['findings']==[] and rd(G/'closure.json')['all_passed'] is True,'Plan predecessor rejected')
 req(rd(A/'cost1-audit.json')['all_passed'] is False,'Original false audit must remain false')
 return [Path(n) for n in binding['sha256']]+[D/'predecessor-bindings.json']
def execution_checks(cfg,inv,post,p,current,pre,hs,sealed,pins,pin_hash,review_hash,reservation,reservation_hash):
 s=inv['supervisor'];start=inv['monotonic_start']
 expected=[inv['python'],'-B',str(D/'guard.py'),'run',str(Q/'accuracy-launch-pins.json'),cfg['output'],'--seconds','39','--deadline',str(start+39),'--',*cfg['command']]
 return dict(host=not pre['matches'] and not hs['matches'] and all(pre[k]==hs[k]==sealed[k] for k in ('head','master','boot_id')),
 no_processes=post['matches']==[] and all(post[k]==pre[k] for k in ('head','master','boot_id')) and set(pre['groups'])<=set(post['groups']),
 identities=current['runner']==p['runner']==s['guard_identity'] and current['child']==p['child'] and all(p[k][field] in post['groups'] for k in ('runner','child') for field in ('pgid','sid')),
 bounded=type(start) in (float,int) and 0<=inv['elapsed_seconds']<=45 and 0<=s['elapsed_seconds']<=45 and s.get('accepted') is True and 'cleanup_error' not in s,
 exit=p['returncode']==0 and p['reason']=='exit0' and s['returncode']==0,
 pins=p['pins_unchanged'] is True,
 command=p['command']==current['command']==cfg['command']==inv['command'] and p['pins_sha256']==current['pins_sha256']==pin_hash==inv['pins_sha256'],
 guard_command=inv['guard_command']==expected and str(Path(inv['python']).resolve())==str(Path(sys.executable).resolve()),
 reservation=reservation==dict(one_attempt=True,phase='accuracy',command=cfg['command'],pins_sha256=pin_hash,review_sha256=review_hash,max_seconds=45),
 invocation=inv['review_sha256']==review_hash and inv['reservation_sha256']==reservation_hash)
def memory_report(resources,p):
 peak=p['child_maxrss_kib'];req(type(peak) in (int,float) and math.isfinite(peak) and peak>0,'Terminal resident highwater')
 rows=[]
 for sample in resources:
  values={}
  for line in sample.get('child_memory',[]):
   name,value,unit=line.split();req(name in ('VmRSS:','VmHWM:','VmPeak:','VmSwap:') and unit=='kB' and name[:-1] not in values,'Memory metadata');values[name[:-1]]=int(value);req(values[name[:-1]]>=0,'Memory nonnegative')
  if values:
   req(set(values)=={'VmRSS','VmHWM','VmPeak','VmSwap'} and values['VmRSS']<=values['VmHWM']<=peak,'RSS/HWM metadata');rows.append(values)
 req(rows,'No sampled process memory')
 return dict(samples=rows,child_maxrss_kib=peak,scope='Fresh guard RUSAGE_CHILDREN after reaping its sole child; sampled VmHWM resident, VmPeak virtual. Not native allocation/free balance.')
def phase_checks(phase):
 cfg=phase_config(phase);out=Path(cfg['output']);paths=phase_paths(phase,cfg);validate_predecessor(phase)
 req(all(p.is_file() for p in paths),'Missing phase evidence')
 req({p.name for p in out.iterdir()}==set(output_names()) and all(p.is_file() for p in out.iterdir()),'Output membership')
 inv=rd(Q/(phase+'-invocation.json'));post=rd(Q/(phase+'-posthost.json'));p=rd(out/'process.json')
 pp=Q/(phase+'-launch-pins.json');pins=rd(pp);sp=Q/(phase+'-sealed-pins.json');sealed=rd(sp);rp=Q/(phase+'-admission.json')
 validate_review(rd(rp),sp,sealed['files']+[str(sp)])
 req(sealed['phase']==phase,'Sealed phase');req(set(pins['files'])==set(sealed['files'])|{str(sp),str(rp)} and pins['trees']==sealed['trees'],'Launch membership')
 req(all(pins['inventory'].get(n)==v for n,v in sealed['inventory'].items()),'Launch/seal drift')
 req(guard.pins_match(pins) and rd(out/'pins.json')==pins,'Actual pin mismatch')
 current=rd(out/'current.json');pre=rd(Q/(phase+'-prehost.json'));hs=rd(Q/(phase+'-seal-host.json'));r=Q/(phase+'-reservation.json')
 checks=execution_checks(cfg,inv,post,p,current,pre,hs,sealed,pins,sha(pp),sha(rp),rd(r),sha(r))
 resources=[json.loads(line) for line in (out/'resources.jsonl').read_text().splitlines()]
 req(resources,'No resource samples');resources.append(p['terminal_memory'])
 checks['resources']=all(r['available_kib']>=6*1024**2 and r['swap_used_kib']<=1024**2 for r in resources)
 def toml(p):return tomllib.loads(p.read_text())
 raw=toml(out/'raw.toml');expected_paths=rd(D/'stdlib-paths.json')
 req(raw['stdlib_paths']==expected_paths,'Loaded stdlib path drift')
 old=toml(D.parent/'DIRECT-LU-BACKEND-PREPARATION/probe-run/fresh.toml')
 mem=memory_report(resources,p)
 result=analyze(raw,{a:toml(out/('lifecycle-'+a+'.toml')) for a in 'CPR'},[toml(out/f'window-{i:03d}.toml') for i in range(1,133)],rd(D/'inputs.json'),old['outputs'][1])
 result['process_memory']=mem
 checks['resident_memory']=True
 checks['diagnostic_integrity']=True
 return checks,result
