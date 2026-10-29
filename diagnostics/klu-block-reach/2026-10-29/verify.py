from pathlib import Path
from array import array
from collections import Counter
import tomllib,json,hashlib,struct,sys,statistics,csv,math
D=Path(sys.argv[1]);data=tomllib.loads((D/'results-1.toml').read_text());profiles={(r['history'],r['state']):r for r in data['profiles']};checks=[]
def require(v,message):
 if not v:raise ValueError(message)
def ints(f,n):
 require(0<=n<=5_000_001,'array size limit');v=array('i');v.fromfile(f,n);return v
def doubles(f,n):
 v=array('d');v.fromfile(f,n);return v
def take(f,n):
 b=f.read(n);require(len(b)==n,'truncated bytes');return b
def closure(ptr,target,flag,seeds):
 active=set(seeds);todo=list(active);visits=0
 while todo:
  a=todo.pop()
  for k in range(ptr[a],ptr[a+1]):
   visits+=1
   if flag[k] and target[k] not in active:active.add(target[k]);todo.append(target[k])
 return active,visits
def reverse(ptr,tar,flag):
 n=len(ptr)-1;c=[0]*n
 for a in tar:c[a]+=1
 p=[0]
 for a in c:p.append(p[-1]+a)
 t=array('i',[0])*len(tar);z=bytearray(len(tar));nxt=p.copy()
 for i in range(n):
  for k in range(ptr[i],ptr[i+1]):
   a=tar[k];j=nxt[a];t[j]=i;z[j]=flag[k];nxt[a]+=1
 return p,t,z
count=0;totalbytes=0
for w in data['witnesses']:
 path=Path(w['path']);require(path.stat().st_size==w['bytes'],'witness bytes')
 h=hashlib.file_digest(path.open('rb'),'sha256').hexdigest();require(h==w['sha256'],'witness hash')
 history=path.stem;statecount=0;lasttoken=None
 with path.open('rb') as f:
  require(take(f,8)==b'KREACH01','witness magic')
  while True:
   header=f.read(64)
   if not header:break
   require(len(header)==64,'record header');state,n,nb,nf,ns,row,nd,reserved=struct.unpack('<8q',header)
   require(state==statecount and 1<=nb<=n<2**31 and nf<=5_000_000 and reserved==0,'record bounds')
   dims=ints(f,nb);lu=ints(f,nb);ptr=[x-1 for x in ints(f,nb+1)];tar=[x-1 for x in ints(f,nf)];flag=take(f,nf)
   rb=ints(f,n);cb=ints(f,n);enter=ints(f,ns);dr=ints(f,nd);old=doubles(f,nd);new=doubles(f,nd)
   require(all(x>0 for x in dims) and sum(dims)==n,'block sizes');require(all(l>=2*d for l,d in zip(lu,dims)),'LU dimensions')
   require(ptr[0]==0 and ptr[-1]==nf and all(a<=b for a,b in zip(ptr,ptr[1:])),'CSR ptr')
   require(all(x in (0,1) for x in flag),'nonzero flags')
   require(all(0<=tar[k]<b for b in range(nb) for k in range(ptr[b],ptr[b+1])),'strict block triangular edges')
   require(Counter(rb)==Counter({i+1:d for i,d in enumerate(dims)}) and Counter(cb)==Counter(rb),'map dimensions')
   require(all(1<=i<=n for i in [*enter,*dr,row]),'original row/column ids')
   rec=profiles[history,state];rptr,rtar,rflag=reverse(ptr,tar,flag)
   full=sum(lu)-n+nf
   require((rec['n'],rec['blocks'],rec['F_stored'],rec['LU_stored'],rec['LU_visits'],rec['full_coefficient_visits'])==(n,nb,nf,sum(lu),sum(lu)-n,full),'full work totals')
   for kind,seeds,tr in [('FTRAN',{rb[r-1]-1 for r in enter},False),('BTRAN',{cb[row-1]-1},True)]:
    active,visits=closure(rptr if tr else ptr,rtar if tr else tar,rflag if tr else flag,seeds)
    luv=sum(lu[b]-dims[b] for b in active);stored=sum(lu[b] for b in active);fc=sum(ptr[b+1]-ptr[b] for b in active)
    expected=dict(seed_blocks=len(seeds),active_blocks=len(active),active_rows=sum(dims[b] for b in active),active_LU_stored=stored,active_LU_visits=luv,active_F_column_visits=fc,active_dependency_visits=visits,block_solve_coefficient_visits=luv+fc,edge_aware_coefficient_visits=luv+visits)
    require(rec[kind]==expected,f'reach/weights {history}/{state}/{kind}')
   own=above=below=scale=0
   for r,a,b in zip(dr,old,new):
    if struct.pack('<d',a)==struct.pack('<d',b):continue
    block=rb[r-1];target=cb[row-1]
    if block==target:own+=1
    elif block<target:above+=1
    else:below+=1
    scale+=abs(a)!=abs(b)
   change=dict(diagonal_block_changed_entries=own,above_block_changed_entries=above,below_block_changed_entries=below,potential_changed_row_sum_scales=scale,preserves_old_upper_partition=below==0,couplings_only_fixed_maps_scales=below==0 and own==0,leaving_block_dimension=dims[cb[row-1]-1])
   require(rec['change']==change,'update classification')
   roots=[n+1]*nb
   for j,b in enumerate(cb,1):roots[b-1]=min(roots[b-1],j)
   token=[roots[b-1] for b in cb];changed=0 if lasttoken is None else sum(a!=b for a,b in zip(token,lasttoken));lasttoken=token
   require(rec['partition_token_changed_column_slots']==changed,'canonical partition labels')
   require(rec['CSR_graph_payload_bytes']==8*(2*(nb+1)+2*nf)+2*nf,'CSR payload')
   require(rec['block_weight_map_payload_bytes']==8*(2*n+2*nb),'map/weight payload')
   require(rec['identity_error']<=min(1e-10,128*n*2**-52),'export identity')
   count+=1;statecount+=1
 require(statecount==161,'history state coverage');totalbytes+=w['bytes'];checks.append(dict(history=history,states=statecount,bytes=w['bytes'],sha256=h))
