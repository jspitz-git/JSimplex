from pathlib import Path
from array import array
from collections import Counter
import hashlib,json,struct,tomllib,statistics,math,csv,resource,signal,subprocess
D=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl/diagnostics/klu-shared-solves/2026-10-29'); W=D.parents[2]
resource.setrlimit(resource.RLIMIT_AS,(768*1024**2,768*1024**2));signal.alarm(150)
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
checks=[]
def ck(q,s):
 if not q:raise AssertionError(s)
 checks.append(s)
pre={str(p):sha(p) for p in D.rglob('*') if p.is_file()}
for f in ['analysis-bindings.json','source-bindings.json','source-bindings-addendum.json']:
 for name,h in json.loads((D/f).read_text())['files'].items():
  p=Path(name) if Path(name).is_absolute() else D/name
  ck(sha(p)==h,'binding '+str(p))
A=json.loads((D/'all-unit-analysis.json').read_text());old=tomllib.loads((W/'diagnostics/klu-block-reach/2026-10-29/results-1.toml').read_text())
S={(x['history'],x['base_state']):x for x in A['summary']}; witnesses={}; rows=[]; bfschecks=0
# Independent orientation: propagate sets of original seed ancestors FORWARD,
# then bit-sliced integer addition accumulates per-seed reached-node weights.
def per_seed_cost(anc,weights,nb):
 planes=[]
 for bits,w in zip(anc,weights):
  for k in range(w.bit_length()):
   if not (w>>k)&1:continue
   carry=bits; j=k
   while carry:
    if j==len(planes):planes.append(0)
    elif j>len(planes):planes.extend([0]*(j-len(planes)+1))
    carry,planes[j]=carry & planes[j],carry ^ planes[j];j+=1
 return [sum(((p>>i)&1)<<j for j,p in enumerate(planes)) for i in range(nb)]
def dist(v,m):
 z=sorted(x for x,n in zip(v,m) for _ in range(n)); n=len(z)
 return dict(min=z[0],p25=z[math.ceil(.25*n)-1],median=statistics.median(z),p75=z[math.ceil(.75*n)-1],p90=z[math.ceil(.9*n)-1],max=z[-1],mean=statistics.fmean(z))
def arr(f,n):
 x=array('i');x.fromfile(f,n);return x
