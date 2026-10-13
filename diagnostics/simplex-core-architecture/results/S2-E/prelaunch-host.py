from pathlib import Path
import json,subprocess,time,hashlib
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/S2-E';D=E.parent/'S2-D'
a=json.loads((D/'allowance.json').read_text());old=json.loads((E/'host-before.json').read_text());groups=set(old['groups']);hits=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();v=s[s.rindex(')')+2:].split()
  if int(v[2]) in groups or int(v[3]) in groups or (p/'comm').read_text().strip().lower().startswith('julia'):hits.append({'pid':int(p.name),'pgid':int(v[2]),'sid':int(v[3]),'start_ticks':int(v[19]),'command':(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')})
 except FileNotFoundError:pass
refs={p:subprocess.check_output(['git','-C',p,'rev-parse','HEAD'],text=True).strip() for p in a['refs']}
remote=dict(line.split()[::-1] for line in subprocess.check_output(['git','ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'],text=True).splitlines())
user={p:hashlib.sha256(Path(p).read_bytes()).hexdigest()==v['sha256'] for p,v in old['user'].items()}
review=json.loads((E/'seal-review.json').read_text())
checks={'accepted_seal_review':review['accepted'] is True and review['all_passed'] is True and review['unresolved_findings']==[] and all(review['checks'].values()),'seal_review_bindings':all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in review['sha256'].items()),'fresh_refs':refs==a['refs'],'fresh_remotes':remote==old['remote'],'full26_groups_AND_sessions_noJulia':len(groups)==26 and not hits,'user6':len(user)==6 and all(user.values()),'unconsumed_attempt':not Path(a['output']).exists() and not any((D/n).exists() for n in ['launcher.log','attempt-reserved.json','invocation.json','audit.json'])}
o={'checks':checks,'all_passed':all(checks.values()),'time_ns':time.time_ns(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'groups':sorted(groups),'matches':hits,'refs':refs,'remote':remote,'user':user,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
with (E/'prelaunch-host.json').open('x') as f:json.dump(o,f,indent=2);f.write('\n')
print(json.dumps(o))
if not o['all_passed']:raise SystemExit(1)
