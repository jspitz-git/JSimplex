from pathlib import Path
import hashlib,json,subprocess,time
R=Path.cwd();V=R/'diagnostics/simplex-core-architecture/results/MA-V';E=V.with_name('MA-V-EXEC')
E.mkdir(exist_ok=False)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def save(p,o):
 with p.open('x') as f:json.dump(o,f,indent=2);f.write('\n')
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
with (E/'entry.py').open('xb') as f:f.write(Path(__file__).read_bytes())
h=rd(V/'host.json');pins=rd(V/'pins.json');pub=rd(V/'publication.json');groups=h['groups'];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  f=(p/'stat').read_text().rsplit(')',1)[1].split()
  if int(f[2]) in groups or int(f[3]) in groups or (p/'exe').resolve().name.startswith('julia'):
   matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'),boot_id=boot))
 except (FileNotFoundError,ProcessLookupError):pass
refs={k:git(*a) for k,a in {'head':['rev-parse','HEAD'],'master':['rev-parse','master'],'branch':['branch','--show-current'],'remote':['ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture']}.items()}
checks=dict(head=refs['head']=='ec439d9c6c5cb80c64352e46fa91002deb583abb',master=refs['master']==h['refs']['master'],remote=set(refs['remote'].splitlines())=={refs['head']+'\trefs/heads/'+refs['branch'],refs['master']+'\trefs/heads/master'},no_stage=not git('diff','--cached','--name-only'),tracked_clean=not git('diff','--name-only','HEAD'),host166=len(groups)==166 and not matches,source514=len(h['master_identity'])==514 and all(sha(R/p)==v for p,v in h['master_identity'].items()),protected6=len(h['protected'])==6 and all(sha(p)==v for p,v in h['protected'].items()),all4342=len(pins['inventory'])==4342 and all(sha(p)==v['sha256'] and str(Path(p).resolve())==v['resolved'] for p,v in pins['inventory'].items()),exact61=len(pub['exact_names'])==61 and all(git('rev-parse','HEAD:'+n)==git('hash-object','--',n) for n in pub['exact_names']),unused=not any((V/n).exists() for n in ['launch-context.json','numerical-review.json','sequence-reservation.json','reservation-1.json','run-1','run-2']))
for n in ['admission-review.json','closure.json','publication.json']:
 o=rd(V/n);checks[n]=o['all_passed'] is True and all(sha(p)==v for p,v in o['sha256'].items())
checks['accepted_review']=rd(V/'admission-review.json')['accepted'] is True and rd(V/'admission-review.json')['findings']==[]
mem={line.split(':')[0]:int(line.split()[1]) for line in Path('/proc/meminfo').read_text().splitlines()};memory=dict(available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree']);checks['memory']=memory['available_kib']>=6*1024**2 and memory['swap_used_kib']<=1024**2
if not all(checks.values()):
 save(E/'entry-failure.json',dict(checks=checks));raise SystemExit(str(checks))
maps=[]
for p,n in [(R/'diagnostics/simplex-core-architecture/STATUS.md','STATUS.md.before-MA-V-execution'),(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md','roadmap.md.before-MA-V-execution')]:
 q=E/n
 with q.open('xb') as f:f.write(p.read_bytes())
 for name in ['admission-review.json','closure.json','publication.json']:
  o=rd(V/name)
  if str(p) in o['sha256']:
   v=o['sha256'][str(p)];
   if sha(q)!=v:raise ValueError('beforecopy')
   maps.append(dict(source=str(V/name),path=str(p),preserved=str(q),sha256=v,kind='sha256'))
 v=pins['inventory'][str(p)]['sha256'];maps.append(dict(source=str(V/'pins.json'),path=str(p),preserved=str(q),sha256=v,kind='inventory'))
save(E/'continuation-map.json',dict(old_bindings=maps,scope='ONLY MA-V current continuation preparation review/closure/publication/inventory bindings; older maps unchanged'))
save(E/'host.json',dict(time=time.time(),refs=refs,boot_id=boot,groups=groups,matches=matches,memory=memory,master_identity=h['master_identity'],protected=h['protected']))
context=dict(refs=refs,boot_id=boot,groups=groups,matches=matches,standing_short_run_permission=True,maximum_processes=2,maximum_seconds_per_process=90,total_cap_seconds=180,no_retry=True,authorization='Direct human request: verify MA-V launch conditions, obtain independent approval and execute short tests/measurement according to accepted plan.',host_sha256=sha(E/'host.json'),pins_sha256=sha(V/'pins.json'),preparation_review_sha256=sha(V/'admission-review.json'))
save(V/'launch-context.json',context)
save(E/'entry.json',dict(all_passed=True,checks=checks,sha256={str(p):sha(p) for p in [E/'entry.py',E/'host.json',E/'continuation-map.json',V/'launch-context.json',V/'pins.json',V/'admission-review.json',V/'closure.json',V/'publication.json']}))
print(json.dumps(dict(checks=checks,maps=len(maps),memory=memory)))
