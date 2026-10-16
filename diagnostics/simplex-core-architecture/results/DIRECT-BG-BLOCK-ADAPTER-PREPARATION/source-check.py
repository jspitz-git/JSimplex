"""Exclusive offline text/hash checks. No Julia parser/import/runtime calls."""
from pathlib import Path
import json,hashlib,subprocess,re
R=Path(__file__).resolve().parents[4];E=Path(__file__).resolve().parent;C=R/'diagnostics/direct-bg-block-upper/reproduce'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(c,m):
 if not c:raise RuntimeError(m)
s=(C/'block-bg.jl').read_text();t=(C/'block-bg-tests.jl').read_text();d=json.loads((E/'adapter-inverse.json').read_text());inv=s
for e in reversed(d['edits']):
 need(inv.count(e['after'])==e.get('count',1),'Inverse selection');inv=inv.replace(e['after'],e['before'])
for a,b in reversed(d['renames']):inv=inv.replace(b,a)
stage=json.loads((E/'overlay.json').read_text());O=Path(stage['path']);old=json.loads((E.parent/'DIRECT-BG-BLOCK-U-PREPARATION/closure.json').read_text())
start=s.index('function _bbg_backsolve!');end=s.index('function _bbg_forward!');solves=s[start:end]
a=s[s.index('function _bbg_eliminate_row!'):s.index('function _bbg_delete_handle!')]
c=s[s.index('function _bbg_clear_column!'):s.index('function _bbg_last_pure')]
checks=dict(
 exact_whole_inverse=inv.encode()==Path(d['reference']).read_bytes(),
 exact_reference_hash=sha(Path(d['reference']))==d['reference_sha256'],
 candidate_inverse_binding=sha(C/'block-bg.jl')==d['candidate_sha256'],
 frozen_Task1_closure_all_bindings=all(sha(R/k)==v for k,v in old['sha256'].items()),
 fixture_byte_exact=(C/'fixtures.jl').read_bytes()==(R/'diagnostics/direct-bg-dynamic-upper/reproduce/fixtures.jl').read_bytes(),
 task1_78_and_task2_81=len(stage['baseline'])==78 and len(stage['sha256'])==81,
 exact_stage_membership={str(p.relative_to(O)) for p in O.rglob('*') if p.is_file()}==set(stage['sha256']),
 stage_hashes=all(sha(O/k)==v for k,v in stage['sha256'].items()),
 baseline77_unchanged=all(sha(O/k)==v for k,v in stage['baseline'].items() if k!='src/JSimplex.jl'),
 root_inverse=(O/'src/JSimplex.jl').read_bytes().replace(stage['root_addition'].encode(),b'')==(Path(stage['source'])/'src/JSimplex.jl').read_bytes(),
 all_three_new_files_exact=all((O/dst).read_bytes()==(C/src).read_bytes() for dst,src in [('src/block-bg.jl','block-bg.jl'),('test/block-bg-tests.jl','block-bg-tests.jl'),('test/fixtures.jl','fixtures.jl')]),
 no_old_slot_primitives=not any(x in s for x in ('_bg_slots','_bg_link!','_bg_unlink!','_bg_set!','BGSlotUpper')),
 private_factor_no_subtype='mutable struct BlockBGFactor{F}\n' in s,
 two_policies='R === :native && policy === _NATIVE_PIVOT_ONE' in s and 'R === :markowitz && policy === _NATIVE_PIVOT_DEFAULT' in s,
 prebackend_limits=s.index('_bgu_limit(Base.Checked.checked_add(size(B,1),1),limit)')<s.index('ordinary=factorize'),
 prebackend_index=s.index('block BG requires Int CSC indices')<s.index('ordinary=factorize'),
 genuine_export_and_normalize='parts=exporter(ordinary)' in s and '_direct_normalize_upper!(parts.upper)' in s,
 contiguous_block_loops=solves.count('values=U.values[s];rows=U.row_ids[s]')==2,
 tail_diagonal_fast_and_fallback=solves.count('if fast')==2 and solves.count('row==rid && continue')==2,
 no_solve_row_index_pack_check=not any(x in solves for x in ('U.rows','_bgu_row','_bgu_check','sparse(','collect(','copy(')),
 two_prepared_entries='entries=ntuple(_->PreparedTriangularSpike{Float64}(nothing,Float64[],Float64[]),2)' in s,
 prepared_exact_identity='entry.destination===direction && isequal(entry.direction,direction)' in s,
 scratch_alias_before_dimensions=s.index('_bbg_destination(f,destination)',s.index('function _bbg_forward!'))<s.index('_bbg_dimensions',s.index('function _bbg_forward!')),
 direct_monotone_source_predecessor='_bgu_insert_at!(U,target,cid,value,k,h,allocate,limit)' in a and '_bgu_set!' not in a and '_bgu_row_search' not in a and '_bgu_predecessor' not in a,
 source_reload_each_iteration='h=_bgu_row_handle(U,source,i)' in a and 'i+=1' in a,
 original_elimination_arithmetic='old-m*_bgu_tuple(U,h)[1]' in a,
 whole_column_capture_next='following=Int(U.next[b])' in c and '_bgu_unlink_block!(U,b);b=following' in c,
 no_whole_column_delete_merge='_bgu_delete!' not in c and '_bgu_merge_next!' not in c,
 copy_publication_after_allocations=s.index('f.shared_update_count=shared;return candidate')>s.index('candidate=BlockBGFactor(_copy_backend'),
 refactor_type_before_publish=s.index('typeof(candidate)===typeof(f)')<s.index('for name in fieldnames(typeof(f))'),
 no_test_oracle_in_candidate='_bgu_check' not in s and '_bgu_materialize' not in s,
 seven_fixtures_both_arms='DirectLUFixtures.export_fixtures(), (backend,policy) in ARMS' in t,
 lifecycle_eight_updates_copy2_refactor4_8='for t in 0:7' in t and 'if t==1' in t and 'if t in (3,7)' in t,
 boundaries='for n in (0,1,31,32,33,64)' in t,
 unsupported_before_backend='struct RejectBackend end' in t and 'GC.@preserve scratch' in t and 'Int32 CSC' not in s[:0],
 allocation_refusal_loop='for stop in 1:total' in t and '(:setup,:copy,:refactor)' in t,
 failed_update_no_solve='No success history or' in t and 'J.refactorize!(d,spdiagm(0=>ones(33)))' in t,
 no_actual_tracked_changes=subprocess.run(['git','diff','--quiet','HEAD'],cwd=R).returncode==0,
 memory_work_complete_terms=all(x in (E/'MEMORY-WORK.md').read_text() for x in ['16C+4R+28K+32n+656','8n+24D','Theta(f*d+f^2)','907.2','external destination','native','coexist']),
 test_first_preserved=sha(E/'block-bg-tests.jl.before-coverage-amendment')==json.loads((E/'tests-first.json').read_text())['sha256'][str(C/'block-bg-tests.jl')]
)
# Pin only relevant source/evidence inputs, not broad unrelated runtime inventories.
paths=[C/x for x in ('block-bg.jl','block-bg-tests.jl','fixtures.jl','block-upper.jl','block-oracles.jl','block-upper-tests.jl','adapter-source-bindings.json','prepare-adapter-overlay.py')]
paths += [E/x for x in ('host.json','authorization.json','prepare-tests.py','tests-first.json','prepare-adapter.py','prepare-adapter-failure.json','prepare-adapter-2.py','adapter-inverse.json','test-amendment.py','test-amendment.json','block-bg-tests.jl.before-coverage-amendment','overlay.json','MEMORY-WORK.md','SOURCE-MAP.md','source-check.py')]
paths += [R/x for x in ('src/triangular_factorization.jl','src/triangular_indices.jl','src/triangular_rows.jl','src/triangular_spikes.jl','src/bartels_golub_rows.jl','diagnostics/direct-lu-policy-adapters/reproduce/direct-factor.jl','diagnostics/direct-lu-policy-adapters/reproduce/factor-export.jl','diagnostics/direct-bg-dynamic-upper/reproduce/dynamic-bg-reviewed.jl','diagnostics/direct-bg-dynamic-upper/reproduce/dynamic-bg-tests-reviewed.jl','docs/superpowers/plans/2026-10-16-direct-bg-block-upper.md','docs/superpowers/specs/2026-10-16-direct-bg-block-upper.md')]
record=dict(all_passed=all(checks.values()),checks=checks,static_testsets=re.findall(r'@testset "([^"]+)"',t),static_assertion_sites=len(re.findall(r'@test(?:_throws)?\b',t)),sha256={str(p.relative_to(R)):sha(p) for p in paths},scope='OFFLINE textual/hash proof only. No Julia or dynamic test/assertion/dispatch/alloc acceptance.')
with (E/'source-check.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=record['all_passed'],checks=len(checks),pins=len(paths),testsets=len(record['static_testsets']),static_assertion_sites=record['static_assertion_sites'],failed=[k for k,v in checks.items() if not v]),indent=2))
need(record['all_passed'],'Source checks failed')
