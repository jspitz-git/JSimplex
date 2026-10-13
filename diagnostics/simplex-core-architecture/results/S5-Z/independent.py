"""Separate author offline checks, no old imports or execution."""
from pathlib import Path
import json,hashlib,re,subprocess
R=Path.cwd();H=Path(__file__).resolve().parent;X=H.parent/'S5-X'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
x=json.loads((H/'pins.json').read_text());s=(X/'candidate.jl').read_text();a=(H/'append.jl').read_text();b=a
for old,new in json.loads((H/'renames.json').read_text()).items():b=b.replace(new,old)
core=s[s.index('    failure = SingularException(42)'):s.index('    observations = Dict(')];helpers=s[s.index('mutable struct S5XProbe'):s.index('function s5x_record_dict')];names=re.findall(r'^        (\w+) = ',core[core.index('    checks = ('):],re.M);actual=(R/'test/simplex_start_state_tests.jl').read_bytes()
c=dict(full_pins=all(sha(k)==v for k,v in x['sha256'].items()),prefix=(H/'candidate.jl').read_bytes()==actual+a.encode() and actual==(H/'original-test.jl').read_bytes(),helpers_inverse=helpers in b,core_inverse=core in b,assertion_bijection=re.findall(r'^    @test checks\.(\w+)$',a,re.M)==names and len(names)==50,one_case=a.count('checks = crash_fallback_observer_checks()')==1 and a.count('JSimplex._crash_workspace(')==1 and a.count('JSimplex.initialize_workspace(')==1,storage=a.count('copy(')==7 and not any(t in a for t in ['Dict(','TOML','ARGS','observations =','open(out']),source_unchanged=not subprocess.check_output(['git','diff','master','--','src','test','.github','Project.toml']),original_failures=(H/'prepare-failure.json').exists() and (H/'prepare-2-failure.json').exists(),native_import_already_available='using Test, JSimplex, Logging, LinearAlgebra' in actual.decode())
paths=[H/'candidate.jl',H/'append.jl',H/'source-check.json',H/'pins.json',H/'entry.json',H/'independent.py',R/'diagnostics/simplex-core-architecture/S5-CRASH-FALLBACK-OBSERVER-TEST-PREPARATION.md',R/'docs/superpowers/plans/2026-10-13-crash-fallback-observer-test-integration.md']
with (H/'independent.json').open('x') as f:json.dump(dict(checks=c,all_passed=all(c.values()),sha256={str(p):sha(p) for p in paths}),f,indent=2);f.write('\n')
print(json.dumps(c));assert all(c.values())
