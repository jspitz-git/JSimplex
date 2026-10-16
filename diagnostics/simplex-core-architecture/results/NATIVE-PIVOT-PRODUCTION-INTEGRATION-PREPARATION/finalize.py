"""One-shot closure after independent offline acceptance; no runtime launch."""
from pathlib import Path
import json,hashlib,subprocess,time
Q=Path(__file__).resolve().parent;R=Q.parents[3];B=Q.parent;T=B/'NATIVE-PIVOT-INTEGRATION-180-QUALIFICATION'
S=R/'diagnostics/simplex-core-architecture/STATUS.md';P=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md';PLAN=R/'docs/superpowers/plans/2026-10-16-native-pivot-production-integration.md'
def need(v,m):
 if not v:raise RuntimeError(m)
def rd(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,o):
 with p.open('x') as f:json.dump(o,f,indent=2);f.write('\n')
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
def path(s):return Path(s) if Path(s).is_absolute() else R/s
review=rd(Q/'review-final.json');need(review['accepted'] is True and not review['findings'],'Review rejected');need(review['scope']=='production integration preparation','Wrong scope')
for record in [rd(Q/'author-check.json'),review]:
 for p,h in record['sha256'].items():
  target=path(p)
  if record is not review and target==PLAN:target=Q/'plan.before-review.md'
  need(sha(target)==h,'Changed review input '+p)
fix=rd(Q/'review-fix.json');need(fix['all_passed'],'Review fix')
for p,h in fix['sha256'].items():need(sha(path(p))==h,'Changed amendment binding '+p)
need(git('rev-parse','HEAD')=='e20d4fd3018a778e853e6c03f1ed1f3063d69ab0','HEAD');need(git('rev-parse','master')=='6f68e24e8ddac42b948da8fcc2d636c010751194','master')
need(not git('diff','master','--name-only','--','src','test','.github','Project.toml'),'Actual files differ from master')
for p,h in rd(Q/'actual-baseline.json').items():need(sha(R/p)==h,'Actual changed '+p)
old=rd(Q/'host.json');groups=old['groups'];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[];unreadable=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  a=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip();exe=''
  try:exe=str((p/'exe').resolve(strict=True))
  except PermissionError:unreadable.append(int(p.name))
  except FileNotFoundError:pass
  if int(a[2]) in groups or int(a[3]) in groups or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):
   matches.append(dict(pid=int(p.name),pgid=int(a[2]),sid=int(a[3]),start_ticks=int(a[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'),comm=comm,exe=exe,boot_id=boot))
 except (FileNotFoundError,ProcessLookupError):pass
save(Q/'closure-host.json',dict(time=time.time(),boot_id=boot,groups=groups,matches=matches,unreadable_exe_pids=unreadable,scope=old['scope'],head=git('rev-parse','HEAD'),master=git('rev-parse','master')))
need(not matches and boot==old['boot_id'],'Host changed')
maps=[]
for f in [T/'closure.json',T/'publication.json']:
 for live,before in [(S,Q/'STATUS.md.before-production'),(P,Q/'roadmap.md.before-production')]:
  key=str(live.relative_to(R));h=rd(f)['sha256'][key];need(sha(before)==sha(live)==h,'Continuation binding')
  maps.append(dict(record=str(f.relative_to(R)),key=key,sha256=h,preserved=str(before.relative_to(R))))
need(len(maps)==4,'Four mappings');save(Q/'continuation-mappings.json',maps)
text=(Q/'continuation-text.md').read_text();s=S.read_text();start=s.index('## Exact next action\n')+len('## Exact next action\n');end=s.find('\n## ',start);need(end>start,'Missing next heading')
# Preserve historical text exactly; insert current instruction before earlier account.
S.write_text((s[:start]+'\n'+text+'\n### Historical previous continuation (superseded)\n'+s[start:]).replace('Updated: 2026-10-15.', 'Updated: 2026-10-16.', 1))
P.write_text(P.read_text().rstrip()+'\n\n## Native pivot production integration preparation (2026-10-16)\n\n'+text.rstrip()+'\n')
checks=dict(independent_review=True,review_bindings=True,actual513_unchanged=True,master_unchanged=True,prior220_groups_sessions_absent=True,no_julia=True,continuation_maps4=True,payload10_exact=len(rd(Q/'payload-manifest.json')['files'])==10,author8_pass=rd(Q/'author-check.json')['all_passed'],new_plan_bound=True)
need(all(checks.values()),'Closure failure')
pins={str(p.relative_to(R)):sha(p) for p in sorted(Q.rglob('*')) if p.is_file()}
for p in [PLAN,S,P]:pins[str(p.relative_to(R))]=sha(p)
save(Q/'closure.json',dict(all_passed=True,checks=checks,sha256=pins));print('Closure',len(checks),'PASS',len(pins),'bindings')
