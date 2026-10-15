"""One-time offline inventory, inverse, source and test contract checks."""
from common import *
import ast
inv=rd(Q/'inverse.json');prep=rd(Q/'prepare.json')
checks={'prepare':prep['all_passed'] is True and bindings(prep),'entry':rd(Q/'entry.json')['all_passed'] is True and bindings(rd(Q/'entry.json'))}
for n in inv['original']:require(sha(n)==inv['original'][n],'Original source changed')
for n in inv['candidate']:require(sha(n)==inv['candidate'][n],'Candidate changed')
for n in inv['original']:
 rel=str(Path(n).relative_to(R));s=(Q/'candidate'/rel).read_text()
 for e in reversed([e for e in inv['edits'] if e['file']==rel]):
  require(s.count(e['after'])==1,'Ambiguous inverse');s=s.replace(e['after'],e['before'])
 require(s==Path(n).read_text(),'Inverse failed')
checks['whole_inverse_7_28']=len(inv['original'])==7 and len(inv['edits'])==28
base=rd(Q.parent/'DIRECT-LU-PREPARATION/baseline.json');checks['baseline514']=len(base['sha256'])==514 and bindings(base)
source_files=sorted((R/'src').rglob('*.jl'));env=[R/n for n in ['Project.toml','Manifest.toml','LocalPreferences.toml']]
require(len(source_files)==70,'Unexpected source universe')
entries=[]
for f in source_files+env:entries.append(dict(destination=str(f.relative_to(R)),source=str(f),sha256=sha(f)))
reference=list(entries);candidate=[]
for e in entries:
 f=Q/'candidate'/e['destination'];candidate.append(dict(destination=e['destination'],source=str(f),sha256=sha(f)) if f.exists() else e)
for n in ['native_pivot_policy_tests.jl','native_pivot_policy_entry.jl']:
 f=Q/'candidate/test'/n;candidate.append(dict(destination='test/'+n,source=str(f),sha256=sha(f)))
save(Q/'overlay-manifest.json',dict(reference=reference,candidate=candidate,scope='73 original files; candidate swaps only7 sources and adds2 test files; no loader/launch admission'))
checks['overlay73_75']=len(reference)==73 and len(candidate)==75 and sum(a!=b for a,b in zip(reference,candidate))==7
checks['auxiliary_hh_moi_direct_unchanged']=all(not (Q/'candidate'/n).exists() for n in ['src/dual_simplex.jl','src/huangfu_hall_factorization.jl','src/moi/attributes.jl','diagnostics/direct-lu-markowitz/reproduce/direct-factor.jl'])
opts=(Q/'candidate/src/options.jl').read_text();fac=(Q/'candidate/src/factorization.jl').read_text();tests=(Q/'candidate/test/native_pivot_policy_tests.jl').read_text()
checks['four_test_groups']=all('@testset "'+s+'"' in tests for s in ['options_and_copy_intent','backend_owned_policy','private_spare_copy_and_failure','precision_and_factory_dispatch'])
checks['fresh_and_spare_failures']='for with_spare in (false,true)' in tests and '@test_throws SingularException J.refactorize!(f,singular)' in tests
checks['controls_private_constant']='const pivot_policy::_NativePivotPolicy' in fac and 'control !== b.factorization.control' in tests and '@test_throws ErrorException setfield!' in tests
checks['default_literal_and_two_stores']='policy === _NATIVE_PIVOT_DEFAULT && return lu(B)' in fac and fac.count('control[SparseArrays.LibSuiteSparse.')==2
checks['legacy16_and_default_validation']='partial_pricing, :default)' in opts and 'native_pivot_policy::Symbol=:default) where {T,M,R}' in opts
checks['copy_policy']='nothing, true, backend.pivot_policy)' in fac
checks['no_hot_policy_reads']=all('policy' not in e['before'] for e in inv['edits'] if e['file']=='src/factorization.jl' and e['before'].startswith('function forward_solve'))
checks['no_production_diff']=not git('diff','--name-only','--','src','test','.github','Project.toml','diagnostics/direct-lu-markowitz/reproduce')
# All positional construction sites inspected, including four internal copies.
construction={str(f.relative_to(R)):[(i,line) for i,line in enumerate(f.read_text().splitlines(),1) if 'SolverOptions{' in line or '_validated_options(' in line] for f in source_files if 'SolverOptions{' in f.read_text() or '_validated_options(' in f.read_text()}
save(Q/'option-call-sites.json',dict(source_sites=construction,changed_copy_sites=['src/options.jl','src/simplex_phase_one.jl','src/simplex_precision.jl','src/solver.jl','src/lp_refinement_driver.jl'],scope='All lexical parametric option sites enumerated; author/reviewer semantic inspection still required'))
for f in Q.glob('*.py'):ast.parse(f.read_text(),filename=str(f))
checks['python_syntax']=True
pins=set(source_files+env+[R/'AGENTS.md',R/'docs/superpowers/specs/2026-10-15-native-pivot-policy-design.md',R/'docs/superpowers/plans/2026-10-15-native-pivot-policy.md',Q.parent/'DIRECT-LU-PREPARATION/baseline.json',R/'diagnostics/direct-lu-markowitz/reproduce/direct-factor.jl'])
pins.update(Q.rglob('*.jl'));pins.update(Q.glob('*.py'));pins.update(Q.glob('*.json'))
save(Q/'source-check.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(f):sha(f) for f in sorted(pins)},scope='Text/inverse/source hashes only; Julia syntax, dispatch and numerics UNEXECUTED'))
require(all(checks.values()),'Source check failed; preserve');print(dict(all_passed=True,checks=len(checks),pins=len(pins)))
