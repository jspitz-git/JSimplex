"""New offline source/inverse checks; no Julia parser or compilation."""
from control import *
import re,ast,tomllib
checks={}
def check(n,v):require(v,n);checks[n]=True
c=rd(D/'source-inverse.json');names=rd(D/'probe-renames.json')
def rename(s):
 for a in sorted(names,key=len,reverse=True):s=re.sub(r'(?<![\w])'+re.escape(a)+r'(?![\w!])',names[a],s)
 return s
for n,meta in c['probe'].items():
 source=Path(meta['original']);text=(D/n).read_text()
 if 'prefix' in meta:
  require(text.startswith(meta['prefix']),'Prefix');text=text.removeprefix(meta['prefix'])
  for anchor,extra in meta['insertions']:require(text.count(extra)==1,'Counter insertion');text=text.replace(extra,'')
 check('inverse_'+n,text==rename(source.read_text()))
check('original_files_unchanged',all(sha(p)==h for p,h in c['originals'].items()))
stage=Path(rd(D/'stages.json')['cost']['path']);old=Path(c['stage_source']);changed=[]
for p in old.rglob('*'):
 if p.is_file():
  q=stage/p.relative_to(old)
  if q.read_bytes()!=p.read_bytes():changed.append(str(p.relative_to(old)))
check('stage_only_root_changed',changed==['src/JSimplex.jl'])
check('stage_root_inverse',(stage/'src/JSimplex.jl').read_text().replace(c['stage_addition'],'')==(old/'src/JSimplex.jl').read_text())
check('stage_two_additions',{str(p.relative_to(stage)) for p in stage.rglob('*') if p.is_file()}-{str(p.relative_to(old)) for p in old.rglob('*') if p.is_file()}=={'src/probe-slots.jl','src/probe-bg.jl'})
check('stage_probes_equal',all((stage/'src'/n).read_bytes()==(D/n).read_bytes() for n in ['probe-slots.jl','probe-bg.jl']))
check('oracles_inverse',(D/'probe-oracles.jl').read_text()==Path(c['oracles_original']).read_text().replace('using Test\n','').replace('::J.BGSlotUpper','::Union{J.BGSlotUpper,J.ProbeBGSlotUpper}'))
s=(D/'cost.jl').read_text();body=s[s.index('function lifecycle'):s.index('# No extra factor solves')]
check('timed_original_factories','J._dynamic_bg_factor(B,backend,policy(backend))' in s and 'J._direct_lu_factor(F,B,backend,policy(backend);normalize=true)' in s)
check('no_probe_in_timed_body',not any(x in body for x in ['Probe','_probe','summarysize','_check_bg','_bg_probe_counts']))
check('top_level_includes',s.index('include("probe.jl")')<s.index('function main()') and s.count('include(')==2)
check('eightcell_schedule','(("BG",J.BartelsGolubFactorization),)' in s and 'for pair in 1:10' in s and 'startswith(PHASE,"cost2")' in s)
check('input_exact_copy',all(sha(D/n)==sha(D.parent/'DIRECT-LU-POLICY-ADAPTER-COST-PREPARATION'/n) for n in ['inputs.json','inputs.toml']))
check('input_formats',rd(D/'inputs.json')==tomllib.loads((D/'inputs.toml').read_text()))
for p in D.glob('*.py'):ast.parse(p.read_text())
check('python_syntax_only',True)
check('no_run_seal_reservation',not (D/'runs').exists())
save(D/'source-check.json',dict(all_passed=True,checks=checks,scope='Text/source inverse only; Julia remains unexecuted',sha256={str(p):sha(p) for p in sorted(D.iterdir()) if p.is_file()}))
print('Offline source',len(checks),'PASS')
