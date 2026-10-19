"""Fresh independent exact-run admission; stdlib only, no numerical entrypoint or prior checker."""
from pathlib import Path
import os,sys,json,hashlib,time,subprocess,importlib.util,copy,math
sys.dont_write_bytecode=True
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
D=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-TYPED-RED1800-HARNESS'
E=D.with_name('DIRECT-BG-BLOCKED-UPDATE-TYPED-RED1800');RUN=D/'runs/red1800';O=D/'outers/red1800'
W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl')
HEAD='cc9d35dc3e2c526bcae8b752ca2ea43dad9a5212';MASTER='26e2291745999f485a74f643298ca997d65c7205'
checks=[]
def ck(v,n):
 checks.append({'name':n,'passed':bool(v)})
 if not v:raise AssertionError(n)
def rd(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def query(root,*args):return subprocess.check_output(['git',*args],cwd=root,text=True).strip()
def hashed(m,label):
 for n,h in m.items():ck(sha(n)==h,label+': '+n)
def refuse(fn,label):
 try:fn()
 except (ValueError,RuntimeError,AssertionError,KeyError,TypeError):ck(True,label);return
 ck(False,label)
def load(name):
 spec=importlib.util.spec_from_file_location(name,D/(name+'.py'));m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
s=rd(RUN/'sealed.json');cfg=rd(RUN/'config.json');pr=rd(D/'review.json');pp=rd(D/'preparation-pins.json');base=rd(D/'baseline.json');rt=rd(D/'runtime-inputs-complete.json')['inventory'];st=rd(D/'stages.json');prior=rd(D/'timeout-bindings.json')
ck(pr['accepted'] is True and pr['findings']==[] and pr['launch_admitted'] is False and pr['scope']=='BG blocked typed RED repeat preparation','qualified preparation only')
ck(len(pp['sha256'])==711 and set(pp['sha256'])==set(rd(D/'required-paths.json')['paths']),'711 preparation required subjects')
ck(pr['pins_sha256']==sha(D/'preparation-pins.json') and pr['sha256']==dict(pp['sha256'],**{str(D/'preparation-pins.json'):sha(D/'preparation-pins.json')}),'712 exact preparation receipt')
hashed(pr['sha256'],'preparation');hashed(pr['evidence_sha256'],'preparation evidence')
prepared=set(pp['sha256'])|{str(D/'preparation-pins.json'),str(D/'review.json')}|set(pr['evidence_sha256'])
expected=prepared|set(rt)|set(prior['sha256'])|{str(root/n) for label,root in [('diagnostic',R),('production',W)] for n in base[label]}|{str(Path(st['red']['path'])/n) for n in st['red']['sha256']}|{str(RUN/'host.json'),str(RUN/'config.json'),str(O/'outer-ready.json')}
ck(s['files']==sorted(expected) and len(expected)==2352,'independently reconstructed 2352 exact sealed subjects')
trees=[st['red']['path'],str(R/'diagnostics/direct-bg-blocked-update/reproduce'),str(D.with_name('DIRECT-BG-ZERO-COUNTS-CANDIDATE')),str(D.with_name('DIRECT-BG-P011-TYPED-REPAIR'))]
ck(s['trees']==trees and s['inputs']==[],'exact four trees/no inputs')
paths=set(expected)
for t in trees:
 root=Path(t);ck(root.is_dir() and not root.is_symlink(),'tree root '+t)
 for p in root.rglob('*'):
  ck(not(p.is_symlink() and (p.is_dir() or not p.exists())),'tree link '+str(p))
  if p.is_file():paths.add(str(p))
ck(paths==set(s['inventory']),'inventory exact membership including tree traversal')
for n in sorted(paths):
 ck(s['inventory'][n]=={'resolved':str(Path(n).resolve(strict=True)),'sha256':sha(n)},'live inventory '+n)
ck(len(rt)==609 and all(s['inventory'][n]==v for n,v in rt.items()),'609 exact runtime resolved bindings')
for label,root in [('diagnostic',R),('production',W)]:
 ck(set(query(root,'ls-files','src','test','.github','Project.toml').splitlines())==set(base[label]),'tracked baseline membership '+label)
 ck(all(s['inventory'][str(root/n)]['sha256']==h for n,h in base[label].items()),'baseline hashes '+label)
ck(sum(map(len,base.values()))==1030,'1030 baseline files')
root=Path(st['red']['path'])
ck(set(str(p.relative_to(root)) for p in root.rglob('*') if p.is_file())==set(st['red']['sha256']),'exact stage membership')
ck(not any(p.is_symlink() for p in root.rglob('*')) and all(s['inventory'][str(root/n)]['sha256']==h for n,h in st['red']['sha256'].items()),'stage hashes and no symlinks')
for name,item in rd(D/'copied-files.json').items():ck(sha(D/name)==sha(item['source'])==item['sha256'],'byte copy '+name)
ck(len(rd(D/'copied-files.json'))==22,'22 frozen copies')
for name,item in rd(D/'control-transform.json').items():
 text=(D/name).read_text();append=item.get('append','')
 if append:ck(text.endswith(append),'append '+name);text=text[:-len(append)]
 for edit in reversed(item['edits']):
  ck(text.count(edit['new'])==edit['count'],'inverse anchors '+name);text=text.replace(edit['new'],edit['old'])
 ck(text.encode()==Path(item['source']).read_bytes() and sha(D/name)==item['prepared_sha256'] and sha(item['source'])==item['source_sha256'],'exact inverse '+name)
hashed(prior['sha256'],'prior evidence');old=rd(prior['audit']);oldreview=rd(prior['review'])
ck(len(prior['sha256'])==81 and old['all_passed'] is False and old['pure_timeout'] is False and oldreview['accepted'] is True and oldreview['qualification_accepted'] is False,'81 frozen prior bindings; failed prefix remains unqualified')
ck(not (Path(prior['run'])/'result-review.json').exists(),'no retroactive prior acceptance')
for n,count in [('tests.json',2378),('independent-preparation-check.json',1067),('independent-boundary-check.json',1136)]:
 j=rd(D/n);ck(j['all_passed'] is True and j['count']==count,'reuse qualified saved '+n)
 hashed(j.get('sha256',{}),'saved checker binding '+n)
j=rd(D/'source-check.json');ck(j['all_passed'] is True and len(j['checks'])==51,'reuse 51 saved source checks');hashed(j['sha256'],'saved source check binding')
ck(s['head']==HEAD and s['master']==MASTER and query(R,'rev-parse','HEAD')==HEAD and query(R,'rev-parse','master')==MASTER and query(W,'rev-parse','HEAD')==MASTER,'live local refs')
remote=query(R,'ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture')
ck(set(remote.splitlines())=={HEAD+'\trefs/heads/codex/simplex-core-architecture',MASTER+'\trefs/heads/master'},'fresh remote refs')
ck(not query(R,'diff','--name-only') and not query(R,'diff','--cached','--name-only'),'tracked clean')
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();ck(boot==s['boot_id']=='1ecae454-f1f5-4e2e-a95c-7b5474243126','actual boot')
ready=rd(O/'outer-ready.json');ident=ready['identity'];hist=rd(D/'historical-groups.json')['groups']
ck(len(hist)==289 and hist==s['groups'] and set(hist)==set(rd(prior['closure'])['host']['groups']) and {209350,210015,210016}<=set(hist),'289 historical PGIDs AND SIDs')
processes=[];matches=[];outermembers=[];unreadexe=[];unreadid=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  f=(p/'stat').read_text().rsplit(')',1)[1].split();cmd=(p/'cmdline').read_bytes();comm=(p/'comm').read_text().strip();exe=''
  try:exe=str((p/'exe').resolve(strict=True))
  except PermissionError:unreadexe.append(int(p.name))
  except FileNotFoundError:pass
  row=dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),boot_id=boot,command=cmd.replace(b'\0',b' ').decode(errors='replace'))
  processes.append(dict(row,comm=comm,argv0=cmd.split(b'\0')[0].decode(errors='replace'),exe=exe))
  if row['pgid'] in hist or row['sid'] in hist or any(Path(v).name.lower().startswith('julia') for v in [comm,cmd.split(b'\0')[0].decode(errors='replace'),exe]):matches.append(row)
  if row['pgid']==ident['pgid'] or row['sid']==ident['sid']:outermembers.append(row)
 except (FileNotFoundError,ProcessLookupError):pass
 except PermissionError:unreadid.append(int(p.name))
