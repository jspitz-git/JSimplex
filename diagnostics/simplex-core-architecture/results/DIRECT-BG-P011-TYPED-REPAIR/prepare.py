from pathlib import Path
import hashlib,json,shutil
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
D=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-P011-TYPED-REPAIR'
D.mkdir(exist_ok=False)
shutil.copyfile(__file__,D/'prepare.py')
for src,name in [('/tmp/p011-repair-host.json','host-entry.json'),('/tmp/p011-helpers.jl','helpers.jl'),('/tmp/p011-replacement.txt','replacement.txt')]:shutil.copyfile(src,D/name)
old=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-RED2-HARNESS/panel-tests.jl'
original=old.read_bytes()
block=b'        # Two identical calls after warm compilation: future harness admits execution.\n        f=carrier(zeros(32,32)); K._bgb_eligibility(f,1)\n        @check "P011" (@allocated K._bgb_eligibility(f,1)) == 0\n'
anchor=b'function run_task1_tests()\n'
if original.count(block)!=1 or original.count(anchor)!=1:raise SystemExit('unique edit anchors required')
# Preparation checks describe missing proposed coverage, not a Julia RED.
(D/'source-before.json').write_text(json.dumps({'scope':'literal preparation only, no Julia RED','missing':{x:x.encode() not in original for x in ['p011_probe','"P095"','"P102"']},'original_sha256':hashlib.sha256(original).hexdigest()},indent=2)+'\n')
(D/'original-block.txt').write_bytes(block)
(D/'panel-tests.jl').write_bytes(original.replace(block,(D/'replacement.txt').read_bytes()).replace(anchor,(D/'helpers.jl').read_bytes()+anchor))
ledger=R/'.superpowers/sdd/2026-10-19-direct-bg-blocked-update/progress.md'
(D/'progress.md.before-p011-repair').write_bytes(ledger.read_bytes())
inputs=[old,R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-ZERO-COUNTS-CANDIDATE/panel.jl',R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-ZERO-COUNTS-HARNESS/operations.jl',R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-ZERO-COUNTS-RUN/REPORT.md',R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-ZERO-COUNTS-RUN/result-review.json',R/'docs/superpowers/plans/2026-10-19-direct-bg-blocked-update.md',R/'src/triangular_factorization.jl',R/'src/triangular_indices.jl',Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/base/timing.jl')]
(D/'inputs.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},indent=2)+'\n')
print(D)
