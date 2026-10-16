"""New closure review: read/hash/parse-only, no imported controls or Julia."""
from pathlib import Path
import hashlib,json,ast,subprocess
E=Path(__file__).resolve().parent;D=E.parent/'DIRECT-BG-DYNAMIC-DRIVER-PREPARATION';P=E.parent/'DIRECT-BG-DYNAMIC-RED';R=E.parents[3];run=D/'runs/green300'
def rd(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def blob(p):
 b=Path(p).read_bytes();return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def path(n):return Path(n) if Path(n).is_absolute() else R/n
checks=[]
def ck(v,n):
 assert v,n
 checks.append(n)
mapping={R/'diagnostics/simplex-core-architecture/STATUS.md':E/'STATUS.md.before-GREEN',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md':E/'roadmap.md.before-GREEN'}
ck(all(p.read_bytes()==q.read_bytes() for p,q in mapping.items()),'current continuation exact preserved bytes')
maps=[]
for name in ['closure.json','publication.json']:
 j=rd(P/name)
 for field,hasher in [('sha256',sha),('git_blobs',blob)]:
  for n,h in j.get(field,{}).items():
   p=path(n);q=mapping.get(p,p)
   ck(hasher(q)==h,'RED '+name+' '+field+' '+n) if p in mapping else None
   assert hasher(q)==h,(name,field,n)
   if p in mapping:maps.append([name,field,n,str(q)])
ck(len(maps)==6,'exact six prior RED continuation mappings')
post=rd(E/'postcheck.json');ck(post['all_passed'] is True and len(post['checks'])==15 and all(post['checks'].values()),'15 postchecks PASS')
ck(all(sha(n)==h for n,h in post['sha256'].items()),'postcheck bindings unchanged')
rv=rd(run/'result-review.json');ck(rv['accepted'] is True and rv['findings']==[] and all(sha(n)==h for n,h in rv['sha256'].items()),'accepted unchanged result')
ck(set(rv['sha256'])=={str(p) for p in run.rglob('*') if p.is_file() and p.name!='result-review.json'},'exact result review membership')
ck(all(sha(n)==h for n,h in rv['evidence_sha256'].items()),'independent result evidence')
close=(E/'close.py').read_text();pub=(E/'publish.py').read_text()
ast.parse(close);ast.parse(pub)
ck(close.index('h=full_host(')<close.index('S.write_text(') and "require(not h['matches']" in close,'fresh host gate precedes writes')
ck("require(len(maps)==6" in close and "old=mapping.get(target,target)" in close and "p.read_bytes()==old.read_bytes()" in close,'restricted exact mapping and preservation gates')
ck("set(review['sha256'])=={str(p) for p in paths}" in close and "and bindings(review)" in close,'exact closure review gate')
ck("git('diff','--cached','--name-only').splitlines()==names" in pub and "git('rev-parse',':'+n)==git('hash-object','--',n)" in pub,'final exact stage names and blobs')
ck("not same(names+['extra'])" in pub and "not same(names[:-1])" in pub and "not same(names+[names[0]])" in pub,'membership negative cases')
ck("require(actual==expected" in pub and "not git('diff','--name-only')" in pub,'exact evidence and no unstaged drift gates')
ck(not any((E/n).exists() for n in ['closure.json','publication.json','continuation-map.json','closure-host.json']),'closure/publication not executed')
report=(E/'REPORT.md').read_text();nexttext=(E/'continuation-next.md').read_text()
ck('not a benchmark' in report and 'source-derived entry counts' in report and 'Seven warnings' in report and 'No unnecessary new production work or retained memory' in report,'honest correctness work memory warning scope')
ck('offline preparation' in nexttext and 'No cost process or production integration' in nexttext,'bounded next continuation')
ck(subprocess.check_output(['git','diff','--name-only'],cwd=R,text=True)=='' and subprocess.check_output(['git','diff','--cached','--name-only'],cwd=R,text=True)=='','unchanged tracked/index before closure')
groups=set(rd(run/'posthost.json')['groups']);matches=[];unreadable=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  fields=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip();exe=''
  try:exe=str((p/'exe').resolve(strict=True))
  except PermissionError:unreadable.append(int(p.name))
  except FileNotFoundError:pass
  if int(fields[2]) in groups or int(fields[3]) in groups or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):matches.append({'pid':int(p.name),'comm':comm})
 except (FileNotFoundError,ProcessLookupError):pass
ck(not matches,'fresh full groups/sessions/comm/readable-exe no matches')
record={'accepted':True,'findings':[],'checks':checks,'count':len(checks),'maps':maps,'fresh_host':{'groups':sorted(groups),'matches':matches,'unreadable_exe_pids':unreadable,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()},'scope':'Independent closure read-only review; scripts not executed'}
with (E/'independent-closure-check.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps({'accepted':True,'checks':len(checks),'maps':len(maps),'groups':len(groups)}))
