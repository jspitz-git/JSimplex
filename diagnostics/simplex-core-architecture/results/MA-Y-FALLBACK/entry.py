from pathlib import Path
import json,hashlib,subprocess,time
R=Path.cwd(); B=R/'diagnostics/simplex-core-architecture'; Y=B/'results/MA-Y'; D=B/'results/MA-Y-FALLBACK'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rd(p): return json.loads(Path(p).read_text())
def git(*a): return subprocess.check_output(['git',*a],text=True).strip()
def save(p,obj):
 with p.open('x') as f: json.dump(obj,f,indent=2);f.write('\n')
def require(ok,msg):
 if not ok: raise SystemExit(msg)
h=rd(Y/'posthost.json'); base=rd(Y/'host.json'); groups=h['groups']; boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip(); matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  f=(p/'stat').read_text().rsplit(')',1)[1].split()
  if int(f[2]) in groups or int(f[3]) in groups or (p/'exe').resolve().name.startswith('julia'):
   matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'),boot_id=boot))
 except (FileNotFoundError,ProcessLookupError): pass
refs={k:git(*a) for k,a in {'head':['rev-parse','HEAD'],'master':['rev-parse','master'],'branch':['branch','--show-current'],'remote':['ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture']}.items()}
pub=rd(Y/'publication.json'); checks={
 'head':refs['head']=='db4f50c7aca3d3b243b6deaeccbf64e7df8c3a5c','master':refs['master']=='6f68e24e8ddac42b948da8fcc2d636c010751194',
 'remote':set(refs['remote'].splitlines())=={refs['head']+'\trefs/heads/'+refs['branch'],refs['master']+'\trefs/heads/master'},
 'clean_tracked':not git('diff','--name-only','HEAD'),'clean_stage':not git('diff','--cached','--name-only'),
 'no_julia_full176_groups_or_sessions':len(groups)==176 and not matches,
 'source514':len(base['master_identity'])==514 and all(sha(R/p)==v for p,v in base['master_identity'].items()),
 'protected6':len(base['protected'])==6 and all(sha(p)==v for p,v in base['protected'].items()),
 'prior_publication74':len(pub['sha256'])==74 and all(sha(p)==v for p,v in pub['sha256'].items()),
 'prior_committed75':len(pub['exact_names'])==75 and set(git('diff-tree','--no-commit-id','--name-only','-r','HEAD').splitlines())==set(pub['exact_names']) and all(git('rev-parse','HEAD:'+n)==git('hash-object','--',n) for n in pub['exact_names']),
 'prior_rejected':rd(Y/'result-review.json')['qualification_accepted'] is False and rd(Y/'closure.json')['qualification_accepted'] is False,
 'new_directory':not D.exists()}
require(all(checks.values()),str(checks));D.mkdir()
(D/'entry.py').write_bytes(Path(__file__).read_bytes())
save(D/'host.json',dict(time=time.time(),refs=refs,boot_id=boot,groups=groups,matches=matches,master_identity=base['master_identity'],protected=base['protected']))
maps=[]
for p,n in [(B/'STATUS.md','STATUS.md.before-MA-Y-FALLBACK'),(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md','roadmap.md.before-MA-Y-FALLBACK')]:
 q=D/n
 with q.open('xb') as f:f.write(p.read_bytes())
 for name in ('closure','publication','continuation'):
  v=rd(Y/(name+'.json'))['sha256'][str(p)];require(sha(q)==v,'before map')
  maps.append(dict(source=str(Y/(name+'.json')),path=str(p),preserved=str(q),sha256=v))
save(D/'continuation-map.json',dict(old_bindings=maps,scope='Only MA-Y current closure/publication/continuation bindings; all older maps remain unchanged.'))
save(D/'entry.json',dict(all_passed=True,checks=checks,scope='Human-requested stored-result/source analysis only; no Julia, old auditor, new measurement or candidate.',sha256={str(p):sha(p) for p in [D/'entry.py',D/'host.json',D/'continuation-map.json',Y/'publication.json',Y/'result-review.json',Y/'closure.json']}))
print('Fresh entry:',len(checks),'PASS;176groups/sessions clear; six beforecopy mappings')
