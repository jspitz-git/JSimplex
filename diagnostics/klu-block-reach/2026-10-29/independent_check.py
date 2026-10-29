from pathlib import Path
from array import array
import struct,tomllib,json,hashlib,csv,statistics,math
D=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl/diagnostics/klu-block-reach/2026-10-29')
raw=tomllib.loads((D/'results-1.toml').read_text());prof={(r['history'],r['state']):r for r in raw['profiles']}
a=json.loads((D/'analysis.json').read_text());fixed=json.loads((D/'fixed-base-analysis.json').read_text())
actualcsv={(r['history'],int(r['state']),r['RHS']):r for r in csv.DictReader((D/'summary.csv').open())}
fixedcsv={(r['history'],int(r['interval']),int(r['state'])):r for r in csv.DictReader((D/'fixed-base-summary.csv').open())}
def take(f,typ,n):
 x=array(typ);x.fromfile(f,n);return x
def q(v):
 v=sorted(v);return dict(min=v[0],p25=v[math.ceil(.25*len(v))-1],median=statistics.median(v),p75=v[math.ceil(.75*len(v))-1],p90=v[math.ceil(.9*len(v))-1],max=v[-1])
def equal(x,y):
 if isinstance(x,dict):assert x.keys()==y.keys();[equal(x[k],y[k]) for k in x]
 elif isinstance(x,float):assert math.isclose(x,y,rel_tol=1e-14,abs_tol=1e-14),(x,y)
 else:assert x==y,(x,y)
def forward(G,seeds):
 n,nb,dims,lu,ptr,tar,z,rb,cb=G;s=bytearray(nb)
 for i in seeds:s[i]=1
 for j in range(nb-1,-1,-1):
  if s[j]:
   for k in range(ptr[j]-1,ptr[j+1]-1):
    if z[k]:s[tar[k]-1]=1
 return s
def transpose(G,seed):
 n,nb,dims,lu,ptr,tar,z,rb,cb=G;s=bytearray(nb);s[seed]=1
 # Reverse closure from row block to later column block via topological recurrence.
 for j in range(nb):
  if not s[j]:s[j]=any(z[k] and s[tar[k]-1] for k in range(ptr[j]-1,ptr[j+1]-1))
 return s
def weights(G,s,trans=False):
 n,nb,dims,lu,ptr,tar,z,rb,cb=G
 active=[i for i in range(nb) if s[i]];lv=sum(lu[i]-dims[i] for i in active);fc=sum(ptr[i+1]-ptr[i] for i in active)
 dep=sum(s[tar[k]-1] for k in range(len(tar))) if trans else fc
 return dict(active_blocks=len(active),active_rows=sum(dims[i] for i in active),active_LU_stored=sum(lu[i] for i in active),active_LU_visits=lv,active_F_column_visits=fc,active_dependency_visits=dep,block_solve_coefficient_visits=lv+fc,edge_aware_coefficient_visits=lv+dep)
