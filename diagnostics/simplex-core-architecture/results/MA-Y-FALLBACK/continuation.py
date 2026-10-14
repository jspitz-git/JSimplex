from pathlib import Path
import json,hashlib,time,subprocess
R=Path.cwd();B=R/'diagnostics/simplex-core-architecture';D=B/'results/MA-Y-FALLBACK'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def require(ok,msg):
 if not ok:raise SystemExit(msg)
def save(p,obj):
 with p.open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
review=rd(D/'review.json');require(review['accepted'] is True and not review['findings'],'independent review');require(all(sha(p)==h for p,h in review['sha256'].items()),'review bindings')
host=rd(D/'host.json');boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();groups=host['groups'];matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  f=(p/'stat').read_text().rsplit(')',1)[1].split()
  if int(f[2]) in groups or int(f[3]) in groups or (p/'exe').resolve().name.startswith('julia'):
   matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'),boot_id=boot))
 except (FileNotFoundError,ProcessLookupError):pass
refs={k:subprocess.check_output(['git','rev-parse',v],text=True).strip() for k,v in [('head','HEAD'),('master','master')]}
require(refs['head']==host['refs']['head'] and refs['master']==host['refs']['master'] and len(groups)==176 and not matches,'fresh host refs/groups')
for item in rd(D/'continuation-map.json')['old_bindings']:require(sha(item['path'])==sha(item['preserved'])==item['sha256'],'continuation beforecopy')
status=B/'STATUS.md';road=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
text='''MA-Y-FALLBACK completed: direct human-requested SOURCE/STORED-EVIDENCE analysis
of both MA-Y failed controls; no Julia or measurement/old-auditor rerun.
See MA-DENSELU-COMPLETE-FALLBACK-ANALYSIS.md and results/MA-Y-FALLBACK/review.
New20checks/36readtime hashes (13original launch-bound) cover480control pairs,
336measured/144warm and960windows with exact two-record journal linkage.
Scoped BigFloat: all42measured pairs equal bytes/events; old MA-S-2 added
128bytes/8events absent. Process3 BTRAN reference median=pair7,299.575us,
candidate=pair5,351.150us; two excess windows4/7 have no recorded GC/compile
and opposite order. Rank arithmetic explained; runtime timing cause unresolved.
Rational:20positive/18negative/4zero byte deltas across42pairs, all events equal;
process3 FTRAN side median+32bytes versus paired delta median+48, not fixed
per-call overhead. Source rejects Rational before rounding/scratch/MA; saved
native usable-size accounting is compatible, not captured causal attribution.
No numerical defect, guaranteed zero guard time, allocator-cause or speedup proof.

MA-Y remains NOT ACCEPTED, allowance consumed, both failed gates unchanged.
This bounded requested investigation is complete; do not repeat equivalent
inventories or the unchanged52-case run. No candidate/driver/admission/retry or
Task3 production integration is opened. Any future causal observation needs a
separate concrete reviewed design; broader plan remains OPEN. CIoff/HHdisabled/
automationpaused unchanged, master6f68e24 unchanged.

Fresh176groups ORsessions/noJulia/refs verified before continuation changes.
MA-Y current closure/publication/continuation STATUS/roadmap hashes map ONLY to
MA-Y-FALLBACK beforecopies (six exact bindings). Older X/Y and earlier maps stay.
All prior and new analysis scripts/raw/reviews remain FROZEN NEVER RERUN/rewrite.
Before future continuation/numerical work require fresh host identities and refs.

## Previous MA-Y qualification (completed, rejected)

'''
s=status.read_text();needle='## Exact next action\n\n';require(s.count(needle)==1,'status anchor');status.write_text(s.replace(needle,needle+text,1))
with road.open('a') as f:f.write('\n## MA-Y-FALLBACK: completed offline failure analysis\n\n'+text.split('## Previous MA-Y qualification')[0].rstrip()+'\n')
save(D/'continuation.json',dict(all_passed=True,scope='Stored-evidence decision only; MA-Y remains rejected',host=dict(time=time.time(),boot_id=boot,groups=groups,matches=matches,refs=refs),sha256={str(p):sha(p) for p in [Path(__file__).resolve(),D/'review.json',D/'review.md',D/'analysis.json',D/'continuation-map.json',status,road]}))
print('Continuation preserved and updated; six exact maps; fresh176groups/sessions absent')
