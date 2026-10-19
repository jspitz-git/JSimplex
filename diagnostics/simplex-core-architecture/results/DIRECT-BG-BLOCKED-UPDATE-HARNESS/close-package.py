from pathlib import Path
import sys,json
H=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-HARNESS');R=H.parents[3]
sys.path.insert(0,str(H));import control as c
c.preparation()
(H/'close-package.py').write_bytes(Path(__file__).read_bytes())
with (H/'FINAL.md').open('x') as f:f.write('''# Accepted offline Task2 RED/GREEN harness

Independent final review accepted with no unresolved findings; R1-R3 corrected with original drafts/rejected review retained. Reviewer261 source/count/hash checks plus283 baseline/binding checks passed. Author final232 source/inverse checks,62 pure mutation controls and32 full-auditor controls passed. These are offline Python/source results only.

Both future modes include identical common candidate structural/lifecycle prechecks. RED numerical subject uses the original scalar suffix and expects exactly6 named N026 coverage failures; GREEN uses blocked updates and expects none. The fixed structural subtotal is11760 assertions; trajectory-dependent checks use independently reviewed exact occurrence formulas over160sites, fixed28units,26cells and512 numerical begin/finish pairs. No invented fixed dynamic total.

First possible execution is a separately admitted RED with inclusive300s; Julia/BLAS1,heap2GiB,VM8GiB,availableRAM6GiB,swap1GiB. Fresh host/groups/sessions/refs, seal and independent exact-run approval remain mandatory. GREEN follows only accepted RED result/outer closure. This deliverable does not execute or reserve either run. No Task3 cost measurement, production integration or master change.

Original candidate14files, stage, source/test/environment/CI/master, global STATUS/roadmap and older evidence unchanged. Automation remains paused. The broad performance plan remains open. No Julia executable/query/parser/import/compiler/numerics used in this step.
''')
future=['host-closure.json','closure.json','publication.json','publication-names.json']
paths={str(p.relative_to(R)) for p in H.rglob('*') if p.is_file()}|{str((H/n).relative_to(R)) for n in future}
c.save(H/'publication-names.json',{'paths':sorted(paths),'scope':'Fixed exact offline harness files only; excludes original candidate/production/master'})
print('Fixed publication package',len(paths))
