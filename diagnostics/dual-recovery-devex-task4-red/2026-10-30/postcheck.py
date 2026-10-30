from pathlib import Path
import hashlib,json,subprocess
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');P=W/'diagnostics/dual-recovery-devex-task4/2026-10-30';R=W/'.superpowers/dual-recovery-devex-task4/qualification-1/red';D=W/'diagnostics/dual-recovery-devex-task4-red/2026-10-30'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def req(v,m):
 if not v:raise RuntimeError(m)
def git(*a):return subprocess.check_output(['git','-C',str(W),*a],text=True).strip()
req(not D.exists(),'fresh result directory required')
proc=json.loads((R/'guard/process.json').read_text());attempt=json.loads((R/'attempt.json').read_text());seal=json.loads((R/'seal.json').read_text());pins=json.loads((R/'pins.json').read_text());audit=json.loads((R/'audit.json').read_text());done=json.loads((R/'completion.json').read_text())
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();groups=set(seal['preflight']['checked_groups']) if boot==seal['preflight']['boot_id'] else set()
owners=[attempt['runner'],proc['runner'],proc['child']]
for a in owners:
 if a['boot_id']==boot:groups.update((a['pgid'],a['sid']))
conflicts=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();a=s[s.rfind(')')+2:].split();pgid,sid,start=int(a[2]),int(a[3]),int(a[19]);comm=(p/'comm').read_text().strip()
  if comm.lower().startswith('julia') or pgid in groups or sid in groups:
   conflicts.append(dict(pid=int(p.name),pgid=pgid,sid=sid,start_ticks=start,boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except(FileNotFoundError,ProcessLookupError):pass
req(not conflicts,'process/group/session present '+str(conflicts))
checks={'expected_raw_process_exit':proc['returncode']==1 and proc['reason']=='exit1','admitted_test_summary':audit['accepted'] and audit['test_summary']=={'Pass':7,'Fail':1,'Total':8},'all217_actual_pins':len(pins['inventory'])==217 and all(sha(Path(n))==v['sha256'] and str(Path(n).resolve(strict=True))==v['resolved'] for n,v in pins['inventory'].items()),'all_audit_raw_bindings':all(sha(Path(n))==h for n,h in audit['bindings'].items()),'launcher_guard_child_full_groups_AND_sessions_absent':not conflicts,'same_admitted_head':git('rev-parse','HEAD')==seal['head']=='68240e80279b1339fd24c002b91664559acfb1dd','master_unchanged':git('rev-parse','master')==git('rev-parse','origin/master')=='c0fa748ffa61ccb7c1caaf248c40324f60bc737b','actual_src_test_unchanged':not git('diff','HEAD','--','src','test','Project.toml','.github'),'shared_ceiling_respected':done['total_inclusive_seconds']<=1800 and done['supervisor_accepted'] is True}
req(all(checks.values()),str(checks))
D.mkdir(parents=True)
portable={}
for p in sorted(R.rglob('*')):
 if p.is_file():
  dest=D/'red'/p.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True)
  with dest.open('xb') as f:f.write(p.read_bytes())
  portable[str(p)]=dict(copy=str(dest),sha256=sha(p));req(sha(dest)==sha(p),'portable mismatch')
# Preserve the admission report's original temporary path binding explicitly.
external={}
for n in ('/tmp/devex-task4-red-admission.md','/tmp/devex-task4-red-admission.json'):
 p=Path(n);dest=D/p.name
 with dest.open('xb') as f:f.write(p.read_bytes())
 external[str(p)]=dict(copy=str(dest),sha256=sha(p))
rows=[json.loads(s) for s in (R/'guard/resources.jsonl').read_text().splitlines()]
record=dict(accepted=True,scope='one original RED only; no candidate correctness/cost/promotion',checks=checks,boot_id=boot,checked_groups=sorted(groups),closed_owner_identities=owners,conflicts=conflicts,portable=portable,external_exact_copies=external,source_seal_sha256=sha(R/'seal.json'),elapsed_inclusive_seconds=done['elapsed_inclusive_seconds'],remaining_guarded_seconds=1800-done['total_inclusive_seconds'],resource_samples=len(rows),minimum_available_kib=min(x['available_kib'] for x in rows),maximum_swap_kib=max(x['swap_used_kib'] for x in rows),warning_lines=[x for x in (R/'guard/run.log').read_text().splitlines() if x.startswith('WARNING:')])
(D/'postcheck.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(dict(accepted=True,checks=len(checks),groups=len(groups),portable_files=len(portable),elapsed=record['elapsed_inclusive_seconds'],remaining=record['remaining_guarded_seconds'],samples=len(rows),warnings=len(record['warning_lines']))))
