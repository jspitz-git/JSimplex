"""One-shot independent offline source/fixture checks; no Julia parser or old scripts."""
from pathlib import Path
from fractions import Fraction as F
from itertools import product
from collections import Counter
import json,hashlib,subprocess
D=Path(__file__).resolve().parent;R=D.parents[3]
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(ok,msg):
 if not ok:raise ValueError(msg)
checks={};inv=read(D/'inverse.json');source=(R/'src/presolve_aggregation.jl').read_text();original=source[source.index('function _equality_implies_column_bounds('):source.index('\nfunction aggregate_sparse_equalities(')]
checks['source_binding']=sha(R/'src/presolve_aggregation.jl')==inv['source_sha256']
checks['reference_inverse']=(D/'reference.jl').read_text().replace('function reference_bounds(','function _equality_implies_column_bounds(',1)==original
parts=inv['parts'];candidate=(D/'candidate.jl').read_text()
checks['candidate_assembly']=parts['header']+parts['private']+'\n'+parts['generic']+'\n'+parts['dispatch']+parts['special']==candidate
back=parts['special']
for e in reversed(inv['special_edits']):
 require(back.count(e['new'])==e['count'],'special inverse multiplicity');back=back.replace(e['new'],e['old'])
checks['special_whole_inverse']=back==original
checks['generic_unchanged']=parts['generic'].replace('function candidate_bounds(','function _equality_implies_column_bounds(',1)==original
checks['final_block_unchanged']=parts['special'].split('    lower_activity = ',1)[1]==original.split('    lower_activity = ',1)[1]
back=(D/'candidate-trace.jl').read_text()
for e in reversed(inv['trace_edits']):
 require(back.count(e['new'])==e['count'],'trace inverse multiplicity');back=back.replace(e['new'],e['old'])
checks['trace_inverse']=back==candidate
jprivate=(D.parent/'MA-J/candidate.jl').read_text();jprivate=jprivate[jprivate.index('function private_add('):jprivate.index('\nfunction candidate_bounds(')].replace('private_add','_mal_private_add')
checks['private_helper_exact']=jprivate==parts['private']
checks['scope_dispatch']='row_terms::Vector{Tuple{Int,Rational{BigInt}}}' in parts['dispatch'] and 'length(row_terms) == 8' in parts['dispatch'] and 'Tuple{LinearProblem,Any,Int,ExactValue,ExactValue}' in parts['dispatch']
checks['no_candidate_instrumentation']='_mal_note_' not in candidate and 'MAL_TRACE' not in candidate
fixtures=read(D/'fixtures.json')['fixtures']+read(D/'extra-fixtures.json')['fixtures']
# Independently enumerate finite endpoint corners; use unboundedness only for the
# extrema it affects. All stored nonQ values are already frozen binary rationals.
def decode(v):return None if v is None else F(v)
def exact_oracle(f):
 c=list(map(F,f['co']));lo=list(map(decode,f['lo']));hi=list(map(decode,f['hi']));k=f['pivot']-1;rhs=F(f['rhs']);unbounded=[False,False];terms=[]
 for j,a in enumerate(c):
  if j==k or a==0:continue
  mn,mx=(lo[j],hi[j]) if a>0 else (hi[j],lo[j])
  unbounded[0] |= mn is None;unbounded[1] |= mx is None
  terms.append([a*b for b in (lo[j],hi[j]) if b is not None] or [F(0)])
 values=[sum(v,F(0)) for v in product(*terms)];points=[(rhs-v)/c[k] for v in values]
 l_inf,h_inf=unbounded[::-1] if c[k]>0 else unbounded
 return (lo[k] is None or not l_inf and min(points)>=lo[k]) and (hi[k] is None or not h_inf and max(points)<=hi[k])
def route_expectation(f):
 if f['scalar']!='Q' or f['container']!='vector' or len(f['co'])!=8:return (0,0,0,0)
 c=list(map(F,f['co']));lo=list(map(decode,f['lo']));hi=list(map(decode,f['hi']));k=f['pivot']-1
 sums=[F(0) if (hi[k] if c[k]>0 else lo[k]) is not None else None,F(0) if (lo[k] if c[k]>0 else hi[k]) is not None else None]
 count=pos0=adds=eqadds=0;decided=None in sums;active=False
 for pos,j in enumerate(range(len(c)),1):
  if pos==4:decided=True
  if j==k:continue
  bounds=[lo[j],hi[j]] if c[j]>0 else [hi[j],lo[j]]
  shared=sums[0]==sums[1];eligible=not decided and None not in sums and None not in bounds and bounds[0]!=bounds[1]
  for side,b in enumerate(bounds):
   if sums[side] is None or b is None:sums[side]=None;continue
   if b==0:continue
   y=c[j]*b;x=sums[side]
   if x==0:sums[side]=y;continue
   if side==1 and shared and bounds[0]==bounds[1]:sums[side]=sums[0];continue
   equal=x.denominator==y.denominator
   if not active and not equal and eligible and not decided and y:
    count+=1
    if count==2:
     decided=True
     if (x>0)==(y>0) and abs(x.numerator).bit_length()>=129 and abs(y.numerator).bit_length()>=129:active=True;pos0=pos
   if active:adds+=1;eqadds+=equal
   sums[side]=x+y
 return pos0,count,adds,eqadds
