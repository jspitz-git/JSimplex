from pathlib import Path
import sys, os, json, hashlib, subprocess, time
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
D=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-P011-HARNESS'
RUN=D/'runs/p011-300'; O=D/'outers/p011-300'; SP=RUN/'sealed.json'
sys.path.insert(0,str(D))
import control as c

def h(p):
 q=hashlib.sha256()
 with Path(p).open('rb') as f:
  for x in iter(lambda:f.read(1024*1024),b''):q.update(x)
 return q.hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def git(*a,root=R):return subprocess.check_output(['git',*a],cwd=root,text=True).strip()
def require(v,m):
 if not v:raise RuntimeError(m)
s=rd(SP); cfg=c.config('p011-300'); start=time.time()
require(s['head']=='11ebe6bdd401084205ebe628d35539ebb2d5e8ae','exact HEAD')
require(s['master']=='26e2291745999f485a74f643298ca997d65c7205','exact master')
require(s['phase']=='p011-300' and s['config']==cfg==rd(RUN/'config.json'),'exact config')
require(len(cfg['command'])==11 and cfg['command'][-2:]==[cfg['payload'],cfg['stage']],'exact two driver args')
c.validate_environment(); prepared=c.preparation()
expected=c.seal_files(cfg,prepared,[])
require(expected==s['files'] and len(expected)==len(set(expected)),'exact file membership')
require(s['trees']==[cfg['stage'],str(c.C),str(c.PROBE)] and s['inputs']==[],'exact trees/no LP inputs')
paths=set(s['files']); tree_counts={}
for t in s['trees']:
 root=Path(t); require(root.is_dir() and not root.is_symlink(),'tree root')
 members=[]
 for p in root.rglob('*'):
  require(not p.is_symlink(),'no tree symlinks')
  if p.is_file(): members.append(str(p));paths.add(str(p))
 tree_counts[t]=len(members)
require(paths==set(s['inventory']),'exact inventory membership')
actual={}; byte_count=0
for p in sorted(paths):
 path=Path(p); actual[p]={'resolved':str(path.resolve(strict=True)),'sha256':h(path)};byte_count+=path.stat().st_size
require(actual==s['inventory'],'all current hashes/resolved paths')
require(h(c.PROBE/'driver.jl')=='29c8d67755e4f86a7375f89536d24a0cb119a06a583650bc3f31bc9eccc956bf','frozen driver')
base=rd(D/'baseline.json'); stage=rd(D/'stages.json')['red'];runtime=rd(D/'runtime-inputs-complete.json')['inventory']
for label,root in [('diagnostic',R),('production',c.W)]:
 require(set(git('ls-files','src','test','.github','Project.toml',root=root).splitlines())==set(base[label]),'baseline tracked membership '+label)
 require(all(actual[str(root/n)]['sha256']==sha for n,sha in base[label].items()),'baseline hashes '+label)
require(set(stage['sha256'])=={str(p.relative_to(Path(cfg['stage']))) for p in Path(cfg['stage']).rglob('*') if p.is_file()},'stage file set')
require(all(actual[str(Path(cfg['stage'])/n)]['sha256']==sha for n,sha in stage['sha256'].items()),'stage hashes')
require(all(actual[n]==v for n,v in runtime.items()),'runtime609 fresh resolved/hash')
require(git('rev-parse','HEAD')==s['head'] and git('rev-parse','master')==s['master']==git('rev-parse','HEAD',root=c.W),'current refs')
require(subprocess.run(['git','merge-base','--is-ancestor',c.ENTRY,'HEAD'],cwd=R).returncode==0,'diagnostic ancestry')
require(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'tracked/index clean')
outer=c.verify_outer('p011-300',s,live=True)
require(Path('/proc',str(outer['pid']),'cwd').resolve()==R,'outer cwd')
require(Path('/proc',str(outer['pid']),'exe').resolve()==Path(sys.executable).resolve(),'outer Python exe')
env={x.split(b'=',1)[0].decode():x.split(b'=',1)[1].decode() for x in Path('/proc',str(outer['pid']),'environ').read_bytes().split(b'\0') if b'=' in x}
require({k:env.get(k) for k in rd(D/'environment.json')}==rd(D/'environment.json'),'actual outer loading env')
require(time.time()-rd(O/'outer-ready.json')['ready_time']<1200,'outer review deadline')
require(set(p.name for p in O.iterdir())=={'outer-ready.json'},'unreleased outer no invocation')
require(set(p.name for p in RUN.iterdir())=={'sealed.json','config.json','host.json'},'unreserved pristine run')
host=c.full_host();host['memory']=c.guard.memory()
require(c.host_safe(host) and not c.guard.pressure(host['memory']),'fresh actual-host/ref/memory gate')
require(host['groups']==s['groups'] and len(host['groups'])==274,'all274 historical PGIDs and sessions')
require(all(host[k]==s[k] for k in ['head','master','boot_id']),'live ref/boot linkage')
owned=c.guard.active_group_members(outer['pid']); require(owned==[outer['pid']],'waiting outer only member')
require(c.guard.process_identity(outer['pid'])==outer,'outer still exact/live')
evidence=dict(all_passed=True,scope='Independent read-only exact P011 admission checks; no Julia or launch entrypoint invoked',start=start,end=time.time(),seal_sha256=h(SP),files_count=len(s['files']),receipt_subject_count=len(s['files'])+1,inventory_count=len(actual),hashed_bytes=byte_count,tree_counts=tree_counts,baseline_counts={k:len(v) for k,v in base.items()},runtime_count=len(runtime),preparation_count=len(rd(D/'preparation-pins.json')['sha256']),host=host,outer_identity=outer,outer_only_members=owned,loading_environment_matches=True,tracked_and_index_clean=True,no_release_reservation_output_payload=True)
with (RUN/'admission-checks.json').open('x') as f:json.dump(evidence,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in evidence.items() if k not in ['host','outer_identity']},indent=2)); print('fresh_memory',host['memory']); print('unreadable_exe_count',len(host['unreadable_exe_pids']))
