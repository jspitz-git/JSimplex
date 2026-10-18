from pathlib import Path
import json,hashlib,re,subprocess
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-SPLIT-ADAPTER-PREPARATION';N=R/'diagnostics/direct-bg-split-upper/reproduce';O=R/'diagnostics/direct-bg-block-upper/reproduce'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(v,m):
 if not v:raise RuntimeError(m)
d=json.loads((E/'adapter-inverse.json').read_text());s=(N/'split-bg.jl').read_text();inv=s
for a,b in reversed(d['renames']):inv=inv.replace(b,a)
parent=json.loads((E.parent/'DIRECT-BG-BLOCK-ADAPTER-PREPARATION/adapter-inverse-reviewed.json').read_text());pi=(O/'block-bg.jl').read_text()
for edit in reversed(parent['edits']):
 need(pi.count(edit['after'])==edit.get('count',1),'parent edit selector');pi=pi.replace(edit['after'],edit['before'])
for a,b in reversed(parent['renames']):pi=pi.replace(b,a)
f=json.loads((E/'tests-first.json').read_text());t=(N/'split-bg-tests.jl').read_text();ti=t
need(ti.count(f['extra'])==1 and ti.count(f['call'])==1,'test addition uniqueness');ti=ti.replace(f['extra'],'').replace(f['call'],'')
for a,b in reversed(f['renames']):ti=ti.replace(b,a)
o=json.loads((E/'overlay.json').read_text());stage=Path(o['path']);old=Path(o['source']);repl=o['replacements']
root=(stage/'src/JSimplex.jl').read_bytes().replace(b'include("split-upper.jl")',b'include("block-upper.jl")').replace(b'include("split-bg.jl")',b'include("block-bg.jl")')
checks=dict(adapter_whole_inverse=inv.encode()==(O/'block-bg.jl').read_bytes(),adapter_pin=sha(N/'split-bg.jl')==d['candidate_sha256'],parent_whole_inverse=pi.encode()==Path(parent['reference']).read_bytes(),parent_pins=sha(O/'block-bg.jl')==parent['candidate_sha256'] and sha(Path(parent['reference']))==parent['reference_sha256'],test_whole_inverse=ti.encode()==(O/'block-bg-tests.jl').read_bytes(),test_first=f['adapter_absent'] and all(sha(Path(p))==h for p,h in f['sha256'].items()),fixtures_exact=(N/'fixtures.jl').read_bytes()==(O/'fixtures.jl').read_bytes(),stage81=len(o['sha256'])==81,stage_membership={str(p.relative_to(stage)) for p in stage.rglob('*') if p.is_file()}==set(o['sha256']),stage_all_hashes=all(sha(stage/k)==h for k,h in o['sha256'].items()),old_stage_all_hashes=all(sha(old/k)==h for k,h in o['baseline'].items()),new_files_exact=all((stage/v).read_bytes()==(N/Path(v).name).read_bytes() for v in repl.values()),unchanged75=all(sha(stage/k)==h for k,h in o['baseline'].items() if k not in repl and k!='src/JSimplex.jl'),root_inverse=root==(old/'src/JSimplex.jl').read_bytes(),no_old_candidate_in_stage=not any('block-bg' in k or 'block-upper' in k for k in o['sha256']),private_type='mutable struct SplitBGFactor{F}\n' in s,seven_both_backends='DirectLUFixtures.export_fixtures(), (backend,policy) in ARMS' in t,new_two_testsets=t.count('@testset')==(O/'block-bg-tests.jl').read_text().count('@testset')+2,complete_ledger=all(x in (E/'MEMORY-WORK.md').read_text() for x in ['16C+4R+28K+32n+656','8n+24D','28*(Kold+Knew)','Theta(f*d+f^2)','external destination','128 paired','149 paired']),actual_tracked_unchanged=subprocess.run(['git','diff','--quiet','HEAD'],cwd=R).returncode==0)
# Actual checkout files and all original source/runtime/evidence text used in review.
paths=[*sorted(N.glob('*')), *sorted(E.glob('*'))]
paths += [R/x for x in ['AGENTS.md','docs/superpowers/specs/2026-10-18-direct-bg-split-free-blocks.md','docs/superpowers/plans/2026-10-18-direct-bg-split-free-blocks.md','src/triangular_factorization.jl','src/triangular_indices.jl','src/triangular_rows.jl','src/triangular_spikes.jl','src/bartels_golub_rows.jl','diagnostics/direct-lu-policy-adapters/reproduce/direct-factor.jl','diagnostics/direct-lu-policy-adapters/reproduce/factor-export.jl']]
paths += [O/x for x in ['block-bg.jl','block-bg-tests.jl','fixtures.jl','adapter-source-bindings-reviewed.json']]
paths += [E.parent/'DIRECT-BG-BLOCK-ADAPTER-PREPARATION'/x for x in ['adapter-inverse-reviewed.json','SOURCE-MAP.md','MEMORY-WORK.md']]
paths += [Path(parent['reference'])]
paths += [E.parent/'DIRECT-BG-SPLIT-U-PREPARATION'/x for x in ['MEMORY-WORK.md','REPORT.md','source-check.json','geometry-model.json','review.md','review.json','closure.json','publication.json']]
# Read-time runtime sources only. No Julia binary invocation.
runtime=json.loads((E.parent/'DIRECT-BG-BLOCK-ADAPTER-PREPARATION/review-fix.json').read_text())['readtime_runtime_sources']
paths += [Path(k) for k in runtime]
rd={str(Path(k)):sha(Path(k)) for k in runtime}
checks['runtime_text_unchanged']=all(rd[k]==v for k,v in runtime.items())
checks['current_original_stage_sources']=all((R/k).read_bytes()==(stage/k).read_bytes() for k in o['sha256'] if k.startswith('src/') and k!='src/JSimplex.jl' and (R/k).exists())
record=dict(scope='Offline text/hash checks only, all Julia UNEXECUTED; no old scripts executed.',all_passed=all(checks.values()),checks=checks,testsets_unexecuted=re.findall(r'@testset "([^"]+)"',t),static_assertion_sites=len(re.findall(r'@test(?:_throws)?\b',t)),runtime_text=rd,sha256={str(p.relative_to(R)) if p.is_relative_to(R) else str(p):sha(p) for p in dict.fromkeys(paths) if p.is_file()})
with (E/'source-check.json').open('x') as out:json.dump(record,out,indent=2);out.write('\n')
print(json.dumps(dict(all_passed=record['all_passed'],checks=len(checks),bindings=len(record['sha256']),testsets=len(record['testsets_unexecuted']),static_assertion_sites=record['static_assertion_sites'],failed=[k for k,v in checks.items() if not v]),indent=2))
need(record['all_passed'],'source check')
