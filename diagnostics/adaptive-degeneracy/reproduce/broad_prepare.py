"""Prepare a fixed, expanded corpus without modifying the source MPS files."""
from pathlib import Path
import gzip,hashlib,json,sys
root=Path(sys.argv[1]).resolve(); root.mkdir(parents=True,exist_ok=True)
netlib='degen2 degen3 cycle stocfor1 stocfor2 scsd1 scsd6 scsd8 ship04s ship08s ship12s pilot4 pilotnov 25fv47 80bau3b wood1p woodw bandm boeing1 capri recipe scorpion'.split()
miplib='air03 air04 air05 mod010 p0201 blend2 markshare1 markshare2 nw04 misc07 10teams'.split()
lines=[]
for collection,names in [('NetLib',netlib),('MIPLib',miplib)]:
 for name in names:
  source=Path('/home/jspitz')/collection/(name+('.mps.gz' if collection=='MIPLib' else '.mps'))
  assert source.resolve().name.lower() not in ('big.mps','largo.mps','anymod.mps')
  raw=source.read_bytes();content=gzip.decompress(raw) if source.suffix=='.gz' else raw
  dest=root/(collection.lower()+'-'+name+'.mps');dest.write_bytes(content)
  entry={'id':collection.lower()+'/'+name,'original_path':str(source),'path':str(dest),
         'sha256':hashlib.sha256(content).hexdigest(),'source_sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(content)}
  lines.append('[[cases]]\n'+'\n'.join(k+' = '+json.dumps(v) for k,v in entry.items())+'\n')
(root/'inputs.toml').write_text('\n'.join(lines))
print('Prepared',len(lines),'models:',root/'inputs.toml')
