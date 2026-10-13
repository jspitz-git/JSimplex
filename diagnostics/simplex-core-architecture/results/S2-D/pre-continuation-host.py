from pathlib import Path
import json,subprocess,hashlib,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/S2-D'
old=json.loads((D/'host-before.json').read_text());groups=old['groups'];hits=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();v=s[s.rindex(')')+2:].split()
  if int(v[2]) in groups or int(v[3]) in groups or (p/'comm').read_text().strip().lower().startswith('julia'):hits.append({'pid':int(p.name),'pgid':int(v[2]),'sid':int(v[3]),'start_ticks':int(v[19]),'command':(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')})
 except FileNotFoundError:pass
refs={n:subprocess.check_output(['git','rev-parse',n],text=True).strip() for n in ['HEAD','master']}
remote=dict(line.split()[::-1] for line in subprocess.check_output(['git','ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'],text=True).splitlines())
user={p:hashlib.sha256(Path(p).read_bytes()).hexdigest()==v['sha256'] for p,v in old['user'].items()}
checks={'refs_unchanged':refs==old['refs'],'remote_equal':remote=={'refs/heads/master':refs['master'],'refs/heads/codex/simplex-core-architecture':refs['HEAD']},'full26_groups_and_sessions_absent':len(groups)==26 and not hits,'user6_unchanged':len(user)==6 and all(user.values()),'no_Julia':not hits}
out={'time_ns':time.time_ns(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'groups':groups,'matches':hits,'refs':refs,'remote':remote,'user':old['user'],'checks':checks,'all_passed':all(checks.values())}
with (D/'pre-continuation-host.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(checks)
if not out['all_passed']:raise SystemExit(1)
