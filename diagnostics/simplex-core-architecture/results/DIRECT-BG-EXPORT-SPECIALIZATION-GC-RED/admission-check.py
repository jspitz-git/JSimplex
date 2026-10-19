"""Independent exact-stage read-only admission verification. Never launches Julia."""
import os,sys,json,time,hashlib,subprocess,traceback
from pathlib import Path
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
P=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-SPECIALIZATION-GC-DRIVER'
Q=P.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-GC-RED')
sys.path.insert(0,str(P))
import control as c
from preparation_schema import KEYS
result={'scope':'Fresh independent redgc300 exact-stage admission checks','started':time.time(),'checks':[],'findings':[]}
def check(v,label):
 if not v:raise AssertionError(label)
 result['checks'].append(label)
def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def git(*a,cwd=R):return subprocess.check_output(['git',*a],cwd=cwd,text=True).strip()
try:
 s=read(P/'runs/redgc300/sealed.json');cfg=read(P/'runs/redgc300/config.json');ready=read(P/'outers/redgc300/outer-ready.json')
 check(cfg==s['config']==c.config('redgc300'),'exact configuration')
 check(s['phase']=='redgc300' and s['inputs']==[],'phase and no alternate inputs')
 check(cfg['seconds']==300 and cfg['expected_exit']==1 and cfg['mode']=='red','one RED300 expected exit1')
 check(s['files']==sorted(set(s['files'])),'unique sorted seal files')
 prepared=c.preparation();result['preparation_paths']=len(prepared)
 check(s['files']==c.seal_files(cfg,prepared,[]),'independently recomputed exact seal file membership')
 check(c.predecessor('redgc300')==([],[]),'RED has no predecessor or reused allowance')
 check(s['trees']==[cfg['stage'],str(c.C)],'exact sealed tree roots')
 actual=set(s['files'])
 for tree in s['trees']:
  root=Path(tree);check(root.is_dir() and not root.is_symlink(),'real tree '+tree)
  for f in root.rglob('*'):
   check(not f.is_symlink(),'no tree symlink '+str(f))
   if f.is_file():actual.add(str(f))
 check(actual==set(s['inventory']),'exact complete inventory membership including trees')
 fresh={};listed_bytes=0
 for n,item in s['inventory'].items():
  f=Path(n);check(set(item)=={'resolved','sha256'},'inventory schema '+n)
  check(str(f.resolve(strict=True))==item['resolved'],'resolved path '+n)
  h=digest(f);check(h==item['sha256'],'fresh sha256 '+n);fresh[n]=h;listed_bytes+=f.stat().st_size
 result.update(sealed_files=len(s['files']),inventory_paths=len(fresh),listed_bytes=listed_bytes,inventory_sha256=fresh,sealed_sha256=digest(P/'runs/redgc300/sealed.json'))
 c.validate_sources();check(True,'current R/W source and tracked membership, all stage bytes, full runtime inventory')
 stages=read(P/'stages.json');check(len(stages['red']['sha256'])==83,'83-file RED stage')
 check(stages['red']==stages['green'],'unchanged shared candidate stage')
 c.validate_environment();check(True,'current login:false loading environment exact')
 outer=c.verify_outer('redgc300',s,live=True);check(outer==ready['identity'],'fresh outer boot/startticks/command/PID/PGID/SID')
 check(outer['pid']==outer['pgid']==outer['sid'],'isolated outer process group/session')
 check(str((Path('/proc')/str(outer['pid'])/'cwd').resolve())==str(R),'outer cwd exact checkout')
 environ=(Path('/proc')/str(outer['pid'])/'environ').read_bytes().split(b'\0')
 liveenv={b.split(b'=',1)[0].decode():b.split(b'=',1)[1].decode() for b in environ if b'=' in b}
 expected=read(P/'environment.json');check({k:liveenv.get(k) for k in expected}==expected,'actual waiting outer exact loading environment')
 check(Path(liveenv.get('PATH','').split(':')[0]).is_absolute(),'outer absolute first PATH component')
 check(str((Path('/proc')/str(outer['pid'])/'exe').resolve())==str(Path(sys.executable).resolve()),'outer pinned Python executable')
 h=c.full_host();h['memory']=c.guard.memory();h['remote']=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture')
 check(len(h['groups'])==259 and h['groups']==s['groups']==read(Q/'host-entry.json')['groups'],'fresh complete 259 prior groups AND sessions')
 check(c.host_safe(h),'all prior PGID/SID absent, no Julia by stat/comm/argv0/readable exe, no unreadable stat identity')
 check(not c.guard.pressure(h['memory']),'RAM>=6GiB swap<=1GiB')
 expectedhead='18ab2a17b16508833d16b83cdcfb832a7c422c18';master='26e2291745999f485a74f643298ca997d65c7205'
 check(h['head']==s['head']==expectedhead and h['master']==s['master']==master,'unchanged exact local HEAD/master')
 check(h['boot_id']==s['boot_id']==outer['boot_id'],'unchanged boot')
 check(h['remote'].splitlines()==sorted([expectedhead+'\trefs/heads/codex/simplex-core-architecture',master+'\trefs/heads/master']),'fresh exact origin branch/master refs')
 check(git('rev-parse','origin/codex/simplex-core-architecture')==expectedhead,'origin tracking ref exact')
 check(git('branch','--show-current')=='codex/simplex-core-architecture','expected branch')
 check(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'clean tracked and staged state')
 c.guard.process_identity(outer['pid'])==outer or (_ for _ in ()).throw(AssertionError('outer identity changed'))
 own=c.full_host([outer['pgid'],outer['sid']]);check(len(own['matches'])==1 and {k:own['matches'][0][k] for k in outer}==outer and own['unreadable_identity_pids']==[],'fresh explicit outer group/session contains exactly admitted waiting outer')
 result['host']=h;result['outer_identity']=outer;result['explicit_outer_snapshot']=own
 result['elapsed_waiting_seconds']=time.time()-ready['ready_time'];check(result['elapsed_waiting_seconds']<1200,'outer admission deadline remains open')
 check({p.name for p in (P/'runs/redgc300').iterdir()}=={'host.json','config.json','sealed.json'},'no prior admission/reservation/output/attempt')
 check({p.name for p in (P/'outers/redgc300').iterdir()}=={'outer-ready.json'},'waiting outer unreleased and no outcome')
 check(len(KEYS)==17,'exact seventeen preparation fields')
 check(read(P/'expected-tests.json')['red']=={'assertions':3,'groups':[['allocation_nonincrease_sparse32',0,1,0,0],['allocation_nonincrease_dense32',0,1,0,0],['allocation_nonincrease_sparse96',0,1,0,0]]},'exact three RED allocation failures test tree')
 cmd=cfg['command'];check(cmd[2:7]==['--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--history-file=no'],'single-process/thread existing modules and 2GiB heap flags')
 gc=c.guard_command(cfg,P/'runs/redgc300/launch-pins.json',0.0);check(gc[gc.index('--seconds')+1]=='292' and gc[gc.index('--deadline')+1]=='292.0','292-second inner guard')
 wrapper=Path(c.WRAPPER).read_text();check('ulimit -v 8388608' in wrapper and 'exec /home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/bin/julia --startup-file=no "$@"' in wrapper,'real wrapper 8GiB inherited VM and exec Julia startup disabled')
 check(digest(P/'runs/redgc300/sealed.json')==result['sealed_sha256'],'seal unchanged through review')
 result['all_passed']=True
except Exception as e:
 result['all_passed']=False;result['findings'].append(repr(e));result['traceback']=traceback.format_exc()
result['completed']=time.time();result['checks_passed']=len(result['checks'])
with (Q/'admission-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({k:result.get(k) for k in ['all_passed','findings','checks_passed','sealed_files','inventory_paths','listed_bytes','preparation_paths','elapsed_waiting_seconds']}))
if not result['all_passed']:sys.exit(1)