ck(matches==[] and unreadid==[],'no historical PGID/SID or visible Julia; all identities readable')
ck(outermembers==[ident] and ident==s['outer_identity'] and ident['pid']==ident['pgid']==ident['sid']==214974 and ident['start_ticks']==14546623,'waiting outer sole isolated process exact live identity')
ck(ready['waiting_only'] is True and ready['phase']=='red1800' and ready['script_sha256']==sha(D/'outer.py') and ready['expected_launcher']==str(D/'launch.py'),'waiting ready record')
ck(set(p.name for p in O.iterdir())=={'outer-ready.json'} and set(p.name for p in RUN.iterdir())=={'sealed.json','host.json','config.json'},'no release invocation reservation payload or admission')
env=rd(D/'environment.json');actual={k:os.environ.get(k) for k in env};reviewer_environment_differences={k:dict(expected=v,actual=actual[k]) for k,v in env.items() if actual[k]!=v}
# Actual executing outer environment below is authoritative; reviewer login PATH is metadata only.
outerenv=dict(x.split(b'=',1) for x in Path('/proc/214974/environ').read_bytes().split(b'\0') if b'=' in x)
ck({k:outerenv.get(k.encode(),b'').decode() if k.encode() in outerenv else None for k in env}==env,'waiting outer loading environment exact')
ck(str(Path('/proc/214974/cwd').resolve())==str(R),'waiting outer cwd')
mem={ln.split(':')[0]:int(ln.split()[1]) for ln in Path('/proc/meminfo').read_text().splitlines()};memory={'available_kib':mem['MemAvailable'],'swap_used_kib':mem['SwapTotal']-mem['SwapFree']}
ck(memory['available_kib']>=6*1024**2 and memory['swap_used_kib']<=1024**2,'actual resources')
# Definitions-only modules; no main, audit/checker entrypoint, numerical operation, or launch.
sys.path.insert(0,str(D));c=load('control');oracle=load('oracle');audit=load('audit');outer=load('outer')
ck(cfg==s['config']==c.config('red1800') and cfg['seconds']==1800 and cfg['expected_exit']==1 and cfg['command'][-1]=='red300','exact command external phase and budgets')
for bad in ['red300','green300','green1800','red1800x']:refuse(lambda:c.config(bad),'reject unprepared '+bad)
command=c.guard_command(cfg,RUN/'launch-pins.json',123.0)
ck(command[command.index('--seconds')+1]=='1792' and command[command.index('--deadline')+1]=='1915.0' and command[-len(cfg['command']):]==cfg['command'],'1792 guard and absolute deadline command')
schedule=rd(D/'schedule.json');sites=rd(D/'assertion-sites.json')
ck(len(schedule['units'])==28 and len(sites)==168 and set(sites)=={f'{prefix}{i:03d}' for prefix,n in [('P',102),('L',40),('N',26)] for i in range(1,n+1)},'28 units 168 exact sites')
ck(schedule['expected_red_units']==[f'{a}/{b}' for a in ['dense96','dense256','dense96-long32'] for b in ['native','markowitz']],'exact six N026 units')
ck(sum(oracle.panel_counts().values())==11768 and all(oracle.panel_counts()[k]==1 for k in ['P011']+[f'P{i:03d}' for i in range(95,103)]),'11768 panel assertions incl typed P011 and P095-P102')
ck(len(oracle.PAYLOAD)==60 and len(oracle.PREPARATION)==31,'60 payload 31 cost files')
metric={'seconds':1800,'bytes':0,'events':0,'gc_seconds':0,'compile_seconds':0,'recompile_seconds':0};ck(oracle.metrics(metric)==metric,'inclusive 1800 cost boundary')
for bad in [1800.000001,-1,float('inf'),float('nan'),True,'1800']:refuse(lambda:oracle.metrics(dict(metric,seconds=bad)),'cost rejection '+repr(bad))
sample={'elapsed':1792,'available_kib':6*1024**2,'swap_used_kib':1024**2};terminal={k:v for k,v in sample.items() if k!='elapsed'}
ck(audit.resource_records([sample],terminal,1792),'inclusive child/resource 1792 boundary')
for bad in [1792.000001,-1,float('inf'),True]:refuse(lambda:audit.resource_records([sample],terminal,bad),'resource elapsed rejection '+repr(bad))
for bad in [dict(sample,available_kib=6*1024**2-1),dict(sample,swap_used_kib=1024**2+1),dict(sample,elapsed=1792.000001)]:refuse(lambda:audit.resource_records([bad],terminal,1792),'resource pressure/order refusal '+repr(bad))
refuse(lambda:oracle.validate({},schedule,{},'red300'),'reject empty prefix')
release=dict(phase='red1800',sealed_sha256='s',admission_sha256='a',outer_ready_sha256='o',one_attempt=True)
ck(outer.valid_release(release,'s','a','o','red1800'),'strict exact release schema')
for k,v in [('phase','red300'),('one_attempt',1),('sealed_sha256','wrong'),('extra',True)]:ck(not outer.valid_release(dict(release,**{k:v}),'s','a','o','red1800'),'release reject '+k)
receipt=dict(accepted=True,findings=[],scope='BG blocked typed RED repeat exact-run admission',phase='red1800',pins_sha256=sha(RUN/'sealed.json'),sha256={n:s['inventory'][n]['sha256'] for n in s['files']})
receipt['sha256'][str(RUN/'sealed.json')]=sha(RUN/'sealed.json')
# Boundary calls reuse saved known hashes to avoid repeatedly rehashing gigabytes.
orig_bindings=c.bindings;c.bindings=lambda v,key='sha256': v[key]==receipt[key]
c.verify_review(receipt,RUN/'sealed.json',s['files']+[str(RUN/'sealed.json')],receipt['scope'],'red1800');ck(True,'exact receipt schema accepted with already independently verified hashes')
for k,v in [('accepted',1),('phase','red300'),('scope','BG blocked typed exact-run admission'),('pins_sha256','wrong')]:
 bad=copy.deepcopy(receipt);bad[k]=v;refuse(lambda:c.verify_review(bad,RUN/'sealed.json',s['files']+[str(RUN/'sealed.json')],receipt['scope'],'red1800'),'receipt reject '+k)
