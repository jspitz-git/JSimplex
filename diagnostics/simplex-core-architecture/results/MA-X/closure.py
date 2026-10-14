from pathlib import Path
import hashlib,json,subprocess,time
D=Path(__file__).resolve().parent;R=D.parents[3];W=D.with_name('MA-W')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
def bound(o):return all(sha(p)==v for p,v in o['sha256'].items())
h=rd(D/'host.json');rev=rd(D/'admission-review.json');pins=rd(D/'pins.json');maps=rd(D/'continuation-map.json')['old_bindings']
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  f=(p/'stat').read_text().rsplit(')',1)[1].split()
  if int(f[2]) in h['groups'] or int(f[3]) in h['groups'] or (p/'exe').resolve().name.startswith('julia'):matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,ProcessLookupError):pass
def oldbound(n):
 mm={m['path']:m['preserved'] for m in maps if m['source']==str(W/n)}
 return all(sha(mm.get(p,p))==v for p,v in rd(W/n)['sha256'].items())
checks=dict(review=rev['accepted'] is True and rev['findings']==[] and bound(rev) and rev['pins_sha256']==sha(D/'pins.json'),manifest=all(sha(p)==v['sha256'] and str(Path(p).resolve())==v['resolved'] for p,v in pins['inventory'].items()),membership=set(rd(D/'required-paths.json'))==set(pins['files'])==set(pins['inventory'])==set(pins['files'])|{str(p) for root in pins['trees'] for p in Path(root).rglob('*') if p.is_file()},six_maps=len(maps)==6 and all(sha(m['preserved'])==m['sha256']==rd(m['source'])['sha256'][m['path']] for m in maps),prior_W=all(oldbound(n) for n in ('closure.json','publication.json','continuation.json')),source514=len(h['master_identity'])==514 and all(sha(R/p)==v for p,v in h['master_identity'].items()),protected6=len(h['protected'])==6 and all(sha(p)==v for p,v in h['protected'].items()),host170=len(h['groups'])==170 and not matches and boot==h['boot_id'],refs=git('rev-parse','HEAD')==h['refs']['head'] and git('rev-parse','master')==h['refs']['master'] and git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture')==h['refs']['remote'],old_rejection=rd(D.with_name('MA-S-2')/'aggregate.json')['accepted'] is False,local_V_accepted=rd(D.with_name('MA-V')/'aggregate.json')['accepted'] is True,tracked_scope=set(git('diff','--name-only','HEAD').splitlines())=={'diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'},no_stage=not git('diff','--cached','--name-only'),diff_clean=subprocess.run(['git','diff','--check'],cwd=R,capture_output=True).returncode==0,no_numerical_artifacts=not any((D/n).exists() for n in ('launch-context.json','numerical-review.json','sequence-reservation.json','reservation-1.json','run-1','run-2','run-3')))
for n in ('entry.json','source-check.json','offline-tests.json','supervisor-tests-final.json','freeze.json','continuation.json'):
 o=rd(D/n);checks[n]=o['all_passed'] is True and bound(o)
names=rd(D/'publication-names.json');omit={str((D/n).relative_to(R)) for n in ('closure.json','publication.json')};paths=[R/n for n in names if n not in omit]
o=dict(all_passed=all(checks.values()),checks=checks,no_new_numerics=True,host=dict(time=time.time(),boot_id=boot,groups=h['groups'],matches=matches),sha256={str(p):sha(p) for p in paths})
with (D/'closure.json').open('x') as f:json.dump(o,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=o['all_passed'],checks=checks,bindings=len(paths))))
if not o['all_passed']:raise SystemExit(1)
