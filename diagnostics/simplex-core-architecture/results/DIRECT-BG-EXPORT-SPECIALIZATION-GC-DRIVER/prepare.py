from pathlib import Path
import json,hashlib
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');B=R/'diagnostics/simplex-core-architecture/results';D=B/'DIRECT-BG-EXPORT-SPECIALIZATION-DRIVER';N=B/'DIRECT-BG-EXPORT-SPECIALIZATION-GC-PREPARATION';P=B/'DIRECT-BG-EXPORT-SPECIALIZATION-GC-DRIVER';Q=B/'DIRECT-BG-EXPORT-SPECIALIZATION-RED'
def write(n,s):
 with (P/n).open('x') as f:f.write(s)
def replace(s,a,b):
 if s.count(a)!=1:raise ValueError((a,s.count(a)))
 return s.replace(a,b)
copies={}
for root,names in [(D,'guard.py supervisor.py allocation_oracle.py analysis.py baseline.json environment.json expected-tests.json inputs.json loaded-paths.json runtime-inputs-complete.json stages.json'),(N,'driver.jl preparation.jl preparation_schema.py red-kernel.jl green-kernel.jl recorder.jl inputs.toml expected-tests.toml')]:
 for name in names.split():
  data=(root/name).read_bytes();(P/name).write_bytes(data);copies[name]={'source':str(root/name),'sha256':hashlib.sha256(data).hexdigest()}
