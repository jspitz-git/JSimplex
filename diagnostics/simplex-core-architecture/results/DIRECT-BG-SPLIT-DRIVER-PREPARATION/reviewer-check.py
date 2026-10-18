"""Independent reviewer text/hash/integer checks. Imports no preparation/candidate code."""
from pathlib import Path
import hashlib,json,re,tomllib,subprocess,os
D=Path(__file__).resolve().parent;R=D.parents[3];C=R/'diagnostics/direct-bg-split-upper/reproduce';checks={}
def read(p):return json.loads(Path(p).read_text())
def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def check(name,v):
 checks[name]=bool(v)
 if not v:raise AssertionError(name)
def save(name,v):
 with (D/name).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True).strip()
pins=read(D/'preparation-pins.json')['sha256'];required=read(D/'required-paths.json')['paths']
check('all_1865_preparation_hashes',len(pins)==1865 and all(digest(p)==h for p,h in pins.items()))
check('exact_required_membership',len(required)==len(set(required)) and set(required)==set(pins))
stages=read(D/'stages.json');stage_summary={}
for mode,count in [('red',75),('green',81)]:
 s=stages[mode];p=Path(s['path']);src=Path(s['source']);actual={str(q.relative_to(p)) for q in p.rglob('*') if q.is_file()}
 check(mode+'_membership',actual==set(s['sha256']) and len(actual)==count and not any(q.is_symlink() for q in p.rglob('*')))
 check(mode+'_source_bytes',s['sha256']==s['baseline_sha256'] and all(digest(p/n)==digest(src/n)==h for n,h in s['sha256'].items()))
 stage_summary[mode]=count
for n in ('split-upper.jl','split-bg.jl'):
 check('candidate_'+n,(Path(stages['green']['path'])/'src'/n).read_bytes()==(C/n).read_bytes())
for n in ('split-oracles.jl','split-upper-tests.jl','split-bg-tests.jl','fixtures.jl'):
 check('test_'+n,(Path(stages['green']['path'])/'test'/n).read_bytes()==(C/n).read_bytes())
check('candidate_committed_bytes',all(git('show','HEAD:'+str(p.relative_to(R)))==p.read_text().rstrip('\n') for p in C.iterdir() if p.is_file()))
runtime=read(D/'runtime-inputs-complete.json')['inventory']
check('runtime_609_resolutions_and_hashes',len(runtime)==609 and all(str(Path(p).resolve(strict=True))==v['resolved'] and digest(p)==v['sha256'] for p,v in runtime.items()))
for n,v in read(D/'reused-helpers.json').items():check('helper_'+n,digest(D/n)==digest(v['source'])==v['sha256'])
lineages={}
for n,v in read(D/'control-lineage.json').items():
 old=Path(v['source']).read_text();new=(D/n).read_text()
 check('lineage_hashes_'+n,digest(v['source'])==v['source_sha256'] and digest(D/n)==v['candidate_sha256'])
 for a,b in [('direct-bg-block-upper','direct-bg-split-upper'),('block BG','split BG'),('Dynamic BG correctness','Split BG correctness'),('8faca92005efbb65ad7212222b17844a248d208a','73216b71debb99c7515b3d265702e0d68afe7064')]:old=old.replace(a,b)
 if n=='audit.py':
  old=old.replace('from oracle import test_results,timeout_only','from oracle import test_results,timeout_only,warning_log').replace('if pure:return',"require(not warning_log(log),'Warning/world-age outcome rejected')\n if pure:return").replace("(8 if cfg['mode']=='red' else 0)","(10 if cfg['mode']=='red' else 0)")
 if n=='oracle.py':
  old=old.replace('import math','import math,re\ndef warning_log(log):return re.search(r"(?i)\\bwarning\\b|world[ -]age",log) is not None').replace('def timeout_only(process,supervisor,raw,log,elapsed,seconds,loaded,phase):','def timeout_only(process,supervisor,raw,log,elapsed,seconds,loaded,phase):\n if warning_log(log):return False')
 check('exact_source_inverse_'+n,old==new);lineages[n]=True
