from pathlib import Path
import json,hashlib,subprocess,time
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');D=R/'diagnostics/simplex-core-architecture';E=D/'results/S4-N'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
a=json.loads((E/'source-contract.json').read_text());m=json.loads((D/'results/S4-M/cost-1-pins.json').read_text())
checks={'initial_61_current':all(sha(p)==h for p,h in a['sha256'].items()),'all_M_inventory_current':all(sha(p)==v['sha256'] for p,v in m['inventory'].items()),'M_inventory_count554':len(m['inventory'])==554}
inv={p:sha(p) for p in sorted(set(a['sha256'])|set(m['inventory']))}
checks['production_master_identical']=subprocess.check_output(['git','diff','master','--','src','test','.github'],cwd=R)==b''
checks['native_binary_matches_M']=all(inv[p]==v['sha256'] for p,v in m['inventory'].items() if p.endswith(('libumfpack.so.6.3.5','libsuitesparseconfig.so.7.10.1')))
res={'checks':checks,'all_passed':all(checks.values()),'sha256':inv,'scope':'Independent full current read-time inventory, including M source/test tree files. No new launch. Initial 61-entry inventory was explicit files only; retained unchanged.'}
with (E/'independent-full.json').open('x') as f:json.dump(res,f,indent=2);f.write('\n')
print(len(inv),len(checks),res['all_passed']);assert res['all_passed']
