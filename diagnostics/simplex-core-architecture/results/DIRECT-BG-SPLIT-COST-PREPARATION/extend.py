from pathlib import Path
import json
E=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/results/DIRECT-BG-SPLIT-COST-PREPARATION');O=E.parent/'DIRECT-BG-BLOCK-COST-PREPARATION'
p=E/'probe.jl';t=p.read_text();t=t.replace('"live"=>U.live,"live_blocks"=>liveblocks,"free_capacity"=>free,','''"live"=>U.live,"live_blocks"=>liveblocks,"free_capacity"=>free,
        "active_slack"=>C-free-U.live,"bin_heads"=>Int.(U.bins),
        "column_heads"=>Int.(U.column_head),"column_tails"=>Int.(U.column_tail),
        "extents"=>[[Int(getfield(U,f)[b]) for f in (:slab,:start,:capacity,:count,:column,:prev,:next)] for b in 1:U.used],''')
t=t.replace('function growth_probe()','function row_growth_probe()')
t+='''
# Fixed structural schedules; helper setup allocations are deliberately outside
# counted operation ledgers. Full initial storage is saved before counter reset.
reset_counts!()=(foreach(k->(J._split_probe_counts[k]=0),keys(J._split_probe_counts));nothing)
function structural_state(U,step)
    return Dict("step"=>step,"storage"=>storage(U),"counts"=>counts())
end
function structural_schedules()
    results=Dict[]
    U=J._probe_sbu_test_free([32]);reset_counts!()
    require(J._probe_sbu_check(U),"Repeated4 initial")
    states=[structural_state(U,0)]
    for c in 1:8
        b=J._probe_sbu_reserve_block!(U,4,J._probe_sbu_allocate,typemax(Int32))
        J._probe_sbu_test_claim!(U,b,c)
        require(J._probe_sbu_check(U) && U.live==c && all(J._probe_sbu_tuple(U,J._probe_sbu_find(U,i,i))[1]===Float64(i) for i in 1:c),"Repeated4 values")
        push!(states,structural_state(U,c))
    end
    push!(results,Dict("name"=>"repeated4","n"=>8,"sets"=>0,"reservations"=>8,"claims"=>8,"invariant_checks"=>9,"states"=>states))
    U=J._probe_sbu_test_free(Int[];n=32);reset_counts!()
    require(J._probe_sbu_check(U),"Monotone initial");states=[structural_state(U,0)]
    for r in 1:32
        J._probe_sbu_set!(U,r,1,Float64(r))
        require(J._probe_sbu_check(U) && U.live==r && all(J._probe_sbu_tuple(U,J._probe_sbu_find(U,i,1))[1]===Float64(i) for i in 1:r),"Monotone values")
        push!(states,structural_state(U,r))
    end
    push!(results,Dict("name"=>"monotone32","n"=>32,"sets"=>32,"reservations"=>0,"claims"=>0,"invariant_checks"=>33,"states"=>states))
    U=J._probe_sbu_test_free(fill(3,16);n=40,K=16);reset_counts!()
    require(J._probe_sbu_check(U),"Fragmented initial");states=[structural_state(U,0)]
    b=J._probe_sbu_reserve_block!(U,3,J._probe_sbu_allocate,typemax(Int32));J._probe_sbu_test_claim!(U,b,1)
    require(J._probe_sbu_check(U) && U.live==1,"Fragmented claim");push!(states,structural_state(U,1))
    J._probe_sbu_set!(U,1,1,0.0);require(J._probe_sbu_check(U) && U.live==0,"Fragmented delete");push!(states,structural_state(U,2))
    for cycle in 1:3
        for r in 1:40
            J._probe_sbu_set!(U,r,1,Float64(r))
            require(J._probe_sbu_check(U) && U.live==r,"Fragmented fill invariant")
        end
        require(all(J._probe_sbu_tuple(U,J._probe_sbu_find(U,r,1))[1]===Float64(r) for r in 1:40),"Fragmented fill values")
        push!(states,structural_state(U,2+80*(cycle-1)+40))
        for r in 1:40
            J._probe_sbu_set!(U,r,1,0.0)
            require(J._probe_sbu_check(U) && U.live==40-r,"Fragmented drain invariant")
        end
        push!(states,structural_state(U,2+80*cycle))
    end
    push!(results,Dict("name"=>"fragmented_refill","n"=>40,"sets"=>241,"reservations"=>1,"claims"=>1,"invariant_checks"=>243,"states"=>states))
    return results
end
function growth_probe()
    result=row_growth_probe();result["schedules"]=structural_schedules();return result
end
''';p.write_text(t)
p=E/'evidence.py';t=p.read_text().replace('def counters_ok(c):','def basic_counters_ok(c):').replace('def storage_ok(s,n):','def basic_storage_ok(s,n):').replace('def growth_ok(v):','def basic_growth_ok(v):')
t+='''
# Exact additional split schema, independent of runtime assertions.
def counters_ok(c):
 basic_counters_ok(c)
 require(c['target_calls']==c['reserve_requests']==c['exact_fit_requests']+c['free_splits'],'Reservation partition')
 require(sum(c['target_'+str(i)] for i in (1,2,4,8,16,32))==c['reserve_requests'],'Target histogram')
 require(sum(i*c['target_'+str(2**(i-1))] for i in range(1,7))==c['target_comparisons'],'Target comparison accounting')
 require(sum(c['remainder_'+str(i)] for i in range(1,33))==c['free_splits']==c['split_descriptors'] and c['remainder_32']==0,'Remainder histogram')
 require(c['reserve_requests']<=c['bin_inspections']<=32*c['reserve_requests'],'Bin inspection bounds')
 require(c['append_descriptors']==8*c['slab_appends'] and c['slab_new_payload']==4096*c['slab_appends'],'Slab descriptor/payload accounting')
 require(c['descriptor_copied_payload']==c['grown_copied_bytes'],'Descriptor copy accounting in no-copy schedules')
 require(c['cleared_cells']>=c['relocation_old_capacity_clears']>=c['relocations'],'Relocation clears')
 return True

def storage_ok(s,n):
 extra={'active_slack','bin_heads','column_heads','column_tails','extents'}
 require(extra<=set(s),'Split partition fields required')
 basic_storage_ok({k:v for k,v in s.items() if k not in extra},n)
 require(int_metric(s['active_slack']) and s['live']+s['active_slack']+s['free_capacity']==s['C'] and s['used']<=s['C'],'Whole capacity partition')
 require(len(s['extents'])==s['used'] and all(type(e) is list and len(e)==7 and all(int_metric(x) for x in e) for e in s['extents']),'Extent records')
 arrays={a['name']:a for a in s['arrays']};per_slab={i:[] for i in range(1,s['S']+1)}
 for b,e in enumerate(s['extents'],1):
  slab,start,cap,count,col,prev,nxt=e
  require(slab in per_slab and 1<=cap<=32 and 1<=start<=start+cap-1<=arrays[f'values[{slab}]']['length'] and count<=cap and col<=n and max(prev,nxt)<=s['used'],'Extent bounds')
  require((col==0 and count==0) or (col>0 and count>0),'Extent active/free')
  per_slab[slab].append((start,cap))
 for i,extents in per_slab.items():
  cursor=1
  for start,cap in sorted(extents):require(start==cursor,'No overlap/hole');cursor+=cap
  require(cursor==arrays[f'values[{i}]']['length']+1,'Exact slab partition')
 seen=set()
 def chain(head,kind,owner):
  require(int_metric(head) and head<=s['used'],'Chain head')
  b=head;previous=0
  while b:
   require(b not in seen,'No chain cycle/duplicate');seen.add(b)
   slab,start,cap,count,col,prev,nxt=s['extents'][b-1]
   require(prev==previous and ((col==0 and cap==owner) if kind=='free' else col==owner),'Chain membership/backlink')
   previous=b;b=nxt
  return previous
 require(len(s['bin_heads'])==32 and len(s['column_heads'])==len(s['column_tails'])==n,'Head lengths')
 for c,head in enumerate(s['bin_heads'],1):chain(head,'free',c)
 for c,head in enumerate(s['column_heads'],1):
  tail=s['column_tails'][c-1];require(int_metric(tail) and chain(head,'active',c)==tail,'Column tail')
 require(len(seen)==s['used'],'All descriptors reachable')
 require(sum(e[3] for e in s['extents'])==s['live'] and sum(e[4]!=0 for e in s['extents'])==s['live_blocks'] and sum(e[2] for e in s['extents'] if e[4]==0)==s['free_capacity'],'Extent totals')
 return True

def schedules_ok(schedules):
 specs=[('repeated4',8,0,8,8,9,list(range(9))),('monotone32',32,32,0,0,33,list(range(33))),('fragmented_refill',40,241,1,1,243,[0,1,2,42,82,122,162,202,242])]
 require(type(schedules) is list and len(schedules)==3,'Three fixed schedules')
 for v,(name,n,sets,reservations,claims,inv,steps) in zip(schedules,specs):
  require(set(v)==set('name n sets reservations claims invariant_checks states'.split()),'Structural schema')
  require(v['name']==name and all(type(v[k]) is int and v[k]==z for k,z in zip(['n','sets','reservations','claims','invariant_checks'],[n,sets,reservations,claims,inv])),'Structural fixed budget')
  require(len(v['states'])==len(steps),'Structural state count');previous=None;previous_storage=None
  for state,step in zip(v['states'],steps):
   require(set(state)=={'step','storage','counts'} and type(state['step']) is int and state['step']==step,'Structural checkpoint order')
   s=state['storage'];c=state['counts'];storage_ok(s,n);counters_ok(c)
   require(previous is None or all(previous[k]<=c[k] for k in c),'Structural monotone counters')
   if previous is None:require(all(x==0 for x in c.values()),'Counters reset after setup')
   else:
    require(s['used']-previous_storage['used']==c['append_descriptors']+c['split_descriptors']-previous['append_descriptors']-previous['split_descriptors'],'New descriptor IDs')
    require(s['C']-previous_storage['C']==256*(c['slab_appends']-previous['slab_appends']),'Slab capacity growth')
   if name=='repeated4':
    require(s['C']==32 and s['K']==16 and s['live']==step and s['R']==2*step and s['free_capacity']==32-4*step and s['active_slack']==3*step,'Repeated4 storage')
    require(c['free_splits']==min(step,7) and c['exact_fit_requests']==int(step==8) and c['reserve_requests']==step and c['target_comparisons']==3*step and c['bin_inspections']==sum(29-4*i for i in range(step)),'Repeated4 work')
    require(all(c['remainder_'+str(i)]==int(i in [32-4*j for j in range(1,min(step,7)+1)]) for i in range(1,33)),'Repeated4 remainders')
   elif name=='monotone32':
    require(s['live']==step and s['R']==2*step and s['C']==(0 if step==0 else 256),'Monotone storage')
    target=0 if step==0 else 1<<(step-1).bit_length();reloc=0 if step==0 else target.bit_length()-1
    require(c['relocations']==reloc and c['extent_tuple_moves']==c['relocation_old_capacity_clears']==max(0,target-1),'Monotone relocation work')
   else:
    require(s['live']==(1 if step==1 else 40 if step in (42,122,202) else 0),'Refill live')
    if step==0:require(s['C']==48 and s['used']==16 and s['K']==16,'Fragmented initial partition')
    if step==1:require(s['C']==304 and s['used']==25 and s['K']==36 and c['descriptor_growths']==2 and c['descriptor_new_payload']==28*(24+36) and c['descriptor_copied_payload']==28*(16+24) and c['descriptor_coexist_payload']==28*(24+36),'Fragmented double growth')
   previous=c;previous_storage=s
 return True

def growth_ok(v):
 require('schedules' in v,'Structural schedules required')
 basic_growth_ok({k:z for k,z in v.items() if k!='schedules'});schedules_ok(v['schedules']);return True
''';p.write_text(t)
# Copy old tests as NEW scripts, with separate new synthetic fixtures below.
for n in ['offline-tests.py','synthetic.py','prefix-tests.py','negative-supplement.py']:
 t=(O/n).read_text().replace('_block_bg','_split_bg').replace('block BG','split BG');(E/n).write_text(t)
# Strong warning handling in BOTH normal and pure-timeout paths.
for n in ['audit.py','evidence.py']:
 p=E/n;t=p.read_text();t='import re\n'+t
 if n=='evidence.py':t=t.replace("and 'BEGIN matched policy cost ' in log", "and not re.search(r'warning|world[ -]age',log,re.I) and 'BEGIN matched policy cost ' in log")
 else:t=t.replace("not any(x in log", "not re.search(r'warning|world[ -]age',log,re.I) and not any(x in log")
 p.write_text(t)
print('New split storage,83 counters,three fixed structural schedules prepared; no Julia')