bad=copy.deepcopy(receipt);bad['sha256'].pop(str(RUN/'sealed.json'));refuse(lambda:c.verify_review(bad,RUN/'sealed.json',s['files']+[str(RUN/'sealed.json')],receipt['scope'],'red1800'),'receipt rejects absent seal')
c.bindings=orig_bindings
result=dict(all_passed=True,count=len(checks),checks=checks,sealed_sha256=sha(RUN/'sealed.json'),sealed_subjects=len(expected),receipt_subjects=len(expected)+1,runtime_entries=len(rt),baseline_files=1030,stage_files=len(st['red']['sha256']),historical_groups=len(hist),host=dict(reviewer_environment_differences=reviewer_environment_differences,time=time.time(),boot_id=boot,head=HEAD,master=MASTER,remote=remote,memory=memory,matches=matches,outer_members=outermembers,unreadable_exe_pids=unreadexe,unreadable_identity_pids=unreadid,processes=processes,scope='All live stat/comm/argv0 and accessible exe checked; inaccessible exe links explicitly limit universal executable identity claims'),runtime_executed=False,scope='Fresh independent exact-run admission checks; no old checker or numerical execution; synthetic receipt hash predicate uses already independently verified hashes')
with (E/'independent-admission-check-v2.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['checks','host']},indent=2));print('resources',memory,'exe_visibility_limit',len(unreadexe))
