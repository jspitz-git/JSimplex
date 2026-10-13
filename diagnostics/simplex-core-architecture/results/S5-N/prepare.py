"""Exclusive text-only candidate extraction. No Julia/parser or old script runs."""
from pathlib import Path
import hashlib,json
R=Path.cwd();H=Path(__file__).resolve().parent;L=H.parent/'S5-L';M=H.parent/'S5-M'
sha=lambda b:hashlib.sha256(b).hexdigest()
old=(R/'test/adaptive_pricing_lifecycle_tests.jl').read_bytes();l=(L/'candidate.jl').read_text();schema=json.loads((M/'schema.json').read_text());assert sha(l.encode())==schema['candidate_sha256']
start=l.index('mutable struct PendingObserverProbe');end=l.index('    observations = (outcome_type=')
core=l[start:end];ending='    return checks\nend\n'
intro='\n# Pending observer failures occur after auxiliary handoff publication.\n# Keep the live/trial identity discriminator and consumed-work checks together.\n'
test='\n@testset "Pending auxiliary handoff observer failure preserves published state" begin\n    checks = pending_observer_case()\n'+''.join('    @test checks.'+name+'\n' for name in schema['checks'])+'end\n'
append=intro+core+ending+test
with (H/'append.jl').open('x') as f:f.write(append)
with (H/'candidate.jl').open('xb') as f:f.write(old+append.encode())
provenance={'original_test':'test/adaptive_pricing_lifecycle_tests.jl','prefix_bytes':len(old),'prefix_sha256':sha(old),'L_sha256':sha(l.encode()),'L_start':start,'L_end':end,'L_removed_prefix':l[:start],'L_removed_suffix':l[end:],'kept_core_sha256':sha(core.encode()),'new_intro':intro,'new_ending':ending,'new_testset':test,'candidate_sha256':sha(old+append.encode()),'append_sha256':sha(append.encode()),'prepare_sha256':sha(Path(__file__).read_bytes()),'checks':schema['checks'],'adaptation':'Reuse three existing helpers; retain exact probe/callback/setup/inspection/40-predicate core. Replace 15-observation return and CLI/TOML tail with checks return and 40 explicit @test expressions. No other candidate-body changes.'}
with (H/'source-inverse.json').open('x') as f:json.dump(provenance,f,indent=2);f.write('\n')
assert append==intro+core+ending+test and l==provenance['L_removed_prefix']+core+provenance['L_removed_suffix']
print(json.dumps({'prefix_bytes':len(old),'append_lines':len(append.splitlines()),'candidate_sha256':provenance['candidate_sha256'],'assertions':len(schema['checks'])}))
