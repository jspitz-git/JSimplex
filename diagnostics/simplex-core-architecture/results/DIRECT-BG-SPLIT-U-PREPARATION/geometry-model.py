# New offline integer geometry model; NOT Julia, candidate execution or timing.
from pathlib import Path
import json,hashlib
Q=Path(__file__).resolve().parent
class Model:
 def __init__(self):
  self.ext={};self.bins={c:[] for c in range(1,33)};self.K=0;self.D=0;self.S=0;self.C=0
  self.payload=self.requests=self.descriptor_copy=self.directory_copy=self.splits=self.relocated=self.cleared=0
 def alloc(self,bytes):self.payload+=bytes;self.requests+=1
 def desc(self,required):
  if required<=self.K:return
  new=max(required,self.K+max(self.K//2,8));self.payload+=28*new;self.requests+=7;self.descriptor_copy+=28*self.K;self.K=new
 def free(self,b):self.bins[self.ext[b]].insert(0,b)
 def reserve(self,required):
  target=next(c for c in [1,2,4,8,16,32] if c>=required)
  donor=next((self.bins[c][0] for c in range(target,33) if self.bins[c]),0)
  if not donor:
   old=len(self.ext);self.desc(old+8);self.payload+=4096;self.requests+=3
   if self.S+1>self.D:
    new=max(self.S+1,self.D+max(self.D//2,1));self.payload+=24*new;self.requests+=3;self.directory_copy+=24*self.S;self.D=new
   self.S+=1;self.C+=256
   for b in range(old+1,old+9):self.ext[b]=32;self.free(b)
   donor=self.bins[32][0]
  cap=self.ext[donor]
  if cap>target:
   new=len(self.ext)+1;self.desc(new);self.bins[cap].remove(donor)
   self.ext[donor]=target;self.ext[new]=cap-target;self.free(donor);self.free(new);self.splits+=1
  return donor
 def take(self,b):self.bins[self.ext[b]].remove(b)
m=Model();active=0
for r in range(1,33):
 m.alloc(8) # new empty row -> capacity2 Int32
 count=r-1
 if not active:
  active=m.reserve(1);m.take(active)
 elif count==m.ext[active]:
  donor=m.reserve(count+1);m.take(donor);m.ext[active],m.ext[donor]=m.ext[donor],m.ext[active]
  m.relocated+=count;m.cleared+=m.ext[donor];m.free(donor)
checks={'monotone_allocations':(m.requests,m.payload,m.descriptor_copy,m.directory_copy)==(52,5048,224,0),'monotone_geometry':(m.C,m.K,m.D,m.S,len(m.ext),m.splits)==(256,16,1,1,13,5),'monotone_movements':m.relocated==m.cleared==31,'partition_capacity':sum(m.ext.values())==m.C,'repeat_four_descriptor_delta':(256//4-256//32)*28==1568}
# Bound on the inherited largest mutation schedule: 1600 fills + 40 refills.
I=1640;n=64;C=256*I;K=(3*(9*I)+1)//2+8;R=n*n+9*n;D=(3*I+1)//2+1
bound=16*C+4*R+28*K+32*n+656+8*n+24*D
out={'scope':'offline integer model of ONE monotone schedule, not runtime/work proof','all_passed':all(checks.values()),'checks':checks,'monotone':{k:v for k,v in vars(m).items() if k not in ['ext','bins']},'monotone_used':len(m.ext),'monotone_live':32,'monotone_core_plus_pointers':16*256+4*64+28*16+32*40+656+8*40+24,'largest_inherited_schedule_conservative_bound':{'insertions':I,'n':n,'C':C,'R':R,'K':K,'D':D,'core_plus_pointers_bytes':bound,'excludes':'headers, physical backing, test oracles/snapshots, allocator/GC/native'},'executed_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
with (Q/'geometry-model.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps(out))
if not out['all_passed']:raise SystemExit(1)
