"""Exclusive post-review L closure; source-only and preserves original inventory."""
from pathlib import Path
import json,hashlib,subprocess,time
r=Path.cwd();d=r/'diagnostics/simplex-core-architecture';o=d/'results/S4-L';x=json.loads((o/'source-contract.json').read_text());fix=json.loads((o/'review-fix.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();plan=r/'docs/superpowers/plans/2026-10-12-hh-symbolic-cost-measurement.md'
checks={}
checks['526_unchanged_source_hashes']=all(sha(p)==h for p,h in x['hashes'].items() if p!=str(plan))
checks['original_plan_preserved']=sha(o/'measurement-plan-before-review.md')==x['hashes'][str(plan)]==fix['before_plan_sha256']
checks['new_plan_bound']=sha(plan)==fix['after_plan_sha256']
checks['review_fix_3_red_3_green']=len(fix['red'])==len(fix['green'])==3 and not any(fix['red'].values()) and all(fix['green'].values())
checks['source_and_independent_gates']=x['all_passed'] and json.loads((o/'independent.json').read_text())['all_passed']
checks['user6']=all(sha(p)==v for p,v in x['user_hashes'].items())
checks['src_test_ci_master_equal']=not subprocess.check_output(['git','diff','master','--','src','test','.github'])
changed=subprocess.check_output(['git','diff','--name-only'],text=True).splitlines();checks['only_authorized_old_files_changed']=set(changed)=={'diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'}
checks['continuation_points_M']='next S4-M bounded NEW sparse/dense' in (d/'STATUS.md').read_text()
matches=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  st=(p/'stat').read_text();a=st[st.rindex(')')+2:].split();cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
  if int(a[2]) in [12358,12360] or int(p.name) in [12359,12360] or (p/'exe').resolve().name=='julia':matches.append({'pid':int(p.name),'pgid':int(a[2]),'start_ticks':a[19],'cmd':cmd})
 except (OSError,ValueError):pass
checks['whole_groups_and_julia_absent']=not matches
files=[p for p in o.iterdir() if p.is_file()]+[plan,d/'S4-SYMBOLIC-COST-CONTRACT.md',d/'S4-SYMBOLIC-COST-CONTRACT-REVIEW.md',d/'STATUS.md',r/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md']
result={'checks':checks,'all_passed':all(checks.values()),'matches':matches,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'hashes':{str(p):sha(p) for p in files},'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'master':subprocess.check_output(['git','rev-parse','master'],text=True).strip(),'time_ns':time.time_ns()}
with (o/'closure.json').open('x') as f:json.dump(result,f,indent=2)
print({'checks':len(checks),'passed':sum(checks.values()),'hashes':len(files),'failures':[k for k,v in checks.items() if not v]});assert result['all_passed']
