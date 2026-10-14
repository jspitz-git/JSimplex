from pathlib import Path
import json,hashlib,subprocess,time
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/MA-S-2';S=E.with_name('MA-S');L=E.with_name('MA-S-LOAD')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def save(n,o):
 with (E/n).open('x') as f:json.dump(o,f,indent=2);f.write('\n')
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
h=read(S/'host.json');pins=read(S/'pins-reviewed.json');rev=read(L/'review.json');groups=read(L/'entry.json')['host']['groups']
refs={k:git(*a) for k,a in {'head':['rev-parse','HEAD'],'master':['rev-parse','master'],'branch':['branch','--show-current'],'remote':['ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture']}.items()}
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  f=(p/'stat').read_text().rsplit(')',1)[1].split();pgid,sid=int(f[2]),int(f[3]);exe=(p/'exe').resolve().name
  if pgid in groups or sid in groups or exe.startswith('julia'):matches.append(dict(pid=int(p.name),pgid=pgid,sid=sid,start_ticks=int(f[19]),boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,ProcessLookupError):pass
checks={'base':refs['head']=='b1555a413facab8337ecaf331ac993b994920071','master':refs['master']==h['refs']['master'],'remote':set(refs['remote'].splitlines())=={refs['head']+'\trefs/heads/'+refs['branch'],refs['master']+'\trefs/heads/master'},'linked_worktree':git('rev-parse','--git-dir')!=git('rev-parse','--git-common-dir') and not git('rev-parse','--show-superproject-working-tree'),'tracked_clean':not git('diff','--name-only','HEAD'),'full160groups_ANDsessions_noJulia':len(groups)==160 and not matches,'source514':len(h['master_identity'])==514 and all(sha(R/p)==s for p,s in h['master_identity'].items()),'protected6':len(h['protected'])==6 and all(sha(p)==s for p,s in h['protected'].items()),'old4262pins':len(pins['inventory'])==4262 and all(sha(p)==v['sha256'] and str(Path(p).resolve())==v['resolved'] for p,v in pins['inventory'].items()),'loader_review40':rev['accepted'] is True and rev['findings']==[] and len(rev['sha256'])==40 and all(sha(p)==s for p,s in rev['sha256'].items()),'failed_sequence_preserved':read(S/'audit-1.json')['all_passed'] is False and read(S/'run-1/process.json')['returncode']==1,'unused_new_sequence':not any((E/n).exists() for n in ['run-1','run-2','run-3','launch-context.json','numerical-review.json','sequence-reservation.json'])}
if not all(checks.values()):raise SystemExit(str(checks))
maps=[]
for p,n in [(R/'diagnostics/simplex-core-architecture/STATUS.md','STATUS.md.before-MA-S-2'),(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md','roadmap.md.before-MA-S-2')]:
 q=E/n
 with q.open('xb') as f:f.write(p.read_bytes())
 for src in ['review.json','closure.json','publication.json']:
  s=read(L/src)['sha256'][str(p)]
  if sha(q)!=s:raise SystemExit('Mapping mismatch')
  maps.append(dict(source=str(L/src),path=str(p),preserved=str(q),sha256=s))
save('continuation-map.json',dict(old_bindings=maps,scope='Only LOAD review/closure/publication current continuation bindings; all older maps unchanged.'))
save('host.json',dict(time=time.time(),boot_id=boot,checks=checks,refs=refs,groups=groups,matches=matches,protected=h['protected'],master_identity=h['master_identity']))
paths=[E/'entry.py',E/'host.json',E/'continuation-map.json',L/'driver.jl',L/'review.json',L/'plan.md',S/'pins-reviewed.json',S/'audit-1.json',S/'run-1/raw.toml']
save('entry.json',dict(all_passed=True,checks=checks,sha256={str(p):sha(p) for p in paths}))
print(json.dumps(dict(checks=checks,bindings=len(paths))))