routes={f['id']:route_expectation(f) for f in fixtures}
checks['all222_exact_oracles']=len(fixtures)==222 and all(exact_oracle(f)==f['expected'] for f in fixtures)
checks['all_route_expectations']=all(routes[f['id']][:3]==(f['route']['position'],f['route']['count'],f['route']['adds']) for f in fixtures)
checks['active_same_denominator_exercised']=routes['same-denominator-after-selection'][3]>=2
checks['unique_ids']=len(set(f['id'] for f in fixtures))==222
checks['canonical_rationals']=all(s is None or s==str(F(s).numerator)+'/'+str(F(s).denominator) for f in fixtures for s in f['co']+f['lo']+f['hi']+[f['rhs']])
checks['valid_bounds']=all(a is None or b is None or F(a)<=F(b) for f in fixtures for a,b in zip(f['lo'],f['hi']))
checks['nonQ_binary_inputs']=all(F(s).denominator & (F(s).denominator-1)==0 for f in fixtures if f['scalar']!='Q' for s in f['co']+f['lo']+f['hi']+[f['rhs']] if s is not None)
checks['cost_grid76']=Counter(f['cost'] for f in fixtures if f['cost'])=={'target':24,'control':52}
checks['targets_and_inactive_controls']=all(bool(f['route']['position'])==(f['cost']=='target' or f['group']=='tail') for f in fixtures if f['cost'])
checks['tight_triples117']=Counter(f['mode'] for f in fixtures if f['mode']!='contain')=={'inside':39,'equal':39,'outside':39} and all(f['expected']==(f['mode']!='outside') for f in fixtures if f['mode']!='contain')
checks['bit_boundary_expectations']=all(bool(f['route']['position'])==(int(f['id'].split('-')[1])>=129) for f in fixtures if f['id'].startswith('bits-'))
checks['lowbits']=all(f['expected']==(f['id'].split('-')[1]=='0') for f in fixtures if f['id'].startswith('lowbits-'))
checks['pivot_coverage']={f['pivot'] for f in fixtures if f['id'].startswith('pivot-')}==set(range(1,9))
# Frozen Julia data must be an exact re-encoding, not an independently editable input.
def jl(v):
 if v is None:return 'nothing'
 if isinstance(v,bool):return 'true' if v else 'false'
 if isinstance(v,int):return str(v)
 if isinstance(v,str):return json.dumps(v)
 if isinstance(v,list):return '['+','.join(jl(x) for x in v)+']'
 raise TypeError(type(v))
for fname,jname in [('fixtures.json','fixtures.jl'),('extra-fixtures.json','extra-fixtures.jl')]:
 rows=[]
 for x in read(D/fname)['fixtures']:
  v={k:z for k,z in x.items() if k!='route'};v.update(route_position=x['route']['position'],route_count=x['route']['count'],route_adds=x['route']['adds'])
  rows.append('    ('+', '.join(k+'='+jl(z) for k,z in v.items())+',),')
 checks['literal_'+jname]=(D/jname).read_text().splitlines()[2:-1]==rows
red=read(D/'structural-red.json');checks['tests_preceded_candidate']=red['missing_candidate_before'] and all(sha(D/(n+'.before-extra-coverage' if n in ('tests.jl','test-helpers.jl') else n))==v for n,v in red['test_hashes'].items())
checks['no_production_changes']=not subprocess.check_output(['git','diff','HEAD','--','src','test','Project.toml','.github'])
checks['source_caps']='2 <= length(terms) <= 8' in source and 'fill_estimate <= 10' in source and 'estimated_updates + fill_estimate <= 200_000' in source
checks['no_launcher_driver']=not (D/'driver.jl').exists() and not (D/'launcher.py').exists()
# Exact prospective Test counts; no claim of executed assertions.
counts={'fixtures':222,'cost_fixtures':76,'case_assertions':222*16,'alias_assertions':9,'lossy_negative_assertions':2,'same_denominator_assertion':1,'snapshot_negative_assertion':1,'green_total':222*16+9+2+1+1,'red_pass':8,'red_expected_fail':2,'ordinary_helper_calls_green':222*4,'ordinary_helper_calls_red':4,'groups':dict(Counter(f['group'] for f in fixtures)),'private_additions_in_trace':sum(f['route']['adds'] for f in fixtures),'scope':'Prospective counts, UNEXECUTED. Internal trace guards are not Test assertions; timing/fixture setup excluded.'}
paths=[p for p in D.iterdir() if p.is_file()]+[R/'src/presolve_aggregation.jl',R/'src/presolve_rows.jl',R/'src/model.jl',R/'Project.toml',R/'docs/superpowers/plans/2026-10-14-ma-presolve-selective-routing.md',R/'docs/superpowers/specs/2026-10-14-ma-presolve-selective-routing-design.md',D.parent/'MA-K/review.json',D.parent/'MA-J/candidate.jl']
record=dict(all_passed=all(checks.values()),checks=checks,counts=counts,sha256={str(p):sha(p) for p in paths},scope='Offline only; no Julia parse, dispatch, mutation behavior, allocations or speedup demonstrated.')
with (D/'source-check.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'counts':counts,'hash_count':len(record['sha256'])},indent=2))
require(record['all_passed'],'source preparation failed; preserve result and stop publication')
