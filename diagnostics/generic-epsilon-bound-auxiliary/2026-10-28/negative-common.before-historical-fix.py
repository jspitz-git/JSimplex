from pathlib import Path
import json,sys,subprocess,hashlib
D=Path(__file__).resolve().parent;M=Path('/home/jspitz/JSimplex.jl');R=D.parents[2]
sys.path.insert(0,str(D/'counter-gc-preparation'));import common as host_common
BASE='235eedf33901fe8c4cc06a3d8c3508ef2fcbb718';CAND='717ef2d5dc40b57bfaff198a0a4a48f7198d00db';OLD='90848b35ca1090522f472d4111d678642b9fef4a'
need=host_common.need;sha=host_common.sha
PRIVATE={'baseline','RED','GREEN','before-master','rollback-before','before-diagnostic','__pycache__'}
MANIFESTS=['pins.json','pins-qualified.json','remaining/pins.json','remaining-qualified/pins.json','RED-run/pins.json','GREEN-run/pins.json','MASTER-run/pins.json','counter-capture/pins.json','counter-gc-preparation/pins.json']
def read(n):return json.loads((D/n).read_text())
def put(n,x):
 with (D/n).open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
def raw(a,root=M):return subprocess.check_output(['/usr/bin/git','-C',str(root),*a],timeout=60)
def git(a,root=M):return raw(a,root).decode().strip()
def tree(root):return {str(p.relative_to(root)):sha(p) for t in ['src','test'] for p in (root/t).rglob('*') if p.is_file()}
def host():
 extra=set()
 for p in D.rglob('output/process.json'):
  x=json.loads(p.read_text());extra.update(x[k][v] for k in ['runner','child'] for v in ['pgid','sid'])
 return host_common.host(extra)
def refs(diagnostic=OLD,live=True,remote_diagnostic=None):
 if remote_diagnostic is None:remote_diagnostic=diagnostic
 need(git(['branch','--show-current'])=='master','master branch')
 need(git(['rev-parse','HEAD'])==git(['rev-parse','master'])==git(['rev-parse','origin/master'])==BASE,'restored master refs')
 need(git(['rev-parse','refs/heads/codex/generic-epsilon-bound-auxiliary'])==CAND,'candidate backup')
 need(git(['rev-list','--parents','-n','1',CAND]).split()==[CAND,BASE],'candidate sole parent')
 need(git(['branch','--show-current'],R)=='codex/simplex-core-architecture' and git(['rev-parse','HEAD'],R)==diagnostic,'diagnostic branch/head')
 for root in [M,R]:need(git(['remote','get-url','--push','--all','origin'],root)=='git@github.com:jspitz-git/JSimplex.git','approved endpoint')
 if live:
  need(git(['ls-remote','origin','refs/heads/master']).split()[0]==BASE,'live master unchanged')
  need(git(['rev-parse','origin/codex/simplex-core-architecture'],R)==git(['ls-remote','origin','refs/heads/codex/simplex-core-architecture'],R).split()[0]==remote_diagnostic,'diagnostic tracking/live ref')
def baseline_and_backup():
 b=read('baseline-tree.json');need({str(p.relative_to(D/'baseline')):sha(p) for p in (D/'baseline').rglob('*') if p.is_file()}==b,'full baseline snapshot')
 need(tree(M)=={n:h for n,h in b.items() if n.startswith(('src/','test/'))},'whole restored baseline source/test')
 co=read('production-commit.json');need(co['commit']==CAND and co['parent']==BASE,'candidate record')
 need(git(['diff-tree','--no-commit-id','--name-only','-r',CAND]).splitlines()==co['names'],'exact four candidate paths')
 for n,v in co['blobs'].items():need(git(['rev-parse',CAND+':'+n])==v and raw(['show',CAND+':'+n])==(D/'GREEN'/n).read_bytes()==(D/'rollback-before'/n).read_bytes(),'preserved candidate '+n)
 for t in ['src','test']:
  current={str(p.relative_to(D/'GREEN')) for p in (D/'GREEN'/t).rglob('*') if p.is_file()}
  need(current=={n for n in b if n.startswith(t+'/')}|{n for n in co['names'] if n.startswith(t+'/')},'full candidate membership')
  for n in current:
   expected=hashlib.sha256(raw(['show',CAND+':'+n])).hexdigest() if n in co['names'] else b[n]
   need(sha(D/'GREEN'/n)==expected,'candidate tree '+n)
 need(not git(['diff','--name-only','HEAD','--','src','test','Project.toml']),'baseline clean')
