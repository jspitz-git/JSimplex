from pathlib import Path
import hashlib,json,subprocess,time,sys,tomllib
r=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');d=r/'diagnostics/simplex-core-architecture';o=d/'results/S5-F'
def sha(p):return hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=r,text=True).strip()
e=json.loads((o/'evidence.json').read_text());i=json.loads((o/'independent.json').read_text());a=json.loads((o/'review-fix.json').read_text());h=json.loads((o/'host-before.json').read_text())
remap={'diagnostics/simplex-core-architecture/S5-PRECISION-JOURNAL-INTERRUPTION-DRIVER.md':o/'report-before-review.md','docs/superpowers/plans/2026-10-13-precision-journal-interruption-qualification.md':o/'qualification-plan-before-review.md'}
checks={'18_initial_checks':len(e['checks'])==18 and e['all_passed'] and all(e['checks'].values()),'six_initial_author_checks':len(i['checks'])==6 and i['all_passed'] and all(i['checks'].values()),'170_initial_pins_unchanged':len(e['sha256'])==170 and all(sha(p)==v for p,v in e['sha256'].items()),'five_initial_bindings_reconciled':all(sha(remap.get(p,r/p))==v for p,v in i['sha256'].items()),'nine_amendment_checks':len(a['checks'])==9 and a['all_passed'] and all(a['checks'].values()),'176_final_pins_current':len(a['sha256'])==176 and all(sha(p)==v for p,v in a['sha256'].items()),'reviewed_manifest':sha(o/'source-pins-reviewed.toml')==a['manifest_sha256'] and tomllib.loads((o/'source-pins-reviewed.toml').read_text())['sha256']==a['sha256'],'review_accepted':'Disposition: ACCEPTED' in (d/'S5-PRECISION-JOURNAL-INTERRUPTION-DRIVER-REVIEW.md').read_text(),'six_user_files':len(h['user_hashes'])==6 and all(sha(p)==v for p,v in h['user_hashes'].items()),'master_unchanged':git('rev-parse','master')=='0eb75c3190096946b0e91e5360230ccd7166f298','source_test_ci_unchanged':not git('diff','master','--','src','test','.github','Project.toml'),'no_runtime_output':not any((o/p).exists() for p in ('stop.toml','throw.toml','summary.toml'))}
procs=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  st=(p/'stat').read_text();f=st[st.rfind(')')+2:].split();cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace');comm=(p/'comm').read_text().strip()
  if int(p.name) in (23256,23257) or int(f[2]) in (23249,23257) or comm=='julia':procs.append(dict(pid=int(p.name),pgid=int(f[2]),start_ticks=f[19],command=cmd))
 except OSError:pass
checks['fresh_groups_julia_absent']=not procs
files=list(o.iterdir())+[d/'S5-PRECISION-JOURNAL-INTERRUPTION-DRIVER.md',d/'S5-PRECISION-JOURNAL-INTERRUPTION-DRIVER-REVIEW.md',d/'STATUS.md',r/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',r/'docs/superpowers/plans/2026-10-13-precision-journal-interruption-qualification.md']
out=dict(checks=checks,all_passed=all(checks.values()),time_ns=time.time_ns(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),process_matches=procs,sha256={str(p.relative_to(r)):sha(p) for p in files if p.is_file()})
with (o/'closure.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'all_passed':out['all_passed']}));sys.exit(0 if out['all_passed'] else 1)
