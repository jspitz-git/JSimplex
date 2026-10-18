from pathlib import Path
import json,re
D=Path(__file__).resolve().parent;R=D.parents[3];C=R/'diagnostics/direct-bg-split-upper/reproduce';O=D.parent/'DIRECT-BG-BLOCK-DRIVER-PREPARATION'
def put(n,j):
 with (D/n).open('x') as f:json.dump(j,f,indent=2);f.write('\n')
old=json.loads((O/'assertion-derivation.json').read_text());struct=old['structural'];adapter=old['adapter']
# Three old reserve calibrations become21,21,14 after append+suffix metadata.
struct=[(name, (sum(2+3*n for n in [21,21,14])+1+2*90) if name=='reserve_failure' else count) for name,count in struct]
extra=[('target_classes',1+5),('donor32_split4_and_exact_fit',7),('repeated_four_requests',8*2+2),('nonpower_bins_and_partition_holes',4+3+3+1),('descriptor_failure_each_array',1+2+7*3),('append_then_split_failure',1+2+13*3+2),('row_reserve_then_split_failure',7*3),('handle_offset_limits',2*2+2+2+1),('relocation_keep_handle_and_monotone_fill_to32',1+32*2+3),('fragmented_exhaustion',3),('delete_merge_refill_work',3*(40+1+40+1)+2)]
extra_adapter=[('Demand-sized growth, split33, suffix reuse and refill',108*2+32*2+2+1+1),('Imported short exact tails and rotations across split extents',21*2+1+3*2+2)]
struct+=extra;adapter+=extra_adapter
names=re.findall(r'@testset "([^"]+)"',(C/'split-upper-tests.jl').read_text())+re.findall(r'@testset "([^"]+)"',(C/'split-bg-tests.jl').read_text())
if names!=[n for n,c in struct+adapter]:raise RuntimeError('testset tree')
e={'red':{'assertions':10,'groups':[['Missing split BG U contracts (ten expected failures)',0,10,0,0]]},'green':{'assertions':sum(c for _,c in struct+adapter),'groups':[[n,c,0,0,0] for n,c in struct+adapter]}}
put('expected-tests.json',e)
s=''
for mode in e:
 s+='['+mode+']\nassertions = '+str(e[mode]['assertions'])+'\n'
 for n,p,f,err,b in e[mode]['groups']:s+='[['+mode+'.groups]]\nname = '+json.dumps(n)+'\npass = '+str(p)+'\nfail = '+str(f)+'\nerror = '+str(err)+'\nbroken = '+str(b)+'\n'
with (D/'expected-tests.toml').open('x') as f:f.write(s)
probe=lambda n:n+n*(n+1)//2
inherited=sum(probe(n) for n in [21,21,14,90,69])
new={'descriptor_each_array':7+probe(7),'append_then_split':13+probe(13)+7,'row_then_split':sum(range(2,9)),'monotone32_counted':52,'three_fill_delete40_cycles':60}
# New deterministic integer geometry for counted40 fill/delete/refill.
# Initial empty rows reserve2 once (40requests). First active extent progression
# needs20requests (7K+3slab+3directory+7suffixK); all later donor classes retained.
# 33 split takes an existing32 donor. Deletion restores donor capacities; cycles2/3
# reuse sizes1/2/4/8/16/32 and retained row buffers, hence0additionalrequests.
geometry={'row_requests_first40':40,'first_slab_descriptor_directory_suffix':20,'first33_split_additional':0,'later_two_cycles_requests':0,'total':60,'scope':'Source-derived integer schedule; no candidate or floating arithmetic executed'}
put('assertion-derivation.json',dict(scope='Prospective source branch arithmetic only; Julia UNEXECUTED. Original frozen assertion bodies preserved, only source-dependent reserve counts recalculated.',structural=struct,adapter=adapter,helpers=old['helpers'],inherited_reserve_requests=[21,21,14],reserve_group=sum(2+3*n for n in [21,21,14])+1+2*90,new_structural_formulas=extra,new_adapter_formulas=extra_adapter,explicit_allocator_requests={'inherited_structural':inherited,'new_structural':new,'adapter':2787,'total':inherited+sum(new.values())+2787},geometry40=geometry))
w=json.loads((O/'work-ledger.json').read_text());w['scope']='NEW prospective source API attempts and explicit allocator callbacks, not native total/physical allocations';w['group_order'].append('split_allocator_differentials')
for key,sides in w['per_group_reference_candidate'].items():
 for side in sides:side.append(2 if key=='constructors' else 0)
w['totals']['constructors']=[55,125];w['factorization_attempts']=[117,272]
w['allocation_probe_operations']={'inherited_structural':220,'new_failure_structural':32,'new_counted_set_operations':272,'adapter':182,'total':706}
w['expected_injected_storage_failures']=419;w['explicit_storage_allocation_requests']=inherited+sum(new.values())+2787;w['completed_before_injected_throw']=w['explicit_storage_allocation_requests']-419
w['new_storage_only_pair_work']={'controlled_pairs':2,'paired_scalar_assignments':129,'paired_rotations':3,'paired_row_merge':1,'additional_basis_solves':0,'full_partition_token_scans':'after each129assignments and3rotations, plus finalmerge and explicit checks; O(n+C+R+K), test-only'}
w['new_injection_detail']={'inherited_reserve_failures':56,'build_failures':90,'copy_failures':69,'new_descriptor_failures':7,'new_append_failures':14,'new_row_then_split_failures':7,'adapter_failures':176}
put('work-ledger.json',w)
print('RED10; GREEN',e['green']['assertions'],'groups',len(names),'allocator callbacks',w['explicit_storage_allocation_requests'],'injectedfailures',w['expected_injected_storage_failures'])