require(count==483 and totalbytes==data['witness_bytes']<=512*1024**2,'whole witness counts')
require(data['completed'] and data['counts']==dict(factorizations=483,combined_extracts=483,basis_solves=0,identity_probes=483),'whole workload counts')
proc=json.loads((D/'reach-1/guard/process.json').read_text());post=json.loads((D/'reach-1/postflight.json').read_text())
require(proc['reason']=='exit0' and proc['returncode']==0 and proc['pins_unchanged'] and not post['conflicts'],'guard/postflight')
pins=json.loads((D/'launch-pins.json').read_text())
require(all(str(Path(p).resolve())==v['resolved'] and hashlib.sha256(Path(p).read_bytes()).hexdigest()==v['sha256'] for p,v in pins['inventory'].items()),'all launch pins')
rows=[]
for r in data['profiles']:
 for kind in ['FTRAN','BTRAN']:
  q=r[kind];rows.append(dict(history=r['history'],state=r['state'],RHS=kind,blocks=r['blocks'],n=r['n'],full_work=r['full_coefficient_visits'],seed_blocks=q['seed_blocks'],active_blocks=q['active_blocks'],active_rows=q['active_rows'],active_LU_visits=q['active_LU_visits'],active_F_column_visits=q['active_F_column_visits'],dependency_visits=q['active_dependency_visits'],block_fraction=q['active_blocks']/r['blocks'],row_fraction=q['active_rows']/r['n'],LU_fraction=q['active_LU_visits']/r['LU_visits'],work_fraction=q['block_solve_coefficient_visits']/r['full_coefficient_visits'],edge_work_fraction=q['edge_aware_coefficient_visits']/r['full_coefficient_visits']))
with (D/'summary.csv').open('x',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
def quant(values):
 a=sorted(values);return dict(min=a[0],p25=a[math.ceil(.25*len(a))-1],median=statistics.median(a),p75=a[math.ceil(.75*len(a))-1],p90=a[math.ceil(.9*len(a))-1],max=a[-1])
summary={}
for history in sorted({r['history'] for r in rows}):
 s={}
 for kind in ['FTRAN','BTRAN']:
  rr=[r for r in rows if r['history']==history and r['RHS']==kind]
  s[kind]={k:quant([r[k] for r in rr]) for k in ['seed_blocks','active_blocks','active_rows','block_fraction','row_fraction','LU_fraction','work_fraction','edge_work_fraction','dependency_visits']}
 rr=[r for r in data['profiles'] if r['history']==history]
 # Last state predicts next exchange but no subsequent partition is captured; keep denominators explicit.
 s['changes']=dict(predictions=len(rr),old_partition_preserved=sum(r['change']['preserves_old_upper_partition'] for r in rr),F_only_fixed_maps_scales=sum(r['change']['couplings_only_fixed_maps_scales'] for r in rr),potential_scale_changes=sum(r['change']['potential_changed_row_sum_scales']>0 for r in rr),actual_transitions=len(rr)-1,partition_token_changed=sum(r['partition_token_changed_column_slots']>0 for r in rr[1:]),leaving_block_dimension=quant([r['change']['leaving_block_dimension'] for r in rr]))
 s['index_payload_bytes']=quant([r['CSR_graph_payload_bytes']+r['block_weight_map_payload_bytes'] for r in rr]);summary[history]=s
result=dict(accepted=True,verified_profiles=count,verified_actual_RHS=len(rows),witness_bytes=totalbytes,witnesses=checks,summary=summary,scope='source-derived coefficients/reach, not numerical skip admission or timing speedup')
(D/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