for wit in old['witnesses']:
 path=Path(wit['path']);ck(path.stat().st_size==wit['bytes'] and sha(path)==wit['sha256'],'whole witness '+path.name);witnesses[str(path)]=sha(path)
 with path.open('rb') as f:
  ck(f.read(8)==b'KREACH01','magic '+path.name)
  for age in range(161):
   state,n,nb,nf,ns,leave,nd,res=struct.unpack('<8q',f.read(64));ck(state==age and res==0,'frame '+path.name+'/'+str(age))
   if age not in (0,80,160):f.seek(4*(3*nb+1+nf+2*n+ns)+nf+20*nd,1);continue
   dim=arr(f,nb); lu=arr(f,nb);ptr=[x-1 for x in arr(f,nb+1)];target=[x-1 for x in arr(f,nf)];flag=f.read(nf);rb=arr(f,n);cb=[x-1 for x in arr(f,n)];arr(f,ns);f.seek(20*nd,1)
   ck(Counter(cb)==Counter(dict(enumerate(dim))) and sum(dim)==n and ptr[0]==0 and ptr[-1]==nf,'Q multiplicities and shape '+path.stem+'/'+str(age))
   anc=[1<<i for i in range(nb)]; groups=[0]*nb; adj=[set() for _ in range(nb)]; stored=[0]*nb
   for i,b in enumerate(cb):groups[b]|=1<<(i//4)
   for b in range(nb):
    for j in range(ptr[b],ptr[b+1]):
     r=target[j];ck(0<=r<b and flag[j] in (0,1),'edge direction/flag')
     stored[r]+=1
     if flag[j]:adj[r].add(b)
   for b in range(nb):
    for nxt in adj[b]:anc[nxt]|=anc[b];groups[nxt]|=groups[b]
   ew=[lu[i]-dim[i]+stored[i] for i in range(nb)];bw=[lu[i]-dim[i]+ptr[i+1]-ptr[i] for i in range(nb)];full=sum(lu)-n+nf
   work=per_seed_cost(anc,ew,nb);blockwork=per_seed_cost(anc,bw,nb);reachedrows=per_seed_cost(anc,dim,nb);reachedblocks=per_seed_cost(anc,[1]*nb,nb)
   s=S[path.stem,age]; total=sum(w*d for w,d in zip(work,dim));ng=(n+3)//4;tail=n-4*(ng-1)
   union=sum(w*(4*g.bit_count()-(4-tail)*((g>>(ng-1))&1)) for w,g in zip(ew,groups))
   ck(total==s['total_edge_coefficient_visits'] and n*full==s['total_full_coefficient_visits'],'independent all-unit weighted total '+path.stem+'/'+str(age))
   ck(union==s['four_RHS_union_padded_visits'] and union/total==s['four_RHS_union_over_independent'],'independent group-ancestor union '+path.stem+'/'+str(age))
   ck(sum(d for w,d in zip(work,dim) if 4*w<3*full)==s['unit_below_75percent'],'all-unit strict threshold '+path.stem+'/'+str(age))
   for field,values,denom in [('edge_aware_fraction',work,full),('block_only_fraction',blockwork,full),('row_fraction',reachedrows,n),('block_fraction',reachedblocks,nb)]:
    q=dist([v/denom for v in values],dim)
    ck(all(math.isclose(q[k],s[field][k],rel_tol=2e-14,abs_tol=1e-16) for k in q),'explicit unit-expanded quantiles '+field+'/'+path.stem+'/'+str(age))
   for root in sorted({0,nb-1,cb[leave-1],*((k*(nb-1))//23 for k in range(24))}):
    seen={root}; todo=[root]
    while todo:
     for nxt in adj[todo.pop()]:
      if nxt not in seen:seen.add(nxt);todo.append(nxt)
    ck(sum(ew[b] for b in seen)==work[root] and sum(dim[b] for b in seen)==reachedrows[root],'direct set traversal');bfschecks+=1
   ck(s['reverse_index_payload_upper_bytes']==8*(2*n+1+2*nf),'reverse index bytes '+path.stem+'/'+str(age))
   rows.append(dict(history=path.stem,state=age,n=n,total=total,full=n*full,fraction=total/(n*full),union=union,ratio=union/total))
  ck(not f.read(1),'exact EOF '+path.name)
ck(sum(r['n'] for r in rows)==172170 and len(rows)==9,'all nine anchors')
ck(A['small_DAG_checks']==1024 and A['actual_BFS_crosschecks']==297 and A['old_selected_unit_crosschecks']==9,'reported original verification counts')
for path,h in pre.items():ck(sha(path)==h,'preserved '+path)
for path,h in witnesses.items():ck(sha(path)==h,'preserved witness '+path)
refs={x:subprocess.check_output(['git','rev-parse',x],cwd=W,text=True).strip() for x in ['HEAD','master','origin/master']}
ck(refs==json.loads((D/'source-bindings.json').read_text())['refs'],'unchanged revision identities')
out=dict(accepted=True,scope='Independent integer-only graph/source review; no original scripts executed, Julia, native calls, factorization, floating-point solves or numerical timing',method='Forward propagation of seed-ancestor bitsets plus bit-sliced weighted addition; unit-expanded quantiles and separately propagated original-position group ancestors',checks=len(checks),direct_BFS_checks=bfschecks,anchors=rows,readtime_refs=refs,all_preexisting_files_preserved=True,witness_bytes=sum(Path(p).stat().st_size for p in witnesses),limits=dict(address_space_bytes=768*1024**2,alarm_seconds=150),process_maxrss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
(D/'review-checks.json').open('x').write(json.dumps(out,indent=2)+'\n')
bindings=dict(scope='Independent review readtime hashes, not launch pins',files=pre,witnesses=witnesses,script_sha256=sha(__file__))
(D/'review-bindings.json').open('x').write(json.dumps(bindings,indent=2)+'\n')
print(json.dumps(out,indent=2))
