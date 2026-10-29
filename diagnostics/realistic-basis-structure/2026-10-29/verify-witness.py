from pathlib import Path
import json,tomllib,struct,array,hashlib,sys,math
D=Path(__file__).resolve().parent
assert sys.byteorder=='little' and array.array('q').itemsize==8
raw=tomllib.loads((D/'results-1.toml').read_text());refs=[]
for c in raw['cases']:
 for p in c['basis_profiles']:refs.append((c['id']+'/B'+str(p['step']),p['profile'],p['witness']))
for c in raw['cold']:
 for p in c['spike_profiles']:
  if 'witness'in p:refs.append((f"{c['case']}/{c['mode']}/{c['backend']}/{c['interval']}/spike{p['step']}",p['profile'],p['witness']))
checks=[];omitted=[]
for name,summary,w in refs:
 if 'path'not in w:omitted.append(name);continue
 path=Path(w['path'])
 if hashlib.sha256(path.read_bytes()).hexdigest()!=w['sha256']:raise RuntimeError('witnesshash '+name)
 def read_array(f,code,n):
  a=array.array(code);a.fromfile(f,n);return a
 with path.open('rb')as f:
  if f.read(8)!=b'JSTRUC01':raise RuntimeError('magic')
  n,e=struct.unpack('<qq',f.read(16));ptr=read_array(f,'q',n+1);rows=read_array(f,'q',e);vals=read_array(f,'d',e);match=read_array(f,'q',n);labels=read_array(f,'q',n)
  if f.read(1):raise RuntimeError('trailingbytes')
 if n!=summary['dimension']or ptr[0]!=1 or ptr[-1]!=e+1 or sorted(match)!=list(range(1,n+1)):raise RuntimeError('dimensions/matching')
 inv=[0]*n
 for j,r in enumerate(match):inv[r-1]=j
 k=max(labels);sizes=[0]*k;roots=[-1]*k;count=[0]*n;nnz=0;off=0
 for i,cid in enumerate(labels):
  if not 1<=cid<=k:raise RuntimeError('labelrange')
  sizes[cid-1]+=1;roots[cid-1]=i
 for j in range(n):
  found=False;previous=0
  if ptr[j]>ptr[j+1]:raise RuntimeError('ptrorder')
  for p in range(ptr[j]-1,ptr[j+1]-1):
   r=rows[p];v=vals[p]
   if not previous<r<=n or not math.isfinite(v):raise RuntimeError('noncanonical/nonfinite')
   previous=r
   if r==match[j]and v!=0:found=True
   if v==0:continue
   i=inv[r-1];count[i]+=1;nnz+=1
   if labels[i]>labels[j]:raise RuntimeError('condensationcycle')
   if labels[i]!=labels[j]:off+=1
  if not found:raise RuntimeError('nonzero diagonal match')
 if not all(sizes):raise RuntimeError('labelgap')
 # Build independent outgoing CSR. Original CSC is the reverse adjacency.
 rp=[0]*(n+1)
 for i in range(n):rp[i+1]=rp[i]+count[i]
 write=rp.copy();edges=array.array('q',[0])*nnz
 for j in range(n):
  for p in range(ptr[j]-1,ptr[j+1]-1):
   if vals[p]!=0:
    i=inv[rows[p]-1];edges[write[i]]=j;write[i]+=1
 for reverse in [False,True]:
  seen=bytearray(n)
  for cid,size in enumerate(sizes,1):
   if size==1:continue
   root=roots[cid-1];stack=[root];seen[root]=1;visited=0
   while stack:
    node=stack.pop();visited+=1
    if reverse:
     candidates=(inv[rows[p]-1]for p in range(ptr[node]-1,ptr[node+1]-1)if vals[p]!=0)
    else:candidates=(edges[p]for p in range(rp[node],rp[node+1]))
    for other in candidates:
     if labels[other]==cid and not seen[other]:seen[other]=1;stack.append(other)
   if visited!=size:raise RuntimeError('component not strongly connected '+name)
 histogram={}
 for size in sizes:histogram[str(size)]=histogram.get(str(size),0)+1
 biggest=sizes.index(max(sizes))+1;inside=0
 for j in range(n):
  for p in range(ptr[j]-1,ptr[j+1]-1):
   if vals[p]!=0 and labels[j]==biggest and labels[inv[rows[p]-1]]==biggest:inside+=1
 if (summary['nnz'],summary['blocks'],summary['singletons'],summary['largest_block'],summary['coupling_nnz'],summary['largest_block_nnz'],summary['block_sizes_histogram'])!=(nnz,k,sizes.count(1),max(sizes),off,inside,histogram):raise RuntimeError('summarycounts '+name)
 # Independently construct a topological component member traversal for depth.
 cp=[0]*(k+1)
 for i in range(k):cp[i+1]=cp[i]+sizes[i]
 cw=cp.copy();members=array.array('q',[0])*n
 for i,cid in enumerate(labels):members[cw[cid-1]]=i;cw[cid-1]+=1
 depth=[1]*k
 for cid in range(k):
  for p in range(cp[cid],cp[cid+1]):
   node=members[p]
   for z in range(rp[node],rp[node+1]):
    target=labels[edges[z]]-1
    if target!=cid:depth[target]=max(depth[target],depth[cid]+1)
 if max(depth)!=summary['condensation_depth']:raise RuntimeError('depth '+name)
 checks.append(dict(name=name,dimension=n,nnz=nnz,blocks=k,largest=max(sizes),sha256=w['sha256']))
result={'accepted':True,'verified_witnesses':len(checks),'omitted_witnesses':omitted,'checks':checks,'raw_sha256':hashlib.sha256((D/'results-1.toml').read_bytes()).hexdigest(),'scope':'all SAVED perfectmatch/SCC partitions independently verified, not unsaved profiles or numeric solves'}
with(D/'witness-verification.json').open('x')as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'accepted':True,'verified':len(checks),'omitted':len(omitted)}))
