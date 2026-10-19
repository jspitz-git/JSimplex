"""New offline stage reconciliation; never executes old checkers or Julia."""
from pathlib import Path
import sys,re,json,subprocess,hashlib
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');H=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-HARNESS';D=H.with_name('DIRECT-BG-BLOCKED-UPDATE-STAGE-REPAIR');sys.path[:0]=[str(D),str(H)];import control as c
from contract_complete import contract,declarations
m=c.rd(D/'stage.json');stage=Path(m['stage']);old=Path(m['failed_stage']);checks={}
def ck(n,v):
 checks[n]=bool(v);c.require(v,n)
master=m['master'];expected=['src/factorization.jl','src/lp_refinement_driver.jl','src/options.jl','src/simplex_phase_one.jl','src/simplex_precision.jl','src/solver.jl','src/triangular_factorization.jl']
ck('master_refs',c.git('rev-parse','master')==master and master+'\trefs/heads/master' in c.git('ls-remote','origin','refs/heads/master'))
ck('new_stage_exact',c.bindings(m) and set(m['stage_files'])=={str(p.relative_to(stage)) for p in stage.rglob('*') if p.is_file()})
ck('no_stage_symlinks',not stage.is_symlink() and not any(p.is_symlink() for p in stage.rglob('*')))
ck('master_membership',set(m['master_files'])==set(c.git('ls-tree','-r','--name-only',master,'src','Project.toml').splitlines()))
for n,item in m['master_files'].items():
 b=subprocess.check_output(['git','show',master+':'+n],cwd=R);actual=(stage/n).read_bytes()
 if n=='src/JSimplex.jl':actual=actual.replace(m['root_insertion'].encode(),b'',1)
 ck('master_blob_'+n,hashlib.sha256(b).hexdigest()==item['sha256'] and b==actual and c.git('rev-parse',master+':'+n)==item['git_blob'])
changed=sorted(n for n in m['stage_files'] if (stage/n).read_bytes()!=(old/n).read_bytes())
ck('only_seven_baseline_changes',changed==expected and sorted(m['baseline_changes'])==expected)
ck('original_stage_frozen',all(c.sha(old/n)==h for n,h in c.rd(H/'stages.json')['red']['sha256'].items()))
ck('original_failed_run_frozen',c.bindings(c.rd(H.with_name('DIRECT-BG-BLOCKED-UPDATE-RED')/'publication-final.json')))
ck('environment_frozen',all(c.sha(stage/n)==c.sha(old/n)==h for n,h in m['environment'].items()))
ck('ordinary_sources_frozen',all(c.sha(stage/'src'/n)==c.sha(R/'diagnostics/direct-lu-policy-adapters/reproduce'/n)==h for n,h in m['ordinary'].items()))
q=c.rd(H.with_name('DIRECT-BG-BLOCKED-UPDATE-TASK2')/'review.json');ck('task2_candidate_review_bound',c.bindings(q))
ck('old_harness_bound',c.bindings(c.rd(H/'preparation-pins-reviewed.json')))
candidate={str(p):c.sha(p) for p in sorted(c.C.iterdir()) if p.is_file()};ck('fourteen_candidate_files',len(candidate)==14)
sm=c.rd(c.C/'adapter-source-map.json');ck('scalar_suffix_in_master',sm['original_suffix'] in (stage/'src/triangular_factorization.jl').read_text());ck('scalar_qualified_suffix_unchanged',sm['qualified_suffix'] in (c.C/'factor.jl').read_text())
oldtri=(old/'src/triangular_factorization.jl').read_text();newtri=(stage/'src/triangular_factorization.jl').read_text()
# All triangular edits lie in the three constructors, so layouts, solve/update,
# begin/finish, copy and prepared-RHS mechanics remain byte-identical.
first='function ForrestTomlinFactorization(B::AbstractMatrix{T}, ::Val{R}) where {T<:Real,R}'
newfirst='ForrestTomlinFactorization(B::AbstractMatrix{T}, backend::Val) where {T<:Real} ='
start=oldtri.index(first);startnew=newtri.index(newfirst)
tail=oldtri.index('\nend',oldtri.index('function BartelsGolubFactorization(B::AbstractMatrix{T}, ::Val{R})'))+4
tailnew=newtri.index('\nend',newtri.index('function BartelsGolubFactorization(B::AbstractMatrix{T}, ::Val{R}, policy::'))+4
ck('triangular_layout_and_kernels_unchanged',oldtri[:start]==newtri[:startnew] and oldtri[tail:]==newtri[tailnew:])
for n in ['triangular_indices.jl','triangular_rows.jl','triangular_spikes.jl','bartels_golub_rows.jl','markowitz_factorization.jl','huangfu_hall_factorization.jl','hypersparse_updates.jl']:
 ck('support_body_unchanged_'+n,(old/'src'/n).read_bytes()==(stage/'src'/n).read_bytes())
