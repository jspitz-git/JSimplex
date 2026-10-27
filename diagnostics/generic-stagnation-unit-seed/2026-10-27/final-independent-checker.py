from pathlib import Path
import json,hashlib,subprocess,statistics,importlib.util,sys,re,ast
sys.dont_write_bytecode=True
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-stagnation-unit-seed/2026-10-27');M=Path('/home/jspitz/JSimplex.jl');R=D.parents[2]
cache={}
def sha(p):
 p=str(p)
 if p not in cache:cache[p]=hashlib.sha256(Path(p).read_bytes()).hexdigest()
 return cache[p]
def read(p):return json.loads(Path(p).read_text())
def need(v,m):
 if not v:raise AssertionError(m)
def put(p,v):
 with Path(p).open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
def git(args,root=M):return subprocess.check_output(['git','-C',str(root),*args]).decode().strip()
co=read(D/'production-commit.json');target=co['commit'];base=co['parent'];pub=read(D/'publication.json');hist=read(D/'historical-path-map.json');integration=read(D/'integration-historical-path-map.json');di=read(D/'diagnostic-index-before.json');protected=read(D/'protected-before.json');masterprotected=read(D/'MASTER-run/protected-before.json');inv=read(D/'source-inverse-final.json');baseline=read(D/'baseline-tree.json');checks={}
def check(k,v):need(v,k);checks[k]=True
check('published_exact_commit',pub['accepted'] is True and pub['normal_nonforce_push'] is True and pub['commit']==target==git(['rev-parse','HEAD'])==git(['rev-parse','master'])==git(['rev-parse','origin/master'])==git(['ls-remote','origin','refs/heads/master']).split()[0])
check('exact_commit_parent_and_paths',git(['rev-list','--parents','-n','1',target]).split()==[target,base] and git(['diff-tree','--no-commit-id','--name-only','-r',base,target]).splitlines()==inv['names']==co['names'])
subprocess.run(['git','-C',str(M),'diff-tree','--check',base,target],check=True);checks['actual_committed_whitespace_clean']=True
old_diag=read(D/'host-before.json')['diagnostic_head'];check('diagnostic_branch_not_yet_published',git(['branch','--show-current'],R)=='codex/simplex-core-architecture' and git(['rev-parse','HEAD'],R)==git(['ls-remote','origin','refs/heads/codex/simplex-core-architecture'],R).split()[0]==old_diag)
check('no_unrelated_staged_changes',not git(['diff','--cached','--raw'],R))
check('approved_origin',git(['remote','get-url','--push','--all','origin'],R)=='git@github.com:jspitz-git/JSimplex.git')
for tree in ['src','test']:
 actual={str(p.relative_to(M)):sha(p) for p in (M/tree).rglob('*') if p.is_file()};expected={n:h for n,h in inv['whole_stage'].items() if n.startswith(tree+'/')};check('current_complete_'+tree,actual==expected)
for root,mapping in [(D/'baseline',baseline),(D/'GREEN-final',inv['whole_stage'])]:
 need({str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}==set(mapping),'full tree membership')
 for n,h in mapping.items():need(sha(root/n)==h,'full tree content '+str(root/n))
checks['all_final_stage_and_baseline_files']=True
check('sole_format_LF',(D/'GREEN-2/src/simplex.jl').read_bytes()==(D/'GREEN-final/src/simplex.jl').read_bytes()+b'\n')
mi=git(['rev-parse','--path-format=absolute','--git-path','index']);ri=git(['rev-parse','--path-format=absolute','--git-path','index'],R)
check('exact_master_before_map',hist['master_before']==integration['master_before']==base and hist['master_source_before']==integration['source_before'] and hist['master_index_before']==integration['master_index_before'])
expected_before={str(M/n) for n in co['names'] if n in baseline};check('exact_changed_existing_source_map_keys',set(hist['master_source_before'])==expected_before)
for path,v in hist['master_source_before'].items():
 before=D/'baseline'/Path(path).relative_to(M);need(v['before']==str(before) and v['sha256']==sha(before)==baseline[str(Path(path).relative_to(M))],'exact source beforeimage')
