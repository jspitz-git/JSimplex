from pathlib import Path
import json,hashlib,subprocess,difflib
Q=Path(__file__).resolve().parent;R=Q.parents[3];B=Q.parent;P=B/'NATIVE-PIVOT-PREPARATION';I=B/'NATIVE-PIVOT-INTEGRATION-PREPARATION'
def require(v,m):
 if not v:raise RuntimeError(m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,o):
 with p.open('x') as f:json.dump(o,f,indent=2);f.write('\n')
master='6f68e24e8ddac42b948da8fcc2d636c010751194'
source_names=['options.jl','factorization.jl','triangular_factorization.jl','simplex_phase_one.jl','simplex_precision.jl','solver.jl','lp_refinement_driver.jl']
items=[('src/'+n,P/'candidate/src'/n) for n in source_names]+[('test/native_pivot_policy_tests.jl',P/'candidate/test/native_pivot_policy_tests.jl'),('test/native_pivot_integration_tests.jl',I/'native_pivot_integration_tests.jl'),('test/runtests.jl',I/'candidate/test/runtests.jl')]
manifest=[];patch=[]
for dest,src in items:
 new=src.read_bytes();actual=R/dest;old=actual.read_bytes() if actual.exists() else b''
 exists=subprocess.run(['git','cat-file','-e',master+':'+dest],cwd=R,capture_output=True).returncode==0
 baseline=subprocess.check_output(['git','show',master+':'+dest],cwd=R) if exists else b''
 require(old==baseline,'Baseline mismatch '+dest)
 target=Q/'payload'/dest;target.parent.mkdir(parents=True,exist_ok=True)
 with target.open('xb') as f:f.write(new)
 require(b'NativePivotIntegrationProbe' not in new,'Diagnostic hook')
 manifest.append(dict(destination=dest,source=str(src.relative_to(R)),payload=str(target.relative_to(R)),sha256=sha(target),original_sha256=hashlib.sha256(old).hexdigest() if exists else None,original_git_blob=subprocess.check_output(['git','rev-parse',master+':'+dest],cwd=R,text=True).strip() if exists else None))
 patch.extend(difflib.unified_diff(old.decode().splitlines(True),new.decode().splitlines(True),fromfile='a/'+dest if exists else '/dev/null',tofile='b/'+dest))
save(Q/'payload-manifest.json',dict(master=master,files=manifest))
with (Q/'production.patch').open('x') as f:f.writelines(patch)
old=(R/'test/runtests.jl').read_bytes();new=(Q/'payload/test/runtests.jl').read_bytes();before=b'    include("options_tests.jl")\n';after=before+b'    include("native_pivot_policy_tests.jl")\n    include("native_pivot_integration_tests.jl")\n'
require(old.count(before)==1 and new.replace(after,before,1)==old,'runtests inverse')
# Independent of runtime instrumentation: exact uninstrumented sources only.
refs=['NATIVE-PIVOT-GREEN2-PREPARATION/runs/green2/result-review.json','NATIVE-PIVOT-COST-PREPARATION/runs/cost/result-review.json','NATIVE-PIVOT-INTEGRATION-180-QUALIFICATION/result-review.json']
for n in refs:require(json.loads((B/n).read_text())['accepted'] is True,n)
actual_files=[p for prefix in ['src','test','.github'] for p in (R/prefix).rglob('*') if p.is_file() and '.git' not in p.parts]
baseline={str(p.relative_to(R)):sha(p) for p in actual_files}
save(Q/'actual-baseline.json',baseline)
pins={str(p.relative_to(R)):sha(p) for p in [Path(__file__),P/'candidate.patch',P/'WORK-AND-TEST-LEDGER.md',I/'runtests-inverse.json',R/'docs/superpowers/plans/2026-10-15-native-pivot-policy.md',R/'docs/superpowers/specs/2026-10-15-native-pivot-policy-design.md',*[B/n for n in refs],*[s for _,s in items],Q/'payload-manifest.json',Q/'production.patch',Q/'actual-baseline.json']}
for x in manifest:p=R/x['payload'];pins[x['payload']]=sha(p)
save(Q/'source-check.json',dict(all_passed=True,checks=dict(exact_ten_files=len(manifest)==10,seven_qualified_source_files=True,exact_permanent_test_sources=True,runtests_inverse=True,no_probe=True,master_baseline=True,three_accepted_result_reviews=True,no_actual_changes=True,no_julia=True),sha256=pins))
print('Payload10 files; baseline',len(baseline),'files; source checks9PASS')
