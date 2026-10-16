"""Offline authoring of NEW controls and driver only; never executes Julia."""
from pathlib import Path
import json
E=Path(__file__).resolve().parent;R=E.parents[3];D=E.parent/'DIRECT-BG-DYNAMIC-DRIVER-PREPARATION';G=E.parent/'DIRECT-BG-DYNAMIC-GREEN'
def change(n,old,new):
 p=E/n;s=p.read_text()
 if old not in s:raise RuntimeError((n,old))
 p.write_text(s.replace(old,new))
for n in ['control.py','seal.py','launch.py','audit.py']:
 s=(E/n).read_text().replace('direct adapter matched cost','dynamic BG matched cost').replace('diagnostics/direct-lu-policy-adapters/reproduce','diagnostics/direct-bg-dynamic-upper/reproduce').replace('9a2b50b9f0bf6a790ea8b6cdd00904828ae2221a','0601df628f30ee3f226066d5ace9ab16928193aa').replace('DIRECT-LU-POLICY-ADAPTER-DRIVER-PREPARATION','DIRECT-BG-DYNAMIC-DRIVER-PREPARATION').replace('direct adapter GREEN result','dynamic BG GREEN result')
 (E/n).write_text(s)
change('audit.py','len(results)==24','len(results)==8');change('audit.py',"['FT','SS','BG']","['BG']")
# Freeze accepted GREEN lineage without mutable continuation files.
paths=[p for p in (D/'runs/green300').rglob('*') if p.is_file()]+[G/n for n in ['REPORT.md','independent-result-review.md','postcheck.json','review.json','closure.json','publication.json']]
import hashlib
(E/'lineage.json').write_text(json.dumps(dict(sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}),indent=2)+'\n')
# Both genuine direct exporters are observed; the timed path uses unchanged factories.
change('cost.jl','factory(::Val{:reference},F,B,backend) = F(B,backend,policy(backend))','factory(::Val{:reference},F,B,backend) = J._direct_lu_factor(F,B,backend,policy(backend);normalize=true)')
change('cost.jl','factory(::Val{:candidate},F,B,backend) = J._direct_lu_factor(F,B,backend,policy(backend);normalize=true)','factory(::Val{:candidate},F,B,backend) = J._dynamic_bg_factor(B,backend,policy(backend))')
change('cost.jl','mode(::Val{:reference},f) = :ordinary','mode(::Val{:reference},f) = J._direct_mode(f)')
change('cost.jl','mode(::Val{:candidate},f) = J._direct_mode(f)','mode(::Val{:candidate},f) = J._dynamic_bg_mode(f)')
change('cost.jl','side===Val(:candidate) ? (:normalized,:direct,:fallback) : (:ordinary,)','(:normalized,:direct,:fallback)')
change('cost.jl','ordinary=F(f.matrices[1],backend,policy(backend));push!(refs,observe_backend(ordinary.base,backend))','reference_exporter=b->begin\n        push!(refs,observe_backend(b,backend));J._export_basis_lu(b)\n    end\n    ordinary=J._direct_lu_factor_with_exporter(F,f.matrices[1],backend,policy(backend),reference_exporter;normalize=true)')
change('cost.jl','J._direct_lu_factor_with_exporter(F,f.matrices[1],backend,policy(backend),exporter;normalize=true)','J._dynamic_bg_with_exporter(f.matrices[1],backend,policy(backend),exporter;normalize=true)')
change('cost.jl','J._direct_mode(candidate)','J._dynamic_bg_mode(candidate)')
change('cost.jl','J.refactorize!(ordinary,f.matrices[index]);push!(refs,observe_backend(ordinary.base,backend))','J._direct_refactorize_with_exporter!(ordinary,f.matrices[index],reference_exporter)')
change('cost.jl','J._direct_refactorize_with_exporter!(candidate,f.matrices[index],exporter)','J._dynamic_bg_refactor_with_exporter!(candidate,f.matrices[index],exporter)')
change('cost.jl','(("FT",J.ForrestTomlinFactorization),("SS",J.SuhlSuhlFactorization),("BG",J.BartelsGolubFactorization))','(("BG",J.BartelsGolubFactorization),)')
change('cost.jl','save("preflight-$cell.toml",preflight(F,Val(backend),f,input))','save("preflight-$cell.toml",preflight(F,Val(backend),f,input))\n                save("probe-$cell.toml",probe(Val(backend),f,input))')
change('cost.jl','const J = JSimplex','const J = JSimplex\ninclude("probe-oracles.jl")\ninclude("probe.jl")')
# All includes above main at global scope: no newly included function lookup in old world.
change('analysis.py',"(('normalized','direct','fallback') if side=='candidate' else ('ordinary',))","('normalized','direct','fallback')")
for n in ['evidence.py']:
 s=(E/n).read_text().replace('range(1,25)','range(1,9)').replace("['FT','SS','BG']","['BG']").replace('finished<24 or windows<480','finished<8 or windows<160').replace('cells=24,windows=480','cells=8,windows=160').replace('finished==24 and windows==480','finished==8 and windows==160')
 s=s.replace("['started','preflight','cell']","['started','preflight','probe','cell']")
 s=s.replace("end=f'cell-{cell}.toml'","end=f'cell-{cell}.toml';probe=f'probe-{cell}.toml'")
 s=s.replace("visited.add(pre);rows=[]","visited.add(pre);rows=[]\n    if probe not in names:continue\n    probe_ok(tomllib.loads((out/probe).read_text()),f,matrices);visited.add(probe)")
 s=s.replace("visited.add(end);finished+=1","for pair in range(1,11):\n      a,b=rows[2*(pair-1):2*pair];require(a['outputs']==b['outputs'] and a['modes']==b['modes'],'Direct bitwise paired outputs/modes')\n     visited.add(end);finished+=1")
 (E/n).write_text(s)
print('Configured new primary8cell/160window controls and direct factories')
