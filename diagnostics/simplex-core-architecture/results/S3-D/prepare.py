"""Exclusive offline rational/input and text-inverse preparation; no Julia."""
from fractions import Fraction as F
from pathlib import Path
import hashlib,json,struct
r=Path.cwd();o=r/'diagnostics/simplex-core-architecture/results/S3-D'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
n=16;I=[[F(i==j) for j in range(n)] for i in range(n)];A=[x[:] for x in I];A[1][0]=F(1,8)
B0=[[-x for x in row] for row in I];B1=[x[:] for x in B0];B2=[x[:] for x in B0]
for i in range(n):B1[i][0]=B2[i][0]=A[i][0];B2[i][1]=A[i][1]
e=lambda i:[F(j==i) for j in range(n)]
prior=[-v for v in [row[0] for row in A]];direction=[-v for v in e(1)];rho=[F(1,8),-F(1)]+[F(0)]*14;tau=[F(1,8),F(65,64)]+[F(0)]*14
rhs=[F(1)]*16;endpoint=[F(1),F(7,8)]+[-F(1)]*14;dualendpoint=[F(7,8),F(1)]+[-F(1)]*14
mv=lambda M,x:[sum(a*b for a,b in zip(row,x)) for row in M]
checks={'prior_direction':mv(B0,prior)==[row[0] for row in A],'entering_direction':mv(B1,direction)==e(1),'unit_btran':mv(list(map(list,zip(*B1))),rho)==e(1),'weight_ftran':mv(B1,tau)==rho,'endpoint_forward':mv(B2,endpoint)==rhs,'endpoint_transpose':mv(list(map(list,zip(*B2))),dualendpoint)==rhs,'norm':sum(x*x for x in rho)==F(65,64),'nonzero_pivots':prior[0]==direction[1]==-1}
# Binary64 input bits are frozen independently from rational reference equations.
vals={'A':A,'B0':B0,'B1':B1,'B2':B2,'prior_direction':prior,'entering_direction':direction,'rho':rho,'tau':tau,'endpoint_rhs':rhs,'endpoint_forward':endpoint,'endpoint_transpose':dualendpoint,'objective':[-F(1)]+[F(0)]*15,'row_upper':[F(1)]+[F(100)]*15}
enc=lambda x: [enc(v) for v in x] if isinstance(x,list) else {'rational':str(x),'binary64_hex':struct.pack('>d',float(x)).hex()}
weights=[1.0]*32;weights[17]=65/64;weights[18]=2**-20
basis=[0]+list(range(17,32));pivot=-1.0;norm=65/64;new=weights[:]
for row,index in enumerate(basis):
 c=float(direction[row]);new[index]=max(1.0/10000,weights[index]+c*(c*(norm/(pivot**2))-2.0*float(tau[row])/pivot))
new[1]=norm
checks['zero_coefficient_floor_sensitive']=new[18]==1/10000 and new[18]!=weights[18]
checks['leaving_floor']=new[17]==1/10000
checks['entering_weight']=new[1]==65/64
inputs={'fixture_origin':'pipeline_support_census.jl fixture(Float64,manager,:native,history), same m=16 A/objective/row_upper; component setup replaces public pivot by explicit first-column update','dimension':16,'values':{k:enc(v) for k,v in vals.items()},'basis_before_zero_based':basis,'weights_before_bits':[struct.pack('>d',v).hex() for v in weights],'weights_after_bits':[struct.pack('>d',v).hex() for v in new],'policy':'NumericalPolicy(Float64;simplex_strategy=:legacy,hypersparse=true,refactor_timing=false), native profile/default guards unchanged','residual_bound':'exact ||M*z-b||inf <= 64*2^-52*max(1,||M||inf*||z||inf,||b||inf); no post-output bound choice','scope':'Component stressed weights; no public reachable trajectory/certificate claim'}
assert all(checks.values())
sources={}
for file,start,end,key in [('src/dual_simplex.jl','function update_dse!','function _switch_dual_pricing_to_devex!','dse'),('src/dual_simplex.jl','function update_dual_pricing_weights!','function dual_iteration!','weights'),('src/simplex_recovery.jl','function _checked_basis_solve!','# Precision-specialized repair','checked')]:
 s=(r/file).read_text();a=s.index(start);b=s.index(end,a);sources[key]={'file':file,'first_line':s[:a].count('\n')+1,'text':s[a:b],'file_sha256':sha(r/file)}
rename={'update_dual_pricing_weights!':'_s3d_update_dual_pricing_weights!','update_dse!':'_s3d_update_dse!','_checked_basis_solve!':'_s3d_checked_basis_solve!'}
for key,v in sources.items():
 c=v['text']
 for before,after in rename.items():c=c.replace(before,after)
 if key=='checked':
  old='_pipeline_basis_solve!(destination,ws,rhs;transposed,operation,prepare_update,unit_row)';newcall='_pipeline_basis_solve!(destination,ws,rhs;transposed,operation,prepare_update,unit_row,kernel_mode=_s3d_weight_mode[])'
  assert c.count(old)==1;c=c.replace(old,newcall)
 inverse=c
 if key=='checked':inverse=inverse.replace(newcall,old)
 for before,after in rename.items():inverse=inverse.replace(after,before)
 assert inverse==v['text'];v['clone_text']=c;v['inverse_exact']=True
 with (o/(key+'-clone.txt')).open('x') as f:f.write(c)
with (o/'exact-inputs.json').open('x') as f:json.dump(inputs,f,indent=2);f.write('\n')
with (o/'source-manifest.json').open('x') as f:json.dump(sources,f,indent=2);f.write('\n')
with (o/'offline-checks.json').open('x') as f:json.dump({'checks':checks,'all_passed':True,'clones_inverse':3,'scope':'Offline rational equations/binary64 recurrence and unexecuted source text only'},f,indent=2);f.write('\n')
print(json.dumps({'checks':len(checks),'clones_inverse':3,'all_passed':True}))
