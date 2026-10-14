from pathlib import Path
import json,hashlib,subprocess,ast
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-V';U=D.with_name('MA-U')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def bound(o):return all(sha(p)==v for p,v in o['sha256'].items())
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
h=rd(D/'host.json');r=rd(D/'admission-review.json');maps=rd(D/'continuation-map.json')['old_bindings'];fix=rd(D/'review-fix-map.json')['old_bindings'];pins=rd(D/'pins.json')
def oldbound(path,mappings):
 m={x['path']:x['preserved'] for x in mappings if x['source']==str(path)}
 return all(sha(m.get(p,p))==v for p,v in rd(path)['sha256'].items())
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  f=(p/'stat').read_text().rsplit(')',1)[1].split()
  if int(f[2]) in h['groups'] or int(f[3]) in h['groups'] or (p/'exe').resolve().name.startswith('julia'):
   matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'),boot_id=boot))
 except (FileNotFoundError,ProcessLookupError):pass
checks=dict(
 review_accepted=r['accepted'] is True and r['findings']==[] and r['all_passed'] is True and r['pins_sha256']==sha(D/'pins.json') and bound(r),
 entry=rd(D/'entry.json')['all_passed'] is True and bound(rd(D/'entry.json')),
 source26=rd(D/'source-check.json')['all_passed'] is True and len(rd(D/'source-check.json')['checks'])==26 and bound(rd(D/'source-check.json')),
 python106=rd(D/'offline-tests-complete.json')['all_passed'] is True and len(rd(D/'offline-tests-complete.json')['checks'])==106 and bound(rd(D/'offline-tests-complete.json')),
 supervisor10=rd(D/'supervisor-tests-final.json')['all_passed'] is True and len(rd(D/'supervisor-tests-final.json')['checks'])==10 and bound(rd(D/'supervisor-tests-final.json')),
 six_continuation_maps=len(maps)==6 and all(sha(x['preserved'])==x['sha256']==rd(x['source'])['sha256'][x['path']] for x in maps),
 prior_U_bindings=all(oldbound(U/n,maps) for n in ['review.json','closure.json','publication.json']),
 nine_fix_maps=len(fix)==9 and all(sha(x['preserved'])==x['sha256']==rd(x['source'])['sha256'][x['path']] for x in fix),
 initial_checks_preserved=all(oldbound(D/n,fix) for n in ['offline-tests.json','offline-tests-final.json','offline-tests-canonical.json','supervisor-tests.json']),
 initial_review_preserved=rd(D/'review-initial.json')['accepted'] is False and bound(rd(D/'review-initial.json')),
 fresh4342=len(pins['inventory'])==4342 and all(sha(p)==v['sha256'] and str(Path(p).resolve())==v['resolved'] for p,v in pins['inventory'].items()),
 manifest_membership=set(rd(D/'required-paths.json'))==set(pins['files'])==set(pins['inventory']),
 source514=len(h['master_identity'])==514 and all(sha(R/p)==v for p,v in h['master_identity'].items()),
 protected6=len(h['protected'])==6 and all(sha(p)==v for p,v in h['protected'].items()),
 host166_noJulia=len(h['groups'])==166 and not matches and boot==h['boot_id'],
 refs=git('rev-parse','HEAD')==h['refs']['head'] and git('rev-parse','master')==h['refs']['master'] and git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture')==h['refs']['remote'],
 tracked_scope=set(git('diff','--name-only','HEAD').splitlines())=={'diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'},
 no_stage=not git('diff','--cached','--name-only'),
 diff_clean=subprocess.run(['git','diff','--check'],capture_output=True).returncode==0,
 no_launch=not any((D/n).exists() for n in ['launch-context.json','numerical-review.json','sequence-reservation.json','reservation-1.json','run-1','run-2']),
 old_rejection=rd(D.with_name('MA-S-2')/'aggregate.json')['accepted'] is False)
module=ast.parse((D/'publication.py').read_text());names=ast.literal_eval(next(n.value for n in module.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='NAMES' for t in n.targets)))
paths=[R/n for n in names if n not in {str((D/'closure.json').relative_to(R)),str((D/'publication.json').relative_to(R))}]
o=dict(all_passed=all(checks.values()),checks=checks,no_new_numerics=True,qualification_accepted=False,host=dict(boot_id=boot,groups=h['groups'],matches=matches),sha256={str(p):sha(p) for p in paths})
with (D/'closure.json').open('x') as f:json.dump(o,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=o['all_passed'],checks=checks,bindings=len(paths))))
if not o['all_passed']:raise SystemExit(1)
