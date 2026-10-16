"""One-shot OFFLINE closure, only after independent preparation acceptance."""
from pathlib import Path
import json,hashlib,subprocess,time
D=Path(__file__).resolve().parent;R=D.parents[3]
STATUS=R/'diagnostics/simplex-core-architecture/STATUS.md';ROAD=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
def rd(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def path(n):return Path(n) if Path(n).is_absolute() else R/n
def require(x,m):
 if not x:raise RuntimeError(m)
def save(p,z):
 with p.open('x') as f:json.dump(z,f,indent=2);f.write('\n')
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
review=rd(D/'review-final.json');pins=rd(D/'preparation-pins-reviewed.json')
require(review['accepted'] is True and review['findings']==[] and review['scope']=='offline integration preparation','Review not accepted')
require(review['pins_sha256']==sha(D/'preparation-pins-reviewed.json'),'Review manifest identity')
require(set(review['sha256'])==set(pins['sha256'])|{str((D/'preparation-pins-reviewed.json').relative_to(R))},'Review exact membership')
for z in [pins,review]:
 for field in ['sha256','evidence_sha256']:
  for n,h in z.get(field,{}).items():require(sha(path(n))==h,'Review/input binding changed '+n)
base=rd(D/'host.json');groups=base['groups'];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[];unreadable=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip();exe=''
  try:exe=str((p/'exe').resolve(strict=True))
  except PermissionError:unreadable.append(int(p.name))
  except FileNotFoundError:pass
  if int(s[2]) in groups or int(s[3]) in groups or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):
   matches.append(dict(pid=int(p.name),pgid=int(s[2]),sid=int(s[3]),start_ticks=int(s[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'),comm=comm,exe=exe,boot_id=boot))
 except (FileNotFoundError,ProcessLookupError):pass
h=dict(time=time.time(),boot_id=boot,groups=groups,matches=matches,unreadable_exe_pids=unreadable,head=git('rev-parse','HEAD'),master=git('rev-parse','master'),scope='Fresh stat/comm/readable-exe scan; unreadable system executable links are a visibility limit')
save(D/'closure-host.json',h)
require(not matches and len(groups)==216 and boot==base['boot_id'] and h['head']==base['head'] and h['master']==base['master'],'Host changed')
require(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'Tracked changes before closure')
require(sha(STATUS)==sha(D/'STATUS.md.before-integration') and sha(ROAD)==sha(D/'roadmap.md.before-integration'),'Continuation preimage')
for m in rd(D/'continuation-mappings.json')['mappings']:
 z=rd(R/m['record'])
 for k in m['pointer']:z=z[k]
 require(z==m['sha256']==sha(R/m['preserved_path']),'Continuation mapping')
text=(D/'continuation-text.md').read_text().strip()+'\n'
s=STATUS.read_text();a=s.index('## Exact next action\n');b=s.index('\n## ',a+1);STATUS.write_text(s[:a]+'## Exact next action\n\n'+text+s[b:])
ROAD.write_text(ROAD.read_text().rstrip()+'\n\n## Native pivot policy public integration preparation (2026-10-16)\n\n'+text)
names=rd(D/'publication-names.json')['names'];expected={str(p.relative_to(R)) for p in D.rglob('*') if p.is_file()}|{str(p.relative_to(R)) for p in [STATUS,ROAD,D/'closure.json',D/'publication.json']}
checks=dict(review_accepted=review['accepted'],host=not matches,exact_names=set(names)==expected and len(names)==len(expected),actual_source=all(sha(R/n)==v for n,v in rd(D/'actual-baseline.json')['sha256'].items()),no_stage=not (R/'.superpowers/native-pivot-integration').exists(),no_runs=not (D/'runs').exists(),source_check=rd(D/'source-check.json')['all_passed'],author_check=rd(D/'author-check.json')['all_passed'],mapping_count=len(rd(D/'continuation-mappings.json')['mappings'])==4,master=h['master']==base['master'])
files=[R/n for n in names if n not in [str((D/'closure.json').relative_to(R)),str((D/'publication.json').relative_to(R))]]
save(D/'closure.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(p.relative_to(R)):sha(p) for p in files},scope='Offline test/source preparation ONLY. Runtime correctness and Task3 integration remain UNEXECUTED.'))
require(all(checks.values()),'Closure failed; preserve');print(dict(checks=len(checks),bindings=len(files),names=len(names)))
