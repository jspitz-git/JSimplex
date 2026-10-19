"""Independent, source-only stage review. Standard-library Python and read-only Git only.
No author checker is imported or executed, and no Julia subprocess is created.
"""
from pathlib import Path
import json, hashlib, subprocess, re, difflib
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
D=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-STAGE-REPAIR'
H=D.with_name('DIRECT-BG-BLOCKED-UPDATE-HARNESS')
C=R/'diagnostics/direct-bg-blocked-update/reproduce'
MASTER='26e2291745999f485a74f643298ca997d65c7205'
HEAD='e7726ed23d26d5cc0739eb5978f3cb1347824ce9'
def rd(p):return json.loads(Path(p).read_text())
def digest(b):return hashlib.sha256(b).hexdigest()
def sha(p):return digest(Path(p).read_bytes())
def git(*args):return subprocess.check_output(['git',*args],cwd=R)
checks={}
def ck(k,v):
 checks[k]=bool(v)
 if not v:raise AssertionError(k)
def bindings(label,items):
 for n,h in items.items():
  p=Path(n);p=p if p.is_absolute() else R/p
  ck(label+':'+str(n),sha(p)==h)
inputs=rd(D/'review-inputs.json');m=rd(D/'stage.json');stage=Path(m['stage']);old=Path(m['failed_stage'])
ck('input_count_129',len(inputs['sha256'])==129)
bindings('input',inputs['sha256'])
ck('HEAD',git('rev-parse','HEAD').decode().strip()==HEAD)
ck('master',git('rev-parse','master').decode().strip()==MASTER==m['master'])
actual={str(p.relative_to(stage)):sha(p) for p in stage.rglob('*') if p.is_file()}
ck('75_exact_stage_files',actual==m['stage_files'] and len(actual)==75)
ck('no_symlinks',not stage.is_symlink() and not any(p.is_symlink() for p in stage.rglob('*')))
ck('stage_bytes',sum((stage/n).stat().st_size for n in actual)==1010881)
tree={line.split('\t',1)[1]:line.split()[2] for line in git('ls-tree','-r',MASTER,'src','Project.toml').decode().splitlines()}
ck('71_master_members',len(tree)==71 and set(tree)==set(m['master_files']))
for n,blob in tree.items():
 b=git('cat-file','blob',blob);s=(stage/n).read_bytes()
 if n=='src/JSimplex.jl':
  insert=m['root_insertion'].encode();ck('root_exact_one_insertion',s.count(insert)==1)
  s=s.replace(insert,b'',1)
 ck('master_blob:'+n,b==s and blob==m['master_files'][n]['git_blob'] and digest(b)==m['master_files'][n]['sha256'])
 ck('diagnostic_HEAD:'+n,(R/n).read_bytes()==git('show',HEAD+':'+n))
expected=['src/factorization.jl','src/lp_refinement_driver.jl','src/options.jl','src/simplex_phase_one.jl','src/simplex_precision.jl','src/solver.jl','src/triangular_factorization.jl']
changed=sorted(n for n in actual if (stage/n).read_bytes()!=(old/n).read_bytes())
ck('exact_seven_changes',changed==expected==sorted(m['baseline_changes']))
for n in changed:
 before=(R/n).read_bytes();after=(stage/n).read_bytes()
 ck('change_hash:'+n,m['baseline_changes'][n]==dict(old_sha256=digest(before),master_sha256=digest(after)))
 diff=''.join(difflib.unified_diff(before.decode().splitlines(True),after.decode().splitlines(True),fromfile='diagnostic/'+n,tofile=MASTER+'/'+n))
 ck('diff_fidelity:'+n,(D/'diffs'/Path(n).with_suffix('.diff')).read_text()==diff)
for n,h in m['ordinary'].items():ck('ordinary:'+n,sha(stage/'src'/n)==sha(R/'diagnostics/direct-lu-policy-adapters/reproduce'/n)==h)
for n,h in m['environment'].items():ck('environment:'+n,sha(stage/n)==sha(old/n)==h)
old_manifest=rd(H/'stages.json')['red']
ck('old_stage_membership',set(old_manifest['sha256'])=={str(p.relative_to(old)) for p in old.rglob('*') if p.is_file()})
for n,h in old_manifest['sha256'].items():ck('old_stage:'+n,sha(old/n)==h)
for name in ['DIRECT-BG-BLOCKED-UPDATE-TASK2/review.json','DIRECT-BG-BLOCKED-UPDATE-HARNESS/preparation-pins-reviewed.json','DIRECT-BG-BLOCKED-UPDATE-RED/publication-final.json']:
 j=rd(D.parent/name);bindings('frozen:'+name,j['sha256'])
candidate={str(p):sha(p) for p in C.iterdir() if p.is_file()}
v=rd(D/'verification.json');ck('candidate_14_exact',candidate==v['candidate_sha256'] and len(candidate)==14)
sm=rd(C/'adapter-source-map.json');t=(stage/'src/triangular_factorization.jl').read_text();ot=(old/'src/triangular_factorization.jl').read_text()
ck('exact_scalar_suffix',sm['original_suffix'] in t and sm['qualified_suffix'] in (C/'factor.jl').read_text())
# Compare outside the constructor interval via the identical adjacent function boundaries.
a=t.index('ForrestTomlinFactorization(B::AbstractMatrix{T}) where');b=t.index('function _check_triangular_dimensions')
oa=ot.index('ForrestTomlinFactorization(B::AbstractMatrix{T}) where');ob=ot.index('function _check_triangular_dimensions')
ck('triangular_layout_and_all_kernels',t[:a]==ot[:oa] and t[b:]==ot[ob:])
# Independently traverse include paths relative to each containing file.
order=[]
def walk(p,stack=()):
 ck('include_no_cycle:'+str(p.relative_to(stage)),p not in stack)
 order.append(str(p.relative_to(stage/'src')))
 for inc in re.findall(r'^\s*include\("([^"\n]+)"\)',p.read_text(),re.M):walk(p.parent/inc,stack+(p,))
