from pathlib import Path
import json,hashlib,shutil
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-SPLIT-ADAPTER-PREPARATION';N=R/'diagnostics/direct-bg-split-upper/reproduce';O=R/'diagnostics/direct-bg-block-upper/reproduce'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(v,m):
 if not v:raise RuntimeError(m)
renames=[('BlockBGFactor','SplitBGFactor'),('BGBlockUpper','BGSplitUpper'),('_block_bg_','_split_bg_'),('_bbg_','_sbg_'),('_bgu_','_sbu_')]
s=(O/'block-bg.jl').read_text();t=s
for a,b in renames:t=t.replace(a,b)
with (N/'split-bg.jl').open('x') as f:f.write(t)
inv=t
for a,b in reversed(renames):inv=inv.replace(b,a)
need(inv==s,'whole inverse')
with (E/'adapter-inverse.json').open('x') as f:json.dump(dict(renames=renames,reference=str(O/'block-bg.jl'),reference_sha256=sha(O/'block-bg.jl'),candidate_sha256=sha(N/'split-bg.jl'),exact_whole_inverse=True),f,indent=2);f.write('\n')
old=json.loads((O/'adapter-source-bindings-reviewed.json').read_text());src=Path(old['path'])
need({str(p.relative_to(src)) for p in src.rglob('*') if p.is_file()}==set(old['sha256']),'old stage membership')
need(all(not (src/k).is_symlink() and sha(src/k)==h for k,h in old['sha256'].items()),'old stage hashes')
stage=R/'.superpowers/sdd/2026-10-18-direct-bg-split-free-blocks/task2-stage';stage.mkdir(exist_ok=False)
replace={'src/block-upper.jl':'src/split-upper.jl','src/block-bg.jl':'src/split-bg.jl','test/block-oracles.jl':'test/split-oracles.jl','test/block-upper-tests.jl':'test/split-upper-tests.jl','test/block-bg-tests.jl':'test/split-bg-tests.jl'}
for k in old['sha256']:
 dst=stage/replace.get(k,k);dst.parent.mkdir(exist_ok=True,parents=True)
 data=(src/k).read_bytes()
 if k in replace:data=(N/Path(replace[k]).name).read_bytes()
 elif k=='src/JSimplex.jl':
  need(data.count(b'include("block-upper.jl")')==1 and data.count(b'include("block-bg.jl")')==1,'root anchors')
  data=data.replace(b'include("block-upper.jl")',b'include("split-upper.jl")').replace(b'include("block-bg.jl")',b'include("split-bg.jl")')
 with dst.open('xb') as f:f.write(data)
r=dict(scope='UNEXECUTED ordinary Task2 source overlay; not runtime/load/cache/launch admission.',path=str(stage),source=str(src),master=old['master'],baseline=old['sha256'],replacements=replace,sha256={str(p.relative_to(stage)):sha(p) for p in sorted(stage.rglob('*')) if p.is_file()})
for p in [E/'overlay.json',N/'adapter-source-bindings.json']:
 with p.open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print('Adapter whole inverse PASS; new stage',len(r['sha256']),'files')
