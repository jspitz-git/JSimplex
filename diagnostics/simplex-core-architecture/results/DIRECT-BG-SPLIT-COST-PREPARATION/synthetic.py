"""Tiny fabricated schema data for Python tests only; never Julia evidence."""
from pathlib import Path
import json
D=Path(__file__).resolve().parent
TOP='values row_ids row_backs slab start capacity count column prev next row_order row_position column_order column_position column_head column_tail rows gap_first gap_length bins scratch_value scratch_row scratch_back'.split()
def counters():return dict.fromkeys(json.loads((D/'probe-inverse.json').read_text())['counts'],0)
def storage(n,rowcap=None):
 cap=n if rowcap is None else rowcap
 lens=dict.fromkeys(TOP,n)
 lens.update(values=1,row_ids=1,row_backs=1,bins=32,scratch_value=33,scratch_row=33,scratch_back=33)
 for k in ['values','row_ids','row_backs']:lens[k+'[1]']=n
 for i in range(1,n+1):lens[f'rows[{i}]']=1 if rowcap is None else cap if i==1 else 0
 arrays=[]
 for name,length in lens.items():
  width=8 if name in ['values','row_ids','row_backs','rows','scratch_value','values[1]'] else 4
  arrays.append(dict(name=name,length=length,element_bytes=width,backing_length=length,backing_bytes=width*length,graph_bytes=width*length+40))
 return dict(active_slack=0,bin_heads=[0]*32,column_heads=list(range(1,n+1)),column_tails=list(range(1,n+1)),extents=[[1,i,1,1,i,0,0] for i in range(1,n+1)],C=n,R=cap,K=n,S=1,D=1,used=n,live=n,live_blocks=n,free_capacity=0,gap_reserve=cap-n,core_payload=16*n+4*cap+28*n+32*n+656,outer_pointer_payload=8*n+24,struct_bytes=216,graph_bytes=9000,arrays=arrays)
def growth():
 states=[];cap=0;g=0;copied=0
 for i in range(1,65):
  if i>cap:copied+=4*(i-1);cap=i+min(8,max(1,cap//8));g+=1
  c=counters();c.update(row_growths=g,row_copied_bytes=copied)
  states.append(dict(insertions=i,row_capacity=cap,counts=c))
 return dict(schedules=["isolated prefix-test placeholder"],complete=True,n=64,insertions=64,factorizations=0,solves=0,states=states,storage=storage(64,cap),counts=c)
