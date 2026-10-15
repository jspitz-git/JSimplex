"""New exact interpretation of already saved vectors; no old auditor or native calls."""
from pathlib import Path
import sys,struct
from fractions import Fraction as Q
E=Path(__file__).resolve().parent;D=E.parent/'DIRECT-LU-BACKEND-PREPARATION';sys.path.insert(0,str(D))
from control import *
def q(t):return Q(struct.unpack('>d',bytes.fromhex(t))[0])
a=rd(D/'probe-audit.json');r=a['result'];f=tomllib.loads((D/'probe-run/fresh.toml').read_text());p=tomllib.loads((D/'probe-run/prefix.toml').read_text());F=f['factor'];P=p['factor']
s=list(map(q,F['Rs']));req(F['do_recip'] in (0,1),'Flag');s=s if F['do_recip']==1 else [1/x for x in s]
row=86;k=F['p'].index(row+1);terms={name:Q(r['decomposition']['fresh'][name][k])/s[row] for name in ('representation_action','combined_application','scaled_original')}
res=next(z for z in r['residuals'] if z['name']=='fresh_dse');orig=Q(res['residual'][row]);bound=Q(res['bound'])
checks=dict(diagnostic_audit=a['all_passed'] is True,
 residual_15pass3fail=sum(z['passed'] for z in r['residuals'])==15 and r['failed_residuals']==['fresh_dse','tail_dse','base_dse'],
 original_failure_reproduced=r['comparisons']['prefix_dse_matches_original_failure'] is True,
 all_three_dse_same=r['comparisons']['ordinary_equals_base'] is True and r['comparisons']['fresh_equals_ordinary'] is True,
 factors_same_except_info=all(F[k]==P[k] for k in F if k!='info'),
 actual_multiply_flag=F['do_recip']==P['do_recip']==1,
 exact_row87_decomposition=orig==terms['scaled_original']==terms['combined_application']-terms['representation_action'],
 both_terms_nonzero=terms['combined_application']!=0 and terms['representation_action']!=0,
 row87_is_max=abs(orig)==Q(res['max_abs']),
 source_inputs_immutable=tomllib.loads((D/'probe-run/raw.toml').read_text())['inputs_unchanged'] is True)
summary=dict(original_row=row+1,permuted_row=k+1,original_residual=str(orig),original_bound=str(bound),ratio=float(abs(orig)/bound),effective_scale=str(s[row]),scale_min=str(min(s)),scale_max=str(max(s)),do_recip=F['do_recip'],lnz=F['lnz'],unz=F['unz'],factor_identity_max=r['decomposition']['fresh']['factor_identity_max'],unscaled_terms={k:str(v) for k,v in terms.items()},unscaled_terms_float={k:float(v) for k,v in terms.items()},scope='Recorded factor representation and combined application consistency both contribute; not native intermediate capture, root cause, fix or speedup')
paths=[Path(__file__),D/'probe-audit.json',D/'probe-run/fresh.toml',D/'probe-run/prefix.toml',D/'probe-run/raw.toml']
save(E/'interpretation.json',dict(all_passed=all(checks.values()),checks=checks,summary=summary,sha256={str(p):sha(p) for p in paths}));print(json.dumps(summary,indent=2));req(all(checks.values()),'Interpretation failed')
