"""Fresh read/hash admission verification only. Imports no project/author code."""
from pathlib import Path
import hashlib,json,os,subprocess,time,traceback
RUN=Path(__file__).resolve().parent;D=RUN.parents[1];R=D.parents[3]
C=R/'diagnostics/direct-lu-policy-adapters/reproduce'
W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl')
MASTER='26e2291745999f485a74f643298ca997d65c7205';HEAD='76a93ee3db78df59f8492c5ca7bbeacb00a28f80'
checks=[];facts={};cache={}
def rd(p):return json.loads(Path(p).read_text())
def sha(p):
 p=Path(p);st=p.stat();key=(str(p),st.st_size,st.st_mtime_ns)
 if key not in cache:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):h.update(b)
  cache[key]=h.hexdigest()
 return cache[key]
def ck(name,value):
 checks.append({'name':name,'passed':bool(value)})
 if not value:raise AssertionError(name)
def path(n):return Path(n) if Path(n).is_absolute() else R/n
def binds(label,m):ck(label,all(sha(path(n))==v for n,v in m.items()))
def historical_binds(label,record):
 m=rd(record)['sha256'];mapping={(x['record'],x['key']):x for x in rd(D/'continuation-mappings.json')}
 resolved={}
 for n,v in m.items():
  entry=mapping.get((str(record.relative_to(R)),n))
  if entry:
   ck(label+' accepted mapping '+n,entry['sha256']==v)
   resolved[str(R/entry['preserved'])]=v
  else:resolved[n]=v
 binds(label,resolved)
def inventory(label,j):
 names=set(j['files'])
 for tree in j['trees']:
  root=Path(tree);ck(label+' tree '+tree,root.is_dir() and not root.is_symlink())
  for p in root.rglob('*'):
   ck(label+' symlink '+str(p),not(p.is_symlink() and (p.is_dir() or not p.exists())))
   if p.is_file():names.add(str(p))
 ck(label+' inventory membership',names==set(j['inventory']))
 ck(label+' inventory content',all(str(Path(n).resolve(strict=True))==v['resolved'] and sha(n)==v['sha256'] for n,v in j['inventory'].items()))
