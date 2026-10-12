from pathlib import Path
import hashlib,json,subprocess
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');D=R/'diagnostics/simplex-core-architecture';E=D/'results/S4-O';a=json.loads((E/'source-attribution.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks={'full592_hashes_current':all(sha(p)==h for p,h in a['sha256'].items()),'26_source_checks_passed':len(a['checks'])==26 and all(a['checks'].values()),'master_source_test_ci_equal':subprocess.check_output(['git','diff','master','--','src','test','.github'],cwd=R)==b'','historical_runtime_limit_explicit':'do not include timing.jl' in (D/'S4-ALLOCATION-COUNTER-ATTRIBUTION.md').read_text(),'native_retention_open':'Native retention remains OPEN' in (D/'S4-ALLOCATION-COUNTER-ATTRIBUTION.md').read_text()}
res={'checks':checks,'all_passed':all(checks.values()),'scope':'Independent author full read-time rehash, not a rerun of source_attribution or M/N scripts'}
with (E/'independent.json').open('x') as f:json.dump(res,f,indent=2);f.write('\n')
print(checks);assert res['all_passed']
(E/'attempts.json').write_text(json.dumps({'upstream_gc_c':'Exactcommit src/gc.c HTTP404 preserved in provenance; gc-stock/common available','absent_selectors':['libjulia:jl_free','libjulia-internal:ijl_free'],'resolution':'Actual exported jl_free in libjulia-internal; empty original asm outputs preserved','nm_filter':'Initial end-anchored regex missed versioned symbols; readelf symbol tables used'},indent=2)+'\n')
