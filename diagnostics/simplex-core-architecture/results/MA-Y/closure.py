from pathlib import Path
import hashlib,json,subprocess,time
D=Path(__file__).resolve().parent;R=D.parents[3];X=D.with_name('MA-X')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
def bound(o):return all(sha(p)==v for p,v in o['sha256'].items())
h=rd(D/'host.json');groups=rd(D/'posthost.json')['groups'];rev=rd(D/'result-review.json');pins=rd(X/'pins.json');maps=rd(D/'continuation-map.json')['old_bindings'];summary=rd(D/'result-summary.json')
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  f=(p/'stat').read_text().rsplit(')',1)[1].split()
  if int(f[2]) in groups or int(f[3]) in groups or (p/'exe').resolve().name.startswith('julia'):matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,ProcessLookupError):pass
def oldbound(n):
 mm={m['path']:m['preserved'] for m in maps if m['source']==str(X/n)}
 return all(sha(mm.get(p,p))==v for p,v in rd(X/n)['sha256'].items())
checks=dict(result_review=rev['accepted'] is True and rev['qualification_accepted'] is False and rev['findings']==[] and bound(rev),manifest=all(sha(p)==v['sha256'] and str(Path(p).resolve())==v['resolved'] for p,v in pins['inventory'].items()),membership=set(rd(X/'required-paths.json'))==set(pins['files'])==set(pins['inventory'])==set(pins['files'])|{str(p) for root in pins['trees'] for p in Path(root).rglob('*') if p.is_file()},six_maps=len(maps)==6 and all(sha(m['preserved'])==m['sha256']==rd(m['source'])['sha256'][m['path']] for m in maps),prior_X=all(oldbound(n) for n in ('closure.json','publication.json','continuation.json')),source514=len(h['master_identity'])==514 and all(sha(R/p)==v for p,v in h['master_identity'].items()),protected6=len(h['protected'])==6 and all(sha(p)==v for p,v in h['protected'].items()),host176=len(groups)==176 and not matches and boot==h['boot_id'],refs=git('rev-parse','HEAD')==h['refs']['head'] and git('rev-parse','master')==h['refs']['master'] and git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture')==h['refs']['remote'],old_rejection=rd(X.with_name('MA-S-2')/'aggregate.json')['accepted'] is False,local_V_accepted=rd(X.with_name('MA-V')/'aggregate.json')['accepted'] is True,tracked_scope=set(git('diff','--name-only','HEAD').splitlines())=={'diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'},no_stage=not git('diff','--cached','--name-only'),diff_clean=subprocess.run(['git','diff','--check'],cwd=R,capture_output=True).returncode==0,three_processes=len(summary['processes'])==3 and summary['total_supervised_seconds']<=270 and all(p['invocation']['elapsed_seconds']<=90 for p in summary['processes']),rejected_preserved=summary['accepted'] is False and rd(X/'audit-3.json')['all_passed'] is False and rd(D/'launch-exit.json')['returncode']==1,no_aggregate=not (X/'aggregate.json').exists(),two_failed_controls={r['id'] for r in summary['failed_cases']}=={'fallback/BigFloat/transpose','fallback/Rational{BigInt}/forward'} and all(r['process']==3 for r in summary['failed_cases']))
for n in ('entry.json','postcheck.json','continuation.json'):
 o=rd(D/n);checks[n]=o['all_passed'] is True and bound(o)
for n in ('admission-review.json','numerical-review.json'):
 o=rd(X/n);checks[n]=o['accepted'] is True and o['findings']==[] and bound(o)
checks['all_audit_bindings']=all(bound(rd(X/f'audit-{i}.json')) for i in (1,2,3))
names=rd(D/'publication-names.json');omit={str((D/n).relative_to(R)) for n in ('closure.json','publication.json')};paths=[R/n for n in names if n not in omit]
o=dict(all_passed=all(checks.values()),checks=checks,qualification_accepted=False,scope='Successful diagnostic closure preserves rejected component qualification',host=dict(time=time.time(),boot_id=boot,groups=groups,matches=matches),sha256={str(p):sha(p) for p in paths})
with (D/'closure.json').open('x') as f:json.dump(o,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=o['all_passed'],checks=checks,bindings=len(paths))))
if not o['all_passed']:raise SystemExit(1)
