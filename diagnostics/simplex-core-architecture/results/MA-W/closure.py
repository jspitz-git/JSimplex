from pathlib import Path
import hashlib,json,subprocess,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-W';V=D.with_name('MA-V-EXEC')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def bound(o):return all(sha(p)==v for p,v in o['sha256'].items())
h=rd(D/'host.json');rev=rd(D/'review.json');maps=rd(D/'continuation-map.json')['old_bindings'];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  f=(p/'stat').read_text().rsplit(')',1)[1].split()
  if int(f[2]) in h['groups'] or int(f[3]) in h['groups'] or (p/'exe').resolve().name.startswith('julia'):
   matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,ProcessLookupError):pass
def oldbound(n):
 mm={m['path']:m['preserved'] for m in maps if m['source']==str(V/n)}
 return all(sha(mm.get(p,p))==v for p,v in rd(V/n)['sha256'].items())
checks=dict(review=rev['accepted'] is True and rev['findings']==[] and rev['all_computed_checks_passed'] is True and all(v is True for v in rev['computed_checks'].values()) and bound(rev),entry14=rd(D/'entry.json')['all_passed'] is True and len(rd(D/'entry.json')['checks'])==14 and bound(rd(D/'entry.json')),evidence19=rd(D/'evidence.json')['all_passed'] is True and len(rd(D/'evidence.json')['checks'])==19 and len(rd(D/'evidence.json')['sha256'])==33 and bound(rd(D/'evidence.json')),continuation=rd(D/'continuation.json')['all_passed'] is True and bound(rd(D/'continuation.json')),six_maps=len(maps)==6 and all(sha(m['preserved'])==m['sha256']==rd(m['source'])['sha256'][m['path']] for m in maps),prior_V=all(oldbound(n) for n in ('closure.json','publication.json','continuation.json')),source514=len(h['master_identity'])==514 and all(sha(R/p)==v for p,v in h['master_identity'].items()),protected6=len(h['protected'])==6 and all(sha(p)==v for p,v in h['protected'].items()),host170=len(h['groups'])==170 and not matches and boot==h['boot_id'],refs=git('rev-parse','HEAD')==h['refs']['head'] and git('rev-parse','master')==h['refs']['master'] and git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture')==h['refs']['remote'],old_rejection=rd(D.with_name('MA-S-2')/'aggregate.json')['accepted'] is False,local_V_accepted=rd(D.with_name('MA-V')/'aggregate.json')['accepted'] is True,tracked_scope=set(git('diff','--name-only','HEAD').splitlines())=={'diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'},no_stage=not git('diff','--cached','--name-only'),diff_clean=subprocess.run(['git','diff','--check'],capture_output=True).returncode==0,no_numerical_artifacts=not any((D/n).exists() for n in ('driver.jl','launcher.py','candidate.jl','run-1','reservation-1.json')))
names=rd(D/'publication-names.json');omit={str((D/n).relative_to(R)) for n in ('closure.json','publication.json')};paths=[R/n for n in names if n not in omit]
o=dict(all_passed=all(checks.values()),checks=checks,no_new_numerics=True,host=dict(time=time.time(),boot_id=boot,groups=h['groups'],matches=matches),sha256={str(p):sha(p) for p in paths})
with (D/'closure.json').open('x') as f:json.dump(o,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=o['all_passed'],checks=checks,bindings=len(paths))))
if not o['all_passed']:raise SystemExit(1)
