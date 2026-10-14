from pathlib import Path
import json,hashlib,subprocess,time
R=Path.cwd(); B=R/'diagnostics/simplex-core-architecture'; P=B/'results/MA-Y-FALLBACK'; D=B/'results/PRESOLVE-EXACT-CACHE'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def req(v,m):
 if not v:raise SystemExit(m)
def save(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
h=rd(P/'host.json'); groups=h['groups']; boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  f=(p/'stat').read_text().rsplit(')',1)[1].split()
  if int(f[2]) in groups or int(f[3]) in groups or (p/'exe').resolve().name.startswith('julia'):
   matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'),boot_id=boot))
 except (FileNotFoundError,ProcessLookupError):pass
refs={k:git(*a) for k,a in {'head':['rev-parse','HEAD'],'master':['rev-parse','master'],'branch':['branch','--show-current'],'remote':['ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture']}.items()}
checks=dict(refs=refs['head']=='a0184621d7a936c806b1fe578820ec8881c57dd2' and refs['master']=='6f68e24e8ddac42b948da8fcc2d636c010751194',remote=set(refs['remote'].splitlines())=={refs['head']+'\trefs/heads/'+refs['branch'],refs['master']+'\trefs/heads/master'},tracked_clean=not git('diff','--name-only','HEAD'),staged_clean=not git('diff','--cached','--name-only'),no_julia_groups_sessions=len(groups)==176 and not matches,source514=len(h['master_identity'])==514 and all(sha(R/p)==v for p,v in h['master_identity'].items()),protected6=len(h['protected'])==6 and all(sha(p)==v for p,v in h['protected'].items()),new_directory=not D.exists())
req(all(checks.values()),str(checks));D.mkdir()
(D/'entry.py').write_bytes(Path(__file__).read_bytes());save(D/'host.json',dict(time=time.time(),refs=refs,boot_id=boot,groups=groups,matches=matches,master_identity=h['master_identity'],protected=h['protected']))
maps=[]
for p,n in [(B/'STATUS.md','STATUS.md.before-cache'),(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md','roadmap.md.before-cache')]:
 q=D/n;q.write_bytes(p.read_bytes())
 for name in ('closure','publication','continuation'):
  v=rd(P/(name+'.json'))['sha256'][str(p)];req(sha(q)==v,'beforemap')
  maps.append(dict(source=str(P/(name+'.json')),path=str(p),preserved=str(q),sha256=v))
save(D/'continuation-map.json',dict(old_bindings=maps,scope='Only MA-Y-FALLBACK current bindings; all older maps preserved.'));save(D/'entry.json',dict(checks=checks,all_passed=True,authorization='User requests testing second hypothesis: Float64 presolve exact conversions; standing short numerical authorization, no production integration.'))
print('Fresh preflight PASS; 176 groups/sessions absent; 514 source and 6 protected files unchanged.')
