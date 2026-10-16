"""New source-to-actual-stage reconciliation; no old auditor execution."""
from pathlib import Path
import json,hashlib,difflib
R=Path(__file__).resolve().parents[4];E=Path(__file__).resolve().parent;d=json.loads((E/'overlay-reviewed.json').read_text());O=Path(d['path'])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(c,m):
 if not c:raise RuntimeError(m)
checks={};pins={};changes=[]
for n in ['triangular_factorization.jl','triangular_rows.jl','triangular_spikes.jl','triangular_indices.jl','bartels_golub_rows.jl']:
 p=R/'src'/n;q=O/'src'/n;a=p.read_text();b=q.read_text();pins[str(p)]=sha(p);pins[str(q)]=sha(q)
 if n=='triangular_factorization.jl':
  transformed=a
  for F,key in [('ForrestTomlinFactorization','forrest_tomlin'),('SuhlSuhlFactorization','suhl_suhl'),('BartelsGolubFactorization','bartels_golub')]:
   old=f'function {F}(B::AbstractMatrix{{T}}, ::Val{{R}}) where {{T<:Real,R}}\n    _supported_value_type(T) || throw(ArgumentError("unsupported basis value type: $T"))\n    base = _factorize_basis(B, Val(R))'
   new=f'{F}(B::AbstractMatrix{{T}}, backend::Val) where {{T<:Real}} =\n    {F}(B, backend, _NATIVE_PIVOT_DEFAULT)\n_basis_factorization(B, ::Val{{:{key}}}, backend::Val, policy::_NativePivotPolicy) =\n    {F}(B, backend, policy)\n\nfunction {F}(B::AbstractMatrix{{T}}, ::Val{{R}}, policy::_NativePivotPolicy) where {{T<:Real,R}}\n    _supported_value_type(T) || throw(ArgumentError("unsupported basis value type: $T"))\n    base = _factorize_basis(B, Val(R), policy)'
   need(transformed.count(old)==1,'Factory selector');transformed=transformed.replace(old,new)
  checks['triangular_factorization_only_three_accepted_policy_factories']=transformed==b
  changes=list(difflib.unified_diff(a.splitlines(),b.splitlines(),fromfile=str(p),tofile=str(q),lineterm=''))
 else:checks[n+'_identical']=a==b
for n in ('direct-factor.jl','factor-export.jl'):
 p=R/'diagnostics/direct-lu-policy-adapters/reproduce'/n;q=O/'src'/n
 checks[n+'_accepted_adapter_identical']=p.read_bytes()==q.read_bytes();pins[str(p)]=sha(p);pins[str(q)]=sha(q)
pins[str(Path(__file__))]=sha(Path(__file__))
record=dict(all_passed=all(checks.values()),checks=checks,sha256=pins,known_factory_diff=changes,scope='Actual master source numerical helpers match accepted stage; only three already accepted policy constructors differ in triangular_factorization.jl. Comparator is accepted staged DIRECT BG, not actual unmodified master dispatch. No Julia.')
with (E/'stage-source-map.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=record['all_passed'],checks=len(checks)),indent=2));need(record['all_passed'],'Stage reconciliation')
