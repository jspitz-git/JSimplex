"""Pure header layout arithmetic and saved instruction checks, no compiler/native call."""
from pathlib import Path
import json,re,hashlib
E=Path(__file__).resolve().parent;J=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu');h=J/'include/julia/jloptions.h';text=h.read_text();prefix=text.split('typedef struct {',1)[1].split('int8_t depwarn;',1)[0];offset=0;fields=[]
for raw in prefix.splitlines():
 line=raw.strip()
 if not line:continue
 name=re.search(r'(\w+);$',line).group(1)
 if '*' in line:size=align=8
 else:
  typ=line.split()[0];size=align={'int8_t':1,'int16_t':2,'int32_t':4}[typ]
 offset=(offset+align-1)//align*align;fields.append(dict(name=name,offset=offset,size=size));offset+=size
if offset!=116:raise RuntimeError('Unexpected pinned aarch64 JLOptions layout')
dis=(E/'world-age-runtime-disassembly.txt').read_text();hdr=(E/'world-age-header.txt').read_text()
checks={'depwarn_offset116':offset==116,'kind11_header':'PARTITION_KIND_BACKDATED_CONST = 0xb' in hdr,'temporary_compatibility_documented':'temporary compatibility' in hdr,'load_option116':'[x0, #116]' in dis,'generic_kind11_declaration':'mov\tx3, #0xb' in dis,'warn_then_return':'print_backdate_admonition.isra.0' in dis and 'b\t6bfd4' in dis}
if not all(checks.values()):raise RuntimeError(checks)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
with (E/'world-age-conditions.json').open('x') as f:json.dump(dict(all_passed=True,checks=checks,depwarn_offset=offset,aarch64_pointer_size=8,fields=fields,scope='Static installed header/instruction evidence, not captured future runtime options or binding partitions',sha256={str(p):sha(p) for p in [Path(__file__),h,E/'world-age-runtime.json',E/'world-age-runtime-disassembly.txt',E/'world-age-header.txt']}),f,indent=2);f.write('\n')
print('World-age condition checks PASS',len(checks),'noJulia')
