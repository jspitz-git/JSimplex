"""Exclusive final diagnostic closure; run separately before publication."""
from pathlib import Path
import hashlib,json,subprocess,time
ROOT=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');H=Path(__file__).resolve().parent
D=ROOT/'diagnostics/simplex-core-architecture';PLAN=ROOT/'docs/superpowers/plans/2026-10-13-precision-journal-interruption-test-preparation.md'
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(name):return json.loads((H/name).read_text())
p=read('qualification-1/process.json');pins=read('qualification-1/pins.json')['inventory'];audit=read('audit.json')
groups={23249,23257,p['runner']['pgid'],p['child']['pgid']};matches=[];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
for q in Path('/proc').glob('[0-9]*'):
 try:
  stat=(q/'stat').read_text();f=stat[stat.rindex(')')+2:].split()
  if int(f[2]) in groups or (q/'comm').read_text().strip()=='julia':matches.append({'pid':int(q.name),'pgid':int(f[2]),'start_ticks':int(f[19]),'boot_id':boot,'command':(q/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')})
 except FileNotFoundError:pass
review=(D/'S5-PRECISION-JOURNAL-INTERRUPTION-QUALIFICATION-REVIEW.md').read_text()
checks={'one_guarded_exit0':p['reason']=='exit0' and p['returncode']==0 and p['pins_unchanged'] is True,'original_false_gate_preserved':audit['all_passed'] is False and len(audit['checks'])==63 and sum(audit['checks'].values())==62 and audit['checks']['throw.outcome'] is False and read('audit-execution.json')['returncode']==1,'separate_outcome_supplement':read('outcome-supplement.json')['all_passed'] is True,'independent_post8':read('independent-post.json')['all_passed'] is True and len(read('independent-post.json')['checks'])==8,'all752_pins_current':len(pins)==752 and all(sha(k)==v['sha256'] and str(Path(k).resolve())==v['resolved'] for k,v in pins.items()),'six_user_files':all(sha(k)==v for k,v in read('host-before.json')['user_hashes'].items()),'master_unchanged':subprocess.check_output(['git','rev-parse','master'],text=True).strip()=='0eb75c3190096946b0e91e5360230ccd7166f298','source_test_CI_equal_master':not subprocess.check_output(['git','diff','master','--','src','test','.github'],text=True),'fresh_groups_absent':not matches and boot==p['runner']['boot_id'],'review_accepted':'Disposition: ACCEPTED' in review and 'No unresolved Critical, Important or Minor findings.' in review,'next_offline_only':'WITHOUT Julia execution' in PLAN.read_text()}
files=[x for x in H.rglob('*') if x.is_file()]+[D/'STATUS.md',D/'S5-PRECISION-JOURNAL-INTERRUPTION-QUALIFICATION.md',D/'S5-PRECISION-JOURNAL-INTERRUPTION-QUALIFICATION-REVIEW.md',PLAN,ROOT/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md']
result={'checks':checks,'all_passed':all(checks.values()),'time_ns':time.time_ns(),'boot_id':boot,'matches':matches,'sha256':{str(x.relative_to(ROOT)):sha(x) for x in files}}
with (H/'closure.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'checks':len(checks),'all_passed':result['all_passed']}));assert result['all_passed']
