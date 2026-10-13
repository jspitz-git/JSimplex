from pathlib import Path
import json,hashlib,subprocess,time
D=Path(__file__).resolve().parent;R=D.parents[3];P=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
review=json.loads((D/'closure-review.json').read_text())
if review.get('accepted') is not False or not review.get('unresolved_findings'):raise ValueError('preserved rejected review first')
# Fresh host check before correcting the pinned continuation, no Julia or old script.
h=json.loads((D/'postprocess.json').read_text())['host'];groups=set(h['groups']);matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();v=s[s.rfind(')')+2:].split();comm=(p/'comm').read_text().strip()
  if int(v[2]) in groups or int(v[3]) in groups or comm.lower().startswith('julia'):matches.append(dict(pid=p.name,pgid=int(v[2]),sid=int(v[3]),start_ticks=int(v[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except FileNotFoundError:pass
refs=[subprocess.check_output(['git','rev-parse',v],cwd=R,text=True).strip() for v in ['HEAD','master']]
if matches or Path('/proc/sys/kernel/random/boot_id').read_text().strip()!=h['boot_id'] or refs!=['c722a8dd0b7e66cc56b1cddecac8454ccdd94198','6f68e24e8ddac42b948da8fcc2d636c010751194']:raise ValueError('host/refs')
old=(D/'roadmap.md.before-MA-I').read_text();wrong=P.read_text();header='## Current continuation — 2026-10-14';a=old.index(header)+len(header);history=old.index('\n### Previous',a);end=old.index('\n## ',history)
wa=wrong.index(header)+len(header);we=wrong.index('\n## ',wa)
fixed=wrong[:we]+old[history:end]+wrong[we:]
checks={'four_historical_subsections':old[history:end].count('\n### Previous')==4,'only_current_MAH_prose_changed':fixed==old[:a]+wrong[wa:we]+old[history:],'historical_suffix_exact':fixed[fixed.index('\n### Previous',a):]==old[history:]}
if not all(checks.values()):raise ValueError(checks)
with (D/'roadmap.before-continuation-fix').open('xb') as f:f.write(P.read_bytes())
P.write_text(fixed)
paths=[P,D/'roadmap.before-continuation-fix',D/'roadmap.md.before-MA-I',D/'continuation.json',D/'closure-review.json',D/'closure-review.md',D/'closure-corrected.py',D/'publication-corrected.py',Path(__file__)]
with (D/'continuation-fix.json').open('x') as f:json.dump(dict(all_passed=True,checks=checks,sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},continuation_map={'continuation.json':{str(P):str(D/'roadmap.before-continuation-fix')}},host=dict(time=time.time(),boot_id=h['boot_id'],groups=sorted(groups),matches=matches),refs=refs,scope='Restore historical subsections exactly; original overbroad continuation and rejected review preserved, numerical evidence unchanged.'),f,indent=2);f.write('\n')
print(checks)
