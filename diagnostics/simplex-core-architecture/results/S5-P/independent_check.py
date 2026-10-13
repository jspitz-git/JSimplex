"""New exclusive author cross-check; independent from saved collection execution."""
from pathlib import Path
import json,hashlib,subprocess,time,collections
R=Path.cwd();P=R/'diagnostics/simplex-core-architecture/results/S5-P';D=P.parent.parent
def h(p):
 s=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):s.update(b)
 return s.hexdigest()
e=json.loads((P/'evidence.json').read_text());host=json.loads((P/'host-before.json').read_text());c=collections.Counter((x['file'].split('/')[0],x['kind']) for x in e['caller_hits'])
checks={
 'full157':len(e['sha256'])==157 and all(h(p)==v for p,v in e['sha256'].items()),
 '22_literal_checks':len(e['checks'])==22 and all(v is True for v in e['checks'].values()),
 'caller_inventory_40':c=={('src','definition'):1,('test','call'):34,('dev','call'):3,('test','isdefined'):2},
 '16_historical_test_files_match':len(e['test_comparisons'])==16 and all(x['whole_file_equal'] and x['current_sha256']==x['historical_sha256'] and h(R/x['file'])==x['current_sha256'] for x in e['test_comparisons']),
 '24_source_comparisons_22_equal':len(e['source_comparisons'])==24 and sum(x['equal'] for x in e['source_comparisons'])==22 and all(x['file']=='src/simplex_perturbation.jl' for x in e['source_comparisons'] if not x['equal']),
 'six_exact_excerpts':len(e['excerpts'])==6 and all(Path(x['path']).read_bytes() in (R/x['file']).read_bytes() and h(x['path'])==x['sha256'] for x in e['excerpts']),
 'user6':len(host['user_hashes'])==6 and all(h(p)==v for p,v in host['user_hashes'].items()),
 'source_test_CI_master_equal':not subprocess.check_output(['git','diff','master','--','src','test','.github']),
 'failed_source_path_only_correction':(P/'source_contract.py').read_text().replace('src/simplex_refactorization.jl','src/refactorization_policy.jl').replace("R/'AGENTS.md'}","R/'AGENTS.md',P/'source_contract.py',P/'source-contract-1-failure.json'}")==(P/'source_contract_2.py').read_text(),
}
paths=[P/'evidence.json',P/'host-before.json',Path(__file__).resolve(),D/'S5-BASIS-INITIALIZATION-CONTRACT.md',R/'docs/superpowers/plans/2026-10-13-basis-initialization-stop-oracle.md',R/'src/transformations.jl',R/'src/simplex_pivot.jl']
out=dict(checks=checks,all_passed=all(checks.values()),sha256={str(p):h(p) for p in paths},time_ns=time.time_ns())
with (P/'independent.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps(out));assert out['all_passed']
