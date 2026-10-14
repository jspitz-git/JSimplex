from pathlib import Path
import json,hashlib,subprocess,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-S-FALLBACK';S=D.with_name('MA-S-2')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def save(n,o):
 with (D/n).open('x') as f:json.dump(o,f,indent=2);f.write('\n')
refs={k:git(*a) for k,a in {'head':['rev-parse','HEAD'],'master':['rev-parse','master'],'branch':['branch','--show-current'],'remote':['ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture']}.items()}
h=rd(S/'host.json');post=rd(S/'execution-postcheck.json');groups=post['host']['groups'];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  f=(p/'stat').read_text().rsplit(')',1)[1].split()
  if int(f[2]) in groups or int(f[3]) in groups or (p/'exe').resolve().name.startswith('julia'):matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'),boot_id=boot))
 except (FileNotFoundError,ProcessLookupError):pass
checks={'head':refs['head']=='1d5117b69ff3313986a4d7c6cb7a79961c91cdee','master':refs['master']==h['refs']['master'],'remote':set(refs['remote'].splitlines())=={refs['head']+'\trefs/heads/'+refs['branch'],refs['master']+'\trefs/heads/master'},'tracked_clean':not git('diff','--name-only','HEAD'),'no_stage':not git('diff','--cached','--name-only'),'full166groups_ANDsessions_noJulia':len(groups)==166 and not matches,'source514':len(h['master_identity'])==514 and all(sha(R/p)==s for p,s in h['master_identity'].items()),'protected6':len(h['protected'])==6 and all(sha(p)==s for p,s in h['protected'].items()),'prior_review96':rd(S/'result-review.json')['accepted'] is True and len(rd(S/'result-review.json')['sha256'])==96 and all(sha(p)==s for p,s in rd(S/'result-review.json')['sha256'].items()),'prior_closure60':rd(S/'execution-closure.json')['all_passed'] is True and len(rd(S/'execution-closure.json')['sha256'])==60 and all(sha(p)==s for p,s in rd(S/'execution-closure.json')['sha256'].items()),'prior_publication61':rd(S/'execution-publication.json')['all_passed'] is True and len(rd(S/'execution-publication.json')['sha256'])==61 and all(sha(p)==s for p,s in rd(S/'execution-publication.json')['sha256'].items()),'rejected_gate_preserved':rd(S/'aggregate.json')['accepted'] is False,'raw_bound':all(all(sha(p)==s for p,s in rd(S/f'audit-{i}.json')['sha256'].items()) for i in (1,2,3))}
if not all(checks.values()):raise SystemExit(str(checks))
maps=[]
for p,n in [(R/'diagnostics/simplex-core-architecture/STATUS.md','STATUS.md.before-MA-S-FALLBACK'),(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md','roadmap.md.before-MA-S-FALLBACK')]:
 q=D/n
 with q.open('xb') as f:f.write(p.read_bytes())
 for name in ['result-review.json','execution-closure.json','execution-publication.json']:
  s=rd(S/name)['sha256'][str(p)]
  if sha(q)!=s:raise SystemExit('Mapping mismatch')
  maps.append(dict(source=str(S/name),path=str(p),preserved=str(q),sha256=s))
save('continuation-map.json',dict(old_bindings=maps,scope='Only six current MA-S-2 result review/execution closure/publication continuation bindings; all earlier mappings unchanged.'))
save('host.json',dict(time=time.time(),refs=refs,boot_id=boot,groups=groups,matches=matches,protected=h['protected'],master_identity=h['master_identity']))
paths=[D/'entry.py',D/'host.json',D/'continuation-map.json',S/'result-review.json',S/'execution-closure.json',S/'execution-publication.json',S/'aggregate.json']
save('entry.json',dict(all_passed=True,checks=checks,sha256={str(p):sha(p) for p in paths},scope='Read-only fresh entry and preserved continuation; no Julia or frozen script execution.'))
print(json.dumps(dict(checks=checks,bindings=len(paths))))