def protected(after_continuations=False,after_staging=False):
 original=read('protected-before.json');rolled=read('rollback-after.json')
 hist=read('negative-historical-map.json') if after_continuations else None
 for p,h in original['files'].items():
  if hist and p in hist['continuation_before']:
   entry=hist['continuation_before'][p];need(entry['sha256']==h==sha(entry['before']),'exact continuation old hash')
   need(Path(p).read_bytes().endswith(Path(entry['before']).read_bytes()),'verbatim continuation')
  else:need(sha(p)==h,'protected file '+p)
 ridx=git(['rev-parse','--path-format=absolute','--git-path','index'],R)
 for p,h in rolled['current_indexes'].items():
  if after_staging and p==ridx:continue
  need(sha(p)==h,'protected index '+p)
 before=read('rollback-before.json');names=read('production-commit.json')['names']
 entries=[r.decode() for r in raw(['ls-files','--stage','-z']).split(b'\0') if r and r.split(b'\t',1)[1].decode() not in names]
 need(entries==before['unrelated_index_entries'] and raw(['diff','--cached','--raw','-z']).hex()==before['cached_diff_raw'],'unrelated staged/index')
 need(raw(['ls-files','--others','--exclude-standard','-z']).hex()==before['untracked'],'untracked user membership')
class Historical:
 def __init__(self):self.used={};self.cache={}
 def digest(self,p):
  p=str(p)
  if p not in self.cache:self.cache[p]=sha(p)
  return self.cache[p]
 def resolve(self,p,h,resolved=None):
  p=Path(p);need(p.is_absolute(),'absolute binding '+str(p))
  # Current path resolution is checked even if the newly introduced file is absent.
  if resolved is not None:need(str(p.resolve(strict=False))==resolved,'original canonical path '+str(p))
  if p.is_file() and self.digest(p)==h:return str(p)
  candidates=[];ri=read('rollback-before.json');im=read('integration-historical-path-map.json');nm=read('negative-historical-map.json')
  for mapping in [ri['source_before'],ri['index_before'],im['source_before'],im['master_index_before'],nm['continuation_before'],read('negative-diagnostic-index-before.json')]:
   if str(p) in mapping:
    e=mapping[str(p)]
    if e['sha256']==h:candidates.append(Path(e['before']))
  if p.is_relative_to(M/'src') or p.is_relative_to(M/'test'):candidates.extend([D/'baseline'/p.relative_to(M),D/'rollback-before'/p.relative_to(M)])
  if p in [D/'WORK-MEMORY.md',D/'PLAN.md']:candidates.append(Path(str(p)+'.before-review'))
  if p==D/'DESIGN.md':candidates.append(D/'DESIGN.md.before-owner-clarification')
  for q in candidates:
   if q.is_file() and self.digest(q)==h:
    self.used[str(p)+'@'+h]=str(q);return str(q)
  raise RuntimeError('unresolved exact historical binding '+str(p)+' @ '+h)
 def manifest(self,n):
  pins=read(n);need(set(pins['files'])==set(pins['inventory']),'manifest membership '+n)
  for p,v in pins['inventory'].items():self.resolve(p,v['sha256'],v['resolved'])
  for t in pins['trees']:
   t=Path(t);expected={str(Path(p).relative_to(t)) for p in pins['inventory'] if Path(p).is_relative_to(t)}
   candidates=[t]
   if t==M/'src' or t==M/'test':candidates.extend([D/'baseline'/t.relative_to(M),D/'GREEN'/t.relative_to(M)])
   matched=[q for q in candidates if q.is_dir() and {str(p.relative_to(q)) for p in q.rglob('*') if p.is_file()}==expected]
   need(matched,'exact historical tree membership '+str(t))
  return len(pins['inventory'])
def artifacts(exclude=()):
 return sorted([p for p in D.rglob('*') if p.is_file() and p.relative_to(D).parts[0] not in PRIVATE and '__pycache__' not in p.parts and p.name not in {'negative-closure.json','negative-publication-plan.json','negative-publication-after.json',*exclude}],key=str)
