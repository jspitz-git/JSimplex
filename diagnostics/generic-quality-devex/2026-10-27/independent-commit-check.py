from pathlib import Path
import subprocess,json,hashlib,os,datetime
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-devex/2026-10-27');M=Path('/home/jspitz/JSimplex.jl');S=D/'GREEN'
def need(x,m):
 if not x:raise RuntimeError(m)
def read(p):return json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def git(*a):return subprocess.check_output(['git','-C',str(M),*a],env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'))
def g(*a):return git(*a).decode().strip()
def put(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
co=read(D/'production-commit.json');staged=read(D/'staged-tree.json');inv=read(D/'source-inverse.json');target=co['commit'];base=co['parent'];names=co['names']
need(target=='ca64312f7f74b1d7bec047718399f229674b3e1d' and base=='7e306e24f064a8aa214bc88379e059def77661ab','target/base')
need(g('rev-list','--parents','-n','1',target).split()==[target,base],'sole parent')
need(g('rev-parse',target+'^{tree}')==co['tree']==staged['tree'],'actual tree')
need(g('rev-parse',co['branch'])==target,'branch')
for ref in ['HEAD','master','origin/master']:need(g('rev-parse',ref)==base,'unintegrated ref '+ref)
need(g('branch','--show-current')=='master','master branch')
def tree(ref):
 out={}
 for x in git('ls-tree','-rz',ref).split(b'\0'):
  if x:
   left,name=x.split(b'\t',1);out[name.decode()]=tuple(left.decode().split())
 return out
old,new=tree(base),tree(target)
need(sorted(n for n in old.keys()|new.keys() if old.get(n)!=new.get(n))==names==staged['names']==inv['names'],'actual exact changed names')
actual_files={};source_count=0
# Read all committed source/test blobs in one cat-file subprocess, rather than trusting only the changed paths.
selected={n:v for n,v in new.items() if n.startswith(('src/','test/'))};need(set(selected)=={str(p.relative_to(S)) for directory in ['src','test'] for p in (S/directory).rglob('*') if p.is_file()},'complete committed/tested membership')
proc=subprocess.Popen(['git','-C',str(M),'cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'))
for n,(mode,kind,oid) in selected.items():
 need(kind=='blob' and mode=='100644','ordinary source/test file '+n);proc.stdin.write((oid+'\n').encode());proc.stdin.flush();header=proc.stdout.readline().decode().split();need(header[:2]==[oid,'blob'],'blob header');data=proc.stdout.read(int(header[2]));need(proc.stdout.read(1)==b'\n','blob delimiter');h=hashlib.sha256(data).hexdigest();need(h==sha(S/n)==inv['whole_stage'][n],'actual committed/tested bytes '+n);actual_files[n]=h;source_count+=1
proc.stdin.close();need(proc.wait()==0,'cat-file exit')
for n in names:
 need(new[n][2]==co['blobs'][n]==staged['blobs'][n],'actual changed blob '+n);need(actual_files[n]==inv['candidate_sha256'][n]==staged['sha256'][n],'actual changed content '+n)
# Whole committed source inverse to actual parent, independently reconstructed.
changes=read(D/'changes.json')
for n in names:
 if n.startswith('src/'):
  s=git('show',target+':'+n).decode()
  for key in ['C','B','A2','A1']:
   x=changes[key]
   if n=='src/'+x['file']:need(s.count(x['new'])==1,'inverse unique '+key);s=s.replace(x['new'],x['old'])
  need(s.encode()==git('show',base+':'+n)==(D/'baseline'/n).read_bytes(),'entire actual source inverse '+n)
need(git('show',target+':test/runtests.jl').decode().replace('    include("generic_quality_devex_tests.jl")\n','',1).encode()==git('show',base+':test/runtests.jl'),'only new ordinary include')
subprocess.run(['git','-C',str(M),'diff-tree','--check',base,target],check=True)
for file in [D/'production-review.json',D/'GREEN-run/result-review.json',D/'publication-preparation-reviewed.json']:
 r=read(file);need(r['accepted'] and r['findings']==[],'required review')
 for n,h in r['bindings'].items():need(sha(Path(n))==h,'review binding '+n)
for group in read(D/'protected-before.json').values():
 for n,h in group.items():need(sha(Path(n))==h,'protected file/index '+n)
need(not g('diff','--name-only','HEAD','--','src','test','Project.toml'),'production untouched')
report=f'''Verdict: actual commit {target} ACCEPTED for local fast-forward, with no unresolved findings. This is actual-object review, not approval to bypass fresh actual-master qualification.

Git records exactly one parent, {base}, and tree {co['tree']}. The complete parent/candidate Git trees differ in exactly the five previously reviewed paths. Each actual changed blob matches staged-tree.json and production-commit.json. All {source_count} committed source/test blobs were read through git cat-file and SHA256-compared with the complete tested GREEN tree; membership and ordinary file modes match. Reversing the three committed production source changes reproduces every byte of the actual parent files. All previous tests are unchanged; runtests adds only the new ordinary include; the new 487-line test is exactly the RED/GREEN-qualified file. Git diff-tree --check passes.

The production work/memory review applies to these exact blobs: A removes unused BigFloat negations at existing magnitude sites; B retains ordered arithmetic, both x reads, all range/precision/alias/finiteness checks and generic fallback, with at most one call-private comparison limit; C preserves the fresh product and creates a fresh overflow cap only for positive infinity. No unnecessary scans, basis solves, copies, conversions or persistent roots were introduced. Local allocation/work savings have the measured evidence already reviewed; three slower quality timing cells and missing end-to-end/x64/native-free coverage remain disclosed. All owner, sign, precision, callback boundary, numerical safeguard and original threshold semantics are identical to the accepted production stage.

GREEN's independent raw result remains bound and accepted: 186622/186622 across 34 ordinary files with no failures/errors/broken/skips. All required review bindings, protected files and both real indexes remain unchanged. Local HEAD/master/origin/master still point to the parent and the dedicated codex branch points to this commit. No Julia, source, index or ref mutation was performed by this review. Local ff-only integration may proceed; publication still requires separately admitted fresh actual-master all-pass evidence and complete tested-tree/preservation checks. The previous allocation exception is not transferred.
'''
with (D/'COMMIT-REVIEW.md').open('x') as f:f.write(report)
files=[D/n for n in ['production-commit.json','staged-tree.json','commit-host.json','production-review.json','PRODUCTION-REVIEW.md','GREEN-run/result-review.json','GREEN-run/RESULT-REVIEW.md','source-inverse.json','changes.json','publication-preparation-reviewed.json','commit-integrate-publish.py','publication_checks.py','COMMIT-REVIEW.md','independent-commit-check.py']]
put(D/'commit-review.json',dict(accepted=True,findings=[],commit=target,parent=base,tree=co['tree'],names=names,committed_source_test_files=source_count,actual_commit_sha256=actual_files,review=str(D/'COMMIT-REVIEW.md'),bindings={str(p):sha(p) for p in files}))
print(json.dumps(dict(accepted=True,commit=target,source_test_files=source_count,sha256=sha(D/'commit-review.json'))))
