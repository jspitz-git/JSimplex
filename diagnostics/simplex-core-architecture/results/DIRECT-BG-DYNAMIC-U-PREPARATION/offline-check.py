"""Task1 source/overlay checks only. No Julia parser or runtime."""
from pathlib import Path
import hashlib,json,re
E=Path(__file__).resolve().parent;R=E.parents[3];C=R/'diagnostics/direct-bg-dynamic-upper/reproduce'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(v,m):
 if not v:raise RuntimeError(m)
def save(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')
s=(C/'slot-upper.jl').read_text();t=(C/'slot-upper-tests.jl').read_text();o=json.loads((E/'overlay.json').read_text());O=Path(o['path']);old=Path(o['source'])
checks={}
checks['tests_written_first']=json.loads((E/'tests-first.json').read_text())['candidate_absent'] and sha(E/'slot-upper-tests.jl.before-author-check')==json.loads((E/'tests-first.json').read_text())['tests_sha256']
fields=s.split('mutable struct BGSlotUpper\n',1)[1].split('\nend',1)[0]
checks['15_owned_vectors_4_scalars']=fields.count('::Vector')==15 and len(re.findall(r'^    \w+::Int$',fields,re.M))==4
checks['seven_slot_arrays']=all(n+'::Vector' in fields for n in ['value','row_id','column_id','row_prev','row_next','column_prev','column_next'])
checks['q_import_order']='for cid in 1:n\n        j=positions[cid]' in s and 'copy(q),positions' in s
checks['exact_zero_deletion']='if iszero(value)\n        _bg_unlink!(U,s)' in s
checks['checked_growth']='Base.Checked.checked_add(C, max(C ÷ 2, 16))' in s and 'Base.Checked.checked_mul(result, sizeof(Int))' in s
checks['allocate_all_before_publish']=s.index('column_next = _bg_grown_buffer') < s.index('U.value=value;')
checks['no_hot_checker_or_test_import']=not any(x in s for x in ['_check_bg_slots','_bg_selected_state','using Test','@test','sort!','Dict{','replace_column!','forward_solve!'])
checks['test_scope_no_solves']=not any(x in t for x in ['solve(','forward_solve!','transpose_solve!','factorize(','@elapsed','@allocated','ccall'])
checks['q_and_zero_oracles']=all(x in t for x in ['[3,1,2]','0x8000000000000000','[1,2,3]','_bg_test_permuted'])
checks['seven_allocator_failure_points']='for failat in 1:7' in t and 'all(a===b' in t and 'isequal(_bg_test_snapshot(U),before)' in t
checks['growth_rules_pinned']=all(x in t for x in ['_bg_capacity(0,1)==16','_bg_capacity(16,17)==32','_bg_capacity(24,25)==40'])
checks['all_corruption_categories']=all(x in t for x in ['U.free_head=U.row_head[1]','U.row_head[1]=0','U.row_position[1]=2','U.column_next[U.free_head]=U.free_head','U.live_count+=1'])
checks['overlay_exact_membership']={str(p.relative_to(O)) for p in O.rglob('*') if p.is_file()}==set(o['sha256']) and len(o['sha256'])==77
checks['overlay_hashes']=all(sha(O/n)==h for n,h in o['sha256'].items())
checks['original75_hashes']=all(sha(old/n)==h for n,h in o['baseline'].items())
addition=b'\ninclude("slot-upper.jl")\n\nend\n';original=(old/'src/JSimplex.jl').read_bytes();root=(O/'src/JSimplex.jl').read_bytes()
checks['root_inverse']=root.count(addition)==1 and root.replace(addition,b'\nend\n')==original
checks['only_expected_additions']=set(o['sha256'])-set(o['baseline'])=={'src/slot-upper.jl','test/slot-upper-tests.jl'}
checks['candidate_test_overlay_identity']=(O/'src/slot-upper.jl').read_bytes()==(C/'slot-upper.jl').read_bytes() and (O/'test/slot-upper-tests.jl').read_bytes()==(C/'slot-upper-tests.jl').read_bytes()
for k,v in checks.items():need(v,k)
paths=sorted(C.iterdir())+[E/'overlay.json',E/'tests-first.json',E/'slot-upper-tests.jl.before-author-check',E/'author-test-amendment.md',Path(__file__).resolve()]
save(E/'offline-check.json',dict(all_passed=True,checks=checks,literal_test_sites=t.count('@test'),scope='18 source-text/ownership/manifest checks, NOT Julia parse/dispatch/runtime correctness',sha256={str(p):sha(p) for p in paths}))
print('Offline checks',len(checks),'PASS; Julia tests UNEXECUTED')
