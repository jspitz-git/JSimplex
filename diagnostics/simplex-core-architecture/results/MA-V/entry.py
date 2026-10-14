from pathlib import Path
import hashlib,json,subprocess,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-V';P=D.with_name('MA-U')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def save(n,o):
 with (D/n).open('x') as f:json.dump(o,f,indent=2);f.write('\n')
h=rd(P/'host.json');groups=h['groups'];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  f=(p/'stat').read_text().rsplit(')',1)[1].split()
  if int(f[2]) in groups or int(f[3]) in groups or (p/'exe').resolve().name.startswith('julia'):
   matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'),boot_id=boot))
 except (FileNotFoundError,ProcessLookupError):pass
refs=dict(head=git('rev-parse','HEAD'),master=git('rev-parse','master'),branch=git('branch','--show-current'),remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'))
checks=dict(head=refs['head']=='e35dbd3b15c56e90ffc93d5f92f5635241cb9963',master=refs['master']==h['refs']['master'],remote=set(refs['remote'].splitlines())=={refs['head']+'\trefs/heads/'+refs['branch'],refs['master']+'\trefs/heads/master'},tracked_clean=not git('diff','--name-only','HEAD'),no_stage=not git('diff','--cached','--name-only'),host166=len(groups)==166 and not matches,source514=len(h['master_identity'])==514 and all(sha(R/p)==v for p,v in h['master_identity'].items()),protected6=len(h['protected'])==6 and all(sha(p)==v for p,v in h['protected'].items()))
for n in ['review.json','closure.json','publication.json']:
 o=rd(P/n);checks[n]=o['all_passed'] is True and all(sha(p)==v for p,v in o['sha256'].items())
checks['source_green34']=len(rd(P/'source-green.json')['sha256'])==34 and all(sha(p)==v for p,v in rd(P/'source-green.json')['sha256'].items())
checks['accepted_plan']=rd(P/'review.json')['accepted'] is True and rd(P/'review.json')['findings']==[]
checks['isolated_branch']=refs['branch']=='codex/simplex-core-architecture' and git('rev-parse','--git-dir')!=git('rev-parse','--git-common-dir') and not git('rev-parse','--show-superproject-working-tree')
if not all(checks.values()):raise SystemExit(str(checks))
maps=[]
for p,n in [(R/'diagnostics/simplex-core-architecture/STATUS.md','STATUS.md.before-MA-V'),(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md','roadmap.md.before-MA-V')]:
 q=D/n
 with q.open('xb') as f:f.write(p.read_bytes())
 for name in ['review.json','closure.json','publication.json']:
  v=rd(P/name)['sha256'][str(p)]
  if sha(q)!=v:raise SystemExit('mapping mismatch')
  maps.append(dict(source=str(P/name),path=str(p),preserved=str(q),sha256=v))
save('continuation-map.json',dict(old_bindings=maps,scope='ONLY six MA-U current review/closure/publication continuation bindings; all older maps unchanged'))
save('host.json',dict(time=time.time(),refs=refs,boot_id=boot,groups=groups,matches=matches,master_identity=h['master_identity'],protected=h['protected']))
save('entry.json',dict(all_passed=True,checks=checks,sha256={str(p):sha(p) for p in [D/'entry.py',D/'host.json',D/'continuation-map.json',P/'review.json',P/'closure.json',P/'publication.json']}))
print(json.dumps(checks))
