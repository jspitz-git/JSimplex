from pathlib import Path
import sys,json,hashlib
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-ratio-monitor/2026-10-27');M=Path('/home/jspitz/JSimplex.jl');R=D.parents[2];sys.path.insert(0,str(D));import common_complete as c
from finalization_checks import verify_protected_files
co=c.read('production-commit.json');target=co['commit'];pub=c.read('publication.json');hist=c.read('historical-path-map.json');di=c.read('diagnostic-index-before.json');protected=c.read('protected-before.json');checks={};used={};cache={}
def digest(p):
 p=str(p)
 if p not in cache:cache[p]=c.sha(p)
 return cache[p]
def check(k,v):c.need(v,k);checks[k]=True
check('published_exact_master',pub['accepted'] is True and pub['commit']==target and c.git(['rev-parse','HEAD'])==c.git(['rev-parse','master'])==c.git(['rev-parse','origin/master'])==c.git(['ls-remote','origin','refs/heads/master']).split()[0]==target)
check('sole_original_parent',c.git(['rev-list','--parents','-n','1',target]).split()==[target,c.TARGET])
check('diagnostic_ref_before',c.git(['rev-parse','HEAD'],R)==c.read('host-before.json')['diagnostic_head'])
for tree in ['src','test']:
 a={str(p.relative_to(M)):digest(p) for p in (M/tree).rglob('*') if p.is_file()};b={str(p.relative_to(D/'GREEN')):digest(p) for p in (D/'GREEN'/tree).rglob('*') if p.is_file()};check('current_tested_'+tree,a==b)
base=c.read('baseline-tree.json');check('baseline_membership',set(base)=={str(p.relative_to(D/'baseline')) for p in (D/'baseline').rglob('*') if p.is_file()})
for n,h in base.items():c.need(digest(D/'baseline'/n)==h,'baseline '+n)
checks['all_baseline_bytes']=True
allowed={str(R/'diagnostics/simplex-core-architecture/STATUS.md'),str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md')}
verify_protected_files(protected['files'],hist['continuation_before'],allowed,c.read('final-review.json')['bindings'],digest,c.need)
checks['all_userfiles_environment']=True
mi=c.git(['rev-parse','--path-format=absolute','--git-path','index']);ri=c.git(['rev-parse','--path-format=absolute','--git-path','index'],R)
for p,h in c.read('MASTER-run/protected-before.json')['indexes'].items():c.need(digest(p)==h,'current protected index '+p)
check('all_current_indexes',True)
def before(p,h):
 p=Path(p)
 if digest(p)==h:return str(p)
 q=None
 if str(p) in hist['master_index_before']:q=Path(hist['master_index_before'][str(p)]['before'])
 elif str(p) in di:q=Path(di[str(p)]['before'])
 elif str(p) in hist['continuation_before']:q=Path(hist['continuation_before'][str(p)]['before'])
 elif p.is_relative_to(M/'src') or p.is_relative_to(M/'test'):q=D/'baseline'/p.relative_to(M)
 c.need(q is not None and q.is_file() and digest(q)==h,'unresolved historical binding '+str(p))
 used[str(p)+'@'+h]=str(q);return str(q)
reviews=['admission-complete.json','result-review.json','production-review.json','publication-preparation-reviewed.json','commit-review.json','RED-run/admission.json','RED-run/result-review.json','GREEN-run/admission.json','GREEN-run/result-review.json','MASTER-run/admission.json','MASTER-run/result-review.json','final-review.json']
for n in reviews:
 r=c.read(n);c.need(r['accepted'] is True and r['findings']==[],'review '+n)
 for p,h in r['bindings'].items():before(p,h)
c.need(c.read('admission.json')['accepted'] is False,'initial offline rejected admission preserved')
c.need(c.read('output/process.json')['returncode']==0 and c.read('output/process.json')['pins_unchanged'],'single accepted comparison')
checks['all_independent_reviews_bound']=True
for phase,manifest in [(D,n) for n in ['pins.json','pins-reviewed.json','pins-final.json','pins-ready.json','pins-complete.json']]+[(D/'RED-run','pins.json'),(D/'GREEN-run','pins.json'),(D/'MASTER-run','pins.json')]:
 pins=json.loads((phase/manifest).read_text())
 c.need(set(pins['files'])==set(pins['inventory']),'pin membership '+str(phase))
 for p,v in pins['inventory'].items():
  c.need(str(Path(p).resolve(strict=True))==v['resolved'],'resolved '+p);before(p,v['sha256'])
 for tree in pins['trees']:
  tree=Path(tree);expected={str(Path(p).relative_to(tree)) for p in pins['inventory'] if Path(p).is_relative_to(tree)};actual={str(p.relative_to(tree)) for p in tree.rglob('*') if p.is_file()}
  if actual!=expected and (tree==M/'src' or tree==M/'test'):
   old=D/'baseline'/tree.relative_to(M);actual={str(p.relative_to(old)) for p in old.rglob('*') if p.is_file()}
  c.need(actual==expected,'historical tree membership '+str(tree))
checks['all_phase_pins_or_exact_beforeimages']=True
red=c.read('RED-run/audit.json');g=c.read('GREEN-run/audit.json');m=c.read('MASTER-run/audit.json');cmp=c.read('audit.json')
check('accepted_numerics',cmp['accepted'] is True and cmp['cases']==1225 and cmp['windows']==22050 and red['accepted'] is True and red['passed']==24721 and red['expected_failures']==4 and g['accepted'] is True and m['accepted'] is True and g['passed']==m['passed']==c.read('MASTER-run/contract.json')['expected_total'] and g['expected_failures']==m['expected_failures']==0)
check('unchanged_old_test', (M/'test/generic_dual_comparisons_tests.jl').read_bytes()==(D/'baseline/test/generic_dual_comparisons_tests.jl').read_bytes())
for p,v in hist['continuation_before'].items():
 c.need(digest(v['before'])==v['sha256'],'continuation before');c.need(Path(p).read_bytes().endswith(Path(v['before']).read_bytes()),'verbatim old continuation')
checks['verbatim_continuation_and_maps']=True
check('diagnostic_index_before',set(di)=={ri} and di[ri]['sha256']==protected['indexes'][ri]==digest(di[ri]['before']))
extra=set()
for path in D.rglob('output/process.json'):
 p=json.loads(path.read_text());extra.update(p[k][v] for k in ['runner','child'] for v in ['pgid','sid'])
c.put('closure-host.json',c.host(extra));checks['fresh_full_groups_sessions_noJulia']=True
private={'baseline','RED','GREEN','GREEN-2','GREEN-final','before-master','before-diagnostic','__pycache__'}
files=[p for p in D.rglob('*') if p.is_file() and not p.relative_to(D).parts[0] in private and '__pycache__' not in p.parts and p.name not in ['closure.json','diagnostic-publication-plan.json','publication-after.json']]
bindings={str(p):digest(p) for p in files};bindings.update({p:digest(p) for p in hist['continuation_before']})
c.put('closure.json',dict(accepted=True,checks=checks,production_commit=target,passed=g['passed'],measured_assertions=52721,bindings=bindings,historical_before_resolutions=used,closure_self_excluded=True))
print('PASS closure',len(checks),'checks',len(bindings),'bindings',len(used),'explicit historical resolutions')
