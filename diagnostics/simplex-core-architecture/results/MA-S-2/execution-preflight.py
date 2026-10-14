from pathlib import Path
import json,hashlib,subprocess,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-S-2'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def save(n,o):
 with (D/n).open('x') as f:json.dump(o,f,indent=2);f.write('\n')
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def bound(o):return all(sha(p)==s for p,s in o['sha256'].items())
h=rd(D/'host.json');pins=rd(D/'pins.json');rev=rd(D/'admission-review.json');groups=h['groups']
refs={k:git(*a) for k,a in {'head':['rev-parse','HEAD'],'master':['rev-parse','master'],'branch':['branch','--show-current'],'remote':['ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture']}.items()}
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  f=(p/'stat').read_text().rsplit(')',1)[1].split();exe=(p/'exe').resolve().name
  if int(f[2]) in groups or int(f[3]) in groups or exe.startswith('julia'):matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,ProcessLookupError):pass
mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()};memory=dict(available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree'])
checks={'published_head':refs['head']=='cfe00c83a1723d5bfce4da663e6bac8606ddad16','master':refs['master']==h['refs']['master'],'remote':set(refs['remote'].splitlines())=={refs['head']+'\trefs/heads/'+refs['branch'],refs['master']+'\trefs/heads/master'},'clean':not git('diff','--name-only','HEAD'),'full160groups_ANDsessions_noJulia':len(groups)==160 and not matches,'memory':memory['available_kib']>=6*1024*1024 and memory['swap_used_kib']<=1024*1024,'source514':len(h['master_identity'])==514 and all(sha(R/p)==s for p,s in h['master_identity'].items()),'protected6':len(h['protected'])==6 and all(sha(p)==s for p,s in h['protected'].items()),'pins4304':len(pins['inventory'])==4304 and all(sha(p)==v['sha256'] and str(Path(p).resolve())==v['resolved'] for p,v in pins['inventory'].items()),'membership':set(rd(D/'required-paths.json'))==set(pins['inventory'])==set(pins['files'])|{str(p) for root in pins['trees'] for p in Path(root).rglob('*') if p.is_file()},'review73':rev['accepted'] is True and rev['findings']==[] and len(rev['sha256'])==73 and bound(rev),'closure29':rd(D/'closure.json')['all_passed'] is True and bound(rd(D/'closure.json')),'publication30':rd(D/'publication.json')['all_passed'] is True and bound(rd(D/'publication.json')),'unused':not any((D/n).exists() for n in ['launch-context.json','numerical-review.json','sequence-reservation.json','run-1','run-2','run-3'])}
if not all(checks.values()):raise SystemExit(str(checks))
context=dict(time=time.time(),boot_id=boot,refs=refs,groups=groups,matches=matches,memory=memory,standing_short_run_permission=True,maximum_processes=3,maximum_seconds_per_process=120,total_cap_seconds=360,exact_launcher=str(D/'launcher.py'),pins_sha256=sha(D/'pins.json'),preparation_review_sha256=sha(D/'admission-review.json'),authorization='Human requested next step after accepted MA-S-2 preparation. Standing permission for short numerical attempts without another question; no retry/tuning under this fixed sequence.')
save('launch-context.json',context)
for p,n in [(R/'diagnostics/simplex-core-architecture/STATUS.md','STATUS.md.before-MA-S-2-execution'),(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md','roadmap.md.before-MA-S-2-execution')]:
 with (D/n).open('xb') as f:f.write(p.read_bytes())
paths=[D/n for n in ['execution-preflight.py','launch-context.json','STATUS.md.before-MA-S-2-execution','roadmap.md.before-MA-S-2-execution','admission-review.json','pins.json','required-paths.json','closure.json','publication.json']]
save('execution-preflight.json',dict(all_passed=True,checks=checks,sha256={str(p):sha(p) for p in paths}))
print(json.dumps(dict(checks=checks,memory=memory,groups=len(groups),bindings=len(paths))))