walk(stage/'src/JSimplex.jl')
dep=rd(D/'dependency-map.json')
ck('72_includes_exact',len(order)==72 and order==dep['include_order'] and set(order)=={str(p.relative_to(stage/'src')) for p in (stage/'src').rglob('*.jl')})
ck('66_symbol_candidates',len(dep['symbols'])==dep['qualified_symbol_count']==66)
for symbol,locs in dep['symbols'].items():
 ck('symbol_nonempty:'+symbol,bool(locs))
 for i,loc in enumerate(locs):
  line=(stage/loc['path']).read_text().splitlines()[loc['line']-1]
  ck('declaration_location:'+symbol+':'+str(i),line==loc['text'] and symbol in line)
bindings('dependency',dep['sha256'])
ck('provider_order',all(order.index(x)<order.index(y) for x,y in [('factorization.jl','markowitz_factorization.jl'),('markowitz_factorization.jl','triangular_factorization.jl'),('triangular_factorization.jl','factor-export.jl'),('huangfu_hall_factorization.jl','factor-export.jl'),('factor-export.jl','direct-factor.jl')]))
# Fresh source-only contract, independently inspect critical lines and compare expected old/new failure sets.
def contract(s):
 f=(s/'src/factorization.jl').read_text();tri=(s/'src/triangular_factorization.jl').read_text();direct=(s/'src/direct-factor.jl').read_text();j=(s/'src/JSimplex.jl').read_text()
 return {
 'enum_provider':'@enum _NativePivotPolicy::UInt8 _NATIVE_PIVOT_DEFAULT _NATIVE_PIVOT_ONE' in f,
 'native_policy_factory':'function _factorize_basis(B::AbstractMatrix{Float64}, ::Val{:native}, policy::_NativePivotPolicy)' in f,
 'markowitz_policy_factory':'function _factorize_basis(B::AbstractMatrix, ::Val{:markowitz}, policy::_NativePivotPolicy)' in f,
 'native_policy_controls':all(x in f for x in ['function _native_lu(', 'UMFPACK_PIVOT_TOLERANCE + 1] = 1.0','UMFPACK_IRSTEP + 1] = 0.0']),
 'native_policy_lifecycle':all(x in f for x in ['const pivot_policy::_NativePivotPolicy','_native_lu(sparse_basis, backend.pivot_policy)','nothing, true, backend.pivot_policy']),
 'manager_policy_constructors':all('function '+x+'(B::AbstractMatrix{T}, ::Val{R}, policy::_NativePivotPolicy)' in tri for x in ['ForrestTomlinFactorization','SuhlSuhlFactorization','BartelsGolubFactorization']),
 'include_provider_before_consumer':j.index('include("factorization.jl")')<j.index('include("markowitz_factorization.jl")')<j.index('include("triangular_factorization.jl")')<j.index('include("factor-export.jl")')<j.index('include("direct-factor.jl")'),
 'ordinary_adapter_consumes_policy':'ordinary=factorize(B,backend,policy)' in direct and 'pivot_policy::_NativePivotPolicy' in direct}
ck('six_old_missing_APIs',contract(old)==rd(D/'structural-red.json')['checks'] and sum(not x for x in contract(old).values())==6)
ck('eight_new_source_contracts',contract(stage)==rd(D/'structural-green.json')['checks'] and all(contract(stage).values()))
ck('176_recorded_source_checks',len(v['checks'])==176 and all(v['checks'].values()) and v['all_passed'] is True)
bindings('verification_artifact',v['sha256'])
for n in ['driver.jl','recorder.jl','oracle.py','panel-tests.jl','numerical-tests.jl','lifecycle-tests.jl']:
 ck('harness:'+n,sha(H/n)==rd(H/'preparation-pins-reviewed.json')['sha256'][str(H/n)])
ck('old_harness_targets_old_stage',str(old)==rd(H/'stages.json')['red']['path'] and "stage=rd(D/'stages.json')[mode]['path']" in (H/'control.py').read_text())
ck('no_runtime_acceptance',m['runtime_acceptance'] is False and m['launch_admitted'] is False)
result=dict(scope=__doc__,all_passed=True,checks=checks,check_count=len(checks),review_inputs_count=len(inputs['sha256']),master=MASTER,head=HEAD,stage_files=75,stage_bytes=1010881,master_members=71,candidate_files=14,include_count=72,symbol_count=66,baseline_changes=changed,source_contract_old=contract(old),source_contract_new=contract(stage),runtime_acceptance=False,numerical_acceptance=False,performance_acceptance=False,launch_admitted=False,script_sha256=sha(Path(__file__)))
with (D/'independent-source-evidence.json').open('x') as out:json.dump(result,out,indent=2);out.write('\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['checks','source_contract_old','source_contract_new','scope']},indent=2))
