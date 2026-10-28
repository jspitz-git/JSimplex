from pathlib import Path
import sys,json,shutil,ast
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-epsilon-bound-auxiliary/2026-10-28');sys.path.insert(0,str(D));import common_qualified as c
P=D/'remaining';Q=D/'remaining-qualified';c.need((P/'admission-rejection.json').exists(),'preserved independent rejection');c.unchanged();h=c.host(c.read('failed-close-host.json')['groups']);h['diagnostic_head']=c.git(['rev-parse','HEAD'],c.R);h['master_head']=c.git(['rev-parse','HEAD']);c.put('remaining-qualified-host.json',h)
shutil.copytree(P,Q,ignore=shutil.ignore_patterns('pins.json','host-before.json','host-seed.json','admission-rejection.json','__pycache__'))
c.put(str(Q/'host-before.json'),h);c.put(str(Q/'host-seed.json'),h)
con=json.loads((Q/'contract.json').read_text());con['command']=[x.replace(str(P),str(Q)) for x in con['command']];(Q/'contract.json').write_text(json.dumps(con,indent=2,sort_keys=True)+'\n')
s=(D/'audit-prefix.py').read_text().replace('auditor_bound_separately_to_admission=True,auditor_in_actual_launchpins=True','auditor_bound_to_original_admission=False,auditor_in_actual_launchpins=False,prefix_auditor_separately_bound_to_remaining_admission=True').replace("'audit-prefix.py','audit-qualified.py'","'audit-prefix-qualified.py','audit-prefix.py','audit-qualified.py'");(D/'audit-prefix-qualified.py').write_text(s)
shutil.copyfile(__file__,D/'remainder-qualified.py')
paths=set(json.loads((P/'pins.json').read_text())['inventory']);paths.update(str(p) for p in D.iterdir() if p.is_file());paths.update(str(p) for p in P.iterdir() if p.is_file());paths.update(str(p) for p in Q.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
c.put(str(Q/'pins.json'),dict(files=sorted(paths),trees=c.read('pins-qualified.json')['trees'],inputs=[str(Q/'grid.toml')],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)}))
import importlib.util
sp=importlib.util.spec_from_file_location('remainder_common',Q/'common.py');pc=importlib.util.module_from_spec(sp);sp.loader.exec_module(pc);pc.unchanged();pc.put('author-host.json',pc.host())
for p in Q.glob('*.py'):ast.parse(p.read_text())
print('qualifiedremaining author unchanged() PASS, noJulia; exactpins',len(paths))
