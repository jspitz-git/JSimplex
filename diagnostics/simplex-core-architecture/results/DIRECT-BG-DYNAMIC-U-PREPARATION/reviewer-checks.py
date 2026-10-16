"""Independent new read-only byte/source checks. Never loads Julia or old helpers."""
from pathlib import Path
import hashlib,json,subprocess
E=Path(__file__).resolve().parent;R=E.parents[3];C=R/'diagnostics/direct-bg-dynamic-upper/reproduce';P=E.parent/'DIRECT-BG-DYNAMIC-U-PLAN'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(p):return json.loads(p.read_text())
def need(v,m):
 if not v:raise RuntimeError(m)
checks={}; mappings=[]; overlays=[]
for manifest,candidate,tests in [('overlay.json','slot-upper.jl','slot-upper-tests.jl'),('overlay-reviewed.json','slot-upper-reviewed.jl','slot-upper-tests-reviewed.jl')]:
 o=rd(E/manifest);O=Path(o['path']);S=Path(o['source'])
 names={str(p.relative_to(O)) for p in O.rglob('*') if p.is_file()};sources={str(p.relative_to(S)) for p in S.rglob('*') if p.is_file()}
 need(len(names)==77 and names==set(o['sha256']),'overlay names')
 need(len(sources)==75 and sources==set(o['baseline']),'source names')
 need(names==sources|{'src/slot-upper.jl','test/slot-upper-tests.jl'},'only additions')
 for n,h in o['baseline'].items():
  need(sha(S/n)==h,'source hash')
  if n!='src/JSimplex.jl':need(sha(O/n)==h,'copied original hash')
 need(all(sha(O/n)==h for n,h in o['sha256'].items()),'overlay hashes')
 insertion=b'\ninclude("slot-upper.jl")\n\nend\n';root=(O/'src/JSimplex.jl').read_bytes();source=(S/'src/JSimplex.jl').read_bytes()
 need(root.endswith(insertion) and root.count(b'include("slot-upper.jl")')==1 and root[:-len(insertion)]+b'\nend\n'==source,'root inverse')
 need(sha(S/'src/JSimplex.jl')==o['root_before_sha256'],'root before')
 need((O/'src/slot-upper.jl').read_bytes()==(C/candidate).read_bytes() and (O/'test/slot-upper-tests.jl').read_bytes()==(C/tests).read_bytes(),'candidate tests')
 need(not O.is_symlink() and not S.is_symlink() and not any(p.is_symlink() for b in (O,S) for p in b.rglob('*')),'symlinks')
 overlays.append(dict(manifest=manifest,members=77,source_members=75,full_hashes=True,root_inverse=True));checks[manifest+'_full_membership_hash_inverse']=True
for record in ['entry.json','preparation-pins.json','preparation-pins-reviewed.json','offline-check.json','offline-check-reviewed.json','review-fix.json']:
 need(all(sha(Path(n))==h for n,h in rd(E/record)['sha256'].items()),'record hashes '+record)
 checks[record+'_bindings']=True
for record in ['review-initial.json','review-initial-supplement.json']:
 for n,h in rd(E/record)['sha256'].items():
  path=Path(n);resolved=path
  if path.parent==E and path.name in ['REPORT.md','progress.md','publication.py']:resolved=E/(path.name+'.before-review')
  need(sha(resolved)==h,'initial review mapping '+n)
  if resolved!=path:mappings.append(dict(record=record,key=n,sha256=h,preserved=str(resolved)))
 checks[record+'_bindings_reconciled']=True
first=rd(E/'tests-first.json');need(first['candidate_absent'] is True and sha(E/'slot-upper-tests.jl.before-author-check')==first['tests_sha256'],'tests first')
need(sha(C/'slot-upper-tests.jl')!=first['tests_sha256'] and sha(C/'slot-upper-tests-reviewed.jl')!=first['tests_sha256'],'tests-first mapping uniqueness')
mappings.append(dict(record='tests-first.json',key='tests_sha256',sha256=first['tests_sha256'],preserved=str(E/'slot-upper-tests.jl.before-author-check')));checks['tests_first_preserved_only']=True
for record in ['closure.json','publication.json']:
 for live,before in [('diagnostics/simplex-core-architecture/STATUS.md','STATUS.md.before-Task1'),('docs/superpowers/plans/2026-10-11-simplex-core-architecture.md','roadmap.md.before-Task1')]:
  h=rd(P/record)['sha256'][live];need(sha(E/before)==h and sha(R/live)==h,'prior continuation')
  mappings.append(dict(record=str(P/record),key=live,sha256=h,preserved=str(E/before)))
