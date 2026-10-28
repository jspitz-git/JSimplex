from pathlib import Path
import json,sys,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-residual-pivot-crash/2026-10-28');sys.path.insert(0,str(D));import common as c
c.unchanged();s=(D/'fixtures-ready.jl').read_text();old='shape===:mixed&&isodd(i) ? -1 : 1)*((i*7)%n+1)//16';new='shape===:mixed&&isodd(density===:sparse ? div(i,4) : i) ? -1 : 1)*((i*7)%n+1)//16'
c.need(s.count(old)==1,'unique sparse mixed selector');s=s.replace(old,new).replace('@assert count(!iszero,column)==(density===:sparse ? div(n,4) : n)','@assert count(!iszero,column)==(density===:sparse ? div(n,4) : n)\n @assert n<8||shape!==:mixed||(any(signbit,column)&&any(x->x>0,column))')
(D/'fixtures-final.jl').write_text(s);(D/'driver-final.jl').write_text((D/'driver-ready.jl').read_text().replace('fixtures-ready.jl','fixtures-final.jl'))
for oldname,newname in [('common_ready.py','common_final.py'),('launch-ready.py','launch-final.py'),('audit-ready.py','audit-final.py')]:
 text=(D/oldname).read_text().replace('common_ready','common_final').replace('admission-ready.json','admission-final.json').replace('contract-ready.json','contract-final.json').replace('pins-ready.json','pins-final.json').replace("'audit-ready.py'","'audit-final.py'")
 if newname=='audit-final.py':text=text.replace('auditor_in_original_launchpins=False','auditor_in_actual_launchpins=True')
 (D/newname).write_text(text);compile(text,str(D/newname),'exec')
con=c.read('contract-ready.json');con['command']=[v.replace('driver-ready.jl','driver-final.jl') for v in con['command']];c.put('contract-final.json',con)
(D/'FINAL-HARNESS-NOTE.md').write_text('''# Final prelaunch harness
The original rejected admission and intermediate READY files/manifests remain byte-identical. Final sparse mixed directions alternate signs by surviving entry index; assertions require the stated nonzero counts and both signs for mixed cases. Candidate Reference/A/B/C source hashes remain unchanged. Grid1192cells/21456windows unchanged. Final auditor is included in the actual pins-final manifest and reports that membership explicitly. The prior scope erratum remains authoritative: PFI-only numerical update comparison, source audit of other shared helper consumers, required fresh HH/triangular/BG whole-file regressions before production. No Julia was run before this fix.
''')
shutil.copyfile(__file__,D/'final-seal.py');c.put('final-host.json',c.host());paths=set(c.read('pins-ready.json')['files']);paths.update(str(p) for p in D.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
c.put('pins-final.json',dict(files=sorted(paths),trees=c.read('pins.json')['trees'],inputs=[str(D/'grid.toml')],inventory={p:dict(resolved=str(Path(p).resolve(strict=True)),sha256=c.sha(p)) for p in sorted(paths)}))
print('final sealed',len(paths),'pins; noJulia, all original and ready files unchanged')
