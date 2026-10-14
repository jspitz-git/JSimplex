from pathlib import Path
import hashlib,json,subprocess,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-X';V=D.with_name('MA-W')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def save(p,o):
 with p.open('x') as f:json.dump(o,f,indent=2);f.write('\n')
h=rd(V/'host.json');source=h;boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  f=(p/'stat').read_text().rsplit(')',1)[1].split()
  if int(f[2]) in h['groups'] or int(f[3]) in h['groups'] or (p/'exe').resolve().name.startswith('julia'):
   matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,ProcessLookupError):pass
refs={k:git(*a) for k,a in {'head':['rev-parse','HEAD'],'master':['rev-parse','master'],'branch':['branch','--show-current'],'remote':['ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture']}.items()}
checks=dict(head=refs['head']=='bb705c15c16480225df86bf803d71835f322ed18',master=refs['master']==h['refs']['master'],remote=set(refs['remote'].splitlines())=={refs['head']+'\trefs/heads/'+refs['branch'],refs['master']+'\trefs/heads/master'},tracked_clean=not git('diff','--name-only','HEAD'),stage_clean=not git('diff','--cached','--name-only'),host170=len(h['groups'])==170 and not matches and boot==h['boot_id'],source514=len(source['master_identity'])==514 and all(sha(R/p)==v for p,v in source['master_identity'].items()),protected6=len(source['protected'])==6 and all(sha(p)==v for p,v in source['protected'].items()))
for n in ('review.json','closure.json','publication.json','continuation.json'):
 o=rd(V/n);checks[n]=all(sha(p)==v for p,v in o['sha256'].items())
checks['accepted']=rd(V/'review.json')['accepted'] is True and rd(V/'review.json')['findings']==[]
pub=rd(V/'publication.json');checks['committed23']=len(pub['exact_names'])==23 and set(git('diff-tree','--no-commit-id','--name-only','-r','HEAD').splitlines())==set(pub['exact_names']) and all(git('rev-parse','HEAD:'+n)==git('hash-object','--',n) for n in pub['exact_names'])
if not all(checks.values()):raise SystemExit(str(checks))
D.mkdir(exist_ok=False)
with (D/'entry.py').open('xb') as f:f.write(Path(__file__).read_bytes())
maps=[]
for p,name in [(R/'diagnostics/simplex-core-architecture/STATUS.md','STATUS.md.before-MA-X'),(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md','roadmap.md.before-MA-X')]:
 q=D/name
 with q.open('xb') as f:f.write(p.read_bytes())
 for n in ('closure.json','publication.json','continuation.json'):
  old=rd(V/n)['sha256'][str(p)]
  if old!=sha(q):raise SystemExit('map')
  maps.append(dict(source=str(V/n),path=str(p),preserved=str(q),sha256=old))
save(D/'continuation-map.json',dict(old_bindings=maps,scope='Only MA-W current closure/publication/continuation STATUS and roadmap bindings; all older maps unchanged'))
save(D/'host.json',dict(time=time.time(),refs=refs,boot_id=boot,groups=h['groups'],matches=matches,master_identity=source['master_identity'],protected=source['protected']))
save(D/'entry.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(p):sha(p) for p in [D/'entry.py',D/'host.json',D/'continuation-map.json',V/'review.json',V/'closure.json',V/'publication.json']}))
print('entry',len(checks),'PASS; six continuation maps; no Julia')
