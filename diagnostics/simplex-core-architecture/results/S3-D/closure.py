from pathlib import Path
import json, hashlib, subprocess, sys
r=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');d=r/'diagnostics/simplex-core-architecture';o=d/'results/S3-D'
def sha(p):return hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=r,text=True).strip()
s=json.loads((o/'source-check.json').read_text());i=json.loads((o/'independent.json').read_text());h=json.loads((o/'host-after.json').read_text());b=json.loads((o/'offline-checks.json').read_text())
checks={
 'offline11':b['all_passed'] and len(b['checks'])==11 and all(b['checks'].values()),
 'source10':s['all_passed'] and len(s['checks'])==10 and all(s['checks'].values()),
 'independent8':i['all_passed'] and len(i['checks'])==8 and all(i['checks'].values()),
 'all69_current_pins':len(s['sha256'])==69 and all(sha(p)==v for p,v in s['sha256'].items()),
 'author_four_bound_files':len(i['sha256'])==4 and all(sha(r/p)==v for p,v in i['sha256'].items()),
 'review_accepted':'Disposition: ACCEPTED FOR OFFLINE PREPARATION ONLY.' in (d/'S3-DSE-MIXED-ROUTE-PREPARATION-REVIEW.md').read_text(),
 'six_user_files':len(h['user_hashes'])==6 and all(sha(p)==v for p,v in h['user_hashes'].items()),
 'master_unchanged':git('rev-parse','master')=='0eb75c3190096946b0e91e5360230ccd7166f298',
 'production_test_ci_unchanged':not git('diff','master','--','src','test','.github','Project.toml'),
 'no_launch_next_plan':'This task still authorizes no numerical launch.' in (r/'docs/superpowers/plans/2026-10-13-dse-mixed-route-driver.md').read_text(),
}
procs=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  stat=(p/'stat').read_text();fs=stat[stat.rfind(')')+2:].split();cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace');comm=(p/'comm').read_text().strip()
  if int(p.name) in (23256,23257) or int(fs[2]) in (23249,23257) or comm=='julia':procs.append({'pid':int(p.name),'pgid':int(fs[2]),'start_ticks':int(fs[19]),'command':cmd})
 except (OSError,ProcessLookupError):pass
checks['fresh_full_groups_and_julia_absent']=not procs
files=list(o.iterdir())+[d/'S3-DSE-MIXED-ROUTE-PREPARATION.md',d/'S3-DSE-MIXED-ROUTE-PREPARATION-REVIEW.md',d/'STATUS.md',r/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',r/'docs/superpowers/plans/2026-10-13-dse-mixed-route-driver.md']
out={'checks':checks,'all_passed':all(checks.values()),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'process_matches':procs,'sha256':{str(p.relative_to(r)):sha(p) for p in files if p.is_file()},'scope':'Separate offline closure; no old script rerun or Julia execution'}
with (o/'closure.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'all_passed':out['all_passed'],'bound_files':len(out['sha256'])}));sys.exit(0 if out['all_passed'] else 1)