def git(*a,root=R):return subprocess.check_output(['git',*a],cwd=root).decode().strip()
try:
 s=rd(RUN/'sealed.json');cfg=rd(RUN/'config.json');host=rd(RUN/'host.json');prep=rd(D/'preparation-pins.json');review=rd(D/'review.json');stage=rd(D/'stages.json')['cost'];S=Path(stage['path']);runtime=rd(D/'runtime-inputs-complete.json')['inventory'];base=rd(D/'baseline.json');lineage=rd(D/'lineage.json')
 ck('phase and refs',s['phase']=='cost1-300' and s['head']==HEAD and s['master']==MASTER)
 ck('seal only initial artifacts',{p.name for p in RUN.iterdir()}=={'host.json','config.json','sealed.json','admission-independent-check.py','admission-independent-checks.json','admission-independent-first-check-note.json',Path(__file__).name})
 ck('config exact canonical',cfg==s['config']==rd(D/'config.json')['cost1-300'])
 command=['/bin/bash','/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh','--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--history-file=no','--project='+str(S),str(D/'cost.jl'),'cost1-300',str(RUN/'output'),str(S)]
 ck('exact command independently reconstructed',cfg==dict(phase='cost1-300',process=1,seconds=300,expected_exit=0,stage=str(S),run=str(RUN),output=str(RUN/'output'),command=command))
 ck('preparation canonical 91',len(prep['sha256'])==91 and set(prep['sha256'])==set(rd(D/'required-paths.json')['paths']))
 binds('preparation hashes',prep['sha256'])
 ck('preparation review acceptance',review['accepted'] is True and review['findings']==[] and review['scope']=='direct adapter matched cost preparation')
 ck('preparation review exact 92',len(review['sha256'])==92 and set(review['sha256'])==set(prep['sha256'])|{str(D/'preparation-pins.json')} and review['pins_sha256']==sha(D/'preparation-pins.json'))
 binds('preparation review hashes',review['sha256']);binds('preparation independent evidence',review['evidence_sha256']);binds('GREEN lineage',lineage['sha256'])
 for label,root,count in [('diagnostic',R,514),('production',W,516)]:
  ck(label+' tracked membership',len(base[label])==count and set(git('ls-files','src','test','.github','Project.toml',root=root).splitlines())==set(base[label]))
  ck(label+' baseline current hashes',all(sha(root/n)==v for n,v in base[label].items()))
 ck('stage 75 exact membership',len(stage['sha256'])==75 and set(stage['sha256'])=={str(p.relative_to(S)) for p in S.rglob('*') if p.is_file()})
 ck('stage no symlinks',not S.is_symlink() and not any(p.is_symlink() for p in S.rglob('*')))
 ck('stage hashes',all(sha(S/n)==v for n,v in stage['sha256'].items()))
 names=git('ls-tree','-r','--name-only',MASTER,'--','src','Project.toml').splitlines()
 for n in names:
  original=subprocess.check_output(['git','show',MASTER+':'+n],cwd=R);actual=(S/n).read_bytes()
  if n=='src/JSimplex.jl':
   anchor=b'include("huangfu_hall_factorization.jl")\n';addition=b'include("factor-export.jl")\ninclude("direct-factor.jl")\n'
   ck('root exact two include inverse',original.count(anchor)==1 and actual==original.replace(anchor,anchor+addition))
  else:ck('master stage inverse '+n,actual==original)
 for n in ['factor-export.jl','direct-factor.jl']:ck('accepted candidate stage '+n,(S/'src'/n).read_bytes()==(C/n).read_bytes())
 ck('runtime 609',len(runtime)==609)
 ck('runtime full resolved hashes',all(str(Path(n).resolve(strict=True))==v['resolved'] and sha(n)==v['sha256'] for n,v in runtime.items()))
 expected=set(prep['sha256'])|{str(D/'preparation-pins.json'),str(D/'review.json')}|set(runtime)|{str(root/n) for label,root in [('diagnostic',R),('production',W)] for n in base[label]}|{str(S/n) for n in stage['sha256']}|set(lineage['sha256'])|{str(D/'lineage.json'),str(RUN/'host.json'),str(RUN/'config.json')}
 ck('seal exact 1809 file membership',len(s['files'])==len(set(s['files']))==1809 and set(s['files'])==expected)
 ck('seal exact trees and no model inputs',s['trees']==[str(S),str(C)] and s['inputs']==[])
 inventory('cost seal',s)
 G=D.parent/'DIRECT-LU-POLICY-ADAPTER-DRIVER-PREPARATION/runs/green300';gr=rd(G/'result-review.json');ga=rd(G/'audit.json')
 ck('GREEN accepted 30455',gr['accepted'] is True and gr['findings']==[] and gr['scope']=='direct adapter GREEN result' and gr['phase']=='green300' and ga['all_passed'] is True and ga['pure_timeout'] is False and ga['result']['assertions']==30455)
 ck('GREEN review complete membership',set(gr['sha256'])=={str(p) for p in G.rglob('*') if p.is_file() and p!=G/'result-review.json'})
 binds('GREEN reviewed files',gr['sha256']);binds('GREEN review evidence',gr['evidence_sha256'])
 for name,count in [('sealed.json',1820),('launch-pins.json',1823)]:
  j=rd(G/name);ck('GREEN '+name+' count',len(j['inventory'])==count);inventory('GREEN '+name,j)
 for n in ['inputs.json','inputs.toml']:ck('immutable old token '+n,sha(D/n)==sha(D.parent/'DIRECT-LU-COST-PREPARATION'/n))
 for d in [D,D.parent/'DIRECT-LU-POLICY-ADAPTER-GREEN']:
  j=rd(d/'closure.json');ck(str(d.name)+' closure accepted',j['all_passed'] is True);historical_binds(str(d.name)+' closure files',d/'closure.json')
  j=rd(d/'publication.json');ck(str(d.name)+' publication accepted',j['all_passed'] is True);historical_binds(str(d.name)+' published files',d/'publication.json')
 ck('diagnostic exact HEAD',git('rev-parse','HEAD')==HEAD)
 ck('local and production master',git('rev-parse','master')==git('rev-parse','HEAD',root=W)==MASTER)
 remote=git('ls-remote','origin','refs/heads/master');ck('remote master',remote==MASTER+'\trefs/heads/master');facts['remote_master']=remote
 ck('tracked index and working clean',not git('diff','--name-only') and not git('diff','--cached','--name-only'))
 env=rd(D/'environment.json');ck('loading environment exact',env=={k:os.environ.get(k) for k in env})
 ck('host seal bindings',all(host[k]==s[k] for k in ('head','master','boot_id','groups')) and host['matches']==[])
 ck('all 226 historical groups',len(s['groups'])==226 and set(rd(D/'host.json')['groups'])|set(rd(G/'posthost.json')['groups'])==set(s['groups']))
 ck('same boot',Path('/proc/sys/kernel/random/boot_id').read_text().strip()==s['boot_id'])
 matches=[];unreadable=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   a=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip();exe=''
   try:exe=str((p/'exe').resolve(strict=True))
   except PermissionError:unreadable.append(int(p.name))
   except FileNotFoundError:pass
   if int(a[2]) in s['groups'] or int(a[3]) in s['groups'] or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):matches.append(dict(pid=int(p.name),pgid=int(a[2]),sid=int(a[3]),comm=comm,exe=exe))
  except (FileNotFoundError,ProcessLookupError):pass
 facts['host']=dict(time=time.time(),matches=matches,unreadable_exe_pids=unreadable,groups=s['groups']);ck('no live Julia or old group/session',not matches)
 mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()};facts['memory']=dict(available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree']);ck('current RAM swap thresholds',facts['memory']['available_kib']>=6*1024**2 and facts['memory']['swap_used_kib']<=1024**2)
 f=rd(D/'inputs.json')['fixtures'];ck('fixed fixture dimensions and steps',len(f)==4 and sorted(x['n'] for x in f)==[32,32,96,96] and all(len(x['matrices'])==9 and len(x['steps'])==8 for x in f))
 facts['counts']=dict(preparation=91,preparation_review=92,sealed_files=1809,admission_files=1810,runtime=609,diagnostic_baseline=514,production_baseline=516,stage=75,cells=24,windows=480,warm_windows=144,measured_windows=336,constructions=480,refactors=960,updates=3840,FTRAN=7680,BTRAN=3840,preflight_constructions=48,preflight_refactors=96,exact_residuals=11520)
 facts['sealed_sha256']=sha(RUN/'sealed.json');facts['command']=command
except Exception:
 facts['error']=traceback.format_exc()
finally:
 result=dict(all_passed=all(c['passed'] for c in checks) and 'error' not in facts,count=len(checks),checks=checks,facts=facts)
 with (RUN/'admission-independent-checks-v2.json').open('x') as out:json.dump(result,out,indent=2);out.write('\n')
 print(json.dumps(dict(all_passed=result['all_passed'],count=result['count'],error=facts.get('error'),facts={k:v for k,v in facts.items() if k!='host'}),indent=2))
