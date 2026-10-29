from pathlib import Path
from fractions import Fraction
from decimal import Decimal,localcontext
import hashlib,json,tomllib,struct,re
D=Path(__file__).resolve().parent
checks={};bindings={}
def require(name,condition):
 checks[name]=bool(condition)
 if not condition:raise RuntimeError(name)
def read(p):
 p=Path(p);data=p.read_bytes();bindings[str(p)]=hashlib.sha256(data).hexdigest();return data
def frac(bits):
 return Fraction.from_float(struct.unpack('>d',bytes.fromhex(bits))[0])
r=tomllib.loads(read(D/'results-1.toml').decode())
p=json.loads(read(D/'diagnosis-1/guard/process.json'));s=json.loads(read(D/'diagnosis-1/supervisor.json'));h=json.loads(read(D/'diagnosis-1/postflight.json'))
require('complete',r['completed'] and len(r['arms'])==3)
require('exact_matrix',r['n']==28453 and r['matrix_hash']=='7b6ab789d7f49d73ec163eee3e2c5c5e9207dadd5f66a3b31972755b367c6d5c')
require('exit_and_guard',p['returncode']==0 and p['reason']=='exit0' and p['pins_unchanged'] and s['accepted'])
require('no_timeout_kill',not any(s.get(k,False) for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']))
require('host_closed',not h['conflicts'] and len(h['checked_groups'])>=725)
require('resource_terminal',p['terminal_memory']['available_kib']>=6*1024**2 and p['terminal_memory']['swap_used_kib']<=1024**2)
for kind in ['runner','child']:
 require('identity_'+kind,all(k in p[kind] for k in ['boot_id','start_ticks','command','pid','pgid','sid']))
 for field in ['pgid','sid']:require('closed_'+kind+'_'+field,p[kind][field] in h['checked_groups'])
pins=json.loads(read(D/'launch-pins.json'))
for path,item in pins['inventory'].items():
 # schema resolved below if needed, fail closed on missing hash
 expected=item if isinstance(item,str) else item['sha256']
 require('launch_pin_'+path,hashlib.sha256(read(path)).hexdigest()==expected)
w=r['witness'];require('witness_size',Path(w['path']).stat().st_size==w['bytes']);require('witness_hash',hashlib.sha256(read(w['path'])).hexdigest()==w['sha256'])
exact=[];arm_summary=[];snapshots=0;corrtotal=0
for arm in r['arms']:
 name=arm['name'];policy=arm['policy'];tol=Fraction.from_float(policy['solve_tolerance'])
 require(name+'_policy',tol==Fraction(1,2**44) and policy['max_refinements']==3 and not policy['solve_refinement'] and not policy['adaptive_refactor'] and not policy['hypersparse'])
 require(name+'_bounded_corrections',arm['correction_calls']==len(arm['corrections'])<=3);corrtotal+=arm['correction_calls']
 snaps=[arm['initial'],arm['final']]
 for correction in arm['corrections']:
  snaps.extend([correction['before'],correction['trial']])
  b,t=correction['before']['quality'],correction['trial']['quality']
  improved=t['reliable'] or t['relative_error']<b['relative_error']
  gate=correction['gate']
  require(name+'_gate_'+str(correction['index']), correction['accepted']==(gate=='accepted') and (gate!='quality_not_improved' or not improved))
  require(name+'_rhs_binding_'+str(correction['index']),correction['correction_rhs_hash']==correction['before']['residual_hash'])
 for snapshot in snaps:
  snapshots+=1;label=snapshot['label'];q=snapshot['quality'];selected=snapshot['selected_equations']
  require(name+'_'+label+'_finite',q['finite'])
  require(name+'_'+label+'_oracle_bits',snapshot['diagnostic_oracle_bits']==137)
  require(name+'_'+label+'_max_selected',any(e['column']==snapshot['max_oracle_ratio_column'] for e in selected))
  for e in selected:
   a=[frac(x) for x in e['coefficients_bits']];x=[frac(x) for x in e['solution_bits']];rhs=frac(e['rhs_bits'])
   require(name+'_'+label+'_equation_'+str(e['column']),len(a)==len(x)==len(e['rows']) and all(1<=i<=r['n'] for i in e['rows']))
   products=[u*v for u,v in zip(a,x)];res=rhs-sum(products,Fraction(0));scale=abs(rhs)+sum(map(abs,products),Fraction(0));ratio=abs(res)/scale if scale else Fraction(0) if not res else None
   require(name+'_'+label+'_nonzero_scale_or_zero',ratio is not None)
   with localcontext() as ctx:
    ctx.prec=80;value=Decimal(ratio.numerator)/Decimal(ratio.denominator)
    # 137-bit oracle accumulation may round, exact witness is authoritative.
    require(name+'_'+label+'_wide_ratio_'+str(e['column']),abs(value-Decimal(e['wide_ratio']))<=Decimal('1e-30')*max(1,abs(value)))
   exact.append(dict(arm=name,snapshot=label,column=e['column'],original_basis_variable=e['original_basis_variable'],nnz=len(a),rhs=str(rhs),residual=str(res),scale=str(scale),ratio=str(ratio),ratio_float=float(ratio),exceeds_tolerance=ratio>tol))
 arm_summary.append(dict(name=name,initial=arm['initial']['quality'],final=arm['final']['quality'],branches=[v['branch'] for v in snaps],corrections=[dict(index=c['index'],gate=c['gate'],before=c['before']['quality'],trial=c['trial']['quality']) for c in arm['corrections']],controls=arm['controls']))
require('solve_budget',corrtotal<=9 and snapshots<=24)
require('three_arm_names',[a['name'] for a in r['arms']]==['native-KLU','local-KLU','UMFPACK'])
require('native_and_local_reject',all(not a['initial']['quality']['reliable'] and not a['final']['quality']['reliable'] for a in r['arms'][:2]))
log=read(D/'diagnosis-1/guard/run.log').decode()
require('ordinary_test_summary','First rejected KLU weight RHS' in log and 'Error During Test' not in log and 'Test Failed' not in log)
result=dict(accepted=True,scope='diagnostic rejection classification, not candidate acceptance',checks=checks,bindings=bindings,arms=arm_summary,selected_exact_equations=exact,snapshots=snapshots,correction_btrans=corrtotal)
(D/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(accepted=True,checks=len(checks),bindings=len(bindings),snapshots=snapshots,correction_btrans=corrtotal,exact_equations=len(exact))))
