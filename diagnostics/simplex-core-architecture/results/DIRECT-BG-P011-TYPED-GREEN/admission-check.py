"""New independent read-only admission checks. No harness imports or Julia execution."""
from pathlib import Path
import hashlib,json,os,subprocess,time,re,tomllib
E=Path(__file__).resolve().parent; D=E.with_name('DIRECT-BG-P011-TYPED-HARNESS'); R=D.parents[3]
W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl')
RUN=D/'runs/p011-green300'; RED=D/'runs/p011-red300'; O=D/'outers/p011-green300'
HEAD='a01d1cde19feb72ee0b6396981281cabf5bd9672'; MASTER='26e2291745999f485a74f643298ca997d65c7205'
checks=[]; hashes={}
def rd(p):return json.loads(Path(p).read_text())
def sha(p):
 p=Path(p); h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def ck(v,n):
 checks.append(dict(name=n,passed=bool(v)))
 if not v:raise AssertionError(n)
def save(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')
def bind(j,key='sha256'):
 for n,h in j[key].items():
  p=Path(n) if Path(n).is_absolute() else R/n
  ck(sha(p)==h,'binding '+str(p))
def git(*a,cwd=R):return subprocess.check_output(['git',*a],cwd=cwd,text=True).strip()
def inventory(files,trees):
 paths={Path(n) for n in files}
 for n in trees:
  root=Path(n);ck(root.is_dir() and not root.is_symlink(),'tree root '+n)
  entries=list(root.rglob('*'));ck(not any(p.is_symlink() for p in entries),'tree no symlinks '+n)
  paths.update(p for p in entries if p.is_file())
 return {str(p):dict(resolved=str(p.resolve(strict=True)),sha256=sha(p)) for p in sorted(paths)}
def identity(pid):
 p=Path('/proc')/str(pid); f=(p/'stat').read_text().rsplit(')',1)[1].split()
 return dict(pid=pid,pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'))
def main():
 s=rd(RUN/'sealed.json');cfg=rd(RUN/'config.json');ready=rd(O/'outer-ready.json');host=rd(RUN/'host.json')
 prep=rd(D/'preparation-pins.json');pr=rd(D/'review.json');stage=rd(D/'stages.json')['red'];runtime=rd(D/'runtime-inputs-complete.json')['inventory'];baseline=rd(D/'baseline.json')
 ck(pr['accepted'] is True and pr['findings']==[] and pr['scope']=='P011 typed harness preparation' and pr['launch_admitted'] is False,'preparation accepted offline')
 ck(pr['pins_sha256']==sha(D/'preparation-pins.json'),'preparation manifest identity')
 ck(set(prep['sha256'])==set(rd(D/'required-paths.json')['paths']),'exact preparation subjects')
 ck(set(pr['sha256'])==set(prep['sha256'])|{str(D/'preparation-pins.json')},'exact preparation review membership')
 bind(prep);bind(pr);bind(pr,'evidence_sha256')
 ck(len(prep['sha256'])==258 and len(runtime)==609,'preparation and runtime counts')
 ck(inventory(runtime,[])==runtime,'fresh 609 runtime/resolved bindings')
 for label,root in [('diagnostic',R),('production',W)]:
  ck(set(git('ls-files','src','test','.github','Project.toml',cwd=root).splitlines())==set(baseline[label]),label+' baseline membership')
  for n,h in baseline[label].items():ck(sha(root/n)==h,label+' baseline '+n)
 ck(len(stage['sha256'])==75,'stage 75')
 stroot=Path(stage['path']);ck({str(p.relative_to(stroot)) for p in stroot.rglob('*') if p.is_file()}==set(stage['sha256']),'exact stage membership')
 for n,h in stage['sha256'].items():ck(sha(stroot/n)==h,'stage '+n)
 for n,j in rd(D/'copied-files.json').items():ck(sha(D/n)==sha(j['source'])==j['sha256'],'copied frozen '+n)
 for dirname,name in [('DIRECT-BG-BLOCKED-UPDATE-STAGE-REPAIR','stage.json'),('DIRECT-BG-BLOCKED-UPDATE-STAGE-REPAIR','review.json'),('DIRECT-BG-BLOCKED-UPDATE-STAGE-REPAIR','publication.json'),('DIRECT-BG-ZERO-COUNTS-CANDIDATE','review.json')]:bind(rd(D.with_name(dirname)/name))
 typed=D.with_name('DIRECT-BG-P011-TYPED-REPAIR');tv=rd(typed/'independent-review.json');bind(tv,'reviewed_bindings')
 ck(tv['findings']==[] and tv['runtime_executed'] is False and tv['disposition']=='ACCEPTED — PREPARATION ONLY' and tv['review_markdown_sha256']==sha(typed/'independent-review.md'),'typed independent preparation')
 ck(sha(typed/'panel-tests.jl')=='15faee72f0f40bddae911818379c99d56aeb4a96e24cb7ce901691f188888910','exact repaired tests')
 ck(sha(D.with_name('DIRECT-BG-ZERO-COUNTS-CANDIDATE')/'panel.jl')=='19dccf0d5259d730b19333b2b1c685a50ee76f93d2cc3b242cb54a762cae9295','same immutable-zero candidate')
 rr=rd(RED/'result-review.json');audit=rd(RED/'audit.json');closure=rd(RED/'outer-closure.json');rs=rd(RED/'sealed.json');post=rd(RED/'posthost.json')
 redfiles={str(p) for p in RED.rglob('*') if p.is_file() and p.name!='result-review.json'}
 ck(len(redfiles)==26 and set(rr['sha256'])==redfiles,'RED exact 26-file review membership')
 ck(rr['accepted'] is True and rr['findings']==[] and rr['scope']=='P011 typed RED result' and rr['phase']=='p011-red300','RED independent acceptance')
 bind(rr);bind(rr,'evidence_sha256');bind(audit);bind(closure)
 ck(audit['all_passed'] is True and audit['phase']=='p011-red300' and audit['result']['totals']==[11759,1,0,0],'RED exact accepted audit')
 redouter=D/'outers/p011-red300';closurepaths={str(redouter/n) for n in ['outer-ready.json','release.json','outer-invocation.json','outer-outcome.json']}|{str(RED/n) for n in ['sealed.json','admission.json','posthost.json','audit.json']}
 ck(set(closure['sha256'])==closurepaths and closure['all_passed'] is True,'RED exact closure membership')
 ri=rd(redouter/'outer-ready.json')['identity'];ch=closure['host']
 ck(closure['outer_identity']==ri==rs['outer_identity'] and ri['pid']==ri['pgid']==ri['sid']==200591,'RED outer identity')
 ck(ch['matches']==[] and ch['unreadable_identity_pids']==[] and all(ch[k]==rs[k]==post[k] for k in ['head','master','boot_id']),'RED saved closure host')
 full=set(ch['groups']);ck(len(full)==283 and {200591,201265,201266}<=full and set(rs['groups'])|set(post['groups'])|{ri['pgid'],ri['sid']}<=full,'full283 predecessor coverage')
 ck(set(rd(E/'host-entry.json')['groups'])==full and rd(E/'entry-check.json')['all_passed'] is True,'entry full283 coverage')
 prepared=set(prep['sha256'])|{str(D/'preparation-pins.json'),str(D/'review.json')}|set(pr['evidence_sha256'])
 predecessors=redfiles|{str(RED/'result-review.json')}|closurepaths
 expected=prepared|set(runtime)|{str(root/n) for label,root in [('diagnostic',R),('production',W)] for n in baseline[label]}|{str(stroot/n) for n in stage['sha256']}|predecessors|{str(RUN/'host.json'),str(RUN/'config.json'),str(O/'outer-ready.json')}
 ck(len(predecessors)==31 and s['files']==sorted(expected),'exact 1932-file seal membership')
 ck(s['trees']==[str(stroot),str(R/'diagnostics/direct-bg-blocked-update/reproduce'),str(D.with_name('DIRECT-BG-ZERO-COUNTS-CANDIDATE')),str(typed)] and s['inputs']==[],'exact four trees and no numerical input')
 ck(inventory(s['files'],s['trees'])==s['inventory'],'fresh complete sealed inventory')
 wrapper='/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh'
 expectedcfg=dict(phase='p011-green300',mode='red',seconds=300,expected_exit=0,stage=str(stroot),run=str(RUN),output=str(RUN/'output'),payload=str(RUN/'payload'),command=['/bin/bash',wrapper,'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--history-file=no','--project='+str(stroot),str(D/'driver.jl'),str(RUN/'payload'),str(stroot),'p011-green300'])
 ck(cfg==s['config']==expectedcfg and s['phase']=='p011-green300','exact GREEN command/config')
 ck(s['groups']==host['groups']==post['groups'] and set(s['groups'])==full-{200591},'documented frozen 282-group coverage')
 ck(ready['waiting_only'] is True and ready['phase']==s['phase'] and ready['script_sha256']==sha(D/'outer.py') and ready['expected_launcher']==str(D/'launch.py'),'waiting outer metadata')
 ck(ready['identity']==s['outer_identity']==identity(ready['identity']['pid']),'live exact outer command/start/boot identity')
 oi=ready['identity'];ck(oi['pid']==oi['pgid']==oi['sid'] and oi['start_ticks']>0,'outer own group/session')
 ck({p.name for p in O.iterdir()}=={'outer-ready.json'} and {p.name for p in RUN.iterdir()}=={'sealed.json','host.json','config.json'},'unreleased/unreserved fresh attempt')
 env=rd(D/'environment.json');ck({k:os.environ.get(k) for k in env}==env,'exact loading environment')
 refs=dict(head=git('rev-parse','HEAD'),master=git('rev-parse','master'),production=git('rev-parse','HEAD',cwd=W),remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'),branch=git('branch','--show-current'))
 ck(refs['head']==HEAD==s['head']==host['head'] and refs['master']==refs['production']==MASTER==s['master']==host['master'],'fresh local refs')
 ck(set(refs['remote'].splitlines())=={HEAD+'\trefs/heads/codex/simplex-core-architecture',MASTER+'\trefs/heads/master'} and refs['branch']=='codex/simplex-core-architecture','fresh remote refs/branch')
 ck(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'no tracked changes')
 boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();ck(boot==s['boot_id']==host['boot_id']==oi['boot_id']==ch['boot_id'],'current boot')
 matches=[];unreadable=[];unreadableid=[];scanned=0
 for p in Path('/proc').glob('[0-9]*'):
  try:
   f=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip();argv0=(p/'cmdline').read_bytes().split(b'\0',1)[0].decode(errors='replace');exe='';scanned+=1
   try:exe=str((p/'exe').resolve(strict=True))
   except PermissionError:unreadable.append(int(p.name))
   except FileNotFoundError:pass
   if int(f[2]) in full or int(f[3]) in full or any(Path(x).name.lower().startswith('julia') for x in (comm,argv0,exe)):matches.append(dict(identity(int(p.name)),comm=comm,argv0=argv0,exe=exe))
  except (FileNotFoundError,ProcessLookupError):pass
  except PermissionError:unreadableid.append(int(p.name))
 mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()};memory=dict(available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree'])
 fresh=dict(time=time.time(),groups=sorted(full),matches=matches,unreadable_exe_pids=unreadable,unreadable_identity_pids=unreadableid,processes_scanned=scanned,boot_id=boot,refs=refs,memory=memory,outer_identity=identity(oi['pid']),environment=env,source_closure_sha256=sha(RED/'outer-closure.json'),scope='Independent full283 PGID AND SID scan plus comm/argv0/readable executable Julia detection; inaccessible executable links remain a visibility limit')
 save(E/'admission-full283.json',fresh)
 ck(not matches and not unreadableid,'fresh full283 closure and no visible Julia')
 ck(memory['available_kib']>=6*1024**2 and memory['swap_used_kib']<=1024**2,'fresh resource thresholds')
 ck(fresh['outer_identity']==oi and time.time()<ready['ready_time']+1200,'outer still waiting within admission deadline')
 counts={f'P{i:03}':1 for i in range(1,103)}
 for i,n in [(1,5),(13,2),(15,4),(27,3),(66,2)]:counts[f'P{i:03}']=n
 for lo,hi,n in [(16,18,10),(19,20,5760),(21,26,10),(34,45,4),(62,64,3),(85,91,3)]:
  for i in range(lo,hi+1):counts[f'P{i:03}']=n
 totals=[sum(counts[f'P{i:03}'] for i in range(lo,hi+1)) for lo,hi in [(1,15),(16,33),(34,65),(66,94)]];totals[0]+=8
 ck(totals==[31,11619,74,44] and sum(totals)==11768,'independent GREEN expected occurrence totals')
 ck(set(re.findall(r'@check(?:throws)? "(P[0-9]+)"',(typed/'panel-tests.jl').read_text()))==set(counts),'repaired exact P001-P102 source sites')
 return dict(sealed_sha256=sha(RUN/'sealed.json'),sealed_files=len(s['files']),inventory_files=len(s['inventory']),preparation_subjects=len(prep['sha256']),runtime_files=len(runtime),stage_files=len(stage['sha256']),baseline_files={k:len(v) for k,v in baseline.items()},predecessor_files=len(predecessors),historical_groups=len(full),frozen_groups=len(s['groups']),green_expected_counts=counts,green_expected_groups=totals,full283_sha256=sha(E/'admission-full283.json'),memory=memory)
result={}
try:result=main();result['all_passed']=True
except Exception as e:result.update(all_passed=False,error=repr(e))
result.update(checks=checks,total=len(checks),passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks),script_sha256=sha(__file__),runtime_executed=False)
save(E/'admission-check.json',result)
print(json.dumps({k:v for k,v in result.items() if k not in ('checks','green_expected_counts')},indent=2))
raise SystemExit(0 if result['all_passed'] else 1)
