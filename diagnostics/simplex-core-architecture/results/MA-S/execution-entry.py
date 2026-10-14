from pathlib import Path
import json,hashlib,subprocess,time
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/MA-S'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def require(v,m):
 if not v:raise SystemExit(m)
def save(p,o):
 with p.open('x') as f:json.dump(o,f,indent=2);f.write('\n')
h=json.loads((E/'host.json').read_text());pins=json.loads((E/'pins-reviewed.json').read_text());rev=json.loads((E/'admission-review-final.json').read_text())
refs={k:git(*a) for k,a in {'head':['rev-parse','HEAD'],'master':['rev-parse','master'],'branch':['branch','--show-current'],'remote':['ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture']}.items()}
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();groups=set(h['groups']);matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  f=(p/'stat').read_text().rsplit(')',1)[1].split();pgid,sid=int(f[2]),int(f[3]);exe=(p/'exe').resolve().name
  if pgid in groups or sid in groups or exe.startswith('julia'):matches.append(dict(pid=int(p.name),pgid=pgid,sid=sid,start_ticks=int(f[19]),boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,ProcessLookupError):pass
mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()};memory=dict(available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree'])
checks={'head':refs['head']=='34a34a7c09fa2c2ce714d044549cc1a727cf79e9','master':refs['master']==h['refs']['master'],'branch':refs['branch']==h['refs']['branch'],'remote':set(refs['remote'].splitlines())=={refs['head']+'\trefs/heads/'+refs['branch'],refs['master']+'\trefs/heads/master'},'tracked_clean':not git('diff','--name-only','HEAD'),'full158groups_ANDsessions_noJulia':len(groups)==158 and not matches,'memory':memory['available_kib']>=6*1024**2 and memory['swap_used_kib']<=1024**2,'protected6':len(h['protected'])==6 and all(sha(p)==s for p,s in h['protected'].items()),'master514':len(h['master_identity'])==514 and all(sha(R/p)==s for p,s in h['master_identity'].items()),'full4262pins':len(pins['inventory'])==4262 and all(sha(p)==v['sha256'] and str(Path(p).resolve())==v['resolved'] for p,v in pins['inventory'].items()),'review23':rev['accepted'] is True and rev['findings']==[] and len(rev['sha256'])==23 and all(sha(p)==s for p,s in rev['sha256'].items()),'exact_membership':set(json.loads((E/'required-paths-reviewed.json').read_text()))==set(pins['inventory'])==set(pins['files'])|{str(p) for root in pins['trees'] for p in Path(root).rglob('*') if p.is_file()},'unused_sequence':not any((E/n).exists() for n in ['launch-context.json','numerical-review.json','sequence-reservation.json','run-1','run-2','run-3'])}
require(all(checks.values()),str(checks))
context=dict(time=time.time(),boot_id=boot,refs=refs,groups=sorted(groups),matches=matches,memory=memory,standing_short_run_permission=True,maximum_processes=3,maximum_seconds_per_process=120,total_cap_seconds=360,exact_launcher=str(E/'launcher-reviewed.py'),pins_sha256=sha(E/'pins-reviewed.json'),preparation_review_sha256=sha(E/'admission-review-final.json'),authorization='Current human request: verify launch conditions and execute MA-S tests and short measurement under accepted plan. No retry or hours-long run.')
save(E/'launch-context.json',context)
mapitems=[]
for p,n in [(R/'diagnostics/simplex-core-architecture/STATUS.md','STATUS.md.before-MA-S-execution'),(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md','roadmap.md.before-MA-S-execution')]:
 q=E/n
 with q.open('xb') as f:f.write(p.read_bytes())
 for name in ['completion-check.json','closure.json','publication.json']:
  d=json.loads((E/name).read_text());s=d['sha256'][str(p)];require(sha(q)==s,'continuation drift');mapitems.append(dict(source=str(E/name),path=str(p),preserved=str(q),sha256=s))
save(E/'execution-continuation-map.json',dict(old_bindings=mapitems,scope='Only MA-S preparation current STATUS/roadmap hashes map here; all earlier maps unchanged.'))
save(E/'execution-entry.json',dict(checks=checks,all_passed=True,time=time.time(),sha256={str(E/n):sha(E/n) for n in ['execution-entry.py','launch-context.json','pins-reviewed.json','admission-review-final.json','commands.json','execution-continuation-map.json']}))
print(json.dumps(dict(checks=checks,memory=memory,head=refs['head'],boot_id=boot)))
