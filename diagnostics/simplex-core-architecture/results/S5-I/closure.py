"""Exclusive final S5-I closure; execute once after final independent review."""
from pathlib import Path
import hashlib,json,subprocess,time,tomllib
R=Path.cwd();M=Path('/home/jspitz/JSimplex.jl');D=R/'diagnostics/simplex-core-architecture';I=D/'results/S5-I';H=I.parent/'S5-H';G=I.parent/'S5-G'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(p.read_text())
def git(*args,cwd=R):return subprocess.check_output(['git',*args],cwd=cwd,text=True).strip()
e=tomllib.loads((I/'expected.toml').read_text());host=read(I/'host-before.json')
pins={label:read(I/label/'pins.json')['inventory'] for label in ('green-1','master-1')}
reviews={name:read(I/'final-review-acceptance.json')[name] for name in ('accepted','unresolved_findings','review_sha256')}
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for q in Path('/proc').glob('[0-9]*'):
 try:
  stat=(q/'stat').read_text();f=stat[stat.rindex(')')+2:].split();comm=(q/'comm').read_text().strip()
  if int(f[2]) in {23249,23257,49081,49084,52772,52774,53479,53481} or comm=='julia':
   matches.append({'pid':int(q.name),'pgid':int(f[2]),'start_ticks':int(f[19]),'boot_id':boot,'command':(q/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')})
 except FileNotFoundError:pass
old=read(H/'closure.json')['sha256'];historical={}
for p,v in old.items():
 path=R/p
 if p.endswith('/STATUS.md') or p.endswith('2026-10-11-simplex-core-architecture.md'):path=I/(Path(p).name+'.before-I')
 historical[p]=sha(path)==v
sources={str(p.relative_to(R)):sha(p) for tree in ('src','test') for p in (R/tree).rglob('*') if p.is_file()}
master_sources={str(p.relative_to(M)):sha(p) for tree in ('src','test') for p in (M/tree).rglob('*') if p.is_file()}
checks={
 'prelaunch_accepted':read(I/'prelaunch-acceptance.json')['accepted'] and not read(I/'prelaunch-acceptance.json')['unresolved_findings'],
 'GREEN24_master25':all(read(I/(label+'-audit.json'))['all_passed'] and len(read(I/(label+'-audit.json'))['checks'])==n for label,n in [('green-1',24),('master-1',25)]),
 'independent9_each':all(read(I/(label+'-independent.json'))['all_passed'] and len(read(I/(label+'-independent.json'))['checks'])==9 for label in pins),
 'full801_1322_pins':len(pins['green-1'])==801 and len(pins['master-1'])==1322 and all(sha(p)==v['sha256'] for inv in pins.values() for p,v in inv.items()),
 'raw_portable_and_audit_bindings':all({str(p.relative_to(I/label)):sha(p) for p in (I/label).rglob('*') if p.is_file()}==read(I/(label+'-audit.json'))['raw_sha256']=={str(p.relative_to(R/'.superpowers/simplex-core-architecture/S5-I'/label)):sha(p) for p in (R/'.superpowers/simplex-core-architecture/S5-I'/label).rglob('*') if p.is_file()} for label in pins),
 'six_user_files':all(sha(p)==v for p,v in host['user_hashes'].items()),
 'actual_candidate_both':sha(R/'test/simplex_precision_state_tests.jl')==sha(M/'test/simplex_precision_state_tests.jl')==e['candidate'],
 'GREEN_master511_identity':len(sources)==511 and sources==master_sources==read(I/'master-source-comparison.json')['sha256'],
 'master_expected':git('rev-parse','master')=='513c05388a82531e4d8fbcfb383e8897fad14ba2' and git('rev-parse','HEAD',cwd=M)=='513c05388a82531e4d8fbcfb383e8897fad14ba2',
 'test_only_integration':git('diff','--name-only','0eb75c3190096946b0e91e5360230ccd7166f298','master')=='test/simplex_precision_state_tests.jl' and git('show','--format=','--name-only','fddfa7374269338ab97cfc37843e52c4899f09ca')=='test/simplex_precision_state_tests.jl',
 'no_production_CI_change':not git('diff','master','--','src','.github') and not git('diff','0eb75c3190096946b0e91e5360230ccd7166f298','master','--','src','.github'),
 'fresh_fullgroups_absent':not matches and boot==host['boot_id'],
 'final_review_accepted':reviews['accepted'] and not reviews['unresolved_findings'] and sha(I/'master-review.md')==reviews['review_sha256'],
 'H_frozen_closure_preserved':all(historical.values()),
 'G_false_and_separate_PASS':not read(G/'audit.json')['all_passed'] and read(G/'outcome-supplement.json')['all_passed'],
 'structural_RED_only':all(read(H/'evidence.json')['structural_red_missing'].values()) and len(read(H/'evidence.json')['structural_red_missing'])==4,
}
files=[p for p in I.rglob('*') if p.is_file()]+[D/'STATUS.md',D/'S5-PRECISION-JOURNAL-INTERRUPTION-TEST-INTEGRATION.md',D/'S5-PRECISION-JOURNAL-INTERRUPTION-TEST-INTEGRATION-REVIEW.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',R/'docs/superpowers/plans/2026-10-13-dual-auxiliary-handoff-ownership.md']
x={'checks':checks,'all_passed':all(checks.values()),'time_ns':time.time_ns(),'boot_id':boot,'matches':matches,'H_closure_reconciliation':historical,'sha256':{str(p.relative_to(R)):sha(p) for p in files}}
with (I/'closure.json').open('x') as f:json.dump(x,f,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'all_passed':x['all_passed']}));raise SystemExit(0 if x['all_passed'] else 1)
