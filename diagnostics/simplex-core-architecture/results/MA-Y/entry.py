from pathlib import Path
import hashlib,json,subprocess,time
R=Path.cwd();X=R/'diagnostics/simplex-core-architecture/results/MA-X';D=X.with_name('MA-Y')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def save(p,o):
 with p.open('x') as f:json.dump(o,f,indent=2);f.write('\n')
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
h=rd(X/'host.json');pins=rd(X/'pins.json');pub=rd(X/'publication.json');rev=rd(X/'admission-review.json');groups=h['groups'];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  f=(p/'stat').read_text().rsplit(')',1)[1].split()
  if int(f[2]) in groups or int(f[3]) in groups or (p/'exe').resolve().name.startswith('julia'):matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'),boot_id=boot))
 except (FileNotFoundError,ProcessLookupError):pass
refs={k:git(*a) for k,a in {'head':['rev-parse','HEAD'],'master':['rev-parse','master'],'branch':['branch','--show-current'],'remote':['ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture']}.items()}
checks=dict(head=refs['head']=='aac5075afcf45f527996edf1a77972ccb48b6cea',master=refs['master']=='6f68e24e8ddac42b948da8fcc2d636c010751194',remote=set(refs['remote'].splitlines())=={refs['head']+'\trefs/heads/'+refs['branch'],refs['master']+'\trefs/heads/master'},no_stage=not git('diff','--cached','--name-only'),tracked_clean=not git('diff','--name-only','HEAD'),host170=len(groups)==170 and not matches,source514=len(h['master_identity'])==514 and all(sha(R/p)==v for p,v in h['master_identity'].items()),protected6=len(h['protected'])==6 and all(sha(p)==v for p,v in h['protected'].items()),all4375=len(pins['inventory'])==4375 and all(sha(p)==v['sha256'] and str(Path(p).resolve())==v['resolved'] for p,v in pins['inventory'].items()),membership=set(rd(X/'required-paths.json'))==set(pins['files'])==set(pins['inventory'])==set(pins['files'])|{str(p) for root in pins['trees'] for p in Path(root).rglob('*') if p.is_file()},exact45=len(pub['exact_names'])==45 and set(git('diff-tree','--no-commit-id','--name-only','-r','HEAD').splitlines())==set(pub['exact_names']) and all(git('rev-parse','HEAD:'+n)==git('hash-object','--',n) for n in pub['exact_names']),unused=not any((X/n).exists() for n in ['launch-context.json','numerical-review.json','sequence-reservation.json','reservation-1.json','run-1','run-2','run-3']),accepted_review=rev['accepted'] is True and rev['findings']==[] and rev['pins_sha256']==sha(X/'pins.json'))
for n in ('admission-review.json','review-check.json','closure.json','publication.json','continuation.json'):
 o=rd(X/n);checks[n]=all(sha(p)==v for p,v in o['sha256'].items())
mem={line.split(':')[0]:int(line.split()[1]) for line in Path('/proc/meminfo').read_text().splitlines()};memory=dict(available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree']);checks['memory']=memory['available_kib']>=6*1024**2 and memory['swap_used_kib']<=1024**2
if not all(checks.values()):raise SystemExit(str(checks))
D.mkdir(exist_ok=False)
with (D/'entry.py').open('xb') as f:f.write(Path(__file__).read_bytes())
maps=[]
for p,n in [(R/'diagnostics/simplex-core-architecture/STATUS.md','STATUS.md.before-MA-Y'),(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md','roadmap.md.before-MA-Y')]:
 q=D/n
 with q.open('xb') as f:f.write(p.read_bytes())
 for name in ('closure.json','publication.json','continuation.json'):
  v=rd(X/name)['sha256'][str(p)]
  if sha(q)!=v:raise ValueError('beforecopy')
  maps.append(dict(source=str(X/name),path=str(p),preserved=str(q),sha256=v))
save(D/'continuation-map.json',dict(old_bindings=maps,scope='Only MA-X current closure/publication/continuation STATUS/roadmap bindings; older maps unchanged'))
save(D/'host.json',dict(time=time.time(),refs=refs,boot_id=boot,groups=groups,matches=matches,memory=memory,master_identity=h['master_identity'],protected=h['protected']))
context=dict(refs=refs,boot_id=boot,groups=groups,matches=matches,standing_short_run_permission=True,maximum_processes=3,maximum_seconds_per_process=90,total_cap_seconds=270,no_retry=True,authorization='Direct human request: proceed with MA-Y, verify launch conditions, independently approve exact run and execute short tests/measurement under accepted MA-W Task2 and MA-X admission.',host_sha256=sha(D/'host.json'),pins_sha256=sha(X/'pins.json'),preparation_review_sha256=sha(X/'admission-review.json'))
save(X/'launch-context.json',context)
save(D/'entry.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(p):sha(p) for p in [D/'entry.py',D/'host.json',D/'continuation-map.json',X/'launch-context.json',X/'pins.json',X/'admission-review.json',X/'closure.json',X/'publication.json']}))
print(json.dumps(dict(checks=checks,maps=len(maps),memory=memory)))