write('copied-files.json',json.dumps(copies,indent=2)+'\n')
# Raw schema adapter retains original strict tree and timeout validation after explicit GC checks.
s=(D/'oracle.py').read_text();s=replace(s,'def test_results(raw,expected,loaded,phase):','def original_test_results(raw,expected,loaded,phase):');s=replace(s,'def timeout_only(process,supervisor,raw,log,elapsed,seconds,loaded,phase):','def original_timeout_only(process,supervisor,raw,log,elapsed,seconds,loaded,phase):')
s+='''
EXTRA={'preparation_calls','preparations_completed'}
BASE={'phase','complete','fatal','loaded','threads','blas_threads','tests'}
def strip_preparation(raw):
 need(type(raw) is dict and set(raw)==BASE|EXTRA,'GC raw schema')
 calls=raw['preparation_calls'];done=raw['preparations_completed']
 need(type(calls) is int and type(done) is int and 0<=done<=calls<=3 and calls-done<=1,'GC raw counters')
 return {k:raw[k] for k in BASE}
def test_results(raw,expected,loaded,phase):
 clean=strip_preparation(raw)
 need(raw['preparation_calls']==raw['preparations_completed']==3,'Complete GC counters')
 return original_test_results(clean,expected,loaded,phase)
def timeout_only(process,supervisor,raw,log,elapsed,seconds,loaded,phase):
 try:clean=None if raw is None else strip_preparation(raw)
 except (KeyError,TypeError,ValueError):return False
 return original_timeout_only(process,supervisor,clean,log,elapsed,seconds,loaded,phase)
''';write('oracle.py',s)
write('preparation_oracle.py','''"""Pure prefix/counter reconciliation. Ordering is source-bound, not timestamp capture."""
from preparation_schema import validate_records,require
from oracle import strip_preparation

def preparation_results(rows,windows,raw,phase,complete):
 validate_records(rows,phase,complete)
 schedule=[f'window-{c}-{w}.toml' for c in range(1,4) for w in range(1,21)]
 require(set(windows)==set(schedule[:len(windows)]),'GC window prefix')
 n=len(windows);done=len(rows)
 # GC is reached after warm window 6 in each cell and before window 7.
 for cell in range(1,4):
  boundary=(cell-1)*20+6
  require(f'preparation-{cell}.toml' not in rows or n>=boundary,'GC before warm pair completion')
  require(n<=boundary or f'preparation-{cell}.toml' in rows,'Observed window without preparation')
 if complete:require(n==60 and raw is not None,'Complete output missing')
 if raw is not None:
  strip_preparation(raw)
  calls=raw['preparation_calls'];finished=raw['preparations_completed']
  require(finished==done,'Saved GC/completed count mismatch')
  require(calls==done or (calls==done+1 and n==done*20+6),'Unfinished GC not at boundary')
  if complete:require(calls==finished==3 and raw['complete'] is True,'Complete GC counters')
 return {'records':[rows[f'preparation-{i}.toml'] for i in range(1,done+1)],
         'saved_preparations':done,'saved_windows':n,
         'raw_counters_available':raw is not None,
         'scope':'Full GC API requests only; no finalizer/native-free proof. Inner GC timing excludes helper compilation, record creation and I/O; whole-process elapsed includes them. Timings overlap and are not additive.'}
''')
s=(D/'control.py').read_text();s=replace(s,"ENTRY='b504ea4fbf3bc40a9fa87cfc0b9a7dd69cc821cd'","ENTRY='ff248544e8f89cc05aecff64806bf60d8b2bd9cf'")
s=replace(s,"('red300','green300','red600','green600')","('redgc300','greengc300')")
s=replace(s,"seconds=300 if phase.endswith('300') else 600","seconds=300")
s=replace(s,"rd(D/'host.json')['groups']","rd(D/'host-entry.json')['groups']")
a=s.index('def preparation():');b=s.index('def result_review(',a)
s=s[:a]+'''def preparation():
 m=D/'preparation-pins.json';j=rd(m)
 require(bindings(j) and set(j['sha256'])==set(rd(D/'required-paths.json')['paths']),'Preparation drift/membership')
 verify_review(rd(D/'review.json'),m,list(j['sha256'])+[str(m)],'BG specialization GC driver preparation')
 n=D.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-GC-PREPARATION');nm=n/'preparation-pins-reviewed.json';nj=rd(nm)
 require(bindings(nj),'Accepted GC amendment drift')
 verify_review(rd(n/'review.json'),nm,list(nj['sha256'])+[str(nm)],'BG specialization fixed GC preparation')
 require(rd(n/'review.json').get('launch_admitted') is False,'Offline review is not launch admission')
 for name,item in rd(D/'copied-files.json').items():
  require(sha(D/name)==sha(item['source'])==item['sha256'],'Copied source drift')
 return sorted(set(j['sha256'])|{str(m),str(D/'review.json')})
''' +s[b:]
a=s.index('def predecessor(');b=s.index('def guard_command(',a)
s=s[:a]+'''def predecessor(phase):
 cfg=config(phase)
 if cfg['mode']=='red':return [],[]
 red='redgc300';f,g=result_review(red,'BG specialization GC RED result','result-review.json')
 run=D/'runs'/red;a=rd(run/'audit.json');closure=rd(run/'outer-closure.json')
 require(a.get('all_passed') is True and a.get('pure_timeout') is False and a.get('phase')==red,'RED not accepted')
 require(closure.get('all_passed') is True and host_safe(closure['host']) and bindings(closure),'External RED closure invalid')
 require(guard.pins_match(rd(run/'sealed.json')),'RED input drift')
 return f,sorted(set(g)|set(closure['host']['groups']))
def outer_dir(phase):
 config(phase)
 return D/'outers'/phase
def verify_outer(phase,sealed=None,live=False):
 o=outer_dir(phase);r=rd(o/'outer-ready.json');i=r['identity']
 require(r['phase']==phase and r['waiting_only'] is True and r['script_sha256']==sha(D/'outer.py') and r['expected_launcher']==str(D/'launch.py'),'Outer ready')
 require(i['pid']==i['pgid']==i['sid'] and i['start_ticks']>0 and i['command'],'Outer identity')
 if sealed is not None:require(sealed['outer_identity']==i,'Sealed outer identity')
 if live:require(guard.process_identity(i['pid'])==i,'Outer no longer alive')
 return i
def verify_outer_invocation(phase,sealed,live=False):
 i=verify_outer(phase,sealed,live);o=outer_dir(phase);run=Path(config(phase)['run']);sp=run/'sealed.json';rp=run/'admission.json'
 require(rd(o/'release.json')==dict(phase=phase,sealed_sha256=sha(sp),admission_sha256=sha(rp),outer_ready_sha256=sha(o/'outer-ready.json'),one_attempt=True),'Release binding')
 require(rd(o/'outer-invocation.json')==dict(identity=i,phase=phase,seal_sha256=sha(sp),review_sha256=sha(rp),release_sha256=sha(o/'release.json'),launcher_sha256=sha(D/'launch.py'),method='runpy.run_path launch.py as __main__ in this outer process'),'Outer invocation')
 if live:require(os.getpid()==i['pid'],'Launcher must run inside admitted outer')
 return i
''' +s[b:];write('control.py',s)
# Explicit outer session, waiting only until a separate exact admission and release.
s=(Q/'outer.py').read_text();s=replace(s,"Q=Path(__file__).resolve().parent\nD=Q.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-DRIVER');sys.path.insert(0,str(D))","D=Path(__file__).resolve().parent;sys.path.insert(0,str(D))")
s=replace(s,"PHASE='red300';RUN=D/'runs'/PHASE\n","\n")
s=replace(s,'def valid_release(v,seal_sha,review_sha,identity_sha):','def valid_release(v,seal_sha,review_sha,identity_sha,phase):');s=replace(s,'phase=PHASE,sealed_sha256','phase=phase,sealed_sha256')
s=replace(s,'def main():\n os.chdir(c.R)','def main(phase):\n PHASE=phase;c.config(phase);Q=c.outer_dir(phase);RUN=D/\'runs\'/phase\n Q.mkdir(parents=True,exist_ok=False)\n os.chdir(c.R)')
s=replace(s,"c.sha(Q/'outer.py')","c.sha(D/'outer.py')") if "c.sha(Q/'outer.py')" in s else s
s=replace(s,"c.sha(Q/'outer-ready.json')))","c.sha(Q/'outer-ready.json'),PHASE))") if "c.sha(Q/'outer-ready.json')))" in s else s
# Actual call closes after require's first argument.
s=replace(s,"c.sha(Q/'outer-ready.json')),'Release binding'","c.sha(Q/'outer-ready.json'),PHASE),'Release binding'")
s=s.replace('BG specialization exact-stage admission','BG specialization GC exact-stage admission').replace('runpy.run_path unchanged launch.py as __main__ in this outer process','runpy.run_path launch.py as __main__ in this outer process')
s=replace(s,"if __name__=='__main__':sys.exit(main())","if __name__=='__main__':sys.exit(main(sys.argv[1]))")
write('outer.py',s)
s=(D/'seal.py').read_text();s=s.replace('BG specialization phase','BG specialization GC phase')
s=replace(s,"cfg=config(phase);validate_environment()","cfg=config(phase);outer=verify_outer(phase,live=True);validate_environment()")
s=replace(s,"str(run/'config.json')]))","str(run/'config.json'),str(outer_dir(phase)/'outer-ready.json')]))")
s=replace(s,"dict(phase=phase,head=","dict(phase=phase,outer_identity=outer,head=");write('seal.py',s)
s=(D/'launch.py').read_text().replace('BG specialization exact-stage admission','BG specialization GC exact-stage admission')
s=replace(s,"require(guard.pins_match(sealed),'Seal changed');h=","verify_outer_invocation(phase,sealed,live=True)\n require(guard.pins_match(sealed),'Seal changed');h=")
s=replace(s,"str(run/'prehost.json')});pp=","str(run/'prehost.json'),str(outer_dir(phase)/'release.json'),str(outer_dir(phase)/'outer-invocation.json')});pp=")
s=s.replace('pure timeout may receive separately admitted600s, never automatic in launcher','no automatic retry; any longer phase needs separate driver/admission amendment')
write('launch.py',s)
s=(D/'audit.py').read_text().replace('BG specialization exact-stage admission','BG specialization GC exact-stage admission')
s=replace(s,"windows={f'window-", "preps={f'preparation-{c}.toml' for c in range(1,4)}\n windows={f'window-")
s=replace(s,"base|{'raw.toml'}|windows and","base|{'raw.toml'}|windows|preps and")
s=replace(s,"str(run/'prehost.json')} and","str(run/'prehost.json'),str(outer_dir(phase)/'release.json'),str(outer_dir(phase)/'outer-invocation.json')} and")
s=replace(s,"require(s['phase']==phase", "verify_outer_invocation(phase,s)\n require(str(outer_dir(phase)/'outer-ready.json') in s['files'],'Outer ready not sealed')\n require(s['phase']==phase")
s=replace(s,"partial_windows({n:tomllib.loads((out/n).read_text()) for n in names & windows},rd(D/'inputs.json')['fixtures'])", "saved_windows={n:tomllib.loads((out/n).read_text()) for n in names & windows}\n partial_windows(saved_windows,rd(D/'inputs.json')['fixtures'])\n from preparation_oracle import preparation_results\n saved_preps={n:tomllib.loads((out/n).read_text()) for n in names & preps}\n prep=preparation_results(saved_preps,saved_windows,raw,phase,False)")
s=replace(s,"result={},error='Pure process timeout; independent result review required before new600s admission'","result={},preparation=prep,error='Pure process timeout; no retry phase prepared; separate reviewed amendment required'")
s=replace(s,"names==base|{'raw.toml'}|windows,","names==base|{'raw.toml'}|windows|preps,")
s=replace(s,"result=test_results(raw,", "prep=preparation_results(saved_preps,saved_windows,raw,phase,True)\n result=test_results(raw,")
s=replace(s,"allocation=allocation,error=''","allocation=allocation,preparation=prep,process_elapsed_seconds=inv['elapsed_seconds'],scope_note='Whole guarded process includes preparation and serialization; inner GC costs are separate overlapping diagnostics, not additive or performance acceptance',error=''")
write('audit.py',s)
write('post-return.py','''"""Future explicit external closure, after outer return. Reads saved audit without rerunning it."""
from control import *
def main(phase):
 cfg=config(phase);run=Path(cfg['run']);o=outer_dir(phase);s=rd(run/'sealed.json');outer=verify_outer_invocation(phase,s)
 outcome=rd(o/'outer-outcome.json')
 require(outcome['identity']==outer and outcome['launched'] is True,'Outer outcome')
 groups=s['groups']+[outer['pgid'],outer['sid']]
 for name in ['posthost.json']:
  if (run/name).exists():groups+=rd(run/name)['groups']
 for name in ['current.json','process.json']:
  p=Path(cfg['output'])/name
  if p.exists():
   for role in ['runner','child']:
    if role in rd(p):groups += [rd(p)[role][k] for k in ['pgid','sid']]
 h=full_host(groups);h['memory']=guard.memory();h['remote']=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture')
 require(host_safe(h) and all(h[k]==s[k] for k in ['head','master','boot_id']),'External process/ref closure failed')
 require(h['head']+'\\trefs/heads/codex/simplex-core-architecture' in h['remote'] and MASTER+'\\trefs/heads/master' in h['remote'],'Remote refs changed')
 files=[o/n for n in ['outer-ready.json','release.json','outer-invocation.json','outer-outcome.json']]+[run/n for n in ['sealed.json','admission.json','posthost.json','audit.json']]
 require(all(p.is_file() for p in files),'Missing closure evidence')
 save(run/'outer-closure.json',dict(all_passed=True,outer_identity=outer,host=h,sha256={str(p):sha(p) for p in files},scope='Outer and all prior/guard/child PGIDs AND SIDs absent; diagnostic closure does not imply qualification acceptance'))
if __name__=='__main__':main(sys.argv[1])
''')
write('request.txt','Prepare separate RED/GREEN admission and full auditor for the fixed GC driver, including all preparation records and independent review. Offline only; no Julia.\n')
write('prepare.py',Path(__file__).read_text())
print(P)
