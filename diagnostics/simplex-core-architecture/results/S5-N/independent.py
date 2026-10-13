"""One independent offline source/evidence reconciliation; no old executables."""
from pathlib import Path
import hashlib,json,subprocess,time
R=Path.cwd();H=Path(__file__).resolve().parent;M=H.parent/'S5-M';L=H.parent/'S5-L'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
e=json.loads((H/'evidence.json').read_text());p=json.loads((H/'source-inverse.json').read_text());c=(H/'candidate.jl').read_bytes();a=(H/'append.jl').read_text();old=(R/p['original_test']).read_bytes();l=(L/'candidate.jl').read_text();core=a[len(p['new_intro']):-(len(p['new_ending'])+len(p['new_testset']))]
checks={'all789_fresh_hashes':len(e['sha256'])==789 and all(sha(f)==v for f,v in e['sha256'].items()),'all19_text_checks':len(e['checks'])==19 and all(e['checks'].values()),'candidate_prefix_and_suffix':c[:len(old)]==old and c[len(old):]==a.encode(),'independent_inverse':p['L_removed_prefix']+core+p['L_removed_suffix']==l,'40_explicit_tests':len([s for s in p['new_testset'].splitlines() if s.strip().startswith('@test ')])==40,'helpers_source_current':all(x['source_text'] in old.decode() for x in json.loads((L/'source-provenance.json').read_text())['helpers']),'M_false_review_and_final_preserved':'NOT ACCEPTED' in (M/'prelaunch-review.md').read_text() and 'ACCEPTED' in (M/'prelaunch-final-review.md').read_text(),'no_source_test_change':not subprocess.check_output(['git','diff','master','--','src','test','.github'])}
files=[H/'evidence.json',H/'prepare.py',H/'source_check.py',H/'source-inverse.json',H/'candidate.jl',H/'append.jl',H/'independent.py']
x={'checks':checks,'all_passed':all(checks.values()),'sha256':{str(f):sha(f) for f in files},'time_ns':time.time_ns()}
with (H/'independent.json').open('x') as f:json.dump(x,f,indent=2);f.write('\n')
print(json.dumps(x));raise SystemExit(0 if x['all_passed'] else 1)
