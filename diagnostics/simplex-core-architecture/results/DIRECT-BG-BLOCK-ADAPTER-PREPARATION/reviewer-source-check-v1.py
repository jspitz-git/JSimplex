from pathlib import Path
import hashlib,json
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
E=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCK-ADAPTER-PREPARATION'
C=R/'diagnostics/direct-bg-block-upper/reproduce'
sha=lambda b:hashlib.sha256(b).hexdigest()
m=json.loads((E/'adapter-inverse.json').read_text())
ref=Path(m['reference']).read_bytes();candidate=(C/'block-bg.jl').read_bytes()
assert sha(ref)==m['reference_sha256'] and sha(candidate)==m['candidate_sha256']
s=ref.decode()
for a,b in m['renames']:s=s.replace(a,b)
for e in m['edits']:
    assert s.count(e['before'])==e.get('count',1)
    s=s.replace(e['before'],e['after'])
assert s.encode()==candidate
for e in reversed(m['edits']):
    assert s.count(e['after'])==e.get('count',1)
    s=s.replace(e['after'],e['before'])
for a,b in reversed(m['renames']):s=s.replace(b,a)
assert s.encode()==ref
assert (C/'fixtures.jl').read_bytes()==(R/'diagnostics/direct-bg-dynamic-upper/reproduce/fixtures.jl').read_bytes()
paths=[C/n for n in ('block-bg.jl','block-bg-tests.jl','fixtures.jl','block-upper.jl','block-oracles.jl')]
paths += [R/'src'/n for n in ('triangular_factorization.jl','triangular_indices.jl','triangular_rows.jl','triangular_spikes.jl','bartels_golub_rows.jl')]
paths += [R/'diagnostics/direct-lu-policy-adapters/reproduce/direct-factor.jl',Path(m['reference']),E/'adapter-inverse.json']
out={'scope':'Independent offline byte checks only; no Julia parse/import/compile/numerical work','inverse_forward':True,'inverse_reverse':True,'fixture_byte_identity':True,'sha256':{str(p.relative_to(R)):sha(p.read_bytes()) for p in paths}}
with (E/'reviewer-source-check-v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps(out,indent=2))
