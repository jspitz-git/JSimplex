from pathlib import Path
import json,hashlib,subprocess,time
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/MA-S'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
h=json.loads((E/'host.json').read_text());rev=json.loads((E/'admission-review-final.json').read_text());pins=json.loads((E/'pins-reviewed.json').read_text());old=json.loads((E/'pins.json').read_text());groups=set(h['groups']);matches=[];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
for p in Path('/proc').glob('[0-9]*'):
 try:
  f=(p/'stat').read_text().rsplit(')',1)[1].split();pgid,sid=int(f[2]),int(f[3]);exe=(p/'exe').resolve().name
  if pgid in groups or sid in groups or exe.startswith('julia'):matches.append(dict(pid=int(p.name),pgid=pgid,sid=sid,start_ticks=int(f[19]),boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,ProcessLookupError):pass
checks={
 'accepted_final_review':rev['accepted'] is True and rev['findings']==[] and rev['pins_sha256']==sha(E/'pins-reviewed.json'),
 'full4262_manifest':len(pins['inventory'])==4262 and all(sha(p)==v['sha256'] and str(Path(p).resolve())==v['resolved'] for p,v in pins['inventory'].items()),
 'exact_required_membership':set(pins['files'])==set(pins['inventory'])==set(json.loads((E/'required-paths-reviewed.json').read_text())),
 'exact_tree_membership':set(pins['inventory'])==set(pins['files'])|{str(p) for root in pins['trees'] for p in Path(root).rglob('*') if p.is_file()},
 'original4247_unchanged':len(old['inventory'])==4247 and all(pins['inventory'][p]==v for p,v in old['inventory'].items()),
 'original_rejection_preserved':json.loads((E/'admission-review.json').read_text())['accepted'] is False,
 'new65_offline_checks':json.loads((E/'offline-tests-reviewed.json').read_text())['all_passed'] is True and len(json.loads((E/'offline-tests-reviewed.json').read_text())['checks'])==65,
 'source12_pass':json.loads((E/'source-check.json').read_text())['all_passed'] is True,
 'fix5_pass':json.loads((E/'review-fix-check.json').read_text())['all_passed'] is True,
 'completion3_pass':json.loads((E/'completion-check.json').read_text())['all_passed'] is True,
 'prior_six_continuation_bindings':all(sha(x['preserved'])==x['sha256'] for x in json.loads((E/'continuation-map.json').read_text())['old_bindings']),
 'master514':len(h['master_identity'])==514 and all(sha(R/p)==s for p,s in h['master_identity'].items()),
 'protected6':len(h['protected'])==6 and all(sha(p)==s for p,s in h['protected'].items()),
 'refs_unchanged':git('rev-parse','HEAD')==h['refs']['head'] and git('rev-parse','master')==h['refs']['master'] and git('branch','--show-current')==h['refs']['branch'],
 'full158groups_ANDsessions_noJulia':len(groups)==158 and not matches and boot==h['boot_id'],
 'only_expected_tracked_changes':set(git('diff','--name-only','HEAD').splitlines())=={'diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'},
 'tracked_diff_clean':subprocess.run(['git','diff','--check'],capture_output=True).returncode==0,
 'no_seal_reservation_or_launch':not any((E/n).exists() for n in ['launch-context.json','numerical-review.json','sequence-reservation.json','run-1','run-2','run-3']),
}
for n,count in [('admission-review.json',16),('admission-review-final.json',23),('source-check.json',11),('review-fix-check.json',17),('completion-check.json',6),('offline-tests.json',3),('offline-tests-reviewed.json',3),('preparation-check.json',5)]:
 d=json.loads((E/n).read_text())['sha256'];checks[n+'_bindings']=len(d)==count and all(sha(p)==s for p,s in d.items())
files=sorted(p for p in E.rglob('*') if p.is_file())+[R/'diagnostics/simplex-core-architecture/STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',R/'diagnostics/simplex-core-architecture/MA-DENSELU-BIGFLOAT-ADMISSION-PREPARATION.md']
obj=dict(checks=checks,all_passed=all(checks.values()),time=time.time(),boot_id=boot,groups=sorted(groups),matches=matches,sha256={str(p):sha(p) for p in files},scope='Preparation-only closure; no Julia/runtime/performance qualification. Minor duplicate cold resource scan deferred in separate note.')
with (E/'closure.json').open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
print(json.dumps(dict(checks=checks,bindings=len(files),all_passed=obj['all_passed'])))
if not obj['all_passed']:raise SystemExit(1)
