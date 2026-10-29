from pathlib import Path
from array import array
from collections import Counter
import json,struct,hashlib,tomllib,statistics,csv,math,resource,signal,itertools
D=Path(__file__).resolve().parent;W=D.parents[2];R=W/'diagnostics/klu-block-reach/2026-10-29'
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));signal.alarm(180)
def need(v,m):
 if not v:raise ValueError(m)
def digest(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ints(f,n):
 need(0<=n<=5_000_001,'integer array bound');a=array('i');a.fromfile(f,n);return a
# Edges are original F column-block -> earlier row-block. Transpose reach reverses them.
def reverse_adjacency(nb,ptr,target,flag):
 adj=[[]for _ in range(nb)];stored=[0]*nb
 for b in range(nb):
  for k in range(ptr[b],ptr[b+1]):
   t=target[k];need(0<=t<b,'strict block-upper edge');stored[t]+=1
   if flag[k]:adj[t].append(b)
 return adj,stored
def all_reach(adj):
 reach=[0]*len(adj)
 for b in range(len(adj)-1,-1,-1):
  bits=1<<b
  for v in adj[b]:bits|=reach[v]
  reach[b]=bits
 return reach
def planes(weights):
 pp=[0]*max(1,max(weights,default=0).bit_length())
 for b,w in enumerate(weights):
  for k in range(w.bit_length()):
   if w&(1<<k):pp[k]|=1<<b
 return pp
def weighted(bits,p):return sum((bits&q).bit_count()<<k for k,q in enumerate(p))
def bfs(adj,seeds):
 seen=set(seeds);todo=list(seeds)
 while todo:
  for v in adj[todo.pop()]:
   if v not in seen:seen.add(v);todo.append(v)
 return seen
def quant(a):
 a=sorted(a);need(bool(a),'nonempty distribution');return dict(min=a[0],p25=a[math.ceil(.25*len(a))-1],median=statistics.median(a),p75=a[math.ceil(.75*len(a))-1],p90=a[math.ceil(.9*len(a))-1],max=a[-1],mean=statistics.fmean(a))
def weighted_quant(values,multiplicity):
 a=sorted((v,m)for v,m in zip(values,multiplicity));n=sum(multiplicity)
 def at(i):
  acc=0
  for v,m in a:
   acc+=m
   if acc>=i:return v
  raise ValueError('quantile')
 return dict(min=a[0][0],p25=at(math.ceil(.25*n)),median=(at((n+1)//2)+at(n//2+1))/2,p75=at(math.ceil(.75*n)),p90=at(math.ceil(.9*n)),max=a[-1][0],mean=sum(v*m for v,m in a)/n)
# Independent set/DFS checks for every subset of every four-node upper DAG.
small_checks=0
for mask in range(64):
 edges=list(itertools.combinations(range(4),2));adj=[[]for _ in range(4)]
 for k,(a,b)in enumerate(edges):
  if mask&(1<<k):adj[a].append(b)
 rr=all_reach(adj);ww=[1,3,7,19];pp=planes(ww)
 for sm in range(16):
  seeds=[b for b in range(4)if sm&(1<<b)];bits=0
  for b in seeds:bits|=rr[b]
  seen=bfs(adj,seeds);need(bits==sum(1<<b for b in seen) and weighted(bits,pp)==sum(ww[b]for b in seen),'exhaustive graph/weight check');small_checks+=1
old=tomllib.loads((R/'results-1.toml').read_text());oldprofiles={(x['history'],x['state']):x for x in old['profiles']};summary=[];bindings={};realchecks=0
for witness in old['witnesses']:
 path=Path(witness['path']);need(path.stat().st_size==witness['bytes'] and digest(path)==witness['sha256'],'unchanged original graph witness');bindings[str(path)]=witness['sha256'];history=path.stem
 with path.open('rb')as f:
  need(f.read(8)==b'KREACH01','witness magic')
  for state in range(161):
   header=f.read(64);need(len(header)==64,'header length');s,n,nb,nf,ns,leaving,nd,reserved=struct.unpack('<8q',header);need(s==state and reserved==0 and 1<=nb<=n<=100000,'header bounds')
   if state not in (0,80,160):f.seek(4*(3*nb+1+nf+2*n+ns)+nf+20*nd,1);continue
   dims=ints(f,nb);lu=ints(f,nb);ptr=[v-1 for v in ints(f,nb+1)];target=[v-1 for v in ints(f,nf)];flags=f.read(nf);rb=ints(f,n);cb=[v-1 for v in ints(f,n)];enter=ints(f,ns);f.seek(20*nd,1)
   need(sum(dims)==n and ptr[0]==0 and ptr[-1]==nf and all(a<=b for a,b in zip(ptr,ptr[1:])) and all(v in (0,1)for v in flags),'graph shape')
   need(Counter(cb)==Counter({b:d for b,d in enumerate(dims)}),'Q map multiplicity')
   adj,reverse_stored=reverse_adjacency(nb,ptr,target,flags);reach=all_reach(adj);luv=[l-d for l,d in zip(lu,dims)];colcounts=[ptr[b+1]-ptr[b]for b in range(nb)]
   blockweights=[luv[b]+colcounts[b]for b in range(nb)];edgeweights=[luv[b]+reverse_stored[b]for b in range(nb)];full=sum(luv)+nf;bp=planes(blockweights);ep=planes(edgeweights);dp=planes(dims)
   blockwork=[weighted(v,bp)for v in reach];edgework=[weighted(v,ep)for v in reach];rows=[weighted(v,dp)for v in reach]
   selected=sorted(set([0,nb-1,cb[leaving-1],*[(k*(nb-1))//31 for k in range(32)]]))
   for b in selected:
    seen=bfs(adj,[b]);bits=sum(1<<j for j in seen)
    need(bits==reach[b] and sum(edgeweights[j]for j in seen)==edgework[b] and sum(blockweights[j]for j in seen)==blockwork[b] and sum(dims[j]for j in seen)==rows[b],'actual set BFS crosscheck');realchecks+=1
   p=oldprofiles[history,state]['BTRAN'];b=cb[leaving-1]
   need(reach[b].bit_count()==p['active_blocks'] and rows[b]==p['active_rows'] and blockwork[b]==p['block_solve_coefficient_visits'] and edgework[b]==p['edge_aware_coefficient_visits'],'old selected-unit source alignment')
   unionwork=0;independentwork=0;group_count=0
   for start in range(0,n,4):
    group=cb[start:start+4];bits=0
    for b in group:bits|=reach[b];independentwork+=edgework[b]
    unionwork+=len(group)*weighted(bits,ep);group_count+=1
   flat=n*full;total=sum(w*d for w,d in zip(edgework,dims));need(0<total<=flat and independentwork==total and unionwork>=total,'total work bounds')
   item=dict(history=history,base_state=state,n=n,blocks=nb,F_stored=nf,full_coefficient_visits_per_RHS=full,unit_RHS_count=n,
     block_only_fraction=weighted_quant([w/full for w in blockwork],dims),edge_aware_fraction=weighted_quant([w/full for w in edgework],dims),row_fraction=weighted_quant([v/n for v in rows],dims),block_fraction=weighted_quant([v.bit_count()/nb for v in reach],dims),
     total_edge_coefficient_visits=total,total_full_coefficient_visits=flat,total_fraction=total/flat,unit_below_75percent=sum(d for w,d in zip(edgework,dims)if 4*w<3*full),
     fixed_four_RHS_groups=group_count,four_RHS_union_padded_visits=unionwork,four_RHS_union_over_independent=unionwork/total,
     reverse_index_payload_upper_bytes=8*(n+1)+16*nf+8*n,
     offline_reach_integer_payload_bytes=sum((v.bit_length()+7)//8 for v in reach),
     bound_note='coefficient/division visit model; no timing or solve, not per-call work cap; reverse index upper assumes rowptr+positions+sourcecols+inverseQ; excludes headers/scratch')
   summary.append(item)
  need(not f.read(1),'witness exact EOF')
need(len(summary)==9 and sum(s['unit_RHS_count']for s in summary)==172170,'nine bases and all-unit count')
rows=[]
for s in summary:rows.append(dict(history=s['history'],base=s['base_state'],n=s['n'],blocks=s['blocks'],block_fraction_median=s['block_only_fraction']['median'],edge_fraction_median=s['edge_aware_fraction']['median'],edge_fraction_total=s['total_fraction'],below75percent=s['unit_below_75percent'],four_rhs_union_over_independent=s['four_RHS_union_over_independent'],reverse_payload_upper_bytes=s['reverse_index_payload_upper_bytes']))
with (D/'all-unit-summary.csv').open('x',newline='')as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
result=dict(accepted=True,scope='new offline all-unit transpose graph analysis; zero Julia, native calls, factors, solves or timing windows',small_DAG_checks=small_checks,actual_BFS_crosschecks=realchecks,old_selected_unit_crosschecks=9,unit_RHS_count=172170,all_unit_graphs=9,original_witness_bindings=bindings,summary=summary,offline_process_maxrss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
(D/'all-unit-analysis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'accepted':True,'all_unit_graphs':9,'unit_RHS_count':172170,'small_checks':small_checks,'actual_BFS_checks':realchecks,'offline_maxrss_kib':result['offline_process_maxrss_kib']}))
