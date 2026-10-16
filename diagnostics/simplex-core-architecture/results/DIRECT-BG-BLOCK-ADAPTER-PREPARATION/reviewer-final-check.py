from pathlib import Path
import hashlib,json
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
E=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCK-ADAPTER-PREPARATION';C=R/'diagnostics/direct-bg-block-upper/reproduce'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((E/'adapter-inverse-reviewed.json').read_text());ref=Path(m['reference']);s=ref.read_text();candidate=(C/'block-bg.jl').read_text()
assert sha(ref)==m['reference_sha256'] and sha(C/'block-bg.jl')==m['candidate_sha256']
for a,b in m['renames']:s=s.replace(a,b)
for e in m['edits']:
 assert s.count(e['before'])==e.get('count',1)
 s=s.replace(e['before'],e['after'])
assert s==candidate
for e in reversed(m['edits']):
 assert s.count(e['after'])==e.get('count',1)
 s=s.replace(e['after'],e['before'])
for a,b in reversed(m['renames']):s=s.replace(b,a)
assert s==ref.read_text()
o=json.loads((E/'overlay-reviewed.json').read_text());stage=Path(o['path']);base=Path(o['source'])
assert len(o['baseline'])==78 and len(o['sha256'])==81
assert {str(p.relative_to(stage)) for p in stage.rglob('*') if p.is_file()}==set(o['sha256'])
assert not any(p.is_symlink() for p in stage.rglob('*'))
assert all(sha(stage/n)==h for n,h in o['sha256'].items())
assert all(sha(base/n)==h for n,h in o['baseline'].items())
for n in o['baseline']:
 if n!='src/JSimplex.jl':assert (base/n).read_bytes()==(stage/n).read_bytes()
root=(stage/'src/JSimplex.jl').read_bytes();addition=o['root_addition'].encode()
assert root.count(addition)==1 and root.replace(addition,b'')==(base/'src/JSimplex.jl').read_bytes()
assert set(o['sha256'])-set(o['baseline'])=={'src/block-bg.jl','test/block-bg-tests.jl','test/fixtures.jl'}
for a,b in [('src/block-bg.jl','block-bg.jl'),('test/block-bg-tests.jl','block-bg-tests.jl'),('test/fixtures.jl','fixtures.jl')]:assert (stage/a).read_bytes()==(C/b).read_bytes()
assert (E/'overlay-reviewed.json').read_bytes()==(C/'adapter-source-bindings-reviewed.json').read_bytes()
assert (C/'fixtures.jl').read_bytes()==(R/'diagnostics/direct-bg-dynamic-upper/reproduce/fixtures.jl').read_bytes()
assert sha(E/'block-bg-tests.jl.before-coverage-amendment')=='5e2def32b7061a32819a05f23da00e7c07ba306f890e0adc4a06d5170bedf869'
assert sha(E/'block-bg-tests.jl.before-alias-review')=='9571e4500c078d4df395b5bcf7ced4e57eb58ec56dcaa947d6b110c4b34b8348'
assert sha(E/'block-bg.jl.before-alias-review')=='e8770ec8ef7e965a9d9c171703bffde37d388ec628354b8e5c408d07478f1190'
assert 'destination===f.work || destination===f.upper.scratch_value' in candidate
t=(C/'block-bg-tests.jl').read_text();assert 'op(empty.work,empty,Float64[])' in t and 'Base.wrap(Array,Core.memoryref(scratch.ref,2),3)' in t
assert 'unsafe_wrap' not in t
paths=[C/n for n in ('block-bg.jl','block-bg-tests.jl','fixtures.jl','block-upper.jl','block-oracles.jl','adapter-source-bindings-reviewed.json')]
paths += [E/n for n in ('adapter-inverse-reviewed.json','overlay-reviewed.json','MEMORY-WORK.md','SOURCE-MAP.md','source-check-reviewed.json','review-fix.json','independent-review-v1.md','independent-review-v2-findings.md')]
paths += [Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/base')/n for n in ('abstractarray.jl','array.jl','boot.jl')]
out={'scope':'Final independent offline byte/source checks; no Julia or numerical execution','all_passed':True,'inverse_both_directions':True,'stage_81_exact':True,'baseline_77_unchanged_and_root_inverse':True,'original_versions_preserved':True,'sha256':{str(p):sha(p) for p in paths},'stage_sha256':o['sha256']}
with (E/'reviewer-final-check.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print('PASS independent exact inverse, final81 stage membership/hashes,77 unchanged/rootinverse, frozen fixtures, preserved originals, final alias source assertions')
