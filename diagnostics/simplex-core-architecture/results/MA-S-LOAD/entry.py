from pathlib import Path
import json,hashlib,subprocess,time
R=Path.cwd();S=R/'diagnostics/simplex-core-architecture/results/MA-S';E=S.with_name('MA-S-LOAD')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def read(n):return json.loads((S/n).read_text())
def save(n,o):
 with (E/n).open('x') as f:json.dump(o,f,indent=2);f.write('\n')
refs={k:git(*a) for k,a in {'head':['rev-parse','HEAD'],'master':['rev-parse','master'],'branch':['branch','--show-current'],'remote':['ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture']}.items()}
h=read('host.json');pins=read('pins-reviewed.json');post=read('execution-postcheck.json');review=read('result-review.json');groups=set(post['host']['groups']);boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  f=(p/'stat').read_text().rsplit(')',1)[1].split();pgid,sid=int(f[2]),int(f[3]);exe=(p/'exe').resolve().name
  if pgid in groups or sid in groups or exe.startswith('julia'):matches.append(dict(pid=int(p.name),pgid=pgid,sid=sid,start_ticks=int(f[19]),boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,ProcessLookupError):pass
checks={'base':refs['head']=='f86674cde521d139c885e66ba64f77967f91cf64','master':refs['master']==h['refs']['master'],'remote':set(refs['remote'].splitlines())=={refs['head']+'\trefs/heads/'+refs['branch'],refs['master']+'\trefs/heads/master'},'linked_worktree':git('rev-parse','--git-dir')!=git('rev-parse','--git-common-dir') and not git('rev-parse','--show-superproject-working-tree'),'tracked_clean':not git('diff','--name-only','HEAD'),'full160groups_ANDsessions_noJulia':len(groups)==160 and not matches,'source514':len(h['master_identity'])==514 and all(sha(R/p)==s for p,s in h['master_identity'].items()),'protected6':len(h['protected'])==6 and all(sha(p)==s for p,s in h['protected'].items()),'pins4262':len(pins['inventory'])==4262 and all(sha(p)==v['sha256'] and str(Path(p).resolve())==v['resolved'] for p,v in pins['inventory'].items()),'review49':review['accepted'] is True and review['qualification_accepted'] is False and len(review['sha256'])==49 and all(sha(p)==s for p,s in review['sha256'].items()),'failed_run_preserved':read('audit-1.json')['all_passed'] is False and read('run-1/process.json')['returncode']==1,'no_later_run':not any((S/n).exists() for n in ['run-2','run-3','aggregate.json'])}
if not all(checks.values()):raise SystemExit(str(checks))
maps=[]
for p,n in [(R/'diagnostics/simplex-core-architecture/STATUS.md','STATUS.md.before-MA-S-LOAD'),(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md','roadmap.md.before-MA-S-LOAD')]:
 q=E/n
 with q.open('xb') as f:f.write(p.read_bytes())
 for source in ['result-review.json','execution-closure.json','execution-publication.json']:
  s=read(source)['sha256'][str(p)]
  if sha(q)!=s:raise SystemExit('Mapping mismatch')
  maps.append(dict(source=str(S/source),path=str(p),preserved=str(q),sha256=s))
save('continuation-map.json',dict(old_bindings=maps,scope='Only MA-S execution result-review/closure/publication current STATUS/roadmap hashes map here. All earlier maps remain.'))
base=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/base')
paths=[S/n for n in ['driver.jl','run-1/run.log','run-1/raw.toml','audit-1.json','result-review.json','execution-publication.json']]+[base/'Base_compiler.jl',base/'boot.jl',E/'entry.py',E/'continuation-map.json']
save('entry.json',dict(time=time.time(),checks=checks,all_passed=True,host=dict(refs=refs,boot_id=boot,groups=sorted(groups),matches=matches),sha256={str(p):sha(p) for p in paths},scope='Fresh read-only offline preparation preflight; no Julia or old script execution.'))
print(json.dumps({'checks':checks,'bindings':len(paths)}))
