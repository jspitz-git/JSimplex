from pathlib import Path
import hashlib,json,os,subprocess,sys,time
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
D=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-P011-TYPED-HARNESS'
E=D.with_name('DIRECT-BG-P011-TYPED-RED'); run=D/'runs/p011-red300'; phase='p011-red300'
W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl')
HEAD='e2b2ad2ce70301693fe142f04e58b2252271393e';MASTER='26e2291745999f485a74f643298ca997d65c7205'
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def git(*args,root=R):return subprocess.check_output(['git',*args],cwd=root,text=True).strip()
checks=[]
def check(value,label):
 checks.append({'name':label,'passed':bool(value)})
 if not value:raise AssertionError(label)
def bind(mapping):return all(sha(Path(p) if Path(p).is_absolute() else R/p)==h for p,h in mapping.items())
def inventory(files,trees):
 paths=set(map(Path,files))
 for t in map(Path,trees):
  check(t.is_dir() and not t.is_symlink(),'inventory root '+str(t))
  for p in t.rglob('*'):
   check(not p.is_symlink(),'tree nonsymlink '+str(p))
   if p.is_file():paths.add(p)
 return {str(p):dict(resolved=str(p.resolve(strict=True)),sha256=sha(p)) for p in sorted(paths)}
result={'scope':'Independent exact P011 RED admission read-only checks','phase':phase,'started':time.time(),'checks':checks,'runtime_executed':False}
try:
 s=read(run/'sealed.json');cfg=read(run/'config.json');p=read(D/'preparation-pins.json');review=read(D/'review.json')
 check(set(p['sha256'])==set(read(D/'required-paths.json')['paths']) and len(p['sha256'])==258,'258 current preparation subjects exact membership')
 check(bind(p['sha256']),'current preparation subject hashes')
 check(review['accepted'] is True and review['findings']==[] and review['launch_admitted'] is False and review['scope']=='P011 typed harness preparation','final preparation review scope')
 check(set(review['sha256'])==set(p['sha256'])|{str(D/'preparation-pins.json')} and bind(review['sha256']) and bind(review['evidence_sha256']),'final preparation receipt bindings')
 check(review['pins_sha256']==sha(D/'preparation-pins.json'),'final preparation manifest hash')
 prep=set(p['sha256'])|{str(D/'preparation-pins.json'),str(D/'review.json')}|set(review['evidence_sha256'])
 baseline=read(D/'baseline.json');stage=read(D/'stages.json')['red'];runtime=read(D/'runtime-inputs-complete.json')['inventory']
 for label,root,count in [('diagnostic',R,514),('production',W,516)]:
  check(len(baseline[label])==count and set(git('ls-files','src','test','.github','Project.toml',root=root).splitlines())==set(baseline[label]),label+' baseline membership')
  check(all(sha(root/n)==h for n,h in baseline[label].items()),label+' baseline bytes')
 check(len(stage['sha256'])==75 and {str(p.relative_to(stage['path'])) for p in Path(stage['path']).rglob('*') if p.is_file()}==set(stage['sha256']),'75 stage exact membership')
 check(all(sha(Path(stage['path'])/n)==h for n,h in stage['sha256'].items()),'75 stage bytes')
 check(len(runtime)==609 and inventory(list(runtime),[])==runtime,'609 runtime resolved paths and bytes')
 expected=prep|set(runtime)|{str(root/n) for label,root in [('diagnostic',R),('production',W)] for n in baseline[label]}|{str(Path(stage['path'])/n) for n in stage['sha256']}|{str(run/'host.json'),str(run/'config.json'),str(D/'outers/p011-red300/outer-ready.json')}
 check(s['files']==sorted(expected) and len(expected)==1901,'1901 exact seal file membership')
 check(s['trees']==[stage['path'],str(R/'diagnostics/direct-bg-blocked-update/reproduce'),str(D.with_name('DIRECT-BG-ZERO-COUNTS-CANDIDATE')),str(D.with_name('DIRECT-BG-P011-TYPED-REPAIR'))] and s['inputs']==[],'four exact sealed trees and no numerical input')
 check(inventory(s['files'],s['trees'])==s['inventory'],'full sealed inventory independently rebuilt')
 sys.path.insert(0,str(D));import control as c
 c.validate_environment();check(True,'current exact loading environment')
 check(cfg==s['config']==c.config(phase) and s['phase']==phase and cfg['seconds']==300 and cfg['expected_exit']==1,'exact RED command/config and 300 second bound')
 check('--compiled-modules=existing' in cfg['command'] and '--threads=1' in cfg['command'] and '--gcthreads=1,0' in cfg['command'],'existing compiled modules and one thread')
 c.validate_stage_binding();c.validate_probe();c.validate_typed();check(True,'stage candidate and typed source provenance bindings')
 check(git('rev-parse','HEAD')==HEAD and git('rev-parse','master')==MASTER and git('rev-parse','HEAD',root=W)==MASTER,'fresh local diagnostic/master/production refs')
 remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture')
 check(set(remote.splitlines())=={HEAD+'\trefs/heads/codex/simplex-core-architecture',MASTER+'\trefs/heads/master'},'fresh exact remote refs')
 check(git('diff','--name-only')==git('diff','--cached','--name-only')=='','no diagnostic tracked changes')
 check(subprocess.run(['git','merge-base','--is-ancestor',c.ENTRY,'HEAD'],cwd=R).returncode==0,'published preparation ancestor')
 boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();ready=read(D/'outers/p011-red300/outer-ready.json');ident=ready['identity'];proc=Path('/proc')/str(ident['pid'])
 stat=(proc/'stat').read_text().rsplit(')',1)[1].split()
 current=dict(pid=ident['pid'],pgid=int(stat[2]),sid=int(stat[3]),start_ticks=int(stat[19]),boot_id=boot,command=(proc/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'))
 check(current==ident==s['outer_identity'] and current['pid']==current['pgid']==current['sid'] and current['start_ticks']>0,'live exact outer pid/session/command/start_ticks/boot')
 check(ready['waiting_only'] is True and ready['phase']==phase and ready['script_sha256']==sha(D/'outer.py') and ready['expected_launcher']==str(D/'launch.py'),'waiting-only outer ready script binding')
 check(s['head']==HEAD and s['master']==MASTER and s['boot_id']==boot,'seal fresh refs and boot')
 groups=set(read(D/'historical-groups.json')['groups']);matches=[];unreadable=[];identity_unreadable=[]
 for q in Path('/proc').glob('[0-9]*'):
  try:
   fields=(q/'stat').read_text().rsplit(')',1)[1].split();comm=(q/'comm').read_text().strip();argv0=(q/'cmdline').read_bytes().split(b'\0')[0].decode(errors='replace');exe=''
   try:exe=str((q/'exe').resolve(strict=True))
   except PermissionError:unreadable.append(int(q.name))
   except FileNotFoundError:pass
   if int(fields[2]) in groups or int(fields[3]) in groups or any(Path(z).name.lower().startswith('julia') for z in (comm,argv0,exe)):matches.append(dict(pid=int(q.name),pgid=int(fields[2]),sid=int(fields[3]),comm=comm,argv0=argv0,exe=exe))
  except (FileNotFoundError,ProcessLookupError):pass
  except PermissionError:identity_unreadable.append(int(q.name))
 mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()}
 host=dict(time=time.time(),groups=sorted(groups),matches=matches,unreadable_exe_pids=unreadable,unreadable_identity_pids=identity_unreadable,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree'],remote=remote,head=HEAD,master=MASTER,boot_id=boot,outer_identity=current,scope='All historical groups AND sessions plus comm/argv0/readable executable names. Inaccessible executable symlinks remain a visibility limit.')
 result['host']=host
 check(len(groups)==280 and groups==set(s['groups']) and matches==[] and identity_unreadable==[],'fresh all 280 groups AND sessions absent and no visible Julia')
 check(host['available_kib']>=6*1024**2 and host['swap_used_kib']<=1024**2,'fresh RAM/swap thresholds')
 for prior in [read(run/'host.json'),read(E/'host-entry.json')]:
  check(prior['head']==HEAD and prior['master']==MASTER and prior['boot_id']==boot and set(prior['groups'])==groups and prior['matches']==[] and prior['unreadable_identity_pids']==[],'entry/sealed host consistency')
 check({x.name for x in run.iterdir()}=={'config.json','host.json','sealed.json'},'no reservation/output/payload/admission before review')
 check({x.name for x in (D/'outers/p011-red300').iterdir()}=={'outer-ready.json'},'no release/invocation/outcome')
 check(not (D/'runs/p011-green300').exists() and not (D/'outers/p011-green300').exists(),'GREEN remains unprepared for execution')
 import oracle
 check(len(oracle.RED_FAILURE_DETAIL)==439 and '208' not in oracle.RED_FAILURE_DETAIL,'exact 439-character P011 rendering without byte amount')
 check(sum(oracle.panel_counts(phase).values())==11760,'source oracle RED 11760 assertions')
 result.update(all_passed=True,findings=[],sealed_sha256=sha(run/'sealed.json'),counts=dict(preparation=len(p['sha256']),preparation_receipt=len(review['sha256']),prepared=len(prep),runtime=len(runtime),diagnostic_baseline=514,production_baseline=516,stage=75,sealed=len(expected),sealed_inventory=len(s['inventory'])))
except Exception as error:
 result.update(all_passed=False,findings=[repr(error)])
result['finished']=time.time()
with (E/'admission-review-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('checks','host')},indent=2));print('checks',len(checks));print(json.dumps(result.get('host',{}),indent=2))
if not result['all_passed']:sys.exit(1)
