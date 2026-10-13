from pathlib import Path
import json,hashlib,subprocess,time
D=Path(__file__).resolve().parent;R=D.parents[3];P=R/'diagnostics/simplex-core-architecture/STATUS.md';Q=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
r=json.loads((D/'result-review.json').read_text());post=json.loads((D/'postprocess.json').read_text())
if r.get('accepted') is not True or r.get('unresolved_findings'):raise ValueError('result review not accepted')
h=post['host'];groups=set(h['groups']);matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();f=s[s.rfind(')')+2:].split();comm=(p/'comm').read_text().strip()
  if int(f[2]) in groups or int(f[3]) in groups or comm.lower().startswith('julia'):matches.append(dict(pid=p.name,pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except FileNotFoundError:pass
if matches or Path('/proc/sys/kernel/random/boot_id').read_text().strip()!=h['boot_id']:raise ValueError('host')
for src,before in [(P,D/'STATUS.md.before-MA-I'),(Q,D/'roadmap.md.before-MA-I')]:
 if src.read_bytes()!=before.read_bytes():raise ValueError('continuation before bytes')
refs=[subprocess.check_output(['git','rev-parse',k],cwd=R,text=True).strip() for k in ('HEAD','master')]
if refs!=['c722a8dd0b7e66cc56b1cddecac8454ccdd94198','6f68e24e8ddac42b948da8fcc2d636c010751194']:raise ValueError('refs')
text='''MA-I completed one admitted short22process attempt with the exact MA-H routing
candidate. RED2expected failures; qualification647/647,48finite fixtures/432rows,
route entries28constructors/28copies/56fullcalls including6expected throws.
All22stage audits and12postchecks PASS;1210pins unchanged;177portable files exact.
All1920steadywindows compile/recompile0;3GCwindows retained. Targets6/6pass,
controls8/32FAIL: complete-forward promotion is NOT ACCEPTED. No integration,
automatic tuning or repeated attempt. Correctness is component scoped, not a
solver/fullsuite/end-to-end speedup or causal explanation of each failed control.
Fresh independent gpt-6-astra admission and result reviews accepted diagnostic
scope with no unresolved findings or unnecessary new production work/memory.
Fresh134old/new PGIDs ANDsessions absent/noJulia; protectedfiles/master6f68e24
unchanged. See MA-MARKOWITZ-ROUTING-QUALIFICATION.md and results/MA-I.

MA-I allowance consumed; exact candidate/controls/manifest/raw/reviews frozen.
No next numerical attempt follows automatically. BroaderMA/S2/S3/S4/S5/S6 remain
OPEN. Proceed only with a genuinely different concrete admitted step; stopped
routes remain stopped. Standing human permission for short attempts persists,
no duplicate approval question, but new technical admission remains mandatory.
Automationpaused/CIoff/HHdisabled. MA-H current STATUS/roadmap bindings in closure,
publication and review map ONLY MA-I/STATUS.md.before-MA-I and roadmap.md.before-MA-I.
All older mapping chains and failures remain unchanged; original MA-I plan frozen.
'''
for p,header in [(P,'## Exact next action'),(Q,'## Current continuation — 2026-10-14')]:
 s=p.read_text();a=s.index(header)+len(header);b=s.index('\n## ',a);s=s[:a]+'\n\n'+text+s[b:]
 if p==P:s=s.replace('MA-F replacement correctness qualified: RED2expected,381assertions+48fixtures; targets6/6 benefit pass, controls6/32 fail; production promotion NOT accepted','MA-I routing correctness647/647+48fixtures; targets6/6pass, controls8/32FAIL; promotion NOT accepted; single allowance consumed')
 p.write_text(s)
with (D/'continuation.json').open('x') as f:json.dump(dict(all_passed=True,host=dict(time=time.time(),boot_id=h['boot_id'],groups=sorted(groups),matches=matches),refs=refs,sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [P,Q,D/'STATUS.md.before-MA-I',D/'roadmap.md.before-MA-I',Path(__file__)]}),f,indent=2);f.write('\n')
print('continuation updated after fresh host/refs and accepted result review')
