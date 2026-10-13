"""Exclusive author verification, independent of preparation/source-check execution."""
from pathlib import Path
import hashlib,json,re,subprocess
R=Path.cwd();H=Path(__file__).resolve().parent;D=H.parent.parent
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
p=read(H/'provenance.json');a=(H/'append.jl').read_text();r=(H.parent/'S5-R/candidate-reviewed.jl').read_text();x=a.split('mutable struct ',1)[1].split('    return checks\nend\n\n@testset',1)[0];x='mutable struct '+x
for before,after in p['renames'].items():x=x.replace(after,before)
source=r[r.index('mutable struct S5RProbe'):r.index('    observations=Dict(')]
inventory=read(H/'pins.json')['sha256'];e=read(H/'evidence.json');s=H.parent/'S5-S'
c={'full891':len(inventory)==891 and all(sha(k)==v for k,v in inventory.items()),'literal_inverse':x==source,'prefix_candidate_exact':(H/'candidate.jl').read_bytes()==(R/'test/simplex_precision_tests.jl').read_bytes()+a.encode(),'forty_unique_explicit':re.findall(r'^    @test checks\.(\w+)$',a,re.M)==p['predicate_names'] and len(set(p['predicate_names']))==40,'evidence21':len(e['checks'])==21 and all(v is True for v in e['checks'].values()) and e['all_passed'] is True,'S_original_closure100':len(read(s/'closure.json')['sha256'])==100 and all(sha(k)==v for k,v in read(s/'closure.json')['sha256'].items()),'user6':len(read(H/'host-before.json')['user_hashes'])==6 and all(sha(k)==v for k,v in read(H/'host-before.json')['user_hashes'].items()),'production_test_CI_master_unchanged':not subprocess.check_output(['git','diff','master','--','src','test','.github','Project.toml']) and subprocess.check_output(['git','rev-parse','master'],text=True).strip()=='35a6a9f4bb61e204b0c61ec9effe96cd9d2de3ab'}
paths=[H/'candidate.jl',H/'evidence.json',H/'pins.json',H/'provenance.json',H/'independent.py',D/'S5-BASIS-INITIALIZATION-STOP-TEST-PREPARATION.md',R/'docs/superpowers/plans/2026-10-13-basis-initialization-stop-test-integration.md']
o=dict(checks=c,all_passed=all(c.values()),sha256={str(k):sha(k) for k in paths})
with (H/'independent.json').open('x') as f:json.dump(o,f,indent=2);f.write('\n')
print(json.dumps(c));raise SystemExit(0 if o['all_passed'] else 1)
