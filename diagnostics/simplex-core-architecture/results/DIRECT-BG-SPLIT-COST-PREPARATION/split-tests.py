"""New synthetic split-accounting tests, not Julia or numerical evidence."""
import copy
import evidence as e
from control import D,save
from synthetic import storage,counters
checks={}
def ok(n,v):
 checks[n]=bool(v)
 if not v:raise RuntimeError(n)
def reject(n,fn):
 try:fn()
 except (RuntimeError,ValueError,KeyError,TypeError,IndexError):ok(n,True)
 else:ok(n,False)
s=storage(2);ok('valid_diagonal_partition',e.storage_ok(s,2));ok('zero_counters',e.counters_ok(counters()))
mutations=[('missing_partition',lambda s:s.pop('extents')),('overlap',lambda s:s['extents'][1].__setitem__(1,1)),('hole',lambda s:s['extents'][1].__setitem__(1,3)),('bad_total',lambda s:s.update(active_slack=1)),('unreachable',lambda s:s['column_heads'].__setitem__(1,0)),('cycle',lambda s:s['extents'][0].__setitem__(6,1)),('wrong_prev',lambda s:s['extents'][1].__setitem__(5,1)),('missing_bin',lambda s:s['bin_heads'].pop()),('bad_tail',lambda s:s['column_tails'].__setitem__(0,2)),('used_gt_C',lambda s:s.update(used=3)),('bool_extent',lambda s:s['extents'][0].__setitem__(0,True))]
for name,mut in mutations:
 v=copy.deepcopy(s);mut(v);reject(name,lambda:e.storage_ok(v,2))
# Exact small request on one32-slot donor: target4, suffix28, no setup counted.
c=counters();c.update(target_calls=1,reserve_requests=1,target_4=1,target_comparisons=3,bin_inspections=29,free_splits=1,split_descriptors=1,remainder_28=1)
ok('valid_split_counter_example',e.counters_ok(c))
for key,value in [('target_comparisons',2),('bin_inspections',0),('exact_fit_requests',1),('remainder_28',0),('remainder_32',1),('split_descriptors',0),('append_descriptors',8),('descriptor_copied_payload',28),('relocations',1),('target_calls',True)]:
 v=dict(c);v[key]=value;reject('counter_'+key,lambda:e.counters_ok(v))
# Growth after16 fragmented descriptors: append needs24 then split needs25 ->36.
c=counters();c.update(descriptor_growths=2,descriptor_new_payload=28*(24+36),descriptor_copied_payload=28*(16+24),grown_copied_bytes=28*(16+24),descriptor_coexist_payload=28*(24+36),slab_appends=1,append_descriptors=8,slab_new_payload=4096,target_calls=1,reserve_requests=1,target_4=1,target_comparisons=3,bin_inspections=29,free_splits=1,split_descriptors=1,remainder_28=1)
ok('two_descriptor_growths_accounted',e.counters_ok(c))
reject('missing_schedules',lambda:e.growth_ok({}));reject('omitted_schedule',lambda:e.schedules_ok([]));reject('extra_schedule',lambda:e.schedules_ok([{}]*4))
text=(D/'probe.jl').read_text()
ok('fixed_structural_budgets',all(s in text for s in ['"invariant_checks"=>9','"invariant_checks"=>33','"invariant_checks"=>243','"sets"=>241','for cycle in 1:3','for r in 1:40']))
ok('structural_helpers_in_module',all(s in (D/'probe-oracles.jl').read_text() for s in ['function _probe_sbu_test_free(','function _probe_sbu_test_claim!(']))
ok('exact70_clock_reads',2*(1+8*4+2)==70 and (D/'cost.jl').read_text().count('time_ns()')==14)
ok('clock_buffer_symmetric',(D/'cost.jl').read_text().count('clocks=zeros(UInt64,6)')==1)
ok('no_old_factories',not any(s in (D/'cost.jl').read_text() for s in ['_block_bg','_dynamic_bg']))
ok('83_fixed_metrics',len(counters())==83)
p=dict(reason='wall_time',returncode=-15,pins_unchanged=True);sup=dict(returncode=1,hard_timeout=False,child_kill=False,guard_term=False,guard_kill=False)
for message in ['world-age','WORLD AGE','Warning','warning','WARNING:']:
 ok('warning_'+message,not e.timeout_ok(p,sup,'BEGIN matched policy cost '+message,292,300))
# No launch, seal, parser or measured allocation conclusions in these tests.
save(D/'split-tests.json',dict(all_passed=True,checks=checks,scope='Pure Python partition/counter negatives and source schedule checks; full Julia structural schedule is unexecuted. Prefix tests isolate schedule validation explicitly.'))
print('Split offline checks',len(checks),'PASS')
