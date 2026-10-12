"""S6-AD exact offline proof and saved-evidence reconciliation; no Julia calls."""
from fractions import Fraction as Q
from pathlib import Path
import json,hashlib,re,tomllib
ROOT=Path(__file__).resolve().parents[3];D=ROOT/'diagnostics/simplex-core-architecture';OUT=D/'results/S6-AD'
checks={}
def check(name,v):checks[name]=bool(v)
def matvec(A,x):return [sum((a*b for a,b in zip(row,x)),Q(0)) for row in A]
def tr(A):return list(map(list,zip(*A)))
def det(A):
 A=[row[:] for row in A];d=Q(1)
 for j in range(len(A)):
  k=next(k for k in range(j,len(A)) if A[k][j]);
  if k!=j:A[j],A[k]=A[k],A[j];d=-d
  pivot=A[j][j];d*=pivot
  for k in range(j+1,len(A)):
   ratio=A[k][j]/pivot
   A[k]=[x-ratio*y for x,y in zip(A[k],A[j])]
 return d
source=(ROOT/'test/dual_pivot_consistency_tests.jl').read_text()
old_text=source.split('B=[',1)[1].split(']',1)[0]
old=[[Q(float(x)) for x in row.split()] for row in old_text.split(';')]
check('old_represented_basis_nonsingular',det(old)!=0)
oldrhs=[-row[1] for row in old];e2=[Q(0),Q(1),Q(0),Q(0)]
check('old_rhs_exact_minus_column2',matvec(old,[-x for x in e2])==oldrhs)
H=tomllib.loads((D/'results/S6-H/census-1-reference.toml').read_text())
check('current_test_matches_saved_H_hash',hashlib.sha256(source.encode()).hexdigest()==H['test_sha256'])
check('saved_H_20_pairs_equal',len(H['records'])==20 and all(r['equal'] for r in H['records']))
check('saved_H_row2_enter5',all(r['probe']['row']==2 and r['probe']['entering']==5 for r in H['records']))
check('saved_H_direction_ok_agreement_false',all(r['probe']['direction_residual_ok'] and not r['probe']['pivot_agrees'] for r in H['records']))
fails=json.loads((D/'results/S6-H/existing-failure-map.json').read_text())
check('two_historical_maps_48_each',len(fails['records'])==2 and all(sum(p['count'] for p in r['predicates'])==48 for r in fails['records']))
check('historical_state_predicates_16_each',all(next(p['count'] for p in r['predicates'] if p['line']==69)==16 for r in fails['records']))
# Candidate: four-dimensional identity with a balanced two-row block.
delta=Q(1,2**23);h=Q(1,2**22);u=Q(1,2**52);roundoff=256*u
B=[[Q(1),Q(1),Q(0),Q(0)],[1-delta,1+delta,Q(0),Q(0)],[Q(0),Q(0),Q(1),Q(0)],[Q(0),Q(0),Q(0),Q(1)]]
a=[row[0] for row in B];rhs=[-row[1] for row in B]
rho=[-(1-delta)/(2*delta),1/(2*delta),Q(0),Q(0)]
bad=[rho[0]-h,*rho[1:]];corr=[h,Q(0),Q(0),Q(0)];direction=[Q(1),Q(0),Q(0),Q(0)]
# Unit solve uses B' rho=e2, hence exact first coordinate includes +1/2.
check('candidate_det_2pow_minus22',det(B)==Q(1,2**22))
check('exact_unit_btran',matvec(tr(B),rho)==e2)
check('exact_duplicate_ftran',matvec(B,direction)==a)
check('exact_primal_minus_e2',matvec(B,[-x for x in e2])==rhs)
res=[x-y for x,y in zip(matvec(tr(B),bad),e2)]
check('declared_row_residual_minus_h_twice',res==[-h,-h,0,0])
corrrhs=[-x for x in res]
check('exact_correction_btran',matvec(tr(B),corr)==corrrhs)
check('corrected_row_exact',matvec(tr(B),[x+y for x,y in zip(bad,corr)])==e2)
zt=Q(float(1e-12));cutoff=Q(float(1e-7));pt=cutoff
scales=[e2[j]+sum(abs(B[i][j]*bad[i]) for i in range(4)) for j in range(4)]
tolerances=[max(zt,roundoff*(s+1)) for s in scales]
check('declared_row_passes_legacy_residual',all(abs(r)<t for r,t in zip(res,tolerances)))
check('h_exceeds_unchanged_harris_cutoff',h>cutoff)
check('only_row2_primal_violation',Q(1)>pt)
price=sum(x*y for x,y in zip(a,bad));correctprice=sum(x*y for x,y in zip(a,rho))
check('duplicate_price_minus_h',price==-h)
check('corrected_duplicate_price_zero',correctprice==0)
check('row_column_pivots_disagree',price<0 and direction[1]==0)
# Verify binary64 representation and simple CSC operation ordering separately.
allq=[x for row in B for x in row]+rho+bad+corr+rhs+corrrhs
check('all_declared_values_binary64_exact',all(Q(float(x))==x for x in allq))
rounded_price=sum(float(a[i])*float(bad[i]) for i in range(4))
check('binary64_csc_duplicate_price_exact',Q(rounded_price)==price)
rounded_res=[];rounded_t=[]
for j in range(4):
 r=-float(e2[j]);s=float(e2[j])
 for i in range(4):
  if B[i][j]:
   term=float(B[i][j])*float(bad[i]);r+=term;s+=abs(term)
 rounded_res.append(Q(r));rounded_t.append(Q(max(float(zt),float(roundoff)*(s+1))))
