"""One-shot offline preparation. No Julia or old executable invocation."""
from pathlib import Path
import json,hashlib,shutil,re
E=Path(__file__).resolve().parent;R=E.parents[3];D=E.parent/'DIRECT-BG-DYNAMIC-DRIVER-PREPARATION';O=E.parent/'DIRECT-LU-POLICY-ADAPTER-COST-PREPARATION';C=R/'diagnostics/direct-bg-dynamic-upper/reproduce'
def put(n,t):
 with (E/n).open('x') as f:f.write(t)
def js(n,x):put(n,json.dumps(x,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
orig={};trans={}
for n in ['guard.py','supervisor.py','baseline.json','environment.json','loaded-paths.json','runtime-inputs-complete.json']:
 p=D/n;shutil.copyfile(p,E/n);orig[str(p)]=sha(p)
for n in ['inputs.json','inputs.toml','analysis.py','evidence.py','control.py','audit.py','launch.py','seal.py','cost.jl']:
 p=O/n;shutil.copyfile(p,E/n);orig[str(p)]=sha(p)
# Separate types/helpers ensure instrumentation never changes timed dispatch.
renames={'BGSlotUpper':'ProbeBGSlotUpper','DynamicBGFactor':'ProbeDynamicBGFactor'}
for n in ['slot-upper-reviewed.jl','dynamic-bg-reviewed.jl']:
 source=(C/n).read_text()
 for symbol in set(re.findall(r'\b_(?:bg_|dbg_|dynamic_bg_)[A-Za-z_0-9]*!?',source)):
  renames[symbol]='_probe'+symbol
js('probe-renames.json',renames)
def renamed(s):
 for a in sorted(renames,key=len,reverse=True):s=re.sub(r'(?<![\w])'+re.escape(a)+r'(?![\w!])',renames[a],s)
 return s
for old,new in [('slot-upper-reviewed.jl','probe-slots.jl'),('dynamic-bg-reviewed.jl','probe-bg.jl')]:
 text=renamed((C/old).read_text());base=text
 if new=='probe-slots.jl':
  inserts=[('    C = _probe_bg_capacity(U.capacity,required)\n','    _bg_probe_counts[1]+=1 # reserve attempts\n'),('    C == U.capacity && return nothing\n','    _bg_probe_counts[2]+=1 # growth attempts\n    _bg_probe_counts[3]+=7*U.capacity # copied scalar entries\n    _bg_probe_counts[4]=max(_bg_probe_counts[4],56*(U.capacity+C)) # old+new arena payload\n'),('    _probe_bg_ids(U,rid,cid)\n    _probe_bg_row_gap','    _bg_probe_counts[5]+=1 # link attempts\n'),('function _probe_bg_unlink!(U::ProbeBGSlotUpper,s::Int)::Nothing\n','    _bg_probe_counts[6]+=1 # unlink attempts\n')]
  # The link insertion is before its anchor; other insertions follow their anchor.
  for i,(anchor,extra) in enumerate(inserts):
   if text.count(anchor)!=1:raise RuntimeError(anchor)
   text=text.replace(anchor,extra+anchor if i==2 else anchor+extra)
  prefix='const _bg_probe_counts=zeros(Int,6) # ONLY separate untimed probe dispatch\n'
  text=prefix+text
  inverse=text.removeprefix(prefix)
  for anchor,extra in inserts:inverse=inverse.replace(extra,'')
  if inverse!=base:raise RuntimeError('Instrumentation inverse')
  trans[new]=dict(original=str(C/old),renamed_inverse=True,insertions=inserts,prefix=prefix)
 else:trans[new]=dict(original=str(C/old),renamed_inverse=True)
 put(new,text)
# Checker in Main loaded at top-level before main, no Test suite execution.
text=(C/'slot-oracles.jl').read_text().replace('using Test\n','').replace('::J.BGSlotUpper','::Union{J.BGSlotUpper,J.ProbeBGSlotUpper}')
put('probe-oracles.jl',text)
stage=R/'.superpowers/sdd/2026-10-16-direct-bg-dynamic-upper/cost-stage'
source=Path(json.loads((D/'stages.json').read_text())['green']['path']);shutil.copytree(source,stage)
for n in ['probe-slots.jl','probe-bg.jl']:shutil.copyfile(E/n,stage/'src'/n)
p=stage/'src/JSimplex.jl';before=p.read_text();suffix='include("probe-slots.jl")\ninclude("probe-bg.jl")\n\n';pos=before.rfind('end\n');p.write_text(before[:pos]+suffix+before[pos:])
if p.read_text().replace(suffix,'')!=before:raise RuntimeError('Stage inverse')
js('stages.json',{'cost':{'path':str(stage),'sha256':{str(p.relative_to(stage)):sha(p) for p in sorted(stage.rglob('*')) if p.is_file()}}})
js('source-inverse.json',dict(originals=orig,probe=trans,stage_source=str(source),stage_addition=suffix,oracles_original=str(C/'slot-oracles.jl'),scope='Original candidate and all existing stage bytes unchanged except new stage root includes and two separate probe sources'))
print('Prepared copies, separate probe types and83-file stage; no Julia')
