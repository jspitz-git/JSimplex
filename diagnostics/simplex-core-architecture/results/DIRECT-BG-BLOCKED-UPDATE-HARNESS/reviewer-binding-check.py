"""Fresh independent final baseline/binding review; read-only git and source checks, no Julia."""
from pathlib import Path
import hashlib,json,subprocess
H=Path(__file__).resolve().parent;R=H.parents[3];W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl')
def rd(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()
def git(root,*a):return subprocess.check_output(['git',*a],cwd=root,text=True).strip()
checks={}
def ck(k,v):
 checks[k]=bool(v)
 if not v:raise RuntimeError(k)
def resolve(n):return Path(n) if Path(n).is_absolute() else R/n
baseline=rd(H/'baseline.json')
for label,root in [('diagnostic',R),('production',W)]:
 b=baseline[label]
 ck('tracked_membership_'+label,set(git(root,'ls-files','src','test','.github','Project.toml').splitlines())==set(b))
 ck('tracked_hashes_'+label,all(sha(root/n)==v for n,v in b.items()))
ck('diagnostic_HEAD',git(R,'rev-parse','HEAD')=='1a824ea2d6478ba5ecbd3afc8ffbe83207bf2fd8')
ck('local_master',git(R,'rev-parse','master')=='26e2291745999f485a74f643298ca997d65c7205')
ck('production_HEAD',git(W,'rev-parse','HEAD')=='26e2291745999f485a74f643298ca997d65c7205')
stage=Path(rd(H/'stages.json')['red']['path']);include='include("factor-export.jl")\ninclude("direct-factor.jl")\n\n'
s=(stage/'src/JSimplex.jl').read_text()
ck('stage_root_include_inverse',s.count(include)==1 and s.replace(include,'')==(R/'src/JSimplex.jl').read_text())
for p in (stage/'src').rglob('*'):
 if p.is_file() and p.name not in ['JSimplex.jl','factor-export.jl','direct-factor.jl']:
  ck('stage_root_'+str(p.relative_to(stage)),sha(p)==sha(R/p.relative_to(stage)))
# Old review hashes resolve only to explicitly preserved original bytes.
fix=rd(H/'review-fix-bindings.json')['maps']
for record,mapping in fix.items():
 old=rd(H/record)
 for n,value in old['sha256'].items():
  target=Path(mapping.get(n,n));target=target if target.is_absolute() else R/target
  ck('preserved_'+record+'_'+str(len(checks)),sha(target)==value)
manifest=H/'preparation-pins-reviewed.json';pins=rd(manifest)['sha256']
ck('exact_156_membership',len(pins)==156 and set(pins)==set(rd(H/'required-paths-reviewed.json')['paths']))
ck('current_156_hashes',all(sha(resolve(n))==v for n,v in pins.items()))
ck('no_runtime_artifacts',not (H/'runs').exists() and not (H/'outers').exists())
with (H/'reviewer-binding-check.json').open('x') as f:json.dump(dict(all_passed=True,checks=checks,pins_sha256=sha(manifest),scope=__doc__),f,indent=2);f.write('\n')
print('Independent final baseline/binding checks PASS',len(checks))
