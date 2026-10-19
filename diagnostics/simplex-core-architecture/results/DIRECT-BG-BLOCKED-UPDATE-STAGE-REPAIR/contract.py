"""Source-text contract only; no Julia parse/load/dispatch claim or numerical calls."""
from pathlib import Path
import re

def contract(root):
    root=Path(root); f=(root/'src/factorization.jl').read_text(); t=(root/'src/triangular_factorization.jl').read_text()
    j=(root/'src/JSimplex.jl').read_text(); d=(root/'src/direct-factor.jl').read_text()
    checks={
      'enum_provider':'@enum _NativePivotPolicy::UInt8 _NATIVE_PIVOT_DEFAULT _NATIVE_PIVOT_ONE' in f,
      'native_policy_factory':'function _factorize_basis(B::AbstractMatrix{Float64}, ::Val{:native}, policy::_NativePivotPolicy)' in f,
      'markowitz_policy_factory':'function _factorize_basis(B::AbstractMatrix, ::Val{:markowitz}, policy::_NativePivotPolicy)' in f,
      'native_policy_controls':all(x in f for x in ['function _native_lu(', 'UMFPACK_PIVOT_TOLERANCE + 1] = 1.0','UMFPACK_IRSTEP + 1] = 0.0']),
      'native_policy_lifecycle':all(x in f for x in ['const pivot_policy::_NativePivotPolicy','_native_lu(sparse_basis, backend.pivot_policy)','nothing, true, backend.pivot_policy']),
      'manager_policy_constructors':all('function '+n+'(B::AbstractMatrix{T}, ::Val{R}, policy::_NativePivotPolicy)' in t for n in ['ForrestTomlinFactorization','SuhlSuhlFactorization','BartelsGolubFactorization']),
      'include_provider_before_consumer':j.index('include("factorization.jl")')<j.index('include("markowitz_factorization.jl")')<j.index('include("triangular_factorization.jl")')<j.index('include("factor-export.jl")')<j.index('include("direct-factor.jl")'),
      'ordinary_adapter_consumes_policy':'ordinary=factorize(B,backend,policy)' in d and 'pivot_policy::_NativePivotPolicy' in d,
    }
    return checks

def declarations(root,symbols):
    result={}
    for name in sorted(symbols):
        escaped=re.escape(name)
        pat=re.compile(r'^\s*(?:(?:@inline|@noinline|Base\.@constprop\s+:\w+)\s+)*(?:(?:mutable\s+)?struct\s+|abstract\s+type\s+|(?:function|const)\s+)?'+escaped+r'(?:\{|\(|\s*(?:::|=))')
        locations=[]
        for p in sorted((Path(root)/'src').glob('*.jl')):
            for i,line in enumerate(p.read_text().splitlines(),1):
                # Whole-line declaration candidates, not arbitrary token mentions.
                if pat.match(line) or (line.startswith('@enum ') and name in line.split()):
                    locations.append(dict(path=str(p.relative_to(root)),line=i,text=line))
        result[name]=locations
    return result
