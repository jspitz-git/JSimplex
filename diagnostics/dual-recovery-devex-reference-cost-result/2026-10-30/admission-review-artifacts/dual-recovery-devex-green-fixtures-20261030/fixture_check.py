"""Bounded text audit of the exact frozen GREEN test graph; never executes Julia.
All admitted call sites are single-line literal includes or read_mps(joinpath(
@__DIR__, literal...)); the one exact endpoint output call is explicitly exempt.
Unknown/dynamic/changed call sites fail closed. This is not a general Julia parser
or a claim about dynamically created dependencies, package initialization or FFI.
"""
from pathlib import Path
import hashlib,json,re,sys
CALL=re.compile(r'\b(include|read_mps|open|read|readlines|readdlm|deserialize|load|parsefile)\s*\(')
STRING=r'"(?:[^"\\]|\\.)*"'
def need(v,m):
 if not v:raise ValueError(m)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def local(root,base,name):
 p=base/Path(name)
 need(not Path(name).is_absolute() and '..' not in Path(name).parts,'escaping path '+name)
 need(p.resolve().is_relative_to(root.resolve()),'escaping path '+name)
 return p
def arguments(line,start):
 depth=1;quoted=False;escaped=False
 for j in range(start,len(line)):
  c=line[j]
  if quoted:
   if escaped:escaped=False
   elif c=='\\':escaped=True
   elif c=='"':quoted=False
  elif c=='"':quoted=True
  elif c=='(':depth+=1
  elif c==')':
   depth-=1
   if depth==0:return line[start:j]
 raise ValueError('unsupported multiline IO/include call')
def check(root,m):
 root=Path(root);seen=set();fixtures=set();queue=[m['entry']];edges=[];uses=[];outputs=[]
 for rel,digest in m['programs'].items():
  p=local(root,root,rel);need(p.is_file(),'missing program '+rel);need(sha(p)==digest,'program hash '+rel)
 while queue:
  rel=queue.pop(0)
  if rel in seen:continue
  need(rel in m['programs'],'unlisted include '+rel);seen.add(rel);p=root/rel
  for number,line in enumerate(p.read_text().splitlines(),1):
   # Exact admitted graph contains no IO-like tokens hidden in string literals,
   # multiline expressions or block comments; source hashes bind that manual audit.
   if line.lstrip().startswith('#'):continue
   for found in CALL.finditer(line):
    name=found.group(1);args=arguments(line,found.end()).strip();site=dict(program=rel,line=number,call=name,arguments=args)
    if name=='include':
     need(re.fullmatch(STRING,args) is not None,'unsupported include '+str(site))
     dest=local(root,p.parent,json.loads(args));target=dest.relative_to(root).as_posix()
     need(dest.is_file(),'missing include '+target);queue.append(target);edges.append(site|dict(target=target))
    elif name=='read_mps':
     match=re.fullmatch(r'joinpath\s*\(\s*@__DIR__\s*,\s*(.*?)\s*\)',args)
     need(match is not None,'unsupported input '+str(site))
     tail=match.group(1);strings=re.findall(STRING,tail)
     need(strings and re.sub(STRING,'',tail).replace(',','').strip()=='','unsupported input '+str(site))
     dest=local(root,p.parent,str(Path(*[json.loads(s) for s in strings])));target=dest.relative_to(root).as_posix()
     need(target in m['fixtures'],'fixture inventory '+target);need(dest.is_file(),'missing fixture '+target)
     need(sha(dest)==m['fixtures'][target],'fixture hash '+target);fixtures.add(target);uses.append(site|dict(target=target))
    else:
     need(site in m['output_calls'],'unclassified IO '+str(site));outputs.append(site)
 need(seen==set(m['programs']),'unreachable program inventory')
 need(fixtures==set(m['fixtures']),'unused fixture inventory')
 need(outputs==m['output_calls'],'output-call classification')
 return dict(accepted=True,scope='offline exact-source test-graph dependencies only; no Julia or runtime qualification',program_count=len(seen),fixture_count=len(fixtures),include_edges=len(edges),includes=edges,fixture_uses=uses,classified_outputs=outputs,program_hashes=m['programs'],fixture_hashes=m['fixtures'])
if __name__=='__main__':
 need(len(sys.argv)==3,'usage: fixture_check.py ROOT MANIFEST')
 try:
  report=check(Path(sys.argv[1]),json.loads(Path(sys.argv[2]).read_text()))
  print(json.dumps(report,indent=2))
 except ValueError as error:
  print(json.dumps(dict(accepted=False,error=str(error))),file=sys.stderr);raise SystemExit(1)
