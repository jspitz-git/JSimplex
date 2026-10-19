from pathlib import Path
P=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-SPECIALIZATION-GC-DRIVER')
s=(P/'offline-tests.py').read_text().replace("D/'offline-tests.json'","D/'offline-tests-reviewed.json'")
with (P/'offline-tests-reviewed.py').open('x') as f:f.write(s)
s=(P/'full-audit-tests.py').read_text().replace("P/'full-audit-tests.json'","P/'full-audit-tests-reviewed.json'")
s=s.replace("'bad_GC_metric':lambda:","'GC_wall_overflow':lambda:mutate('preparation-1.toml',lambda v:v.update(seconds=3.)),\n   'strict_reservation_bool':lambda:(run/'reservation.json').write_text(json.dumps(dict(docs['reservation.json'],one_attempt=1))),\n   'bad_GC_metric':lambda:")
s=s.replace("v=a.checks_for('greengc300');ck('complete_GREEN_8640'", "import allocation_oracle\n  with patch.object(allocation_oracle,'partial_windows',wraps=allocation_oracle.partial_windows) as partial, patch.object(allocation_oracle,'allocation_results',wraps=allocation_oracle.allocation_results) as full, patch.object(a.tomllib,'loads',wraps=json.loads) as codec:\n   v=a.checks_for('greengc300')\n   ck('one_full_residual_pass_zero_partial',full.call_count==1 and partial.call_count==0)\n   ck('decode_each_TOML_once',codec.call_count==64)\n  ck('complete_GREEN_8640'")
with (P/'full-audit-tests-reviewed.py').open('x') as f:f.write(s)
