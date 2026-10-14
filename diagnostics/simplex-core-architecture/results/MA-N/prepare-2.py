"""MA-N offline mechanical repair; never loads Julia or old generators."""
from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;M=D.parent/'MA-M'
def save(name,text):
 with (D/name).open('x') as f:f.write(text)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
changes={}
def transform(src,dst,edits):
 text=(M/src).read_text();original=text
 entries=[]
 for old,new,count in edits:
  if text.count(old)!=count:raise ValueError('unexpected multiplicity '+src+' '+old)
  text=text.replace(old,new);entries.append(dict(old=old,new=new,count=count))
 
 if (D/dst).exists():
  if dst!='driver.jl' or (D/dst).read_text()!=text:raise ValueError('existing output differs')
 else:save(dst,text)
 inverse=text
 for e in reversed(entries):
  if inverse.count(e['new'])!=e['count']:raise ValueError('inverse multiplicity '+src)
  inverse=inverse.replace(e['new'],e['old'])
 if inverse!=original:raise ValueError('inverse mismatch '+src)
 changes[dst]=dict(source=str(M/src),source_sha256=sha(M/src),sha256=sha(D/dst),edits=entries)
transform('driver-reviewed.jl','driver.jl',[("# MA-M single frozen qualification","# MA-N offline-prepared qualification",1),('"MAL_TRACE[].scratch == 1"','"(MAL_TRACE[]).scratch == 1"',1)])
transform('audit_reviewed.py','audit.py',[("MA-M auditor","MA-N auditor",1),("'pins-reviewed.json'","'pins.json'",2),("'commands-reviewed.json'","'commands.json'",1),("'admission-review-final.json'","'admission-review.json'",1),("'MAL_TRACE[].scratch == 1'","'(MAL_TRACE[]).scratch == 1'",1)])
# Path-only bindings; source identity and resource behavior remain unchanged.
s=(M/'launcher-reviewed.py').read_text();edits=[]
for old,new in [('MA-M sequence','MA-N prepared sequence'),('import audit_reviewed as audit','import audit'),("'launcher-reviewed.py'","'launcher.py'"),("'pins-reviewed.json'","'pins.json'"),("'admission-review-final.json'","'admission-review.json'"),("'required-paths-reviewed.json'","'required-paths.json'"),("'commands-reviewed.json'","'commands.json'")]:edits.append((old,new,s.count(old)))
transform('launcher-reviewed.py','launcher.py',edits)
save('guard.py',(M/'guard.py').read_text());(D/'env').mkdir()
for n in ('Project.toml','Manifest.toml'):(D/'env'/n).write_bytes((M/'env'/n).read_bytes())
commands=json.loads((M/'commands-reviewed.json').read_text())
for i,cmd in commands.items():
 cmd[-3]=str(D/'driver.jl');cmd[-1]=str(D/f'run-{i}')
save('commands.json',json.dumps(commands,indent=2)+'\n')
save('inverse.json',json.dumps(changes,indent=2)+'\n')
print('Prepared exact repair and path-only copies; no execution')
