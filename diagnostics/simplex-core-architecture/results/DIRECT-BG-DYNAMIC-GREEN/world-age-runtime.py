"""Read installed ELF/header only; no dlopen, Julia process, parser or native function execution."""
from pathlib import Path
import subprocess,json,hashlib
E=Path(__file__).resolve().parent;J=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu');lib=J/'lib/julia/libjulia-internal.so';header=J/'include/julia/julia.h'
def save(p,s):
 with p.open('x') as f:f.write(s)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sections={}
for symbol in ['jl_get_binding_value_in_world','jl_eval_globalref','jl_f_getglobal','print_backdate_admonition.isra.0','jl_declare_constant_val3']:
 sections[symbol]=subprocess.check_output(['/usr/bin/objdump','-d','--disassemble='+symbol,str(lib)],text=True)
 if '<'+symbol+'>:' not in sections[symbol]:raise RuntimeError('Missing symbol '+symbol)
save(E/'world-age-runtime-disassembly.txt','\n'.join(sections.values()))
lines=header.read_text().splitlines();save(E/'world-age-header.txt','\n'.join(lines[671:755])+'\n')
with (E/'world-age-runtime.json').open('x') as f:json.dump(dict(scope='Installed ELF/header read-only; not a runtime trace or fresh Julia execution',commands=[['/usr/bin/objdump','-d','--disassemble='+s,str(lib)] for s in sections],sha256={str(p):sha(p) for p in [Path(__file__),lib,lib.resolve(),header,Path('/usr/bin/objdump'),E/'world-age-runtime-disassembly.txt',E/'world-age-header.txt']}),f,indent=2);f.write('\n')
print('Installed runtime five symbol excerpts saved, no library loaded or Julia executed')
