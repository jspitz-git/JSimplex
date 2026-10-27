from pathlib import Path
import hashlib,json,subprocess,importlib.util,sys
sys.dont_write_bytecode=True
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-stagnation-unit-seed/2026-10-27');M=Path('/home/jspitz/JSimplex.jl')
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(x,m):
 if not x:raise AssertionError(m)
def put(p,v):
 with Path(p).open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
def git(*args):return subprocess.check_output(['git','-C',str(M),*args])
co=read(D/'production-commit.json');target=co['commit'];base=co['parent'];inv=read(D/'source-inverse-final.json');stage=read(D/'staged-tree.json')
need(target=='3d3787b24c802043caf8a931b4d142b62c961940' and base=='c01900c2dff3de465846ae44333903889c867626','exact IDs')
need(git('rev-list','--parents','-n','1',target).decode().split()==[target,base],'sole parent')
need(git('rev-parse',co['branch']).decode().strip()==target,'new branch exact')
need(git('rev-parse',target+'^{tree}').decode().strip()==co['tree']==stage['tree'],'actual tree')
names=git('diff-tree','--no-commit-id','--name-only','-r',base,target).decode().splitlines();need(names==co['names']==inv['names']==stage['names'] and len(names)==4,'exact four names')
subprocess.run(['git','-C',str(M),'diff-tree','--check',base,target],check=True)
def entries(ref):
 out={}
 for raw in git('ls-tree','-r','-z',ref).split(b'\0'):
  if raw:
   metadata,name=raw.split(b'\t',1);out[name.decode()]=metadata.decode().split()
 return out
oldtree=entries(base);newtree=entries(target)
need(set(newtree)-set(oldtree)=={'test/generic_stagnation_unit_seed_tests.jl'} and not(set(oldtree)-set(newtree)),'only new test membership')
for n,v in newtree.items():
 if n not in names:need(v==oldtree[n],'untouched complete Git tree entry '+n)
for n in names:need(newtree[n]==['100644','blob',co['blobs'][n]] and co['blobs'][n]==stage['blobs'][n],'actual commit mode/blob '+n)
tracked=[n for n in newtree if n.startswith(('src/','test/')) or n=='Project.toml']
need(set(tracked)==set(inv['whole_stage'])-{'Manifest.toml','LocalPreferences.toml'},'complete committed production membership')
p=subprocess.Popen(['git','-C',str(M),'cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
for n in tracked:
 p.stdin.write((target+':'+n+'\n').encode());p.stdin.flush();h=p.stdout.readline().decode().split();data=p.stdout.read(int(h[2]));need(p.stdout.read(1)==b'\n','git record')
 need(data==(D/'GREEN-final'/n).read_bytes() and hashlib.sha256(data).hexdigest()==inv['whole_stage'][n],'actual full committed source/test bytes '+n)
p.stdin.close();need(p.wait()==0,'Git batch exit')
for n in ['formatting-review.json','production-review-2.json','GREEN-2-run/result-review.json','publication-preparation-final.json']:
 review=read(D/n);need(review['accepted'] is True and review['findings']==[],'accepted prerequisite '+n)
 for path,h in review['bindings'].items():need(sha(path)==h,'bound prerequisite '+path)
qualified=read(D/'GREEN-2-run/result-review.json');need(qualified['passed']==qualified['total']==257423 and qualified['whole_files']==45,'qualified original count')
a=(D/'GREEN-2/src/simplex.jl').read_bytes();b=(D/'GREEN-final/src/simplex.jl').read_bytes();need(a==b+b'\n' and b.endswith(b'end\n'),'format-only qualification')
spec=importlib.util.spec_from_file_location('commit_review_common',D/'common_reviewed.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c);c.unchanged();host=c.host(read(D/'GREEN-2-run/audit-host.json')['groups']);need(len(host['groups'])==617,'full historical group/session set');put(D/'commit-review-host.json',host)
need(git('branch','--show-current').decode().strip()=='master' and git('rev-parse','HEAD').decode().strip()==base,'actual master still original')
need(git('ls-remote','origin','refs/heads/master').decode().split()[0]==base,'remote still original')
(D/'actual-commit-review-checker.py').write_bytes(Path(__file__).read_bytes())
put(D/'actual-commit-review-checks.json',dict(accepted=True,commit=target,parent=base,complete_git_tree_files=len(newtree),committed_production_files=len(tracked),exact_names=names,all_other_git_modes_blobs_unchanged=True,diff_check_passed=True,protected_files_indexes_unchanged=True,historical_groups_and_sessions=617,no_Julia=True))
paths=[D/n for n in ['production-commit.json','staged-tree.json','source-inverse-final.json','formatting-review.json','production-review-2.json','GREEN-2-run/result-review.json','GREEN-2-run/contract.json','publication-preparation-final.json','commit-integrate-publish-final.py','actual-commit-review-checker.py','actual-commit-review-checks.json','commit-review-host.json']]+[D/'GREEN-final'/n for n in names]
put(D/'commit-review.json',dict(accepted=True,findings=[],commit=target,parent=base,scope='Independent actual Git commit review; authorizes only guarded local ff-only integration to this exact commit and preparation of fresh actual-master admission. No push authorization until fresh MASTER result review.',required_MASTER_total=257423,required_whole_files=45,unnecessary_added_production_work_or_memory_found=False,declined_to_judge=[],bindings={str(p):sha(p) for p in paths}))
(D/'COMMIT-REVIEW.md').write_text(f'''# Independent actual commit review

No findings. Accept actual commit `{target}` with sole parent `{base}` for the separately guarded local ff-only integration. Push remains gated on fresh actual-master admission and independent all-pass result review: exactly the same 45 whole files and frozen 257423 passes.

Inspected the actual Git objects, rather than relying on staged claims. The commit changes exactly four paths: src/primal_simplex.jl, src/simplex.jl, the new ordinary regression and its runtests include. Verified every committed src/test/Project byte against the complete final stage, actual tree ID and four blob IDs/modes, and all other Git tree entries/modes/blobs unchanged from the sole baseline parent. The new regression is the only added tree member. Actual diff-tree whitespace check passes. The final source differs from the accepted GREEN-2 source only by the independently qualified final LF removal; every numerical token/body, test and threshold is unchanged.

The method loading order correction is retained: the concrete BigFloat stagnation signature follows SimplexWorkspace in simplex.jl; original simplex_stalling.jl is unchanged. B/C preserve their reviewed dispatch, rounding, scan/write order and owners. The fresh actual commit introduces no additional numerical work, allocation or retained memory beyond the accepted and measured source. The scoped work/memory conclusion remains no unnecessary added production cost; no broader speedup or native-memory claim is implied.

Verified prior source/formatting/GREEN result and helper bindings, new codex ref, unchanged actual master/tracking/remote baseline, actual protected user files/indexes and fresh 617 historical process groups AND sessions with boot/start ticks/commands and no Julia. No Julia, old validator, Git write, integration or publication was performed by this review. Original rejected runs and precommit failure remain preserved. Declined-to-judge behaviors: none; broader/full-suite/x64/public-trajectory and native-retention coverage remain open.
''')
print(json.dumps({'accepted':True,'commit':target,'complete_git_tree_files':len(newtree),'committed_production_files':len(tracked),'next':'guarded local ff-only; fresh MASTER before push'}))
