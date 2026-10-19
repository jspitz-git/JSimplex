"""Offline immutable preparation membership; no Julia or operational admission."""
from pathlib import Path
import sys
D=Path(__file__).resolve().parent;R=D.parents[3];sys.path.insert(0,str(D));import control as c
paths=set(c.gcbase.preparation());extra,groups=c.predecessor('cost1-300');paths.update(extra)
O=D.with_name('DIRECT-BG-EXPORT-WORKSPACE-COST-PREPARATION')
paths.update(str(O/n) for n in ['ADMISSION.md','MEMORY-WORK.md','cost.jl','probe.jl','clone_source.py','analysis.py','evidence.py','audit.py','control.py','inputs.json','inputs.toml','review.json','review.md','probe-inverse.json'])
paths.update(str(R/n) for n in ['AGENTS.md','docs/superpowers/plans/2026-10-19-direct-bg-export-specialization.md','docs/superpowers/specs/2026-10-19-direct-bg-export-specialization.md','diagnostics/direct-bg-export-specialized/reproduce/work-memory-ledger.md'])
paths.update(str(p) for p in D.iterdir() if p.is_file())
stage=Path(c.rd(D/'stages.json')['cost']['path']);paths.update(str(p) for p in stage.rglob('*') if p.is_file());paths=sorted(paths)
c.require(len(groups)==265 and not (D/'runs').exists() and not (D/'outers').exists(),'No runtime, full groups')
c.save(D/'required-paths.json',dict(paths=paths));c.save(D/'preparation-pins.json',dict(sha256={p:c.sha(p) for p in paths},scope='Read-time preparation pins; not launch pins; original evidence remains frozen'))
print('Sealed offline preparation paths:',len(paths))