for n,v in contract(stage).items():ck('source_contract_'+n,v)
# Resolve literal include closure in source order, including nested indices file.
order=[]
def walk(n,stack=()):
 ck('include_exists_'+n,(stage/'src'/n).is_file());c.require(n not in stack,'Include cycle')
 order.append(n)
 for x in re.findall(r'^include\("([^"\n]+)"\)',(stage/'src'/n).read_text(),re.M):walk(x,stack+(n,))
walk('JSimplex.jl');ck('every_stage_source_reachable',set(order)=={str(p.relative_to(stage/'src')) for p in (stage/'src').rglob('*.jl')})
symbols=set()
for p in list(c.C.glob('*.jl'))+[H/n for n in ['panel-tests.jl','numerical-tests.jl','lifecycle-tests.jl']]:symbols.update(re.findall(r'\bJ\.([A-Za-z_][A-Za-z_0-9!]*)',p.read_text()))
symbols.update(['_NativePivotPolicy','Float64UMFPACK','UMFPACKBackend','MarkowitzBackend','HHExtractWorkspace','_hh_extract_parts','_hh_scale_mode','_factorize_basis','_copy_backend','_backend_storage_count','_backend_forward_solve!','_backend_transpose_solve!','sparse_solve_view','_identity_upper','ForrestTomlinUpdate','SuhlSuhlUpdate','ForrestTomlinFactorization','SuhlSuhlFactorization','_export_basis_lu'])
providers=declarations(stage,symbols)
# Enum type is declared on the @enum line with an explicit storage type.
providers['_NativePivotPolicy']=[dict(path='src/factorization.jl',line=17,text=(stage/'src/factorization.jl').read_text().splitlines()[16])]
ck('all_required_symbol_declaration_candidates',all(providers.values()))
c.save(D/'dependency-map.json',dict(scope='Reviewed source declaration candidates and literal include order, not Julia parsing or full dispatch proof',include_order=order,symbols=providers,qualified_symbol_count=len(symbols),sha256={str(stage/'src'/n):c.sha(stage/'src'/n) for n in order}))
ck('same_assertion_oracles',all(c.sha(H/n)==c.rd(H/'preparation-pins-reviewed.json')['sha256'][str(H/n)] for n in ['driver.jl','oracle.py','recorder.jl','panel-tests.jl','numerical-tests.jl','lifecycle-tests.jl']))
paths=[Path(__file__),D/'contract_complete.py',D/'verify-2.py',D/'contract.py',D/'build.py',D/'verify.py',D/'stage.json',D/'structural-red.json',D/'structural-green.json',D/'dependency-map.json']+list((D/'diffs').rglob('*.diff'))
c.save(D/'verification.json',dict(all_passed=True,checks=checks,stage_bytes=sum(p.stat().st_size for p in stage.rglob('*') if p.is_file()),stage_files=len(m['stage_files']),candidate_sha256=candidate,sha256={str(p):c.sha(p) for p in paths},scope=__doc__))
print('Offline reconciliation',len(checks),'PASS;',len(symbols),'symbols;',len(order),'ordered includes')