count=total=0;summary={};fixedsummary={}
for witness in raw['witnesses']:
 p=Path(witness['path']);h=p.stem;assert p.stat().st_size==witness['bytes'];assert hashlib.sha256(p.read_bytes()).hexdigest()==witness['sha256']
 graphs={};supports={};rlist=[];last=None
 with p.open('rb') as f:
  assert f.read(8)==b'KREACH01'
  for state in range(161):
   state2,n,nb,nf,ns,row,nd,res=struct.unpack('<8q',f.read(64));assert state2==state and res==0
   dims=take(f,'i',nb);lu=take(f,'i',nb);ptr=take(f,'i',nb+1);tar=take(f,'i',nf);z=f.read(nf);rb=take(f,'i',n);cb=take(f,'i',n);enter=take(f,'i',ns);dr=take(f,'i',nd);old=take(f,'d',nd);new=take(f,'d',nd)
   G=n,nb,dims,lu,ptr,tar,z,rb,cb
   assert sum(dims)==n and all(d>0 for d in dims) and all(l>=2*d for l,d in zip(lu,dims))
   assert ptr[0]==1 and ptr[-1]==nf+1 and all(x<=y for x,y in zip(ptr,ptr[1:]))
   assert all(1<=tar[k]<j+1 for j in range(nb) for k in range(ptr[j]-1,ptr[j+1]-1));assert set(z)<={0,1}
   for mp in [rb,cb]:assert sorted(mp)==[i+1 for i,d in enumerate(dims) for _ in range(d)]
   r=prof[h,state];full=sum(lu)-n+nf
   assert (r['n'],r['blocks'],r['F_stored'],r['LU_stored'],r['LU_visits'],r['full_coefficient_visits'])==(n,nb,nf,sum(lu),sum(lu)-n,full)
   for kind,seeds in [('FTRAN',set(rb[i-1]-1 for i in enter)),('BTRAN',{cb[row-1]-1})]:
    s=forward(G,seeds) if kind=='FTRAN' else transpose(G,next(iter(seeds)));w=weights(G,s,kind=='BTRAN');w['seed_blocks']=len(seeds);assert w==r[kind],(h,state,kind,w,r[kind])
    c=actualcsv[h,state,kind]
    rr=dict(seed_blocks=len(seeds),active_blocks=w['active_blocks'],active_rows=w['active_rows'],block_fraction=w['active_blocks']/nb,row_fraction=w['active_rows']/n,LU_fraction=w['active_LU_visits']/(sum(lu)-n),work_fraction=w['block_solve_coefficient_visits']/full,edge_work_fraction=w['edge_aware_coefficient_visits']/full,dependency_visits=w['active_dependency_visits'])
    for k,v in rr.items():assert math.isclose(float(c[k]),v,rel_tol=1e-14)
    rlist.append((kind,rr))
   own=above=below=scale=0
   for i,o,v in zip(dr,old,new):
    if struct.pack('<d',o)==struct.pack('<d',v):continue
    b=rb[i-1];t=cb[row-1];own+=b==t;above+=b<t;below+=b>t;scale+=abs(o)!=abs(v)
   change=dict(diagonal_block_changed_entries=own,above_block_changed_entries=above,below_block_changed_entries=below,potential_changed_row_sum_scales=scale,preserves_old_upper_partition=below==0,couplings_only_fixed_maps_scales=below==0 and own==0,leaving_block_dimension=dims[cb[row-1]-1]);assert change==r['change']
   groups={}
   for i,b in enumerate(cb,1):groups.setdefault(b,i)
   token=[groups[b] for b in cb];changed=0 if last is None else sum(x!=y for x,y in zip(token,last));last=token;assert changed==r['partition_token_changed_column_slots']
   assert r['CSR_graph_payload_bytes']==16*(nb+1)+18*nf
   assert r['block_weight_map_payload_bytes']==16*(n+nb)
   if state%20==0:graphs[state]=G
   supports[state]=enter;count+=1
  assert not f.read(1)
 total+=p.stat().st_size
 s={}
 for kind in ['FTRAN','BTRAN']:
  sr=[r for k,r in rlist if k==kind];s[kind]={key:q([r[key] for r in sr]) for key in sr[0]}
  equal(s[kind],a['summary'][h][kind])
 rr=[prof[h,i] for i in range(161)];cs=a['summary'][h]['changes']
 for k,v in dict(predictions=161,actual_transitions=160,old_partition_preserved=sum(r['change']['preserves_old_upper_partition'] for r in rr),F_only_fixed_maps_scales=sum(r['change']['couplings_only_fixed_maps_scales'] for r in rr),potential_scale_changes=sum(r['change']['potential_changed_row_sum_scales']>0 for r in rr),partition_token_changed=sum(r['partition_token_changed_column_slots']>0 for r in rr[1:])).items():assert cs[k]==v
 equal(cs['leaving_block_dimension'],q([r['change']['leaving_block_dimension'] for r in rr]));equal(a['summary'][h]['index_payload_bytes'],q([r['CSR_graph_payload_bytes']+r['block_weight_map_payload_bytes'] for r in rr]))
 for interval in [20,80,160]:
  rr=[]
  for state in range(161):
   base=state//interval*interval;G=graphs[base];n,nb,dims,lu,ptr,tar,z,rb,cb=G;seeds={rb[i-1]-1 for i in supports[state]};s=forward(G,seeds);w=weights(G,s);full=sum(lu)-n+len(tar)
   r=dict(history=h,interval=interval,state=state,base_state=base,age=state-base,n=n,blocks=nb,active_blocks=w['active_blocks'],active_rows=w['active_rows'],full_work=full,LU_visits=w['active_LU_visits'],F_visits=w['active_F_column_visits'],dependency_visits=w['active_dependency_visits'],work_fraction=w['block_solve_coefficient_visits']/full,LU_fraction=w['active_LU_visits']/(sum(lu)-n),block_fraction=w['active_blocks']/nb,row_fraction=w['active_rows']/n)
   for k,v in r.items():
    if isinstance(v,str):assert fixedcsv[h,interval,state][k]==v
    else:assert math.isclose(float(fixedcsv[h,interval,state][k]),v,rel_tol=1e-14)
   rr.append(r)
  equal(fixed['summary'][h+'/'+str(interval)],{k:q([r[k] for r in rr]) for k in ['work_fraction','LU_fraction','block_fraction','row_fraction','dependency_visits']})
 print(h,'independent ordered-DAG current/fixed profiles and quantiles: PASS',flush=True)
assert count==483 and total==raw['witness_bytes']==265791904 and len(actualcsv)==966 and len(fixedcsv)==1449
pins=json.loads((D/'launch-pins.json').read_text())['inventory'];assert len(pins)==53
for p,v in pins.items():assert str(Path(p).resolve())==v['resolved'] and hashlib.sha256(Path(p).read_bytes()).hexdigest()==v['sha256']
b=json.loads((D/'boundary-source-bindings.json').read_text())
for p,sha in b['files'].items():assert hashlib.sha256((D.parents[2]/p).read_bytes()).hexdigest()==sha
proc=json.loads((D/'reach-1/guard/process.json').read_text());post=json.loads((D/'reach-1/postflight.json').read_text());pre=json.loads((D/'reach-1/preflight.json').read_text())
print('ALL PASS',dict(graphs=count,RHS=len(actualcsv),fixed=len(fixedcsv),bytes=total,pins=len(pins),post_groups=len(post['checked_groups']),pre_groups=len(pre['checked_groups']),post_conflicts=post['conflicts'],duration=proc['elapsed_including_launch']))