check('binary64_legacy_row_residual_matches',rounded_res==res)
check('binary64_legacy_row_accepts',all(abs(r)<t for r,t in zip(rounded_res,rounded_t)))
# Identity duplicate has no eligible price: not an alternative recovery fixture.
check('identity_duplicate_zero_price',sum(x*y for x,y in zip(e2,direction))==0)
files=['src/dual_simplex.jl','src/simplex_pivot.jl','src/legacy_dual_correction.jl','src/simplex_numerics.jl','src/simplex.jl','src/simplex_recovery.jl','src/hypersparse_pipeline.jl','src/dual_ratio.jl','src/simplex_diagnostics.jl','src/options.jl','test/dual_pivot_consistency_tests.jl']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
check('actual_master_same_contract_files',all(sha(ROOT/f)==sha(Path('/home/jspitz/JSimplex.jl')/f) for f in files))
result={'checks':checks,'all_passed':all(checks.values()),'source_hashes':{f:sha(ROOT/f) for f in files},'evidence_hashes':{str(p.relative_to(ROOT)):sha(p) for p in [D/'results/S6-H/census-1-reference.toml',D/'results/S6-H/existing-failure-map.json',D/'S6-DUAL-BOUNDARY-REVIEW.md',D/'results/S6-J/green-1-rejected-test-source.jl']},'candidate':{'delta':str(delta),'h':str(h),'B':[[str(x) for x in row] for row in B],'primal_rhs':list(map(str,rhs)),'unit_rhs':list(map(str,e2)),'exact_rho':list(map(str,rho)),'declared_rho':list(map(str,bad)),'duplicate_rhs':list(map(str,a)),'direction':list(map(str,direction)),'correction_rhs':list(map(str,corrrhs)),'correction':list(map(str,corr)),'row_residual':list(map(str,res)),'legacy_tolerances':list(map(str,tolerances)),'rounded_legacy_tolerances':list(map(str,rounded_t))},'old_basis_determinant':str(det(old)),'scope':'New offline rational algebra plus explicitly labeled Python binary64 operation checks; no Julia, factor, workspace, callback, certificate or solver calls. Conditional endpoint contract, not runtime qualification or historical cause.'}
with (OUT/'exact-contract.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'all_passed':result['all_passed']},indent=2));assert result['all_passed']
