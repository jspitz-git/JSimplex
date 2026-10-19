"""Independent exact RED300 admission. Standard library, read-only target inspection.
No Julia execution, no prior checker execution, no control/launch imports.
Only this review's new evidence files are written; acceptance is a separate step.
"""
from pathlib import Path
import hashlib,json,os,subprocess,time,re,tomllib,importlib.util,copy
E=Path(__file__).resolve().parent;D=E.with_name('DIRECT-BG-BLOCKED-UPDATE-TYPED-HARNESS');R=D.parents[3]
W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl')
RUN=D/'runs/red300';O=D/'outers/red300'
HEAD='9a537a3ec590351f2a7b516a4efc53f7c790efaa';MASTER='26e2291745999f485a74f643298ca997d65c7205'
checks=[]
def rd(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def ck(v,n):
 checks.append(dict(name=n,passed=bool(v)))
 if not v:raise AssertionError(n)
def save(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def binding(v,key='sha256'):
 for n,h in v[key].items():
  p=Path(n) if Path(n).is_absolute() else R/n
  ck(p.is_file() and sha(p)==h,'bound '+str(p))
def git(*args,cwd=R):return subprocess.check_output(['git',*args],cwd=cwd,text=True).strip()
def inventory(files,trees):
 paths={Path(n) for n in files}
 for n in trees:
  root=Path(n);ck(root.is_dir() and not root.is_symlink(),'tree root '+n)
  for p in root.rglob('*'):
   ck(not p.is_symlink(),'tree regular '+str(p))
   if p.is_file():paths.add(p)
 out={}
 for p in sorted(paths):
  ck(p.is_file(),'inventory regular '+str(p))
  out[str(p)]=dict(resolved=str(p.resolve(strict=True)),sha256=sha(p))
 return out
BOOT=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
def identity(pid):
 p=Path('/proc')/str(pid);a=(p/'stat').read_text().rsplit(')',1)[1].split()
 return dict(pid=pid,pgid=int(a[2]),sid=int(a[3]),start_ticks=int(a[19]),boot_id=BOOT,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'))
def fresh_host(groups,refs,env,oi):
 matches=[];unreadable=[];unreadableid=[];processes=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   a=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip();argv0=(p/'cmdline').read_bytes().split(b'\0',1)[0].decode(errors='replace');exe=''
   try:exe=str((p/'exe').resolve(strict=True))
   except PermissionError:unreadable.append(int(p.name))
   except FileNotFoundError:pass
   row=dict(pid=int(p.name),pgid=int(a[2]),sid=int(a[3]),start_ticks=int(a[19]),state=a[0],comm=comm,argv0=argv0,exe=exe);processes.append(row)
   if row['pgid'] in groups or row['sid'] in groups or any(Path(v).name.lower().startswith('julia') for v in (comm,argv0,exe)):matches.append(row)
  except (FileNotFoundError,ProcessLookupError):pass
  except PermissionError:unreadableid.append(int(p.name))
 m={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()}
 return dict(time=time.time(),groups=sorted(groups),matches=matches,unreadable_exe_pids=unreadable,unreadable_identity_pids=unreadableid,processes=processes,boot_id=BOOT,refs=refs,environment=env,outer_identity=identity(oi['pid']),memory=dict(available_kib=m['MemAvailable'],swap_used_kib=m['SwapTotal']-m['SwapFree']),scope='Full 286 historical PGIDs AND SIDs plus comm/argv0/readable executable Julia detection. Inaccessible exe links are an explicit visibility limit.')
def reject(fn,label):
 try:fn()
 except (ValueError,KeyError,TypeError):ck(True,label);return
 ck(False,label)
def synthetic(schedule,loaded,pc):
 spec=importlib.util.spec_from_file_location('reviewed_pure_oracle',D/'oracle.py');o=importlib.util.module_from_spec(spec);spec.loader.exec_module(o)
 ck(len(o.PAYLOAD)==60 and len(o.PREPARATION)==31 and o.panel_counts()==pc,'pure oracle exact contracts')
 def tree(name,a,children=[]):return dict(name=name,**dict(zip(['pass','fail','error','broken'],a)),children=children)
 def row(i):
  name=schedule['units'][i-1];events={};apis={};obs=[];failures=[]
  if i==1:
   sites=pc.copy();children=[tree(n,[v,0,0,0]) for n,v in zip(['budget and cheap eligibility','independent arithmetic, policy and canonical zeros','packed commit, incidence, support and source counters','computed commit cap and independent work witnesses'],[31,11619,74,44])]
  elif i==2:
   sites={f'L{k:03}':1 for k in range(1,41)}
   for lo,hi,n in [(1,22,2),(31,32,2),(33,35,3)]:
    for k in range(lo,hi+1):sites[f'L{k:03}']=n
   del sites['L025'];del sites['L030'];sites.update({f'N{k:03}':3 for k in range(5,13)})
   events=dict(finish=3,event_finish=3,event_begin=3);apis=dict(factory_candidate=2,factory_micro=12,FTRAN=13,BTRAN=2,replace=8,copy=6,refactor=8,eliminate=8,eliminate_fault=4)
   children=[tree('blocked BG lifecycle and failure ownership',[sum(sites.values()),0,0,0])]
  else:
   f=schedule['fixtures'][(i-3)//2];u=f['updates'];sites={f'N{k:03}':2*u for k in range(5,13)};sites.update({f'N{k:03}':u for k in range(15,26)});sites.update(N013=1,N014=1,N021=2*u,N026=1)
   if not f['pivot_agreement']:del sites['N024']
   events=dict(finish=2*u,event_finish=2*u,event_begin=2*u);apis=dict(factory_reference=1,factory_candidate=1,FTRAN=6*u,BTRAN=2*u,replace_reference=u,replace_candidate=u)
   obs=[dict(panels=0,rejections=0,growth=1.0,minpivot=1.0) for _ in range(u)];children=[]
   if name in schedule['expected_red_units']:failures=[dict(site='N026',kind='fail',detail='Test Failed: observed >= minimum_panels\n')]
  a=[sum(sites.values())-len(failures),len(failures),0,0]
  return dict(index=i,name=name,complete=True,fatal='',tests=tree(name,[0,0,0,0] if children else a,children),records=dict(sites=sites,events=events,apis=apis,failures=failures,failure_count=len(failures),active=''),observations=obs),a
 payload={n:dict(seconds=0.1,bytes=0,events=0,gc_seconds=0.0,compile_seconds=0.0,recompile_seconds=0.0) for n in o.PREPARATION};tot=[0]*4
 for i in range(1,29):
  r,a=row(i);payload[f'unit-{i}.toml']=r;tot=[x+y for x,y in zip(tot,a)]
 payload['raw.toml']=dict(phase='red300',complete=True,fatal='',units_completed=28,loaded=loaded,threads=1,blas_threads=1,totals=tot)
 ck(o.validate(payload,schedule,loaded,'red300')['totals']==tot and tot[1:]==[6,0,0],'independent synthetic RED 28-unit ledger')
 log=''.join(f"UNIT BEGIN {i} {payload[f'unit-{i}.toml']['name']}\nUNIT END {i} {payload[f'unit-{i}.toml']['name']}\n"+''.join('TEST FAILURE: N026 '+f['detail'] for f in payload[f'unit-{i}.toml']['records']['failures']) for i in range(1,29))
 ck(not o.warning_log(log,payload,'red300'),'six exact synthetic log renderings')
 for text in ['WARNING: invalid\n','ERROR: bad\n','world age\n','Test Failed\n','TEST FAILURE: other\n']:
  ck(o.warning_log(log+text,payload,'red300'),'reject log '+text.strip())
 for n in o.PAYLOAD:
  bad=copy.deepcopy(payload);del bad[n];reject(lambda:o.validate(bad,schedule,loaded,'red300'),'reject missing payload '+n)
 for n in o.PREPARATION:
  for k,v in [('bytes',0.5),('events',True),('seconds',float('nan')),('gc_seconds',-1),('compile_seconds',301),('recompile_seconds',float('inf'))]:
   bad=copy.deepcopy(payload);bad[n][k]=v;reject(lambda:o.validate(bad,schedule,loaded,'red300'),'reject metric '+n+' '+k)
 for i in range(1,29):
  bad=copy.deepcopy(payload);bad[f'unit-{i}.toml']['complete']=False;reject(lambda:o.validate(bad,schedule,loaded,'red300'),'reject incomplete unit '+str(i))
 for site in ['P011']+[f'P{k:03}' for k in range(95,103)]:
  bad=copy.deepcopy(payload);bad['unit-1.toml']['records']['sites'][site]+=1;reject(lambda:o.validate(bad,schedule,loaded,'red300'),'reject typed multiplicity '+site)
 for i in range(3,29):
  bad=copy.deepcopy(payload);bad[f'unit-{i}.toml']['records']['apis']['FTRAN']+=1;reject(lambda:o.validate(bad,schedule,loaded,'red300'),'reject API budget '+str(i))
 return dict(synthetic_only=True,totals=tot,units=28,payload=60,cost_records=31)
def main():
 s=rd(RUN/'sealed.json');cfg=rd(RUN/'config.json');host=rd(RUN/'host.json');ready=rd(O/'outer-ready.json');prep=rd(D/'preparation-pins.json');pr=rd(D/'review.json');stage=rd(D/'stages.json')['red'];rt=rd(D/'runtime-inputs-complete.json')['inventory'];base=rd(D/'baseline.json')
 ck(pr['accepted'] is True and pr['findings']==[] and pr['launch_admitted'] is False and pr['scope']=='BG blocked typed harness preparation','offline preparation disposition')
 ck(pr['pins_sha256']==sha(D/'preparation-pins.json'),'prep manifest hash')
 ck(len(prep['sha256'])==581 and set(prep['sha256'])==set(rd(D/'required-paths.json')['paths']),'exact 581 prep members')
 ck(len(pr['sha256'])==582 and set(pr['sha256'])==set(prep['sha256'])|{str(D/'preparation-pins.json')},'exact 582 review members')
 for n in prep['sha256']:ck(Path(n).is_file() and not Path(n).is_symlink(),'prep regular '+n)
 binding(prep);binding(pr);binding(pr,'evidence_sha256')
 prepared=set(prep['sha256'])|{str(D/'preparation-pins.json'),str(D/'review.json')}|set(pr['evidence_sha256']);ck(len(prepared)==586,'586 prepared seal members')
 ck(len(rt)==609 and inventory(rt,[])==rt,'609 actual runtime/resolved bindings')
 for label,root in [('diagnostic',R),('production',W)]:
  ck(set(git('ls-files','src','test','.github','Project.toml',cwd=root).splitlines())==set(base[label]),'baseline membership '+label)
  for n,h in base[label].items():ck(sha(root/n)==h,'source '+label+' '+n)
 st=Path(stage['path']);ck(len(stage['sha256'])==75 and {str(p.relative_to(st)) for p in st.rglob('*') if p.is_file()}==set(stage['sha256']),'75 exact repaired stage members')
 for n,h in stage['sha256'].items():ck(sha(st/n)==h,'stage '+n)
 repair=D.with_name('DIRECT-BG-BLOCKED-UPDATE-STAGE-REPAIR');m=rd(repair/'stage.json');ck(m['master']==MASTER and m['stage']==str(st) and m['stage_files']==stage['sha256'],'repaired master stage binding')
 for n in ['stage.json','review.json','publication.json']:binding(rd(repair/n))
 ck(rd(repair/'review.json')['accepted'] is True and rd(repair/'review.json')['findings']==[],'repair acceptance')
 for n,item in rd(D/'copied-files.json').items():ck(sha(D/n)==sha(item['source'])==item['sha256'],'exact copy '+n)
 probe=D.with_name('DIRECT-BG-ZERO-COUNTS-CANDIDATE');typed=D.with_name('DIRECT-BG-P011-TYPED-REPAIR');pv=rd(probe/'review.json');binding(pv);ck(pv['accepted'] is True and pv['findings']==[],'shared-zero reviewed')
 tv=rd(typed/'independent-review.json');binding(tv,'reviewed_bindings');ck(tv['disposition']=='ACCEPTED — PREPARATION ONLY' and tv['findings']==[] and tv['runtime_executed'] is False and tv['review_markdown_sha256']==sha(typed/'independent-review.md'),'typed preparation acceptance')
 ck(sha(D/'panel.jl')=='19dccf0d5259d730b19333b2b1c685a50ee76f93d2cc3b242cb54a762cae9295' and sha(D/'panel-tests.jl')=='15faee72f0f40bddae911818379c99d56aeb4a96e24cb7ce901691f188888910','exact shared-zero and typed module')
 ft=rd(D/'fault-transform.json');text=(D/'panel-fault.jl').read_text()
 for old,new in reversed(ft['edits']):ck(text.count(new)==1,'fault inverse anchor '+new);text=text.replace(new,old,1)
 ck(text.encode()==Path(ft['source']).read_bytes() and sha(ft['source'])==ft['source_sha256'] and sha(D/'panel-fault.jl')==ft['prepared_sha256'],'exact fault inverse')
 q=rd(D/'qualification-bindings.json');binding(q)
 for p in q['accepted_receipts']:
  v=rd(p);ck(v['accepted'] is True and v['findings']==[],'qualification accepted '+p);binding(v)
  if 'evidence_sha256' in v:binding(v,'evidence_sha256')
 expected=prepared|set(rt)|{str(root/n) for label,root in [('diagnostic',R),('production',W)] for n in base[label]}|{str(st/n) for n in stage['sha256']}|{str(RUN/'host.json'),str(RUN/'config.json'),str(O/'outer-ready.json')}
 ck(len(expected)==2220 and s['files']==sorted(expected),'2220 exact sealed files, no predecessor substitution')
 ck(s['trees']==[str(st),str(R/'diagnostics/direct-bg-blocked-update/reproduce'),str(probe),str(typed)] and s['inputs']==[],'exact four trees/no model input')
 ck(inventory(s['files'],s['trees'])==s['inventory'] and len(s['inventory'])==2220,'complete actual sealed bytes/resolutions/trees')
 wrapper='/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh'
 expectedcfg=dict(phase='red300',mode='red',seconds=300,expected_exit=1,stage=str(st),run=str(RUN),output=str(RUN/'output'),payload=str(RUN/'payload'),command=['/bin/bash',wrapper,'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--history-file=no','--project='+str(st),str(D/'driver.jl'),str(RUN/'payload'),str(st),'red300'])
 ck(cfg==s['config']==expectedcfg and s['phase']=='red300','exact RED300 command/config')
 full=set(rd(D/'historical-groups.json')['groups']);ck(len(full)==286 and s['groups']==host['groups']==sorted(full),'full 286 frozen PGID/SID roster')
 entry=rd(E/'entry-check.json');binding(entry);ck(entry['all_passed'] is True and entry['prepared_members']==586 and set(rd(E/'host-entry.json')['groups'])==full,'fresh root entry bound')
 ck(host['matches']==[] and host['unreadable_identity_pids']==[],'sealed host clean with visibility limit')
 oi=ready['identity'];ck(oi==s['outer_identity']==identity(209350) and oi['pid']==oi['pgid']==oi['sid']==209350 and oi['start_ticks']>0,'actual exact waiting outer PID/PGID/SID/boot/start/command')
 ck(ready['waiting_only'] is True and ready['phase']=='red300' and ready['script_sha256']==sha(D/'outer.py') and ready['expected_launcher']==str(D/'launch.py'),'outer metadata binding')
 ck({p.name for p in O.iterdir()}=={'outer-ready.json'} and {p.name for p in RUN.iterdir()}=={'sealed.json','host.json','config.json'},'no release/reservation/invocation/output/admission')
 env=rd(D/'environment.json');ck({k:os.environ.get(k) for k in env}==env,'actual exact loading environment')
 refs=dict(head=git('rev-parse','HEAD'),master=git('rev-parse','master'),production=git('rev-parse','HEAD',cwd=W),branch=git('branch','--show-current'),remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'))
 ck(refs['head']==HEAD==s['head']==host['head'] and refs['master']==refs['production']==MASTER==s['master']==host['master'],'actual local refs')
 ck(refs['branch']=='codex/simplex-core-architecture' and set(refs['remote'].splitlines())=={HEAD+'\trefs/heads/codex/simplex-core-architecture',MASTER+'\trefs/heads/master'},'actual origin refs')
 ck(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'clean tracked source')
 ck(BOOT==s['boot_id']==host['boot_id']==oi['boot_id'],'actual sealed boot')
 sites=rd(D/'assertion-sites.json');ck(len(sites)==168 and set(sites)=={f'P{k:03}' for k in range(1,103)}|{f'L{k:03}' for k in range(1,41)}|{f'N{k:03}' for k in range(1,27)},'168 exact source site universe')
 for name,v in sites.items():ck((D/v['file']).read_text().splitlines()[v['line']-1].strip()==v['source'] and name in v['source'],'source site '+name)
 driver=(D/'driver.jl').read_text();ck(driver.count('include("panel-tests.jl")')==1 and driver.index('include("lifecycle-tests.jl")')<driver.index('function main()') and not re.search(r'\b(eval|invokelatest)\s*\(',driver),'top-level single test composition')
 pc={f'P{k:03}':1 for k in range(1,103)}
 for k,n in [(1,5),(13,2),(15,4),(27,3),(66,2)]:pc[f'P{k:03}']=n
 for lo,hi,n in [(16,18,10),(19,20,5760),(21,26,10),(34,45,4),(62,64,3),(85,91,3)]:
  for k in range(lo,hi+1):pc[f'P{k:03}']=n
 ck(sum(pc.values())==11768,'panel independent 11768 exact counts')
 schedule=rd(D/'schedule.json');fixtures=tomllib.loads((R/'diagnostics/direct-bg-blocked-update/reproduce/fixtures.toml').read_text())['fixtures']
 ck(schedule['fixtures']==fixtures and schedule['units']==['panel','lifecycle']+[f['name']+'/'+b for f in fixtures for b in ['native','markowitz']],'exact fixture order and 28 units')
 ck(schedule['expected_red_units']==[n+'/'+b for n in ['dense96','dense256','dense96-long32'] for b in ['native','markowitz']],'exact six expected N026 units')
 loaded=dict(rd(D/'loaded-paths.json'),JSimplex=str(st/'src/JSimplex.jl'));syn=synthetic(schedule,loaded,pc)
 fresh=fresh_host(full,refs,env,oi);save(E/'admission-full286.json',fresh)
 ck(fresh['matches']==[] and fresh['unreadable_identity_pids']==[],'fresh full286 PGIDs AND SIDs absent/no visible Julia')
 mem=fresh['memory'];ck(mem['available_kib']>=6*1024**2 and mem['swap_used_kib']<=1024**2,'fresh RAM >=6GiB swap <=1GiB')
 ck(fresh['outer_identity']==oi and time.time()<ready['ready_time']+1200,'outer remains same within waiting deadline')
 ck(not (O/'release.json').exists() and {p.name for p in RUN.iterdir()}=={'sealed.json','host.json','config.json'},'still unreleased and unreserved')
 return dict(sealed_sha256=sha(RUN/'sealed.json'),sealed_files=len(s['files']),inventory_files=len(s['inventory']),preparation_subjects=581,preparation_review_bindings=582,prepared_members=586,runtime_files=609,stage_files=75,baseline_files={k:len(v) for k,v in base.items()},historical_groups=286,source_sites=168,panel_assertions=11768,expected_red_failures=6,synthetic=syn,full286_sha256=sha(E/'admission-full286.json'),memory=mem)
result={}
try:result=main();result['all_passed']=True
except Exception as e:result.update(all_passed=False,error=repr(e))
result.update(checks=checks,total=len(checks),passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks),script_sha256=sha(__file__),runtime_executed=False)
save(E/'admission-check.json',result)
print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))
raise SystemExit(0 if result['all_passed'] else 1)
