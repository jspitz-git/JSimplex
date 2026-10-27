from pathlib import Path
import sys,json,subprocess,hashlib,os
sys.dont_write_bytecode=True;os.environ['GIT_OPTIONAL_LOCKS']='0'
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-bounds-norm-infeasibility/2026-10-27');sys.path.insert(0,str(D));import common as c
load=lambda n:json.loads((D/n).read_text())
git=lambda a:subprocess.check_output(['/usr/bin/git','-C',str(c.M),*a])
g=lambda a:git(a).decode().strip()
co=load('production-commit.json');st=load('staged-tree.json');inv=load('source-inverse.json');target=co['commit'];base=c.TARGET
assert target=='ce5d4a74019e0dc2e656d08161641c498b159e7b' and base=='9d29b1f0aa21932217b03ca7b35dd91281baaae6'
assert g(['rev-list','--parents','-n','1',target]).split()==[target,base]
assert g(['rev-parse',target+'^{tree}'])==co['tree']==st['tree']
assert co['names']==st['names']==inv['names'] and len(co['names'])==4
assert co['blobs']==st['blobs'] and st['sha256']==inv['candidate_sha256']
assert g(['rev-parse',co['branch']])==target and co['parent']==st['base']==base
assert g(['branch','--show-current'])=='master' and g(['rev-parse','HEAD'])==g(['rev-parse','master'])==g(['rev-parse','origin/master'])==base
assert g(['ls-remote','origin','refs/heads/master']).split()[0]==base
assert g(['diff-tree','--no-commit-id','--name-only','-r',target]).splitlines()==co['names']
check=subprocess.run(['/usr/bin/git','-C',str(c.M),'diff-tree','--check',base,target],capture_output=True,text=True);assert check.returncode==0 and not check.stdout and not check.stderr
for n in co['names']:
 data=git(['show',target+':'+n]);assert data==(D/'GREEN'/n).read_bytes()
 assert hashlib.sha256(data).hexdigest()==inv['candidate_sha256'][n]
 assert g(['rev-parse',target+':'+n])==co['blobs'][n]
def tree(rev):
 return {row.split(b'\t',1)[1].decode():row.split(b'\t',1)[0].decode() for row in git(['ls-tree','-r','-z',rev]).split(b'\0') if row}
a,b=tree(base),tree(target);assert set(b)==set(a)|{'test/generic_bounds_norm_infeasibility_tests.jl'}
assert {n for n in set(a)|set(b) if a.get(n)!=b.get(n)}==set(co['names'])
assert all(b[n].startswith('100644 blob ') for n in co['names'])
assert git(['show','-s','--format=%B',target]).decode().rstrip() == (D/'commit-message.txt').read_text().rstrip()
for n in ['production-review.json','GREEN-run/result-review.json','publication-preparation-reviewed.json']:
 r=load(n);assert r['accepted'] and not r['findings']
 for p,h in r['bindings'].items():assert c.sha(p)==h
c.unchanged();extra=set()
for p in D.glob('*-run/audit-host.json'):extra.update(json.loads(p.read_text())['groups'])
h=c.host(extra);assert len(h['groups'])==647
c.put('independent-commit-host.json',h)
with (D/'independent-commit-review.py').open('x') as f:f.write(Path(__file__).read_text())
report=f'''# Independent actual commit review

Accepted actual commit `{target}`, tree `{co['tree']}`, with sole parent `{base}` for local fast-forward followed by fresh actual-MASTER qualification. No findings. Master, HEAD, origin/master and the live remote master are still the exact parent; the reviewed candidate branch points to the new commit. This does not attest integration, MASTER tests or publication.

I inspected the actual Git objects, not only the staging manifest. Actual complete commit bytes and each blob match the accepted GREEN candidate, source-inverse record and private staged-tree record for all four paths: src/primal_simplex.jl, src/dual_simplex.jl, test/generic_bounds_norm_infeasibility_tests.jl and test/runtests.jl. Full recursive parent/commit tree comparison shows exactly those changes and only the one intended new path; every other tree entry is identical. All changed entries have ordinary 100644 blob modes. The actual sole parent, tree, branch target, commit message and complete diff membership agree with the saved record. Git diff-tree --check passes with no output.

Production numerical/work/memory review and the independent GREEN result remain fully bound and current. GREEN passed 314,009/314,009 ordinary assertions in the specified 51 whole files. The actual source therefore has the reviewed private comparison zero, lazy positive-overflow cap and exact-zero/conditional-magnitude certificate changes, with no additional implementation change. No unnecessary production scan, solve, copy, conversion, invariant pass or retained numerical cache is introduced; readiness-branch and cold method-metadata costs remain acknowledged. Short whole-function allocation evidence does not establish broad solver timing or native-memory savings.

Fresh observation of 647 historical groups and sessions/start ticks/commands/boot found no Julia, and protected refs, files, real indexes and inherited environment remain unchanged. Only the existing exact unrelated-WSL identity allowance applies. This reviewer ran read-only Git and Python checks and wrote exclusive new reviewer artifacts; no Julia or Git mutation occurred. Fresh actual-MASTER execution with the same 51 files and frozen GREEN total is still mandatory before normal push.
'''
with (D/'COMMIT-REVIEW.md').open('x') as f:f.write(report)
paths=[D/n for n in ['production-commit.json','staged-tree.json','source-inverse.json','commit-message.txt','production-review.json','GREEN-run/result-review.json','GREEN-run/audit.json','publication-preparation-reviewed.json','COMMIT-REVIEW.md','independent-commit-host.json','independent-commit-review.py']]+[D/'GREEN'/n for n in co['names']]
c.put('commit-review.json',dict(accepted=True,findings=[],commit=target,parent=base,tree=co['tree'],names=co['names'],blobs=co['blobs'],master_still_parent=True,actual_tree_entries_verified=len(b),Julia_executed=False,Git_mutated=False,groups=len(h['groups']),bindings={str(p):c.sha(p) for p in paths}))
print('accepted actual commit',target,'exact4paths',len(b),'treeentries; noJulia/Gitmutation')
