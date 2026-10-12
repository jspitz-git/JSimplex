from pathlib import Path
from fractions import Fraction as Q
import json,hashlib,struct,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';E=D/'results/S4-P';a=json.loads((E/'source-contract.json').read_text());x=json.loads((E/'exact-inputs.json').read_text());checks={};sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();q=lambda h:Q.from_float(struct.unpack('>d',bytes.fromhex(h))[0]);n=48
checks['all567_readtime_hashes_current']=len(a['sha256'])==567 and all(sha(p)==h for p,h in a['sha256'].items())
checks['source26_all_passed']=len(a['checks'])==26 and all(a['checks'].values())
F=[q(h) for h in x['zF_bits']];B=[q(h) for h in x['zB_bits']];assert F==[Q(-1 if i%2 else 1) for i in range(1,49)] and B==[Q(i%3-1) for i in range(1,49)]
count=96
for fixture in x['fixtures']:
 kind=fixture['name'];mats=[]
 for s in fixture['states']:
  k=s['stage'];mat=[[Q(0) for _ in range(n)] for _ in range(n)]
  for j in range(n):
   for z in range(s['colptr'][j]-1,s['colptr'][j+1]-1):mat[s['rowval'][z]-1][j]=q(s['nzval_bits'][z])
  active=[[],[3],[3,17],[3,17,31],[3,17],[3],[]][k]
  for ii in range(n):
   for jj in range(n):
    i=ii+1;j=jj+1
    if i==j:v=Q(192+i%5,32)
    elif kind=='sparse':v=Q(1,64) if j-i==1 else Q(-1,128) if i-j==1 else Q(0)
    elif i<j:v=Q(1+(i+2*j)%3,4096)
    else:v=-Q(1+(2*i+j)%5,8192)
    if j in active:v+=Q(1,8) if i==j else Q(1,256) if i==j+1 else Q(0)
    assert mat[ii][jj]==v
  assert s['nnz']==(142 if kind=='sparse' else 2304)
  margin=min(mat[i][i]-sum(abs(mat[i][j]) for j in range(n) if i!=j) for i in range(n));assert margin==Q(s['row_dominance_margin']) and margin>5
  assert any(mat[i][j]!=mat[j][i] for i in range(n) for j in range(n))
  assert [sum(mat[i][j]*F[j] for j in range(n)) for i in range(n)]==list(map(q,s['rhsF_bits']))
  assert [sum(mat[j][i]*B[j] for j in range(n)) for i in range(n)]==list(map(q,s['rhsB_bits']))
  count+=s['nnz']+96;mats.append(mat)
 for t in fixture['transitions']:
  k=t['step'];j=t['column']-1;old=mats[k-1];new=mats[k];incoming=list(map(q,t['incoming_bits']));assert incoming==[row[j] for row in new]
  assert all(old[i][c]==new[i][c] for i in range(n) for c in range(n) if c!=j)
  delta=[new[i][j]-old[i][j] for i in range(n)];m=Q(fixture['states'][k-1]['row_dominance_margin']);assert max(map(abs,delta))==Q(1,8)
  assert Q(1)-Q(1,8)/m==Q(t['exact_pivot_lower_bound'])>Q(39,40)
  assert delta[j-1]==0 and old[j-1][j]!=0 and delta[j]!=0;count+=48
 assert mats[0]==mats[6]
 checks[kind+'_all7_formula_rhs_dominance']=True;checks[kind+'_six_transition_pivot_nonunit']=True
checks['independent_19138_bits']=count==19138
schedule=[dict(stage=stage,round=r,fixture=f,side=side) for stage,rounds in [('warmup',2),('measured',8)] for r in range(1,rounds+1) for f in ['sparse','dense'] for side in (['reference','candidate'] if r%2 else ['candidate','reference'])]
checks['40_lifecycles_8warm32measured']=len(schedule)==40 and sum(t['stage']=='warmup' for t in schedule)==8
checks['balanced_four_RC_four_CR_eachfixture']=all([sum(t['stage']=='measured' and t['fixture']==f and t['side']=='reference' and t['round']%2==par for t in schedule) for par in [0,1]]==[4,4] for f in ['sparse','dense'])
work={'constructors':40,'refactors':80,'updates':240,'prepared_F':240,'ordinary_F':360,'B':360,'direct_solves':960,'internal_unit_transpose_source':240,'apply_entries_source':1200,'numeric_extraction_entries_source':120,'reference_symbolic_source':60,'candidate_initial_symbolic_source':20,'candidate_pattern_scans_source':40,'orientation_solves_upper_bound':120,'explicit_GC_entries':80,'runtime_residual_matvecs':960,'output_vectors':960,'output_Float64_values':46080}
checks['whole_work_arithmetic']=work['direct_solves']==work['prepared_F']+work['ordinary_F']+work['B']==40*24 and work['apply_entries_source']==40*(2*sum(range(3))+4*sum(range(1,4)))
checks['production_test_ci_unchanged']=subprocess.check_output(['git','diff','master','--','src','test','.github'])==b''
with (E/'independent.json').open('x') as f:json.dump(dict(checks=checks,all_passed=all(checks.values()),rehash_count=len(a['sha256']),reconstructed_entries=count,scope='Independent author exact bit decoding/formula/RHS/dominance/transition checks and full rehash; no factorization or native calls'),f,indent=2);f.write('\n')
with (E/'work-contract.json').open('x') as f:json.dump(dict(schedule=schedule,whole_process=work,scope='Prospective exact call contract, zero runtime observations'),f,indent=2);f.write('\n')
print(checks);assert all(checks.values())
