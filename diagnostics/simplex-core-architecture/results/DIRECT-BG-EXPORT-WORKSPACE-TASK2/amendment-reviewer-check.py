"""New independent Task2 amendment check; read/hash/text only, never imports prior scripts or Julia."""
from pathlib import Path
import hashlib,json,re
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
C=R/'diagnostics/direct-bg-export-workspace/reproduce';E=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-WORKSPACE-TASK2'
def read(n):return json.loads((E/n).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
a=read('source-check.json');v=read('review.json');vcheck=read('reviewer-check.json');fix=read('review-fix.json');supp=read('amendment-check.json');lin=read('lineage.json')
expected_names=('factor.jl','lifecycle-tests.jl','composition-ledger.md','overlay-manifest.json')
expected_mapping={str(C/n):str(E/(n+'.before-review')) for n in expected_names}
assert lin['before_mapping']==expected_mapping
mapping=expected_mapping
mismatches={}
def verify(label,pins,mapped=False):
 bad={p:sha(mapping.get(p,p) if mapped else p) for p,h in pins.items() if sha(mapping.get(p,p) if mapped else p)!=h}
 mismatches[label]=bad
 return not bad
checks={
 'exact_four_before_mappings':lin['before_mapping']==expected_mapping,
 'all702_original_author_bindings':len(a['readtime_sha256'])==702 and verify('original_author',a['readtime_sha256'],True),
 'all710_initial_reviewer_bindings':len(v['readtime_sha256'])==710 and verify('initial_review',v['readtime_sha256'],True),
 'all708_initial_reviewer_check_bindings':len(vcheck['readtime_sha256'])==708 and verify('initial_check',vcheck['readtime_sha256'],True),
 'all719_author_supplement_bindings':len(supp['readtime_sha256'])==719 and verify('supplement',supp['readtime_sha256']),
 'all_lineage_current_and_preserved':verify('lineage',lin['sha256']),
 'all_four_amendment_result_bindings':len(fix['sha256'])==4 and verify('fix_result',fix['sha256']),
 'initial_rejected_review_preserved':not v['accepted'] and v['important']==1 and v['minor']==3,
}
m=json.loads((C/'overlay-manifest.json').read_text())
checks['all679_original_stage_runtime_bindings']=len(m['original_readtime_sha256'])==679 and verify('original_stage',m['original_readtime_sha256'])
checks['Task1_all_eight_frozen']=len(m['candidate_task1_frozen'])==8 and verify('task1',m['candidate_task1_frozen'])
changed={p for p,h in a['readtime_sha256'].items() if sha(p)!=h}
checks['exact_changed_original_file_set']=changed==set(mapping)
f=(C/'factor.jl').read_text();oldf=(E/'factor.jl.before-review').read_text();t=(C/'lifecycle-tests.jl').read_text();oldt=(E/'lifecycle-tests.jl.before-review').read_text();ledger=(C/'composition-ledger.md').read_text()
expected_factor=oldf.replace('make_inner=_init_direct_manager,check_inner=_bgx_check_inner)','make_inner=_init_direct_manager,check_inner=nothing)').replace('''        check_inner(f.inner,candidate)
        # Keep the invariant even if a diagnostic hook returns without checking.
        typeof(candidate)===typeof(f.inner) || throw(ArgumentError("BG export refactorization type changed"))''','''        isnothing(check_inner) || check_inner(f.inner,candidate)
        # One mandatory guard, also after any diagnostic hook.
        _bgx_check_inner(f.inner,candidate)''')
checks['exact_factor_delta_only_optional_hook_single_guard']=f==expected_factor and f.count('_bgx_check_inner(f.inner,candidate)')==1
checks['mandatory_guard_before_only_publication']=f.count('f.inner=candidate')==1 and f.index('_bgx_check_inner(f.inner,candidate)')<f.index('f.inner=candidate')
warm=(E/'warm-witness.txt').read_text();anchor='            @test publications[]==1 && f.inner!==old && !f.busy\n'
expected_test=oldt.replace('publications[]+=1;X._bgx_check_inner(active,candidate)','publications[]+=1;nothing').replace(anchor,anchor+warm)
checks['exact_test_delta_warm_witness_plus_nonchecking_hook']=t==expected_test
checks['real_export_zero_helper_requests']='X._bgx_export(ordinary,owner;allocate=helpers)' in warm and 'helpers.calls==0' in warm
checks['native_full_group_and_markowitz_none_asserted']='R===:native ? !isnothing(orientation) : isnothing(orientation)' in warm
checks['successful_reuse_precedes_history_copy_failure']=warm.index('warm,2.0*dense;export_parts=reused_export')<warm.index('X.replace_column!(warm')<warm.index('warmcopy=X._bgx_copy(warm)')<warm.index('preserve_failure(warm,warmcopy,input')
checks['failure_after_real_export_poison_preserves_graphs']=all(s in warm for s in ('reuse_hits[]==2','fill!(seen,true)','fill!(v,NaN)','samegraph(warm.inner,warmstate)','samegraph(warmcopy.inner,copystate)','throw(sentinel)','inputowners=(input.colptr,input.rowval,input.nzval)'))
checks['source_budget_64_full_triangles_fits_all_helpers']=(16*(2080+2080)+8*65)//16>=512+8+32*64
checks['added_explicit_solve_entries34']=2*(2*6+2+1+2)==34 and '34total' in ledger
checks['static_assertion_sites78']=len(re.findall(r'@test(?:_throws)?\b',t))==78
checks['corrected14fieldcount']='14 fields' in ledger and '15 fields' not in ledger
expected_additions=[{'source':str(C/n),'source_sha256':sha(C/n),'staged_relative':'src/_bgx_'+n,'include_literal':'include("_bgx_'+n+'")'} for n in ('workspace.jl','export.jl','import.jl','factor.jl')]
checks['exact_ordered_source_destination_includes']=m['root_additions']==expected_additions
checks['absolute_tests_preserve_fixture_relative_include']=m['test_order']==[str(C/n) for n in ('workspace-tests.jl','import-tests.jl','lifecycle-tests.jl')] and 'absolute source paths' in m['test_loading_rule']
checks['vacuous_gate_explicitly_disclaimed']='vacuous empty-generator' in supp['note'] and 'NOT preservation evidence' in supp['note']
paths=set(a['readtime_sha256'])|set(v['readtime_sha256'])|set(supp['readtime_sha256'])|set(lin['sha256'])|{str(E/n) for n in ('amendment-check.json','amendment-reviewer-check.py')}
out={'all_passed':all(checks.values()),'checks':checks,'mismatches':mismatches,'readtime_sha256':{p:sha(p) for p in sorted(paths)},'scope':'Independent offline amendment review only; no Julia, numerical calls, syntax parser, old script execution or performance acceptance','source_observations':{'static_assertion_sites':78,'added_explicit_solve_entries':34,'n64_full_triangle_policy_budget':4192,'seen_plus_complete_orientation_charge':2568}}
with (E/'amendment-reviewer-check.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({'checks':len(checks),'all_passed':out['all_passed'],'readtime_bindings':len(paths),'failures':[k for k,b in checks.items() if not b]}))
if not out['all_passed']:raise SystemExit(1)
