from pathlib import Path
from array import array
import sys,struct,tomllib,json,hashlib,statistics,csv,math
D=Path(sys.argv[1]);original=tomllib.loads((D/'results-1.toml').read_text());summaries={};allrows=[]
def ints(f,n):
 a=array('i');a.fromfile(f,n);return a
def need(v,m):
 if not v:raise ValueError(m)
def quant(a):
 a=sorted(a);return dict(min=a[0],p25=a[math.ceil(.25*len(a))-1],median=statistics.median(a),p75=a[math.ceil(.75*len(a))-1],p90=a[math.ceil(.9*len(a))-1],max=a[-1])
for witness in original['witnesses']:
 path=Path(witness['path']);history=path.stem
 with path.open('rb') as f:need(hashlib.file_digest(f,'sha256').hexdigest()==witness['sha256'],'unchanged witness')
 graphs={};inputs={}
 with path.open('rb') as f:
  need(f.read(8)==b'KREACH01','magic')
  for state in range(161):
   h=struct.unpack('<8q',f.read(64));s,n,nb,nf,ns,row,nd,reserved=h;need(s==state and reserved==0,'record header')
   if state%20==0:
    dims=ints(f,nb);lu=ints(f,nb);ptr=ints(f,nb+1);target=ints(f,nf);flags=f.read(nf);rb=ints(f,n)
    f.seek(4*n,1) # original-column map is not needed for forward reach
    graphs[state]=(n,nb,dims,lu,ptr,target,flags,rb)
   else:
    f.seek(4*(3*nb+1+nf+2*n)+nf,1)
   inputs[state]=ints(f,ns);f.seek(20*nd,1) # delta row ids plus old/new values
  need(not f.read(1),'exact EOF')
 for interval in [20,80,160]:
  rows=[]
  for state in range(161):
   base=state//interval*interval;n,nb,dims,lu,ptr,target,flags,rb=graphs[base]
   seeds=set(rb[r-1]-1 for r in inputs[state]);active=set(seeds);todo=list(seeds);visits=0
   while todo:
    b=todo.pop()
    for k in range(ptr[b]-1,ptr[b+1]-1):
     visits+=1
     if flags[k]:
      t=target[k]-1
      if t not in active:active.add(t);todo.append(t)
   lv=sum(lu[b]-dims[b] for b in active);fc=sum(ptr[b+1]-ptr[b] for b in active);full=sum(lu)-n+len(target)
   need(fc==visits,'forward edge/column budget')
   rows.append(dict(history=history,interval=interval,state=state,base_state=base,age=state-base,n=n,blocks=nb,active_blocks=len(active),active_rows=sum(dims[b] for b in active),full_work=full,LU_visits=lv,F_visits=fc,dependency_visits=visits,work_fraction=(lv+fc)/full,LU_fraction=lv/(sum(lu)-n),block_fraction=len(active)/nb,row_fraction=sum(dims[b] for b in active)/n))
  allrows+=rows;summaries[history+'/'+str(interval)]={k:quant([r[k] for r in rows]) for k in ['work_fraction','LU_fraction','block_fraction','row_fraction','dependency_visits']}
with (D/'fixed-base-summary.csv').open('x',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(allrows[0]),lineterminator='\n');w.writeheader();w.writerows(allrows)
result=dict(accepted=True,scope='additional offline fixed-base FTRAN scenarios only; no Julia/factor/solve/timing rerun',cases=len(allrows),intervals=[20,80,160],summary=summaries,source_evidence_sha256=hashlib.sha256((D/'results-1.toml').read_bytes()).hexdigest())
(D/'fixed-base-analysis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
