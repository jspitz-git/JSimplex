from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';E=D/'results/S4-S';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();a=json.loads((E/'source-contract.json').read_text());i=json.loads((E/'independent.json').read_text());fix=json.loads((E/'review-fix.json').read_text());h=json.loads((E/'host-final.json').read_text());checks={}
checks['audit28_author10_pass']=len(a['checks'])==28 and all(a['checks'].values()) and len(i['checks'])==10 and all(i['checks'].values())
checks['584_unchanged_two_preserved']=len(a['sha256'])==586 and len(fix['before'])==2 and all(sha(fix['before'][p]['preserved'] if p in fix['before'] else p)==v for p,v in a['sha256'].items())
checks['two_final_amended_hashes']=len(fix['after'])==2 and all(sha(p)==v for p,v in fix['after'].items()) and all(fix['checks'].values())
checks['user6_unchanged']=all(sha(p)==v for p,v in h['user_hashes'].items())
checks['source_test_CI_equal_master']=not subprocess.check_output(['git','diff','master','--','src','test','.github'])
old=['diagnostics/simplex-core-architecture/results/S4-'+x for x in 'EFGHIJKLMNOPQR'];checks['old_evidence_unchanged']=not subprocess.check_output(['git','diff','HEAD','--',*old,'diagnostics/simplex-core-architecture/reproduce'])
checks['refs_unchanged_precommit']=subprocess.check_output(['git','rev-parse','HEAD','master'],text=True)==h['refs']
matches=[]
for d in Path('/proc').iterdir():
 if not d.name.isdigit():continue
 try:
  t=(d/'stat').read_text();v=t[t.rindex(')')+2:].split();comm=(d/'comm').read_text().strip()
  if int(v[2]) in (23249,23257) or comm.lower().startswith('julia'):matches.append(dict(pid=int(d.name),pgid=int(v[2]),start_ticks=int(v[19]),command=(d/'cmdline').read_bytes().decode(errors='replace').replace('\0',' ')))
 except (FileNotFoundError,ProcessLookupError,PermissionError):pass
checks['fresh_fullgroups_noJulia']=not matches and not any(Path('/proc',str(p)).exists() for p in (23256,23257))
review=(D/'S4-ISOLATED-MODULE-LOADING-CONTRACT-REVIEW.md').read_text();checks['accepted_final_review']='no unresolved Critical, Important or Minor' in review and 'T MUST pin' in review
checks['continuation_no_launch']='Next S4-T source/exact-offline' in (D/'STATUS.md').read_text() and 'SOURCE/EXACT-OFFLINE ONLY' in (R/'docs/superpowers/plans/2026-10-12-hh-isolated-public-lp-work-contract.md').read_text()
files=[D/'STATUS.md',D/'S4-ISOLATED-MODULE-LOADING-CONTRACT.md',D/'S4-ISOLATED-MODULE-LOADING-CONTRACT-REVIEW.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',R/'docs/superpowers/plans/2026-10-12-hh-isolated-public-lp-work-contract.md',*sorted(E.iterdir())]
obj=dict(checks=checks,all_passed=all(checks.values()),matches=matches,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),final_sha256={str(p):sha(p) for p in files if p.is_file()})
with (E/'closure.json').open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
print(json.dumps(checks));assert obj['all_passed']
