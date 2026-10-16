"""One-shot OFFLINE text preparation. No Julia parser/import/execution."""
from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parent; R=P.parents[3]; C=R/'diagnostics/direct-lu-policy-adapters/reproduce'; O=R/'diagnostics/direct-lu-markowitz/reproduce'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(path,obj):
 with path.open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
def need(x,m):
 if not x:raise RuntimeError(m)
save(P/'tests-before-candidate.json',{str(p.relative_to(R)):sha(p) for p in sorted(C.glob('*.jl'))})
s=(O/'direct-factor.jl').read_text(); original=s
replacements=[
('    normalize_requested::Bool\n','    normalize_requested::Bool\n    pivot_policy::_NativePivotPolicy\n'),
('b.diagonal,b.normalize_requested,fallback,similar(b.work))','b.diagonal,b.normalize_requested,b.pivot_policy,fallback,similar(b.work))'),
('                                         exporter;normalize::Bool=true) where {R}',
 '                                         policy::_NativePivotPolicy,exporter;normalize::Bool=true,\n                                         factorize=_factorize_basis) where {R}'),
('    ordinary=_factorize_basis(B,backend) # Exactly one factorization.',
 '    R === :markowitz && policy !== _NATIVE_PIVOT_DEFAULT &&\n        throw(ArgumentError("Markowitz does not support a native pivot policy"))\n    ordinary=factorize(B,backend,policy) # Exactly one factorization; test seam is not retained.'),
('normalize,ordinary,Float64[])','normalize,policy,ordinary,Float64[])'),
('D,normalize,nothing,zeros(length(parts.rows)))','D,normalize,policy,nothing,zeros(length(parts.rows)))'),
('''_direct_lu_factor(Factor,B::AbstractMatrix{Float64},backend::Val;normalize::Bool=true)=
    _direct_lu_factor_with_exporter(Factor,B,backend,_export_basis_lu;normalize)
_direct_lu_factor(Factor,B::AbstractMatrix{T},backend::Val;normalize::Bool=true) where {T<:Real}=
    Factor(B,backend)''',
 '''# Compatibility entry points preserve the previous default-policy meaning.
_direct_lu_factor_with_exporter(Factor,B::AbstractMatrix{Float64},backend::Val,
                               exporter;normalize::Bool=true)=
    _direct_lu_factor_with_exporter(Factor,B,backend,_NATIVE_PIVOT_DEFAULT,exporter;normalize)
_direct_lu_factor(Factor,B::AbstractMatrix{Float64},backend::Val,
                  policy::_NativePivotPolicy;normalize::Bool=true)=
    _direct_lu_factor_with_exporter(Factor,B,backend,policy,_export_basis_lu;normalize)
_direct_lu_factor(Factor,B::AbstractMatrix{T},backend::Val,
                  policy::_NativePivotPolicy;normalize::Bool=true) where {T<:Real}=
    Factor(B,backend,policy)
_direct_lu_factor(Factor,B::AbstractMatrix{T},backend::Val;normalize::Bool=true) where {T<:Real}=
    _direct_lu_factor(Factor,B,backend,_NATIVE_PIVOT_DEFAULT;normalize)'''),
('                                            exporter;normalize=f.base.normalize_requested)',
 '                                            f.base.pivot_policy,exporter;normalize=f.base.normalize_requested)')]
for old,new in replacements:
 need(s.count(old)==1,'Replacement uniqueness '+old);s=s.replace(old,new,1)
(C/'direct-factor.jl').write_text(s)
(C/'factor-export.jl').write_bytes((O/'factor-export.jl').read_bytes())
back=s
for old,new in reversed(replacements):
 need(back.count(new)==1,'Inverse uniqueness');back=back.replace(new,old,1)
need(back==original,'Whole-source inverse')
save(P/'candidate-inverse.json',dict(all_passed=True,replacements=replacements,original_sha256=sha(O/'direct-factor.jl'),candidate_sha256=sha(C/'direct-factor.jl'),export_byte_identical=(C/'factor-export.jl').read_bytes()==(O/'factor-export.jl').read_bytes(),fixtures_byte_identical=(C/'fixtures.jl').read_bytes()==(O/'fixtures.jl').read_bytes(),script_sha256=sha(Path(__file__))))
print('Candidate text:8 unique edits; whole-source inverse PASS; export/fixtures byte-identical; UNEXECUTED')
