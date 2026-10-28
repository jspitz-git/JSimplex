from pathlib import Path
import json,hashlib,tomllib,statistics as st,importlib.util,subprocess,os,re
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-residual-pivot-crash/2026-10-28');M=Path('/home/jspitz/JSimplex.jl');R=D.parents[2];G=D/'GREEN';os.environ['GIT_OPTIONAL_LOCKS']='0'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(b,m):
 if not b:raise RuntimeError(m)
def git(a,root=M):return subprocess.check_output(['/usr/bin/git','-C',str(root),*a])
def gt(a,root=M):return git(a,root).decode().strip()
spec=importlib.util.spec_from_file_location('final_review_common',D/'common.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
co=read(D/'production-commit.json');target=co['commit'];base=c.TARGET;hist=read(D/'historical-path-map.json');protected=read(D/'protected-before.json');baseline=read(D/'baseline-tree.json');integration=read(D/'integration-historical-path-map.json');diag=read(D/'diagnostic-index-before.json')
need(hist['master_before']==integration['master_before']==base,'historical master')
need(hist['master_source_before']==integration['source_before'] and hist['master_index_before']==integration['master_index_before'],'exact historical map preservation')
expected_existing={str(M/n) for n in co['names'] if n in baseline};need(set(hist['master_source_before'])==expected_existing,'exact mapped old files')
for path,v in hist['master_source_before'].items():
 n=str(Path(path).relative_to(M));need(v['before']==str(D/'baseline'/n) and v['sha256']==baseline[n]==sha(v['before']),'source beforeimage')
mi=gt(['rev-parse','--path-format=absolute','--git-path','index']);ri=gt(['rev-parse','--path-format=absolute','--git-path','index'],R)
need(set(hist['master_index_before'])=={mi} and set(diag)=={ri},'exact index paths')
for path,v in {**hist['master_index_before'],**diag}.items():need(v['sha256']==protected['indexes'][path]==sha(v['before']),'original index beforeimage')
expected_cont={str(R/'diagnostics/simplex-core-architecture/STATUS.md'),str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md')};need(set(hist['continuation_before'])==expected_cont,'only intended continuations')
for path,v in hist['continuation_before'].items():
 need(v['sha256']==protected['files'][path]==sha(v['before']),'old continuation hash')
 need(Path(path).read_bytes().endswith(Path(v['before']).read_bytes()),'verbatim old suffix')
 prefix=Path(path).read_bytes()[:-len(Path(v['before']).read_bytes())].decode()
 need('pending' in prefix and 'candidates closed' not in prefix and 'At preparation' in prefix,'temporally explicit prepublication continuation state')
need(set(baseline)=={str(p.relative_to(D/'baseline')) for p in (D/'baseline').rglob('*') if p.is_file()},'baseline members')
for n,h in baseline.items():need(sha(D/'baseline'/n)==h,'baseline bytes')
source=read(D/'source-inverse.json');need({str(p.relative_to(G)):sha(p) for p in G.rglob('*') if p.is_file()}==source['whole_stage'],'reviewed stage immutable')
for tree in ['src','test']:
 aa={str(p.relative_to(M)):sha(p) for p in (M/tree).rglob('*') if p.is_file()};bb={str(p.relative_to(G)):sha(p) for p in (G/tree).rglob('*') if p.is_file()};need(aa==bb,'actual tested tree '+tree)
 for n in aa:need(git(['show',target+':'+n])==(M/n).read_bytes(),'committed current source '+n)
need(gt(['rev-list','--parents','-n','1',target]).split()==[target,base],'sole baseline parent')
commit_evidence=read(D/'commit-review-evidence.json');need(gt(['rev-parse',target+'^{tree}'])==co['tree']==commit_evidence['tree'],'exact tree');need(hashlib.sha256(git(['ls-tree','-rz','--full-tree',target])).hexdigest()==commit_evidence['full_tree_sha256'],'exact whole committed tree')
need(not gt(['diff','--name-only','HEAD','--','src','test','Project.toml']),'actualmaster no source drift')
need(c.environment()==read(D/'environment.json')['inherited'],'environment')
for path,h in protected['files'].items():
 if path not in expected_cont:need(sha(path)==h,'protected file')
for path,h in read(D/'MASTER-run/protected-before.json')['indexes'].items():need(sha(path)==h,'current index')
need(sha(ri)==protected['indexes'][ri],'diagnostic original index')
mapold={**hist['master_source_before'],**hist['master_index_before'],**hist['continuation_before']};used={}
def bound(path,h):
 if sha(path)==h:return
 need(path in mapold,'unmapped changed binding '+path);v=mapold[path];need(v['sha256']==h and sha(v['before'])==h,'exact historical binding '+path);used[path+'@'+h]=v['before']
reviews=['admission-final.json','result-review.json','production-review.json','publication-preparation-reviewed.json','commit-review.json','RED-run/admission.json','RED-run/result-review.json','GREEN-run/admission.json','GREEN-run/result-review.json','MASTER-run/admission.json','MASTER-run/result-review.json','finalization-preparation-review.json']
review_counts={}
for name in reviews:
 r=read(D/name);need(r['accepted'] is True and r['findings']==[],'accepted '+name)
 for path,h in r['bindings'].items():bound(path,h)
 review_counts[name]=len(r['bindings'])
manifest_counts={}
for name in ['pins.json','pins-ready.json','pins-final.json','RED-run/pins.json','GREEN-run/pins.json','MASTER-run/pins.json']:
 p=read(D/name);need(set(p['files'])==set(p['inventory']),'manifest membership')
 for path,v in p['inventory'].items():need(str(Path(path).resolve(strict=True))==v['resolved'],'resolved path');bound(path,v['sha256'])
 for tree in p['trees']:
  tree=Path(tree);expected={str(Path(path).relative_to(tree)) for path in p['inventory'] if Path(path).is_relative_to(tree)};actual={str(v.relative_to(tree)) for v in tree.rglob('*') if v.is_file()}
  if actual!=expected:
   need(tree in [M/'src',M/'test'],'only master source membership history');old=D/'baseline'/tree.relative_to(M);need({str(v.relative_to(old)) for v in old.rglob('*') if v.is_file()}==expected,'exact old tree membership')
 manifest_counts[name]=len(p['inventory'])
need(read(D/'admission.json')['accepted'] is False,'original rejection preserved')
fix=read(D/'final-prose-review-fix.json');initial=read(D/'final-review-initial.json');need(initial['accepted'] is False,'initial final review preserved')
for path,v in fix['beforeimages'].items():
 need(sha(v['before'])==v['sha256'],'exact generated beforeimage')
 need(initial['bindings'][path]==fix['after_sha256'][path],'initial finding saved after first correction')
for path,h in fix['after_sha256'].items():
 if sha(path)==h:continue
 temporal=read(D/'final-temporal-review-fix.json');v=temporal['changes'][path];need(v['sha256']==h and sha(v['before'])==h and sha(path)==v['after_sha256'],'exact temporal correction chain')
need(fix['numerics_rerun'] is False and fix['Julia_executed'] is False,'prose-only fix')
raw=tomllib.loads((D/'output/results.toml').read_text());summ=read(D/'summary.json');stats=read(D/'result-review-statistics.json');grid=read(D/'expected-cases.json');need(len(raw['cells'])==len(summ)==len(grid)==1192 and len(raw['preparation'])==1230,'raw counts')
meds={};gc=0;windows=0
for cell,row,spec in zip(raw['cells'],summ,grid):
 need(all(cell[k]==row[k]==v for k,v in spec.items()),'cell identity')
 ww=cell['windows'];need(len(ww)==18,'18 windows');windows+=len(ww)
 for j,w in enumerate(ww):
  pair=j//2+1;arms=['original',spec['variant']] if pair%2 else [spec['variant'],'original'];need(w['pair']==pair and w['arm']==arms[j%2],'alternating all pairs');need(w['compile_seconds']==w['recompile_seconds']==0,'zero compile');gc+=w['gc_seconds']>0
 for k in ['seconds','bytes','events']:
  ratios=[];a=[];b=[]
  for pair in range(1,10):
   left=next(v for v in ww if v['pair']==pair and v['arm']=='original');right=next(v for v in ww if v['pair']==pair and v['arm']==spec['variant']);need(type(left['result']) is type(right['result']) and left['result']==right['result'],'same measured result')
   a.append(left[k]);b.append(right[k]);ratios.append(right[k]/left[k] if left[k] else (1.0 if right[k]==0 else None))
  need(row[k]['paired_ratios']==ratios and row[k]['before']==st.median(a) and row[k]['after']==st.median(b),'raw-summary exact')
  need(row[k]['paired_median']==st.median(ratios),'raw cell median')
need(windows==21456 and gc==14 and stats['windows']==windows and len(stats['gc_windows'])==gc and stats['preparation_records']==1230 and stats['assertions']==45382,'independent statistics agree')
need(stats['gc_windows']==[dict(arm=w['arm'],cell=cell['id'],gc_seconds=w['gc_seconds'],pair=w['pair']) for cell in raw['cells'] for w in cell['windows'] if w['gc_seconds']>0],'exact retained GC windows')
report=(D/'FINAL-REPORT.md').read_text();table=[]
for variant,typ,scope,label in [('A','BigFloat','residual','BigFloat complete BTRAN row residual'),('B','BigFloat','update','BigFloat complete PFI column replacement'),('C','BigFloat','crash','BigFloat complete crash row selection'),('C','Rational{BigInt}','crash','RationalBigInt complete crash row selection')]:
 rows=[r for r in summ if r['variant']==variant and r['type']==typ and r['scope']==scope];ratios={k:st.median(r[k]['paired_median'] for r in rows) for k in ['seconds','bytes','events']};line='| '+label+' | '+str(len(rows))+' | '+' | '.join(f'{ratios[k]:.6f}' for k in ['seconds','bytes','events'])+' |';need(line in report,'exact report table '+label)
 group=next(v for v in stats['groups'] if v['grouping']==['variant','type'] and v['key']=={'variant':variant,'type':typ});need(group['cells']==len(rows) and all(group[k]['median_of_paired_cell_medians']==ratios[k] for k in ratios),'independent group agreement');table.append(dict(variant=variant,type=typ,cells=len(rows),ratios=ratios))
for variant,typ,shape in [('B','BigFloat','negative'),('C','Rational{BigInt}','positive')]:
 rows=[r for r in summ if r['variant']==variant and r['type']==typ and r['shape']==shape];need(all(r['events']['before']==r['events']['after'] for r in rows) and st.median(r['bytes']['paired_median'] for r in rows)==1.0,'no-event-gain controls; median paired bytes neutral')
need('negative' in report and 'all-positive' in report and 'no allocation' in report,'explicit no-gain caveats')
completed=read(D/'completed.json');need(f"{completed['elapsed_shared_seconds']:.3f}" in report and f"{read(D/'supervisor.json')['elapsed_seconds']:.3f}" in report,'both correctly distinguished elapsed values')
red=read(D/'RED-run/result-review.json');green=read(D/'GREEN-run/result-review.json');master=read(D/'MASTER-run/result-review.json');need(red['passed']==7252 and red['expected_failures']==6 and red['total']==7258,'RED');need(green['passed']==green['total']==master['passed']==master['total']==362111 and green['expected_failures']==master['expected_failures']==0,'GREEN MASTER');need(read(D/'GREEN-run/contract.json')['files']==read(D/'MASTER-run/contract.json')['files'] and len(read(D/'MASTER-run/contract.json')['files'])==67,'same67')
need(read(D/'publication.json')['accepted'] is True and read(D/'publication.json')['commit']==target and read(D/'publication.json')['normal_nonforce_push'] is True,'actual publication')
need(not (D/'closure.json').exists() and not (D/'diagnostic-publication-plan.json').exists() and not (D/'publication-after.json').exists(),'future closure/publication not claimed')
refs={'master_HEAD':gt(['rev-parse','HEAD']),'master':gt(['rev-parse','master']),'origin_master':gt(['rev-parse','origin/master']),'live_master':gt(['ls-remote','origin','refs/heads/master']).split()[0],'diagnostics_HEAD':gt(['rev-parse','HEAD'],R),'live_diagnostics':gt(['ls-remote','origin','refs/heads/codex/simplex-core-architecture'],R).split()[0]}
need(all(refs[k]==target for k in ['master_HEAD','master','origin_master','live_master']) and refs['diagnostics_HEAD']==refs['live_diagnostics']==read(D/'host-before.json')['diagnostic_head'],'published refs')
extra=set()
for path in D.rglob('output/process.json'):
 p=read(path);extra.update(p[k][v] for k in ['runner','child'] for v in ['pgid','sid'])
h=c.host(extra);need(len(h['groups'])==667 and len(h['processes'])>10,'fresh fullhost667')
e={'accepted':True,'commit':target,'parent':base,'tree':co['tree'],'table':table,'raw_counts':{'assertions':45382,'cases':1192,'windows':21456,'gc_windows':14,'preparation':1230},'completed_comparison_seconds':completed['elapsed_shared_seconds'],'GREEN_total':362111,'MASTER_total':362111,'same_whole_files':67,'review_binding_counts':review_counts,'six_manifest_counts':manifest_counts,'exact_historical_resolutions':used,'all_current_source_committed_and_tested':True,'all_original_tests_and_guards_preserved':True,'protected_current_files_and_indexes_verified':True,'original_continuation_suffixes_verbatim':True,'initial_final_findings_resolved_with_preserved_generated_beforeimages':True,'future_closure_and_diagnostic_publication_pending':True,'host':h,'refs':refs}
Path('/tmp/rpc-final-review-evidence.json').write_text(json.dumps(e,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in e.items() if k not in ['host','exact_historical_resolutions','review_binding_counts','table']}));print(json.dumps({'host_time':h['time_utc'],'groups':len(h['groups']),'processes':len(h['processes']),'no_Julia':h['no_Julia'],'available_kib':h['available_kib'],'swap':h['swap_used_kib']}))
