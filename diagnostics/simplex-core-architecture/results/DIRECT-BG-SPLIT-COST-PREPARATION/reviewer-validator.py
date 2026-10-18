"""Fresh synthetic validator negatives, no Julia and no author test script execution."""
from pathlib import Path
import json,copy,tempfile,struct,traceback
from unittest.mock import patch
import evidence as e
E=Path(__file__).resolve().parent; checks={}
def ok(name,v):
 checks[name]=bool(v)
 if not v:raise AssertionError(name)
def reject(name,fn):
 try:fn()
 except (ValueError,RuntimeError,KeyError,TypeError,IndexError):ok(name,True)
 else:ok(name,False)
def storage():
 top='values row_ids row_backs slab start capacity count column prev next row_order row_position column_order column_position column_head column_tail rows gap_first gap_length bins scratch_value scratch_row scratch_back'.split()
 lens={n:1 for n in top}
 for n in ['slab','start','capacity','count','column','prev','next']:lens[n]=2
 lens.update(bins=32,scratch_value=33,scratch_row=33,scratch_back=33)
 lens.update({'values[1]':4,'row_ids[1]':4,'row_backs[1]':4,'rows[1]':2})
 a=[]
 for n,L in lens.items():
  w=8 if n in ['values','row_ids','row_backs','rows','scratch_value','values[1]'] else 4
  a.append(dict(name=n,length=L,element_bytes=w,backing_length=L,backing_bytes=w*L,graph_bytes=w*L+48))
 return dict(C=4,R=2,K=2,S=1,D=1,used=2,live=1,live_blocks=1,free_capacity=3,gap_reserve=1,active_slack=0,core_payload=16*4+4*2+28*2+32+656,outer_pointer_payload=8+24,struct_bytes=216,graph_bytes=4096,arrays=a,extents=[[1,1,3,0,0,0,0],[1,4,1,1,1,0,0]],bin_heads=[0,0,1]+[0]*29,column_heads=[2],column_tails=[2])
try:
 s=storage();ok('valid_arbitrary3_free_plus_active_extent',e.storage_ok(s,1))
 mutations=[('hole',lambda z:z['extents'][1].__setitem__(1,5)),('overlap',lambda z:z['extents'][1].__setitem__(1,3)),('unreachable_free',lambda z:z['bin_heads'].__setitem__(2,0)),('wrong_bin',lambda z:z['bin_heads'].__setitem__(1,1)),('active_cycle',lambda z:z['extents'][1].__setitem__(6,2)),('active_wrong_previous',lambda z:z['extents'][1].__setitem__(5,1)),('spare_reference',lambda z:z['column_heads'].__setitem__(0,3)),('tail_mismatch',lambda z:z['column_tails'].__setitem__(0,0)),('missing_backing',lambda z:z['arrays'][0].pop('backing_bytes')),('backing_underreports',lambda z:z['arrays'][0].update(backing_length=0)),('wrong_free_total',lambda z:z.update(free_capacity=2)),('wrong_used',lambda z:z.update(used=3)),('bool_extent',lambda z:z['extents'][0].__setitem__(0,True))]
 for name,mut in mutations:
  b=copy.deepcopy(s);mut(b);reject(name,lambda:e.storage_ok(b,1))
 token=lambda x:struct.pack('>d',x).hex()
 ident=dict(n=1,colptr=[1,2],rowval=[1],nzval=[token(1.)])
 f=dict(name='reviewer_synthetic',n=1,matrices=[ident]*9,steps=[dict(j=1,a=[token(1.)],dse=[token(1.)],unit=[token(1.)])]*8)
 original_rd=e.rd
 with tempfile.TemporaryDirectory(prefix='review-prefix-',dir=E) as td,patch.object(e,'rd',lambda p:dict(fixtures=[f]*4) if Path(p)==E/'inputs.json' else original_rd(p)):
  out=Path(td);cfg=dict(process=1,phase='cost1-300')
  for n in e.BASE:(out/n).write_text('synthetic, not execution evidence')
  result,counts=e.output_checks(out,cfg,partial=True);ok('before_growth_empty_prefix',result==[] and counts==dict(cells=0,windows=0,exact_residuals=0))
  def extra(name,content,check):
   p=out/name;p.write_text(content)
   reject(check,lambda:e.output_checks(out,cfg,partial=True));p.unlink()
  extra('started-1.toml','fixture="reviewer_synthetic"\nmanager="BG"\nbackend="native"\npolicy="threshold_one"\n','start_before_growth_rejected')
  extra('window-1-1.toml','pair=1\n','orphan_window_rejected')
  extra('preflight-1.toml','constructions=2\n','orphan_preflight_rejected')
  extra('probe-1.toml','constructions=3\n','orphan_probe_rejected')
  extra('cell-1.toml','windows=20\n','orphan_completion_rejected')
  extra('raw.toml','completed=true\n','raw_not_pure_timeout')
  extra('growth.toml','complete=true\n','incomplete_growth_rejected_without_mock')
  extra('unknown.toml','x=1\n','extra_output_rejected')
  p=out/'growth.toml';p.symlink_to(out/'pins.json');reject('output_symlink_rejected',lambda:e.output_checks(out,cfg,partial=True));p.unlink()
  reject('complete_requires199',lambda:e.output_checks(out,cfg))
 # Every measured final graph pair gates, even when medians would mask a spike.
 rows=[]
 for pair in range(4,11):
  for side in ['reference','candidate']:
   rows.append(dict(pair=pair,side=side,seconds=1. if side=='reference' else .95,bytes=100,events=2,retained_bytes=100,gc_seconds=0.,compile_seconds=0.,recompile_seconds=0.,nested_seconds=[0.]*6))
 st=e.summarize(rows);ok('inclusive_time_boundary',st['time_median_gate'] and st['allocation_gate'] and st['memory_gate'])
 next(z for z in rows if z['side']=='candidate')['retained_bytes']=111
 ok('single_final_memory_spike_rejects',not e.summarize(rows)['memory_gate'])
 rows[1]['retained_bytes']=110;ok('inclusive_memory_boundary',e.summarize(rows)['memory_gate'])
 outcome=dict(all_passed=True,checks=checks,scope='Fresh synthetic partial-prefix, partition/backing and gate tests. No schedule mocks. No full Julia schedule execution or numerical evidence.')
except BaseException:outcome=dict(all_passed=False,checks=checks,error=traceback.format_exc())
with (E/'reviewer-validator.json').open('x') as f:json.dump(outcome,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=outcome['all_passed'],checks=len(checks),error=outcome.get('error',''))))
if not outcome['all_passed']:raise SystemExit(1)