checks['four_prior_continuation_bindings']=True
old=(C/'slot-upper.jl').read_text();new=(C/'slot-upper-reviewed.jl').read_text()
expected=old.replace('    fill!(fresh,zero(T))\n    copyto!(fresh,1,old,1,length(old))','    copyto!(fresh,1,old,1,length(old))\n    for i in length(old)+1:C\n        fresh[i]=zero(T)\n    end')
need(new==expected and new!=old,'exact suffix-only amendment');checks['exact_candidate_amendment']=True
oldtests=(C/'slot-upper-tests.jl').read_text();newtests=(C/'slot-upper-tests-reviewed.jl').read_text();start=newtests.index('    # Success with deliberately dirty fresh buffers:');end=newtests.index('    for failat in 1:7\n',start)
need(newtests[:start]+newtests[end:]==oldtests,'exact test addition');need('return fill(T(77),n)' in newtests[start:end] and 'calls[]==7' in newtests[start:end],'dirty allocation oracle');checks['exact_test_amendment']=True
need(len(rd(E/'offline-check.json')['checks'])==19 and len(rd(E/'offline-check-reviewed.json')['checks'])==19,'check count');need('18 source-text' in rd(E/'offline-check.json')['scope'] and '19 source-text' in rd(E/'offline-check-reviewed.json')['scope'],'count annotation');checks['count_erratum_preserves_original']=True
canonical=rd(E/'canonical.json');need(canonical['candidate']=='slot-upper-reviewed.jl' and canonical['tests']=='slot-upper-tests-reviewed.jl' and canonical['overlay']=='overlay-reviewed.json' and canonical['author_checks']=='offline-check-reviewed.json' and canonical['pins']=='preparation-pins-reviewed.json' and canonical['prepare']=='prepare-reviewed.py','canonical');checks['canonical_successors']=True
need((R/'.superpowers/sdd/2026-10-16-direct-bg-dynamic-upper/progress.md').read_bytes()==(E/'progress.md').read_bytes(),'progress identity');checks['progress_current_identity']=True
pub=(E/'publication.py').read_text();guard="need(len(actual)==len(set(actual)) and set(actual)==expected,'Unbound/missing prepublication file')";need(guard in pub and pub.index(guard)<pub.index("save(P/'publication-names.json'")<pub.index("subprocess.run(['git','add'"),'publication exact gate');checks['publication_bound_membership_before_staging']=True
for actual,expected,want in [(['a','b'],{'a','b'},True),(['a','b','new'],{'a','b'},False),(['a'],{'a','b'},False),(['a','a','b'],{'a','b'},False)]:need((len(actual)==len(set(actual)) and set(actual)==expected)==want,'membership independent cases')
checks['four_pure_membership_cases']=True
for n,h in rd(P/'helper-pins.json')['sha256'].items():need(sha(Path(n))==h,'helper pins')
checks['bounded_helper_pins']=True
host=rd(E/'host.json');need(len(host['groups'])==228 and not host['matches'],'saved host');checks['saved228_groups_clear_visibility_limit_retained']=True
need(subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()=='2ad323617d16a26289ed05a9afac3fbe27b0133e','HEAD')
need(subprocess.check_output(['git','rev-parse','master'],cwd=R,text=True).strip()=='26e2291745999f485a74f643298ca997d65c7205','master')
need(not subprocess.check_output(['git','diff','HEAD','--name-only','--','src','test','.github','Project.toml'],cwd=R,text=True).strip(),'tracked code')
need(not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=R,text=True).strip(),'index');checks['refs_tracked_code_index_unchanged']=True
with (E/'reviewer-checks.json').open('x') as f:json.dump(dict(all_passed=True,scope='Independent offline source, byte/hash, mapping and pure membership checks; no Julia or prior helper execution',checks=checks,overlays=overlays,prior_hash_mappings=mappings,script_sha256=sha(Path(__file__).resolve())),f,indent=2);f.write('\n')
print('Independent reviewer checks:',len(checks),'PASS; Julia remains UNEXECUTED')
