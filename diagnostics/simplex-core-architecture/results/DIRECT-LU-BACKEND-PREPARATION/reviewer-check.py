"""Independent synthetic review only; no Julia or stage-control execution."""
import sys, json, struct, copy, hashlib
from pathlib import Path
from fractions import Fraction as Q
D=Path(__file__).resolve().parent;R=D.parents[3]
sys.path.insert(0,str(D))
import analysis as a, guard, control
checks={}
def check(k,v):
 if not v:raise AssertionError(k)
 checks[k]=True
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def tok(v):return struct.pack('>d',float(v)).hex()
def tokens(v):return list(map(tok,v))
def product(A,B):return [[sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def mult(A,x):return [sum(v*w for v,w in zip(row,x)) for row in A]
def sp(A,csr):
 ptr=[1];inds=[];vals=[]
 for j in range(3):
  for i in range(3):
   v=A[j][i] if csr else A[i][j]
   if v:inds.append(i+1);vals.append(v)
  ptr.append(len(inds)+1)
 return dict(format='csr' if csr else 'csc',ptr=ptr,indices=inds,values=tokens(vals))
L=[[1,0,0],[2,1,0],[-1,3,1]];U=[[2,-1,4],[0,3,2],[0,0,5]]
P=product(L,U);p=[1,2,0];q=[2,0,1];s=[Q(1,2),Q(1,4),Q(1,8)];B=[[Q(0)]*3 for _ in range(3)]
for i in range(3):
 for j in range(3):B[p[i]][q[j]]=Q(P[i][j])/s[p[i]]
z=sp(B,False);m=dict(n=3,colptr=z['ptr'],rowval=z['indices'],nzval=z['values']);x=[1,-2,3];rhs=mult(B,x);trhs=mult(list(map(list,zip(*B))),x)
c=dict(tokens=tokens([0]*20),irstep_index=8,irstep_zero=True)
f=dict(n=3,lnz=6,unz=6,nzd=3,status=0,do_recip=1,L=sp(L,True),U=sp(U,False),p=[v+1 for v in p],q=[v+1 for v in q],Rs=tokens(s),control=c['tokens'],info=tokens([0]*90),native_owned=True,native_match=True,native_colptr=[v-1 for v in m['colptr']],native_rowval=[v-1 for v in m['rowval']],native_nzval=m['nzval'])
data=a.factors(f,m);dec=a.decomposition(data,tokens(x),tokens(rhs))
check('different_noninvolutive_permutations_multiply',dec['factor_identity_exact'] and dec['scaled_original']==['0']*3)
g=copy.deepcopy(f);g['do_recip']=0;g['Rs']=tokens([1/v for v in s]);check('same_call_divide_contract',a.factors(g,m)==data)
g=copy.deepcopy(f);g['U']['values'][-1]=tok(6);d=a.decomposition(a.factors(g,m),tokens([2,-2,3]),tokens(rhs))
# Independently derive M*y-t and E*y; no tested matrix/permutation helper reused.
y=[2,-2,3];expected=[s[i]*(mult(B,y)[i]-rhs[i]) for i in p]
check('nonzero_decomposition_original',d['scaled_original']==list(map(str,expected)))
check('nonzero_decomposition_representation',d['representation_action']==['0','0',str(y[q[2]])])
check('decomposition_app_minus_rep',all(Q(o)==Q(ap)-Q(e) for o,ap,e in zip(d['scaled_original'],d['combined_application'],d['representation_action'])))
check('nonsymmetric_transpose_residual',a.residual(a.transpose(a.matrix(m)),tokens(x),tokens(trhs))['passed'])
fixture=dict(matrices=[m]*5,steps=[dict(a=tokens(rhs),dse=tokens(rhs),unit=tokens(trhs),j=1)]*5)
xx=tokens(x);fresh=dict(controls_before=c,controls_after=c,outputs=[xx]*3,factor=f)
prefix=dict(controls_before=c,controls_after_refactor=c,controls_after=c,reset={k:True for k in a.RESET},prefix_outputs=[xx]*12,tail_outputs=[xx]*3,ordinary_before_base=[xx]*2,factor=f,fresh_context_retained=True)
raw=dict(completed=True,fatal='',loaded_path='/synthetic/src/JSimplex.jl',counts=dict(factorization=3,ftran=13,btran=5,replace=4,refactor=1,snapshot=2),inputs_unchanged=True)
result=a.analyze(raw,fresh,prefix,fixture,dict(outputs=[xx]*24),'/synthetic')
check('all18_nonsymmetric_residuals',len(result['residuals'])==18 and not result['failed_residuals'])
prefix['tail_outputs']=[xx,tokens([2,-2,3]),xx];prefix['ordinary_before_base']=prefix['tail_outputs'][:2]
result=a.analyze(raw,fresh,prefix,fixture,dict(outputs=[xx]*24),'/synthetic')
check('false_gate_and_nonreproduction_preserved',result['failed_residuals']==['tail_dse'] and result['cost_qualified'] is False and result['comparisons']['prefix_dse_matches_original_failure'] is False)
pins=json.loads((D/'preparation-pins.json').read_text());required=json.loads((D/'required.json').read_text())
check('full4744_inventory_rehash',len(pins['inventory'])==4744 and guard.pins_match(pins))
check('required43_exact_unique',len(required)==len(set(required))==43 and set(required)<=set(pins['files']))
base=json.loads((D.parent/'DIRECT-LU-PREPARATION/baseline.json').read_text())['sha256']
check('production514_unchanged',len(base)==514 and all(sha(R/n)==h for n,h in base.items()))
check('ordinary_overlay4_unchanged',all(sha(R/'src'/n)==sha(R/'.superpowers/direct-lu-markowitz-green-2/candidate/src'/n) for n in ('factorization.jl','triangular_factorization.jl','triangular_rows.jl','triangular_spikes.jl')))
check('sourcecheck_only_filename_changed',(D/'source-check.py').read_text().replace('prepared_spikes.jl','triangular_spikes.jl')==(D/'source-check-2.py').read_text())
for name,count in [('source-check.json',17),('offline-tests.json',52)]:
 v=json.loads((D/name).read_text());check(name+'_frozen_pass_and_hashes',v['all_passed'] is True and len(v['checks'])==count and all(v['checks'].values()) and all(sha(n)==h for n,h in v['sha256'].items()))
check('old_cost1_still_false',json.loads((D.parent/'DIRECT-LU-COST-PREPARATION/cost1-audit.json').read_text())['all_passed'] is False)
check('no_stage_or_attempt',not any(D.glob('probe-*')))
check('guard_supervisor_unchanged',all(sha(D/n)==sha(D.parent/'DIRECT-LU-COST-PREPARATION'/n) for n in ('guard.py','supervisor.py')))
check('host204_prior_groups',len(json.loads((D/'host.json').read_text())['groups'])==204)
check('single45second_phase',control.phase_config('probe')['seconds']==45 and set(json.loads((D/'config.json').read_text()))=={'probe'})
record=dict(all_passed=all(checks.values()),checks=checks,scope='Independent source/hash and synthetic Python review only; no Julia, frozen scripts, stage sealing, reservation, launch or auditor execution',sha256={str(p):sha(p) for p in (Path(__file__),D/'analysis.py',D/'control.py',D/'guard.py',D/'preparation-pins.json')})
with (D/'reviewer-check.json').open('x') as stream:json.dump(record,stream,indent=2);stream.write('\n')
print(json.dumps({'checks':len(checks),'all_passed':record['all_passed']}))
