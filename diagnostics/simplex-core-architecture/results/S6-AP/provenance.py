"""Exclusive offline provenance: bytes and stored text only; no Julia or MPS parsing."""
from pathlib import Path
import hashlib,json
R=Path.cwd();H=Path(__file__).resolve().parent;D=H.parent.parent;W=Path('/mnt/c/Users/jiris/OneDrive/Simplex_tests');pins={}
def sh(p):
 p=Path(p);h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 pins[str(p)]=h.hexdigest();return pins[str(p)]
def snap(p,name):
 p=Path(p);b=p.read_bytes();q=H/name
 with q.open('xb') as f:f.write(b)
 assert sh(p)==sh(q)
 return b.decode('utf-8-sig')
a=Path('/mnt/c/Users/jiris/.codex/attachments/605d34e2-b2cf-441d-b79b-06aecf724099/Vložený text.txt')
t=snap(a,'user-failure.log');lines=t.splitlines()
w=snap(W/'test_new.jl','windows-test_new.jl.txt')
manifest=snap(W/'Manifest.toml','windows-Manifest.toml.txt')
snap(W/'Project.toml','windows-Project.toml.txt');snap(W/'failure_test.jl','windows-failure_test.jl.txt')
s0=R/'diagnostics/simplex-core-architecture/results/S0/preflight.json';sh(s0)
rec=next(x for x in json.loads(s0.read_text())['inputs'] if x['id']=='test')
model=Path(rec['resolved']);actual=sh(model)
f11=R/'diagnostics/simplex-modernization/F11-results.json';sh(f11);records=[]
def walk(v):
 if isinstance(v,dict):
  if v.get('path')==str(model):records.append(v)
  for x in v.values():walk(x)
 elif isinstance(v,list):
  for x in v:walk(x)
walk(json.loads(f11.read_text()))
for p in ['src/solver.jl','src/dual_simplex.jl','src/native_certificate_recovery.jl','diagnostics/simplex-core-architecture/BASELINE.md','diagnostics/numerical-guard-repair/results/greenbea-baseline.log','diagnostics/simplex-modernization/F25-repeat-summary.json','docs/superpowers/plans/2026-10-13-test-mps-failure-provenance.md']:sh(R/p)
s=(R/'src/dual_simplex.jl').read_text();sol=(R/'src/solver.jl').read_text()
c={
'raw_exact':sh(a)=='22da06e3955a94ffa25fc1f0a0630e933c124aa4a137a25e159b57877030e115',
'raw_size_lines':a.stat().st_size==88807 and len(lines)==817,
'raw_model_dimensions':'rows=614038 columns=526231 nnz=1714776' in lines[1],
'raw_presolve_dimensions':'rows=570020 columns=394798 nnz=1801979' in lines[3],
'raw_restart':'completed iterations=255115' in lines[805] and 'original-objective optimality certificate is inconclusive' in lines[805],
'raw_final':'iterations=256164 time=14814.7718616s' in lines[813] and 'eligible pivots are below the Harris safety cutoff' in lines[813],
'raw_allocation':'607.91 M allocations: 293.240 GiB, 0.47% gc time' in lines[814],
'no_model_filename_in_log':'test.mps' not in t and 'runtime.mps' not in t,
'current_linux_model_matches_S0':actual==rec['sha256']=='f60dd96b23d14433b75c43eabda983e34d264a7b769db15adfb7c6bec8a5c4cb',
'F11_matching_metadata':bool(records) and all((v['rows'],v['columns'],v['nonzeros'],v['decompressed_sha256'])==(614038,526231,1714776,actual) for v in records),
'current_script_different_name':'filename = "runtime.mps"' in w and 'basis_update=:huangfu_hall' in w and 'refactorization_interval = 320' in w,
'current_manifest_tree':'11a7400235decec77ee1be2d02698d4b989c6cd8' in manifest,
'capture_path_missing':not Path('/mnt/c/tmp/capture-failure.jl').exists(),
'current_certificate_branch':'if status == OPTIMAL && !_original_optimality_certified(workspace, primal)' in s,
'current_harris_predicate':'(!exhausted || !_dual_pivot_eligible(workspace, index, coefficient,' in s,
'current_retry_aggregate':'previous.iterations + retry.iterations' in sol,
'no_matching_original_counter_log':'completed iterations=255115' not in (R/'diagnostics/numerical-guard-repair/results/greenbea-baseline.log').read_text(),
}
sh(__file__)
out=dict(checks=c,all_passed=all(c.values()),sha256=pins,original_log_lines={str(n):lines[n-1] for n in [1,2,4,805,806,814,815,816,817]},historical_test_record=rec,current_model_bytes=model.stat().st_size,F11_matching_records=len(records),reported_retry_iteration_difference=256164-255115,missing_original=['Windows input hash/name binding','invocation and options at run time','source commit/tree and runtime identity at run time','stored primal/basis/dual certificate input and failed subpredicate'],scope='Current file hashes and same dimensions do not bind the historical Windows run. No numerical execution or model parsing.')
with (H/'provenance.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps(dict(checks=c,pins=len(pins))));assert all(c.values())
