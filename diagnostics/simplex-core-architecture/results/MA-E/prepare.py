from pathlib import Path
import json,hashlib,shutil,tomllib
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');D=R/'diagnostics/simplex-core-architecture/results/MA-E';O=D.parent/'MA-D'
def put(n,s):
 p=D/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:f.write(s)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
# Ordinary source/test overlays; no .git, caches, resolution or installed env edits.
manifest={}
for side in ('reference','candidate'):
 B=D/'overlays'/side;B.mkdir(parents=True)
 for folder in ('src','test'):
  shutil.copytree(R/folder,B/folder)
 for n in ('Project.toml','Manifest.toml','LocalPreferences.toml'):shutil.copyfile(R/n,B/n)
 # Direct diagnostic dependency on reference too, without importing it in production.
 (B/'Project.toml').write_bytes((O/'candidate-Project.toml').read_bytes())
 if side=='candidate':
  for a,b in [('candidate-markowitz.jl','src/markowitz_factorization.jl'),('candidate-JSimplex.jl','src/JSimplex.jl'),('candidate-runtests.jl','test/runtests.jl')]: (B/b).write_bytes((O/a).read_bytes())
 (B/'test/markowitz_ma_upper_tests.jl').write_bytes((O/'candidate-tests-reviewed.jl').read_bytes())
 manifest[side]={str(p.relative_to(B)):sha(p) for p in sorted(B.rglob('*')) if p.is_file()}
put('overlay-hashes.json',json.dumps(manifest,indent=2)+'\n')
# Immutable exact fixtures in stdlib TOML format. All fractions also checked offline.
f=json.loads((O/'fixtures.json').read_text());txt='scalar_cases = '+json.dumps(f['scalar_cases'])+'\n'
for x in f['fixtures']:
 txt+='\n[[fixtures]]\n'
 for k in ('name','n','family','storage','matrix','rhs'):txt+=k+' = '+json.dumps(x[k])+'\n'
put('fixtures.toml',txt)
# Original helper diagnostic-local; complete exact inverse bound by original text.
s=(O/'helpers.jl').read_text();a=s.index('function _markowitz_upper_solve!');b=s.index('\n_markowitz_ma_rounding_matches')
put('reference-upper.jl',s[a:b].replace('_markowitz_upper_solve!','reference_upper!',1))
# Copy guarded Test collector definitions only, no old driver execution.
s=(D.parent/'S4-AD/driver.jl').read_text();s=s[s.index('mutable struct RecordedTests'):s.index('const before_precision')]
put('test-collector.jl',s)
put('test-counts.json',json.dumps({'MA upper dispatch and fallback':62,'MA upper scalar ownership':31,'MA upper sequential arithmetic':96,'MA upper rounding fallback':42,'MA upper exceptions':78,'MA upper lifecycle':72},indent=2)+'\n')
print('ordinary overlays', {s:len(v) for s,v in manifest.items()},'fixtures',len(f['fixtures']))
