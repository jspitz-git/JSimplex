"""One-shot draft hardening before source checks, no Julia or launch."""
from pathlib import Path
E=Path(__file__).resolve().parent
p=E/'control.py';t=p.read_text();anchor=" cfg=config(phase);j=rd(D/'lineage.json');require(bindings(j),'GREEN lineage drift')"
new=""" cfg=config(phase);j=rd(D/'lineage.json');require(bindings(j),'GREEN lineage drift')
 allowed={phase}
 if phase.endswith('600'):allowed.add(phase[:-3]+'300')
 if cfg['process']==2:allowed.update(['cost1-300','cost1-600'])
 actual={p.name for p in (D/'runs').iterdir()} if (D/'runs').exists() else set()
 require(actual<=allowed,'Unprepared or out-of-order attempt')"""
if t.count(anchor)!=1:raise RuntimeError('anchor')
p.write_text(t.replace(anchor,new))
