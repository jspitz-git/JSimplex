from pathlib import Path
import json,hashlib,tomllib
D=Path(__file__).resolve().parent;R=D.parents[3];H=D.parent/'MA-H';F=D.parent/'MA-F-repair';E=D.parent/'MA-E';checks={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for n in ['kernels.jl','tests-instrumented.jl','fixtures.toml','reference-upper.jl','test-collector.jl','finite_oracle.py','guard-reviewed.py']:
 checks['unchanged_'+n]=(D/n).read_bytes()==(F/n).read_bytes()
for n,src,meta in [('route-tests-instrumented.jl',H/'route-tests.jl','route-instrumentation.json'),('driver.jl',F/'driver.jl','driver-instrumentation.json')]:
 s=(D/n).read_text();m=json.loads((D/meta).read_text())
 for a,b in reversed(m['replacements']):
  if s.count(b)!=1:raise ValueError('nonunique inverse')
  s=s.replace(b,a)
 checks['inverse_'+n]=s==src.read_text()
checks['reference_forward']=(D/'reference-forward.jl').read_bytes()==(H/'reference-forward.jl').read_bytes()
checks['candidate_exact']=sha(D/'overlays/candidate/src/markowitz_factorization.jl')=='dca3d1c7cabfc6ecf8e09832cadd097bcfe4a6e5982e42d914b72333bf853dea'
checks['reference_master']=(D/'overlays/reference/src/markowitz_factorization.jl').read_bytes()==(R/'src/markowitz_factorization.jl').read_bytes()
checks['counts9_647']=list(json.loads((D/'test-counts.json').read_text()).values())==[62,31,96,42,78,72,126,54,86]
checks['all_overlay_inverse']=True
for side in ['reference','candidate']:
 for p in (D/'overlays'/side).rglob('*'):
  if not p.is_file():continue
  rel=p.relative_to(D/'overlays'/side);old=E/'overlays'/side/rel
  wanted=H/'candidate-markowitz.jl' if side=='candidate' and str(rel)=='src/markowitz_factorization.jl' else old
  checks['all_overlay_inverse'] &= p.read_bytes()==wanted.read_bytes()
configs=list((D/'configs').glob('*.toml'));checks['22configs']=len(configs)==22
for p in configs:
 c=tomllib.loads(p.read_text());checks['config_'+p.name]=c['root']==str(D/'overlays'/c['side']) and c['source_sha256']==sha(D/'overlays'/c['side']/'src/markowitz_factorization.jl') and c['output']==str(R/'.superpowers/simplex-core-architecture/MA-I/attempt-1'/p.stem)
checks['no_launch_yet']=not (D/'execution-seal.json').exists() and not (D/'attempt-reserved.json').exists()
for n in ['synthetic.json','synthetic-admission.json','context-supplement.json']:checks[n]=json.loads((D/n).read_text())['all_passed'] is True
checks['additional_original_preserved']=json.loads((D/'additional-tests.json').read_text())['all_passed'] is False
pins={str(p):sha(p) for p in sorted(D.rglob('*')) if p.is_file()}
with (D/'verification.json').open('x') as f:json.dump(dict(all_passed=all(checks.values()),checks=checks,sha256=pins),f,indent=2);f.write('\n')
print(sum(checks.values()),'/',len(checks),len(pins),'bindings')
if not all(checks.values()):raise SystemExit(1)
