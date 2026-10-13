from pathlib import Path
import json,hashlib,subprocess,time
H=Path(__file__).resolve().parent;R=H.parents[3];G=H.parent/'MA-G'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
h=json.loads((G/'host.json').read_text());groups=set(h['groups']);matches=[]
for p in Path('/proc').iterdir():
 if not p.name.isdecimal():continue
 try:
  stat=(p/'stat').read_text();v=stat[stat.rfind(')')+2:].split();cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace');comm=(p/'comm').read_text().strip()
 except (FileNotFoundError,PermissionError,ProcessLookupError):continue
 if int(v[2]) in groups or int(v[3]) in groups or comm.lower().startswith('julia'):matches.append({'pid':int(p.name),'pgid':int(v[2]),'sid':int(v[3]),'start_ticks':int(v[19]),'command':cmd})
refs={k:git(*a) for k,a in {'head':('rev-parse','HEAD'),'master':('rev-parse','master'),'branch':('branch','--show-current'),'git_dir':('rev-parse','--git-dir'),'common_dir':('rev-parse','--git-common-dir'),'superproject':('rev-parse','--show-superproject-working-tree'),'remote':('ls-remote','origin','refs/heads/codex/simplex-core-architecture','refs/heads/master')}.items()}
checks={'groups90_ANDsessions_noJulia':len(groups)==90 and not matches,'refs':refs['head']=='e04a83a93521dbe89252fa8cbb52181d02bbeb6b' and refs['master']=='6f68e24e8ddac42b948da8fcc2d636c010751194' and refs['branch']=='codex/simplex-core-architecture' and refs['remote']==refs['head']+'\trefs/heads/codex/simplex-core-architecture\n'+refs['master']+'\trefs/heads/master','linked_worktree':refs['git_dir']!=refs['common_dir'] and not refs['superproject'],'protected':all(sha(Path(k))==v for k,v in h['protected_sha256'].items()),'no_actual_changes':not git('diff','HEAD','--name-only','--','src','test','Project.toml','.github'),'empty_index':not git('diff','--cached','--name-only')}
for n in ['closure.json','publication.json','review.json']:
 d=json.loads((G/n).read_text());checks[n]=all(sha(Path(k) if Path(k).is_absolute() else R/k)==v for k,v in d['sha256'].items())
o={'all_passed':all(checks.values()),'checks':checks,'refs':refs,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'groups':sorted(groups),'matches':matches,'protected_sha256':h['protected_sha256'],'time':time.time(),'entry_sha256':sha(Path(__file__))}
with (H/'host.json').open('x') as f:json.dump(o,f,indent=2);f.write('\n')
print(json.dumps({'all_passed':o['all_passed'],'checks':checks},indent=2))
if not o['all_passed']:raise SystemExit(1)
for source,name in [(R/'diagnostics/simplex-core-architecture/STATUS.md','STATUS.md.before-MA-H'),(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md','roadmap.md.before-MA-H')]:
 with (H/name).open('xb') as f:f.write(source.read_bytes())
