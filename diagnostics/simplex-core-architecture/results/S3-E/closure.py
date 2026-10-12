from pathlib import Path
import hashlib,json,subprocess,time,sys
r=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');d=r/'diagnostics/simplex-core-architecture';o=d/'results/S3-E'
def sha(p):return hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=r,text=True).strip()
s=json.loads((o/'source-check.json').read_text());i=json.loads((o/'independent.json').read_text());h=json.loads((o/'host-before.json').read_text())
checks={'source11':s['all_passed'] and len(s['checks'])==11 and all(s['checks'].values()),'author7':i['all_passed'] and len(i['checks'])==7 and all(i['checks'].values()),'all84_hashes':len(s['sha256'])==84 and all(sha(p)==v for p,v in s['sha256'].items()),'author_bound_files':all(sha(r/p)==v for p,v in i['sha256'].items()),'review_accepted':'Disposition: ACCEPTED' in (d/'S3-DSE-COUNTER-SEAM-LIMIT-REVIEW.md').read_text(),'six_user_files':len(h['user_hashes'])==6 and all(sha(p)==v for p,v in h['user_hashes'].items()),'master_unchanged':git('rev-parse','master')=='0eb75c3190096946b0e91e5360230ccd7166f298','production_test_ci_unchanged':not git('diff','master','--','src','test','.github','Project.toml'),'distinct_next_plan':'S5-D' in (d/'STATUS.md').read_text() and 'No speculative implementation' in (r/'docs/superpowers/plans/2026-10-13-precision-journal-transfer-contract.md').read_text()}
procs=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  st=(p/'stat').read_text();f=st[st.rfind(')')+2:].split();cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace');comm=(p/'comm').read_text().strip()
  if int(p.name) in (23256,23257) or int(f[2]) in (23249,23257) or comm=='julia':procs.append(dict(pid=int(p.name),pgid=int(f[2]),start_ticks=f[19],command=cmd))
 except OSError:pass
checks['fresh_groups_julia_absent']=not procs
files=list(o.iterdir())+[d/'S3-DSE-COUNTER-SEAM-LIMIT.md',d/'S3-DSE-COUNTER-SEAM-LIMIT-REVIEW.md',d/'STATUS.md',r/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',r/'docs/superpowers/plans/2026-10-13-precision-journal-transfer-contract.md']
out={'checks':checks,'all_passed':all(checks.values()),'time_ns':time.time_ns(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'process_matches':procs,'sha256':{str(p.relative_to(r)):sha(p) for p in files if p.is_file()},'scope':'Separate closure after independent review. No Julia or prior exclusive audit executed.'}
with (o/'closure.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'all_passed':out['all_passed']}));sys.exit(0 if out['all_passed'] else 1)
