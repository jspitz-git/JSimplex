"""Exclusive H closure, executed separately before fail-fast publication."""
from pathlib import Path
import hashlib,json,subprocess,time
R=Path.cwd();H=R/'diagnostics/simplex-core-architecture/results/S5-H';D=H.parent.parent;G=H.parent/'S5-G'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(p.read_text())
e=read(H/'evidence.json');a=read(H/'independent.json');host=read(H/'host-before.json')
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for q in Path('/proc').glob('[0-9]*'):
 try:
  stat=(q/'stat').read_text();f=stat[stat.rindex(')')+2:].split()
  if int(f[2]) in {49081,49084,23249,23257} or (q/'comm').read_text().strip()=='julia':
   matches.append({'pid':int(q.name),'pgid':int(f[2]),'start_ticks':int(f[19]),'boot_id':boot,'command':(q/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')})
 except FileNotFoundError:pass
review=(D/'S5-PRECISION-JOURNAL-INTERRUPTION-TEST-PREPARATION-REVIEW.md').read_text()
gc=read(G/'closure.json')['sha256']
checks={
 'evidence18':e['all_passed'] and len(e['checks'])==18,
 'structural_red4':len(e['structural_red_missing'])==4 and all(e['structural_red_missing'].values()),
 'independent10':a['all_passed'] and len(a['checks'])==10,
 'full780_current':len(e['sha256'])==780 and all(sha(p)==v for p,v in e['sha256'].items()),
 'six_user_files':all(sha(p)==v for p,v in host['user_hashes'].items()),
 'actual_prefix_candidate':(H/'candidate.jl').read_bytes()==(R/'test/simplex_precision_state_tests.jl').read_bytes()+(H/'append.jl').read_bytes(),
 'no_source_test_CI_change':not subprocess.check_output(['git','diff','master','--','src','test','.github']),
 'master_unchanged':subprocess.check_output(['git','rev-parse','master'],text=True).strip()=='0eb75c3190096946b0e91e5360230ccd7166f298',
 'fresh_fullgroups_absent':not matches and boot==host['boot_id'],
 'review_accepted':'Disposition: ACCEPTED' in review and 'No Critical, Important or Minor findings.' in review,
 'G_false_plus_supplement_preserved':not read(G/'audit.json')['all_passed'] and read(G/'outcome-supplement.json')['all_passed'],
 'G_old_continuation_text_preserved':all(sha(H/(Path(k).name+'.before-H'))==v for k,v in gc.items() if k.endswith('/STATUS.md') or k.endswith('2026-10-11-simplex-core-architecture.md'))}
files=list(p for p in H.rglob('*') if p.is_file())+[D/'STATUS.md',D/'S5-PRECISION-JOURNAL-INTERRUPTION-TEST-PREPARATION.md',D/'S5-PRECISION-JOURNAL-INTERRUPTION-TEST-PREPARATION-REVIEW.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',R/'docs/superpowers/plans/2026-10-13-precision-journal-interruption-test-integration.md']
x={'checks':checks,'all_passed':all(checks.values()),'time_ns':time.time_ns(),'boot_id':boot,'matches':matches,'sha256':{str(p.relative_to(R)):sha(p) for p in files}}
with (H/'closure.json').open('x') as f:json.dump(x,f,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'all_passed':x['all_passed']}));raise SystemExit(0 if x['all_passed'] else 1)