check('exact_main_index_before',set(hist['master_index_before'])=={mi} and hist['master_index_before'][mi]['before']==str(D/'before-master/master.index') and hist['master_index_before'][mi]['sha256']==sha(D/'before-master/master.index')==protected['indexes'][mi])
check('exact_diagnostic_index_before',set(di)=={ri} and di[ri]['before']==str(D/'before-diagnostic/diagnostic.index') and di[ri]['sha256']==sha(D/'before-diagnostic/diagnostic.index')==protected['indexes'][ri])
allowed={str(R/'diagnostics/simplex-core-architecture/STATUS.md'),str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md')};check('exact_continuation_map_keys',set(hist['continuation_before'])==allowed)
for path,h in protected['files'].items():
 if path in allowed:
  v=hist['continuation_before'][path];before=Path(v['before']);need(v['sha256']==h==sha(before),'continuation beforehash');old=before.read_bytes();current=Path(path).read_bytes();need(current.endswith(old) and current[:-len(old)].startswith(b'# Current continuation') and target.encode() in current[:-len(old)],'current prefix and exact old suffix')
 else:need(sha(path)==h,'unrelated protected file '+path)
for path,h in masterprotected['indexes'].items():need(sha(path)==h,'current index '+path)
checks['protected_files_current_indexes_verbatim_continuations']=True
resolved={}
def historical(path,h):
 path=Path(path)
 if sha(path)==h:return str(path)
 candidates=[]
 for mapping in [hist['master_index_before'],di,hist['continuation_before']]:
  if str(path) in mapping:candidates.append(Path(mapping[str(path)]['before']))
 if path.is_relative_to(M/'src') or path.is_relative_to(M/'test'):candidates.append(D/'baseline'/path.relative_to(M))
 good=[p for p in candidates if p.is_file() and sha(p)==h];need(len(good)==1,'unique exact historical beforeimage '+str(path));resolved[str(path)+'@'+h]=str(good[0]);return str(good[0])
reviews=['admission.json','comparison-2/admission.json','result-review.json','production-review-2.json','formatting-review.json','publication-preparation-final.json','preparation-review-final.json','commit-review.json','RED-run/admission.json','RED-run/result-review.json','GREEN-2-run/admission.json','GREEN-2-run/result-review.json','MASTER-run/admission.json','MASTER-run/result-review.json']
for n in reviews:
 review=read(D/n);need(review['accepted'] is True and review['findings']==[],'accepted review '+n)
 for path,h in review['bindings'].items():need(Path(path).is_absolute(),'absolute review binding');historical(path,h)
checks['all_current_prerequisite_reviews_bound']=True
phases=[(D,'pins-reviewed.json'),(D/'comparison-2','pins-reviewed.json'),(D/'RED-run','pins.json'),(D/'GREEN-run','pins.json'),(D/'GREEN-2-run','pins.json'),(D/'MASTER-run','pins.json')];pin_counts={}
for phase,name in phases:
 pins=read(phase/name);need(set(pins['files'])==set(pins['inventory']),'complete pin inventory');pin_counts[str(phase.relative_to(D))]=len(pins['inventory'])
 for path,v in pins['inventory'].items():need(str(Path(path).resolve(strict=True))==v['resolved'],'unchanged resolved path '+path);historical(path,v['sha256'])
 for tree in pins['trees']:
  tree=Path(tree);expected={str(Path(p).relative_to(tree)) for p in pins['inventory'] if Path(p).is_relative_to(tree)};actual={str(p.relative_to(tree)) for p in tree.rglob('*') if p.is_file()}
  if actual!=expected:
   need(tree in [M/'src',M/'test'],'only integrated tree can differ');before=D/'baseline'/tree.relative_to(M);need(expected=={str(p.relative_to(before)) for p in before.rglob('*') if p.is_file()},'exact historical tree membership')
checks['all_six_phase_pins_exact_or_mapped']=True
for phase in [D,D/'GREEN-run']:
 process=read(phase/'output/process.json');need(process['returncode']==1 and process['pins_unchanged'] is True,'rejected attempt still failed')
check('original_loader_no_tests', 'UndefVarError: `SimplexWorkspace` not defined' in (D/'GREEN-run/output/run.log').read_text() and 'INCLUDING ' not in (D/'GREEN-run/output/run.log').read_text())
check('original_comparison_104540_19',bool(re.search(r'^Stagnation unit seed whole-function comparison\s*\|\s*104540\s+19\s+104559', (D/'output/run.log').read_text(),re.M)))
red=read(D/'RED-run/audit.json');green=read(D/'GREEN-2-run/audit.json');master=read(D/'MASTER-run/audit.json');cmp=read(D/'comparison-2/audit.json')
check('exact_accepted_counts',red['passed']==30806 and red['expected_failures']==5 and red['total']==30811 and green['passed']==master['passed']==257423 and green['expected_failures']==master['expected_failures']==0 and cmp['assertions']==105921)
check('same_45_files_and_frozen_master_total',read(D/'MASTER-run/contract.json')['files']==read(D/'GREEN-2-run/contract.json')['files'] and len(read(D/'MASTER-run/contract.json')['files'])==45 and read(D/'MASTER-run/contract.json')['expected_total']==257423)
for arm,count in [('GREEN-2',257423),('MASTER',257423)]:
 log=(D/(arm+'-run/output/run.log')).read_text();need(bool(re.search(r'^Stagnation unit seed '+arm+r'\s*\|\s*'+str(count)+r'\s+'+str(count)+r'\s',log,re.M)),'ordinary all-pass summary');need('Test Failed at ' not in log and 'Error During Test' not in log,'no ordinary failures')
checks['all_pass_log_counts']=True
report=(D/'FINAL-REPORT.md').read_text();rows=read(D/'comparison-2/summary.json')['cases'];table=[]
for arm,scope,typ,label in [('A','values','BigFloat','Whole stagnation metrics'),('A','observe','BigFloat','Whole primal observation'),('A','observe_dual','BigFloat','Whole dual observation'),('B','unit','BigFloat','Whole BigFloat unit gate'),('B','unit','Rational{BigInt}','Whole RationalBigInt unit gate'),('B','init','BigFloat','Whole initialization B'),('C','init','BigFloat','Whole initialization C'),('BC','init','BigFloat','Whole composed initialization')]:
 rr=[r for r in rows if r['variant']==arm and r['scope']==scope and r['type']==typ];need(rr,'statistics cells')
 ratio=statistics.median(r['paired_ratio'] for r in rr)
 def rel(k):return statistics.median(r['candidate'][k]/r['original'][k] if r['original'][k] else 1.0 for r in rr)
 line=f'| {label} | {ratio:.4f} | {rel("bytes"):.4f} | {rel("events"):.4f} |';need(line in report,'published table arithmetic');table.append(line)
check('reported_elapsed',f"{cmp['elapsed_seconds']:.3f}s" in report and f"{green['elapsed_shared_seconds']:.3f}s" in report and f"{master['elapsed_shared_seconds']:.3f}s" in report)
check('explicit_limits_and_failures',all(s in report for s in ['23GCwindows','7856extra bytes','96fewer events','No universal/end-to-end','Thirteen runtime binaries','Original GREEN rejected before tests','First commit preparation stopped failfast','one trailing LF','fullsuite/x64']))
for name in ['closure-final.py','diagnostic-publish-final.py']:ast.parse((D/name).read_text(),filename=name)
prep=read(D/'preparation-review-final.json')
for name in ['closure-final.py','diagnostic-publish-final.py','finalize-final.py']:need(sha(D/name)==prep['bindings'][str(D/name)],'canonical final helper unchanged')
check('future_closure_publication_not_run',not(D/'closure.json').exists() and not(D/'diagnostic-publication-plan.json').exists() and not(D/'publication-after.json').exists())
spec=importlib.util.spec_from_file_location('final_review_common',D/'common_reviewed.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c);extra=set(read(D/'MASTER-run/audit-host.json')['groups'])
for p in D.rglob('output/process.json'):
 v=read(p);extra.update(v[k][j] for k in ['runner','child'] for j in ['pgid','sid'])
host=c.host(extra);need(len(host['groups'])==619,'full619groups');put(D/'final-independent-host.json',host);checks['fresh619groups_sessions_noJulia']=True
(D/'final-independent-checker.py').write_bytes(Path(__file__).read_bytes())
put(D/'final-independent-checks.json',dict(accepted=True,checks=checks,phase_pin_counts=pin_counts,historical_before_resolutions=resolved,production_commit=target,passed=257423,whole_files=45,report_table=table))
(D/'FINAL-REVIEW.md').write_text(f'''# Independent final release and evidence review

No outstanding findings. Production `{target}` is the exact reviewed four-path commit, normally pushed and verified against local master, origin/master and the remote. Fresh actual master passed 257423 tests across the same 45 whole files in {master['elapsed_shared_seconds']:.3f}s; GREEN-2 passed the same count in {green['elapsed_shared_seconds']:.3f}s. Accept this final report, current continuations and the prepared canonical closure/publication procedure. Diagnostic publication is still pending: one successful closure and exact staged/committed-name/blob checks must precede its normal push.

A new independent offline checker verified actual committed parent/diff/whitespace, complete current production trees, all final-stage and baseline bytes, every pin and resolution in six phases, every accepted prerequisite review binding, and exact historical source/index/continuation beforeimages. Protected user/environment files and current main/diagnostic indexes are preserved. Both current continuation files retain their exact former bytes as a suffix; current prefixes are included in this review's absolute SHA bindings. Fresh process inspection covered all 619 historical groups AND sessions with boot/start ticks/commands and no Julia, retaining only the fixed unrelated identity exemption.

Recalculated all eight report table rows from the accepted per-cell summaries and checked reported counts/times against ordinary Test logs and accepted result artifacts. The first comparison remains 104540 passes plus 19 setup errors, the original GREEN remains a pre-test loader failure, and the precommit EOF warning is preserved. Corrected loading order and the sole-final-LF qualification are explicit. The final source was actually loaded and tested on master. No failure was converted into a pass or previous numerical run/auditor repeated.

The numerical/work-memory conclusion remains no unnecessary added production work or retained numerical memory. A removes repeated scalar zeros and discarded nonnegative magnitude work; B retains structural scans and negative BigFloat rounding while avoiding unit temporaries; C replaces repeated shared-row cacheability checks with one first-site check and unchanged stores. Arithmetic order, guards, generic methods, owners, callbacks and exception behavior are preserved. The report retains GC/outliers, the single byte-increase observation, compilation/setup distinctions, sparse/dense scope and the absence of universal/end-to-end/native-retention claims. Full-suite/x64 and broader performance coverage remain open.

Canonical closure-final.py and diagnostic-publish-final.py match their accepted preparation hashes. Closure requires exact current source, beforeimages, all accepted reviews, phase pins and fresh quiescence. Publisher requires PASS closure/final review, exact artifact membership, every staged and committed blob including its self-described plan, expected parent and protected files/indexes before fail-fast normal nonforce push. This reviewer performed no Julia run, existing validator rerun, Git mutation, closure or publication. Declined-to-judge behaviors: none.
''')
private={'baseline','RED','GREEN','GREEN-2','GREEN-final','before-master','before-diagnostic','__pycache__'}
paths=[p for p in D.rglob('*') if p.is_file() and p.relative_to(D).parts[0] not in private and '__pycache__' not in p.parts and p.name not in ['final-review.json','closure.json','closure-host.json','diagnostic-publication-plan.json','publication-after.json']]
paths += [Path(p) for p in allowed]
put(D/'final-review.json',dict(accepted=True,findings=[],scope='Independent final release/report/current-continuation and canonical closure/publication source acceptance. One separate PASS closure and exact all staged/committed blobs remain required before diagnostic publication.',production_commit=target,passed=257423,whole_files=45,historical_groups_and_sessions=619,no_Julia=True,unnecessary_added_production_work_or_memory_found=False,declined_to_judge=[],bindings={str(p):sha(p) for p in paths}))
print(json.dumps({'accepted':True,'checks':len(checks),'phase_pins':pin_counts,'historical_resolutions':len(resolved),'bindings':len(paths),'production_commit':target,'diagnostic_publication':'pending closure and exact publication'}))
