"""Fresh independent GREEN exact-stage checks. Reads only inputs; never launches Julia.
Derived by inspecting the frozen RED checker as source; GREEN lineage is checked explicitly.
"""
import os,sys,json,time,hashlib,subprocess,traceback,tomllib
from pathlib import Path
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
P=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-SPECIALIZATION-GC-DRIVER'
Q=P.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-GC-GREEN')
PHASE='greengc300';RUN=P/'runs'/PHASE;O=P/'outers'/PHASE
sys.path.insert(0,str(P))
import control as c
from preparation_schema import KEYS
result={'scope':'Fresh independent greengc300 exact-stage admission checks','started':time.time(),'checks':[],'findings':[]}
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
 s=read(RUN/'sealed.json');cfg=read(RUN/'config.json');ready=read(O/'outer-ready.json')
 check(cfg==s['config']==c.config(PHASE),'exact GREEN configuration')
 check(s['phase']==PHASE and s['inputs']==[],'phase and no alternate inputs')
 check(cfg['seconds']==300 and cfg['expected_exit']==0 and cfg['mode']=='green','one GREEN300 expected exit0')
 check(s['files']==sorted(set(s['files'])),'unique sorted seal files')
 prepared=c.preparation();result['preparation_paths']=len(prepared)
 extra,groups=c.predecessor(PHASE)
 check(len(extra)==86 and len(groups)==262,'GREEN exact successful RED predecessor:86 paths and262 groups')
 rr=P/'runs/redgc300';review=read(rr/'result-review.json');closure=read(rr/'outer-closure.json');a=read(rr/'audit.json')
 files={str(p) for p in rr.rglob('*') if p.is_file() and p.name!='result-review.json'}
 check(len(files)==81 and set(review['sha256'])==files,'RED result review exact81 files')
 check(review['accepted'] is True and review['findings']==[] and review['checks_passed']==29224,'RED independent result accepted29224 checks')
 check(review['residual_checks']==1440 and review['paired_bit_checks']==30 and review['preparations']==3,'RED independent residual/pair/preparation coverage')
 check(set(closure['sha256'])=={str(p) for p in c.closure_paths('redgc300')} and len(closure['sha256'])==8,'RED exact eight external closure bindings')
 check(set(extra)==files|{str(rr/'result-review.json')}|set(closure['sha256']),'predecessor exact union without old rejected RED')
 for kind,bindings in [('REDresult',review['sha256']),('REDevidence',review['evidence_sha256']),('REDclosure',closure['sha256'])]:
  for n,h in bindings.items():check(digest(n)==h,kind+' fresh binding '+n)
 check(a['all_passed'] is True and a['pure_timeout'] is False and a['phase']=='redgc300','successful RED audit non-timeout')
 check(a['result']['assertions']==3 and len(a['allocation'])==3 and all(x['statistics']['allocation_gate'] is False for x in a['allocation']),'RED exact three expected allocation failures')
 check(a['preparation']['saved_windows']==60 and a['preparation']['saved_preparations']==3,'RED complete60 windows3 preparations')
 raw=tomllib.loads((rr/'output/raw.toml').read_text())
 check(raw['preparation_calls']==raw['preparations_completed']==3,'RED raw preparation counts')
 check(all(len(x)==17 for x in a['preparation']['records']),'RED seventeen-field records')
 outcome=read(P/'outers/redgc300/outer-outcome.json')
 check(outcome['launched'] is True and outcome['returncode']==0 and outcome['error']=='' and outcome['identity']==closure['outer_identity'],'successful RED actual outer identity and outcome')
 check(s['files']==c.seal_files(cfg,prepared,extra),'independently recomputed exact GREEN seal membership')
 check(set(extra)<=set(s['files']),'all successful RED files and external closure sealed')
 check(s['trees']==[cfg['stage'],str(c.C)],'exact sealed tree roots')
 actual=set(s['files'])
 for tree in s['trees']:
  root=Path(tree);check(root.is_dir() and not root.is_symlink(),'real tree '+tree)
  for f in root.rglob('*'):
   check(not f.is_symlink(),'no tree symlink '+str(f))
   if f.is_file():actual.add(str(f))
 check(actual==set(s['inventory']),'exact full inventory membership including trees')
 fresh={};listed_bytes=0
 for n,item in s['inventory'].items():
  f=Path(n);check(set(item)=={'resolved','sha256'},'inventory schema '+n)
  check(str(f.resolve(strict=True))==item['resolved'],'resolved path '+n)
  h=digest(f);check(h==item['sha256'],'fresh sha256 '+n);fresh[n]=h;listed_bytes+=f.stat().st_size
 result.update(sealed_files=len(s['files']),inventory_paths=len(fresh),listed_bytes=listed_bytes,inventory_sha256=fresh,sealed_sha256=digest(RUN/'sealed.json'),predecessor_paths=len(extra),predecessor_review_bindings=len(files),predecessor_closure_bindings=len(closure['sha256']))
 c.validate_sources();check(True,'current R/W source and tracked membership, all stage bytes, full runtime inventory')
 stages=read(P/'stages.json');check(len(stages['green']['sha256'])==83 and stages['red']==stages['green'],'unchanged shared83-file GREEN stage')
 c.validate_environment();check(True,'current login:false loading environment exact')
 outer=c.verify_outer(PHASE,s,live=True);check(outer==ready['identity'],'fresh actual outer boot/startticks/command/PID/PGID/SID')
 check(outer['pid']==outer['pgid']==outer['sid'],'isolated outer process group/session')
 proc=Path('/proc')/str(outer['pid'])
 check(str((proc/'cwd').resolve())==str(R),'outer cwd exact checkout')
 argv=(proc/'cmdline').read_bytes().split(b'\0');argv=[v.decode() for v in argv if v]
 check(argv==['/usr/bin/python3','-B','diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-SPECIALIZATION-GC-DRIVER/outer.py',PHASE],'actual outer exact Python-B command')
 environ=(proc/'environ').read_bytes().split(b'\0');liveenv={b.split(b'=',1)[0].decode():b.split(b'=',1)[1].decode() for b in environ if b'=' in b}
 expected=read(P/'environment.json');check({k:liveenv.get(k) for k in expected}==expected,'actual outer exact loading environment')
 check(str((proc/'exe').resolve())==str(Path(sys.executable).resolve()),'actual outer pinned Python executable')
 h=c.full_host(groups);h['memory']=c.guard.memory();h['remote']=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture')
 check(len(h['groups'])==262 and h['groups']==s['groups']==read(Q/'host-entry.json')['groups'],'fresh complete262 prior groups AND sessions')
 check(c.host_safe(h),'all prior PGID/SID absent, no Julia via stat/comm/argv0/readable exe, no unreadable stat identity')
 check(not c.guard.pressure(h['memory']),'RAM>=6GiB swap<=1GiB')
 head='3a8b393bd8bef95ec2cd3ece52129ea6ed1f5944';master='26e2291745999f485a74f643298ca997d65c7205'
 check(h['head']==s['head']==head and h['master']==s['master']==master,'unchanged exact local HEAD/master')
 check(h['boot_id']==s['boot_id']==outer['boot_id'],'unchanged boot')
 check(h['remote'].splitlines()==sorted([head+'\trefs/heads/codex/simplex-core-architecture',master+'\trefs/heads/master']),'fresh exact origin branch/master refs')
 check(git('rev-parse','origin/codex/simplex-core-architecture')==head,'origin tracking ref exact')
 check(git('branch','--show-current')=='codex/simplex-core-architecture','expected branch')
 check(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'clean tracked and staged state')
 check(c.guard.process_identity(outer['pid'])==outer,'outer identity unchanged')
 own=c.full_host(groups+[outer['pgid'],outer['sid']]);check(len(own['matches'])==1 and {k:own['matches'][0][k] for k in outer}==outer and own['unreadable_identity_pids']==[],'fresh explicit outer group/session contains exactly admitted waiting outer')
 result['host']=h;result['outer_identity']=outer;result['explicit_outer_snapshot']=own
 result['elapsed_waiting_seconds']=time.time()-ready['ready_time'];check(result['elapsed_waiting_seconds']<1200,'outer admission deadline remains open')
 check({p.name for p in RUN.iterdir()}=={'host.json','config.json','sealed.json'},'no prior admission/reservation/output/attempt')
 check({p.name for p in O.iterdir()}=={'outer-ready.json'},'waiting outer unreleased and no outcome')
 check(len(KEYS)==17,'exact seventeen preparation fields')
 tests=read(P/'expected-tests.json')['green'];tg=tests['groups']
 check(tests['assertions']==8640 and sum(g[1] for g in tg)==8640 and all(g[2:]==[0,0,0] for g in tg),'exact GREEN8640 passes and no failed/error/broken leaves')
 check(len(tg)==17 and tg[-3:]==[['allocation_nonincrease_'+f,1,0,0,0] for f in ['sparse32','dense32','sparse96']],'exact GREEN17 groups including all3 successful allocation predicates')
 cmd=cfg['command'];check(cmd[2:7]==['--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--history-file=no'],'single Julia/thread existing modules and2GiB heap flags')
 gc=c.guard_command(cfg,RUN/'launch-pins.json',0.0);check(gc[gc.index('--seconds')+1]=='292' and gc[gc.index('--deadline')+1]=='292.0','292-second inner guard')
 wrapper=Path(c.WRAPPER).read_text();check('ulimit -v 8388608' in wrapper and 'exec /home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/bin/julia --startup-file=no "$@"' in wrapper,'actual wrapper8GiB inherited VM and exec Julia startup disabled')
 check('BLAS.set_num_threads(1)' in (P/'green-kernel.jl').read_text(),'GREEN BLAS single thread')
 check(digest(RUN/'sealed.json')==result['sealed_sha256'],'seal unchanged through review')
 result['all_passed']=True
except Exception as e:
 result['all_passed']=False;result['findings'].append(repr(e));result['traceback']=traceback.format_exc()
result['completed']=time.time();result['checks_passed']=len(result['checks'])
with (Q/'admission-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({k:result.get(k) for k in ['all_passed','findings','checks_passed','sealed_files','inventory_paths','listed_bytes','preparation_paths','predecessor_paths','elapsed_waiting_seconds']}))
if not result['all_passed']:sys.exit(1)