# Independent integer extent geometry: ordered bins and row memberships only;
# no floating values, Julia source execution, backend calls, or external process.
class Geometry:
 def __init__(self):self.K=0;self.used=0;self.slabs=0;self.bins={i:[] for i in range(1,33)};self.caps={};self.chain=[];self.rows=set();self.calls=0
 def grow(self,n):
  if n>self.K:self.K=max(n,self.K+max(self.K//2,8));self.calls+=7
 def free(self,b):self.bins[self.caps[b]].insert(0,b)
 def reserve(self,n):
  target=1
  while target<n:target*=2
  cap=next((i for i in range(target,33) if self.bins[i]),None)
  if cap is None:
   self.grow(self.used+8);self.calls+=6 if self.slabs==0 else 3;self.slabs+=1
   for b in range(self.used+1,self.used+9):self.caps[b]=32;self.free(b)
   self.used+=8;cap=32
  b=self.bins[cap][0]
  if cap>target:
   self.grow(self.used+1);self.bins[cap].remove(b);self.caps[b]=target;self.used+=1;self.caps[self.used]=cap-target;self.free(b);self.free(self.used)
  self.bins[target].remove(b);return b
 def insert(self,r):
  if r not in self.rows:self.rows.add(r);self.calls+=1
  if not self.chain:self.chain=[[self.reserve(1),[]]]
  b,rr=self.chain[-1];n=len(rr)
  if n==32:
   other=self.reserve(32);allrows=rr+[r];self.chain[-1][1]=allrows[:16];self.chain.append([other,allrows[16:]])
  else:
   if n==self.caps[b]:
    donor=self.reserve(n+1);self.caps[b],self.caps[donor]=self.caps[donor],self.caps[b];self.free(donor)
   rr.append(r)
 def delete(self,r):
  k=next(i for i,(_,rr) in enumerate(self.chain) if r in rr);b,rr=self.chain[k];rr.remove(r)
  if not rr:self.free(b);self.chain.pop(k)
  elif k+1<len(self.chain):
   nb,nrr=self.chain[k+1]
   if len(rr)+len(nrr)<=max(self.caps[b],self.caps[nb]):
    keep,drop=(b,nb) if self.caps[b]>=self.caps[nb] else (nb,b);self.chain[k:k+2]=[[keep,rr+nrr]];self.free(drop)
g=Geometry();cycles=[]
for cycle in range(3):
 before=g.calls
 for r in range(1,41):g.insert(r)
 check('two_blocks_cycle_'+str(cycle),len(g.chain)==2)
 for r in range(1,41):g.delete(r)
 cycles.append(g.calls-before)
check('40_fill_delete_cycles_60_0_0',cycles==[60,0,0])
g32=Geometry()
for r in range(1,33):g32.insert(r)
check('monotone32_geometry',g32.calls==52 and g32.used==13 and g32.K==16 and g32.slabs==1)
# Each short insert: row1 + initial descriptor7 + slab3 + directory3 + suffix7.
reserves=[1+7+3+3+7,1+7+3+3+7,1+7+3+3]
build=23+64+3;copy=23+40+2*3;adapter=23+3+3
check('source_allocator_calibrations',reserves==[21,21,14] and (build,copy,adapter)==(90,69,29))
row_growth=0;cap=0
for degree in range(1,161):
 if degree>cap:cap=degree+min(8,max(1,cap//8));row_growth+=1
struct_counts=[6*3+3,3+16+2,6*2,6,15*2,3*3,9*2,33*2+1+15+3,sum(2+3*n for n in reserves)+1+2*build,17,4,2*160+row_growth+2,2*40*40+1+40+1,6+2+3*copy]
new_counts=[1+5,7,8*2+2,4+3+3+1,1+2+7*3,1+2+13*3+2,7*3,2*2+2+2+1,1+2*32+3,3,3*(40+1+40+1)+2]
# Inherited adapter counts retain accepted frozen assertion bodies; source inverse
# and prior Task2 review pin this derivation. New loops independently expanded.
old=read(D.parent/'DIRECT-BG-BLOCK-DRIVER-PREPARATION/assertion-derivation.json')
adapter_counts=[v for _,v in old['adapter']]+[(32+1+1+16+16+33+9)*2+32*2+4,(7+14)*2+1+3*2+2]
e=read(D/'expected-tests.json');counts=struct_counts+new_counts+adapter_counts
names=re.findall(r'@testset "([^"]+)"',(C/'split-upper-tests.jl').read_text())+re.findall(r'@testset "([^"]+)"',(C/'split-bg-tests.jl').read_text())
check('34_group_names_counts',len(counts)==34 and e['green']['groups']==[[n,c,0,0,0] for n,c in zip(names,counts)] and sum(counts)==15929)
t=tomllib.loads((D/'expected-tests.toml').read_text())
check('json_toml_match',all(t[m]['assertions']==e[m]['assertions'] and [[v[k] for k in ['name','pass','fail','error','broken']] for v in t[m]['groups']]==e[m]['groups'] for m in ('red','green')))
syms=re.findall(r'isdefined\(JSimplex,:(\w+!?)\)',(D/'red.jl').read_text());red='\n'.join(p.read_text() for p in (Path(stages['red']['path'])/'src').rglob('*.jl'));new=(C/'split-upper.jl').read_text()+(C/'split-bg.jl').read_text()
check('ten_absent_red_present_green',len(syms)==len(set(syms))==10 and all(not re.search(r'\b'+re.escape(s)+r'(?![A-Za-z0-9_])',red) and s in new for s in syms))
tri=lambda n:n+n*(n+1)//2
callbacks=sum(tri(n) for n in reserves+[build,copy])+7+tri(7)+13+tri(13)+7+sum(range(2,9))+g32.calls+sum(cycles)+6*tri(adapter)+3
operations=sum(1+n for n in reserves+[build,copy])+9+16+7+32+240+6*(1+adapter)+2
failures=sum(reserves)+build+copy+7+14+7+6*adapter+2
w=read(D/'work-ledger.json')
check('allocator_totals_independent',(callbacks,operations,failures,callbacks-failures)==(10392,706,419,9973))
check('ledger_matches_counts',(w['explicit_storage_allocation_requests'],w['allocation_probe_operations']['total'],w['expected_injected_storage_failures'],w['completed_before_injected_throw'])==(callbacks,operations,failures,callbacks-failures))
check('outer_work_totals',all([sum(side) for side in sides]==w['totals'][k] for k,sides in w['per_group_reference_candidate'].items()) and w['factorization_attempts']==[55+62,125+153-6])
s=(D/'driver.jl').read_text();main=s[s.index('function main()'):]
check('top_level_includes_and_raw_first','include(' not in main and s.index('test/split-bg-tests.jl')<s.index('function main()') and s.index('TOML.print(io,raw)')<s.index('expected=TOML.parsefile'))
check('exact_loaded_schema',set(read(D/'loaded-paths.json'))=={'SparseArrays','LinearAlgebra','TOML','Test','PrecompileTools'} and '(JSimplex,SparseArrays,LinearAlgebra,TOML,Test,PrecompileTools)' in s)
check('warning_before_timeout_accept',(D/'audit.py').read_text().index('require(not warning_log(log)')<(D/'audit.py').read_text().index('if pure:return'))
# Test only independently written pure predicates, compare source spelling first.
pattern=r'(?i)\bwarning\b|world[ -]age'
check('warning_predicate_source',('re.search(r"'+pattern+'",log) is not None') in (D/'oracle.py').read_text())
for i,token in enumerate(['Warning: x','WARNING: x','\x1b[33m┌ Warning: x','world age mismatch','world-age mismatch']):check('synthetic_warning_'+str(i),re.search(pattern,token) is not None)
check('clean_warning_predicate',re.search(pattern,'BEGIN split BG driver green300\nEND lifecycles') is None)
check('author_synthetic_results',all(read(D/n)['all_passed'] and all(read(D/n)['checks'].values()) for n in ['offline-tests.json','negative-supplement.json','warning-tests.json']))
check('no_runs',not (D/'runs').exists())
check('head_master',git('rev-parse','HEAD')=='73216b71debb99c7515b3d265702e0d68afe7064' and git('rev-parse','master')=='26e2291745999f485a74f643298ca997d65c7205')
check('tracked_unchanged',git('diff','--name-only')==git('diff','--cached','--name-only')=='')
# Fresh read-only host examination, no signals or process creation except git above.
groups=set(read(D/'host.json')['groups']);matches=[];unreadable=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  a=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip();exe=''
  try:exe=str((p/'exe').resolve(strict=True))
  except PermissionError:unreadable.append(int(p.name))
  except FileNotFoundError:pass
  if int(a[2]) in groups or int(a[3]) in groups or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):matches.append(dict(pid=int(p.name),pgid=int(a[2]),sid=int(a[3]),start_ticks=int(a[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,ProcessLookupError):pass
check('fresh_host_no_match',not matches and len(groups)==240)
result=dict(all_passed=all(checks.values()),checks=checks,preparation_pins_sha256=digest(D/'preparation-pins.json'),bindings_verified=len(pins),runtime_files=len(runtime),stages=stage_summary,counts=dict(green=15929,groups=34,red=10,callbacks=callbacks,operations=operations,failures=failures,completed=callbacks-failures,factorization_outer_entries=389,fill40_callbacks=cycles),host=dict(boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),groups=sorted(groups),matches=matches,unreadable_exe_pids=unreadable),scope='Pure offline text/hash/integer checks; no author/old code executed; no Julia or phase activity')
save('reviewer-check.json',result)
print(json.dumps({k:result[k] for k in ['all_passed','bindings_verified','runtime_files','stages','counts']}))
