"""Fresh offline reviewer: bytes/text and saved JSON only; no prior script import/execution, no Julia."""
from pathlib import Path
import hashlib, json, difflib, subprocess
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
Q=R/'diagnostics/simplex-core-architecture/results/NATIVE-PIVOT-PREPARATION'
def read(p): return json.loads(Path(p).read_text())
def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def abs_path(p): return Path(p) if Path(p).is_absolute() else R/p
def bind(z): return all(digest(abs_path(p))==h for p,h in z.items())
def section(s,a,b):
    assert s.count(a)==1 and s.count(b)==1
    return s[s.index(a):s.index(b)]
required=read(Q/'review-required.json')['paths']
# Read all required bytes independently. Hash every historical baseline entry as well.
inputs={p:Path(p).read_bytes() for p in required}
pins={p:hashlib.sha256(b).hexdigest() for p,b in inputs.items()}
checks={'required116_unique_readable':len(inputs)==len(required)==116}
base=read(Q.parent/'DIRECT-LU-PREPARATION/baseline.json')
checks['baseline514']=len(base['sha256'])==514 and bind(base['sha256'])
recorded={}
for p,b in inputs.items():
    if p.endswith('.json'):
        obj=json.loads(b)
        if isinstance(obj,dict) and isinstance(obj.get('sha256'),dict):
            recorded[p]={'count':len(obj['sha256']),'matched':bind(obj['sha256'])}
checks['all_recorded_required_binding_maps']=all(x['matched'] for x in recorded.values())
checks['author6_source15']=len(read(Q/'author-check.json')['checks'])==6 and all(read(Q/'author-check.json')['checks'].values()) and len(read(Q/'source-check.json')['checks'])==15 and all(read(Q/'source-check.json')['checks'].values())
inv=read(Q/'inverse.json')
checks['inverse_hashes']=bind(inv['original']) and bind(inv['candidate'])
reconstructed={}
patch=[]
for path in inv['original']:
    rel=str(Path(path).relative_to(R)); original=Path(path).read_text(); candidate=(Q/'candidate'/rel).read_text(); s=candidate
    for edit in reversed([x for x in inv['edits'] if x['file']==rel]):
        assert s.count(edit['after'])==1
        s=s.replace(edit['after'],edit['before'])
    reconstructed[rel]=s==original
    patch.extend(difflib.unified_diff(original.splitlines(True),candidate.splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))
checks['whole_inverse7_edits28']=len(reconstructed)==7 and len(inv['edits'])==28 and all(reconstructed.values())
checks['exact_patch']=''.join(patch)==(Q/'candidate.patch').read_text()
a=(R/'src/factorization.jl').read_text();b=(Q/'candidate/src/factorization.jl').read_text()
checks['complete_solve_update_pattern_identity']=section(a,'function _check_rhs_dimension','function _refactorize_backend(backend::UMFPACKBackend')==section(b,'function _check_rhs_dimension','function _refactorize_backend(backend::UMFPACKBackend')
checks['native_refactor_only_fresh_call']=section(a,'function _refactorize_backend(backend::UMFPACKBackend','function _recycle_pfi_updates!')==section(b,'function _refactorize_backend(backend::UMFPACKBackend','function _recycle_pfi_updates!').replace('_native_lu(sparse_basis, backend.pivot_policy)','lu(sparse_basis)')
checks['triangular_post_constructors_identity']=(R/'src/triangular_factorization.jl').read_text().split('function _check_triangular_dimensions',1)[1]==(Q/'candidate/src/triangular_factorization.jl').read_text().split('function _check_triangular_dimensions',1)[1]
manifest=read(Q/'overlay-manifest.json')
checks['overlay_hashes_and_safe_destinations']=all(digest(e['source'])==e['sha256'] and not Path(e['destination']).is_absolute() and '..' not in Path(e['destination']).parts for arm in ('reference','candidate') for e in manifest[arm])
ref={e['destination']:e for e in manifest['reference']};can={e['destination']:e for e in manifest['candidate']}
checks['overlay73_75_seven_substitutions']=len(ref)==73 and len(can)==75 and len(set(can)-set(ref))==2 and sum(can[k]!=e for k,e in ref.items())==7
checks['unchanged_auxiliary_hh_direct']=can['src/dual_simplex.jl']==ref['src/dual_simplex.jl'] and can['src/huangfu_hall_factorization.jl']==ref['src/huangfu_hall_factorization.jl'] and digest(R/'diagnostics/direct-lu-markowitz/reproduce/direct-factor.jl')==read(Q/'source-check.json')['sha256'][str(R/'diagnostics/direct-lu-markowitz/reproduce/direct-factor.jl')]
checks['default_lu_and_exact_control_stores']='policy === _NATIVE_PIVOT_DEFAULT && return lu(B)' in b and b.count('control[SparseArrays.LibSuiteSparse.')==2 and 'const pivot_policy::_NativePivotPolicy' in b
checks['recorded_failed_author_attempt']=read(Q/'author-check-failure.json')['source_sha256']==digest(Q/'author-check.py') and read(Q/'author-check-failure.json')['exit_code']==1
refs={x:subprocess.check_output(['git','rev-parse',x],cwd=R,text=True).strip() for x in ('HEAD','master')}
checks['expected_refs']=refs=={'HEAD':'94ea8af804367f4ae3b2e23c416881809608306b','master':'6f68e24e8ddac42b948da8fcc2d636c010751194'}
checks['production_tracked_diff_empty']=not subprocess.check_output(['git','diff','HEAD','--','src','test','.github','Project.toml','diagnostics/direct-lu-markowitz/reproduce'],cwd=R,text=True)
output={'all_passed':all(checks.values()),'checks':checks,'required_count':116,'baseline_count':514,'required_bytes_read':sum(map(len,inputs.values())),'recorded_binding_maps':recorded,'reconstructed':reconstructed,'sha256':pins|{str(Q/'review-required.json'):digest(Q/'review-required.json'),str(Q/'reviewer-check.py'):digest(Q/'reviewer-check.py'),str(Q/'reviewer-check-2.py'):digest(Q/'reviewer-check-2.py'),str(Q/'reviewer-check-failure.json'):digest(Q/'reviewer-check-failure.json')},'scope':'OFFLINE byte/text evidence only. No Julia/parser/import/compile/numerics, no old script executed; overlay UNEXECUTED. Passing evidence checks do not accept incomplete tests.'}
with (Q/'reviewer-check.json').open('x') as f: json.dump(output,f,indent=2);f.write('\n')
print(json.dumps({'all_passed':output['all_passed'],'checks':len(checks),'required':116,'baseline':514,'recorded_binding_maps':recorded},indent=2))
assert output['all_passed']
