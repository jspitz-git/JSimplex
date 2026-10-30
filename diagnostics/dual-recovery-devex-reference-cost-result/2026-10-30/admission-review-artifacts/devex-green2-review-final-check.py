"""Fresh bounded independent review. Read-only inputs, selected pure parser definitions only."""
import ast,hashlib,json,math,re,subprocess,types
from pathlib import Path
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/dual-recovery-devex-green2-admission/2026-10-30'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
checks={};bindings={}
def ck(name,v):
 checks[name]=bool(v)
 assert v,name
initial=read('/tmp/devex-green2-preparation-review.json');maps=read(D/'initial-review-maps.json');portable=read(D/'review-initial-portable-maps.json');fix=read(D/'review-fix-check.json')
ck('initial_is_rejected',initial['accepted'] is False and initial['runtime_qualified'] is False and initial['numerical_admission'] is False)
ck('only_previous_doc_remapped',set(maps)=={str(D/'ADMISSION-PREPARATION.md')})
ck('five_exact_initial_copies',len(portable)==5)
for old,q in portable.items():
 ck('portable:'+old,sha(old)==sha(q['copy'])==q['sha256']);bindings[old]=sha(old);bindings[q['copy']]=sha(q['copy'])
combined=maps|portable
for old,h in initial['bindings'].items():
 target=combined.get(old,{}).get('copy',old)
 ck('initial_binding:'+old,sha(target)==h)
 if old in combined:ck('map_hash:'+old,combined[old]['sha256']==h)
 bindings[target]=h
ck('all432_initial_bindings',len(initial['bindings'])==432)
for n,h in read(D/'source-check.json')['bindings'].items():ck('original_source:'+n,sha(n)==h);bindings[n]=h
ck('all425_source_bindings',len(read(D/'source-check.json')['bindings'])==425)
for n,h in read(D/'preservation.json')['frozen_publications'].items():ck('historical:'+n,sha(n)==h)
ck('all402_historical',len(read(D/'preservation.json')['frozen_publications'])==402)
for n,h in fix['bindings'].items():ck('fix_binding:'+n,sha(n)==h);bindings[n]=h
ck('fix43_bindings',len(fix['bindings'])==43)
ck('author_fix13_checks',len(fix['checks'])==13 and all(v is True for v in fix['checks'].values()))
old=(D/'audit.py').read_text();new=(D/'audit_reviewed.py').read_text()
oldblock=" post=summary(log,'TASK4_POST_FALLBACK')\n C.require(post.get('Pass')==post.get('Total')==46 and all(post.get(k,0)==0 for k in ('Fail','Error','Broken')),'endpoint46 ordinary assertions')\n"
newblock=" # Successful nested DefaultTestSets need not be printed by Julia Test.\n # All46 assertions remain in the pinned endpoint program and aggregate parent.\n # If a verbose/failed-style child row is present, its literal budget stays checked.\n if any('|' in row and row.split('|',1)[0].strip()=='TASK4_POST_FALLBACK' for row in log.splitlines()):\n  post=summary(log,'TASK4_POST_FALLBACK')\n  C.require(post.get('Pass')==post.get('Total')==46 and all(post.get(k,0)==0 for k in ('Fail','Error','Broken')),'endpoint46 ordinary assertions')\n"
ck('exact_auditor_inverse',old.count(oldblock)==new.count(newblock)==1 and new.replace(newblock,oldblock)==old)
launch=(D/'launch-reviewed.py').read_text()
ck('exact_launcher_inverse',launch.replace('import audit_reviewed as audit #','import audit #').replace("C.D/'audit_reviewed.py'","C.D/'audit.py'")==(D/'launch.py').read_text())
ck('early_intended_module',launch.index('import audit_reviewed as audit')<launch.index('sys.path.insert(0,str(C.D/\'guard\'))') and "C.D/'audit_reviewed.py'" in launch)
contract=read(D/'contract.json')
def require(v,m):
 if not v:raise ValueError(m)
C=types.SimpleNamespace(require=require,includes=lambda:contract['green_includes'])
def pure_parser(source,path):
 ns=dict(C=C,re=re,math=math)
 tree=ast.parse(source)
 exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'summary','ordinary'}],type_ignores=[]),str(path),'exec'),ns)
 return ns['ordinary']
a=pure_parser(new,D/'audit_reviewed.py');original=pure_parser(old,D/'audit.py')
base=''.join('TASK4_INCLUDED '+p+'\n' for p in C.includes())+'Test Summary: | Pass Total Time\nTASK4_GREEN | 6000 6000 1.0s\nTASK4_GREEN_COMPLETED\n'
ck('nonverbose_parent_accepted',a(base)==dict(Pass=6000,Total=6000))
try:original(base)
except ValueError as e:ck('original_expected_false_rejection',str(e)=='missing/duplicate ordinary summary TASK4_POST_FALLBACK')
else:raise AssertionError('original unexpectedly accepted')
child='  TASK4_POST_FALLBACK | 46 46 0.1s\n'
verbose=base.replace('TASK4_GREEN_COMPLETED',child+'TASK4_GREEN_COMPLETED')
ck('optional_present_child_accepted',a(verbose)==dict(Pass=6000,Total=6000))
mutants={
'wrong_child46':verbose.replace('46 46','45 45'),
'duplicate_child':verbose.replace(child,child+child),
'non_green_parent':base.replace('6000 6000','5999 6000'),
'empty_parent':base.replace('6000 6000','0 0'),
'missing_completion':base.replace('TASK4_GREEN_COMPLETED',''),
'duplicate_completion':base+'TASK4_GREEN_COMPLETED\n',
'missing_include':base.replace('TASK4_INCLUDED endpoint.jl\n',''),
'duplicate_include':base+'TASK4_INCLUDED endpoint.jl\n',
'world_age':base+'world age\n',
'error':base+'ERROR: failure\n',
'duplicate_parent':base+'TASK4_GREEN | 6000 6000 1.0s\n',
'failed_child':verbose.replace('Pass Total Time','Pass Fail Total Time').replace('6000 6000 1.0s','6000 0 6000 1.0s').replace('46 46 0.1s','45 1 46 0.1s'),
'old_recorded_failure':(W/'diagnostics/dual-recovery-devex-task4-green/2026-10-30/green/guard/run.log').read_text(),
}
for name,log in mutants.items():
 try:a(log)
 except (ValueError,KeyError):ck('parser_refuses:'+name,True)
 else:raise AssertionError('mutant accepted '+name)
# Compare all previous test methods, allowing solely the necessary module import change.
def methods(p):return {n.name:ast.dump(n,include_attributes=False) for c in ast.parse(p.read_text()).body if isinstance(c,ast.ClassDef) for n in c.body if isinstance(n,ast.FunctionDef)}
before=methods(D/'offline_tests_final.py');after=methods(D/'offline_tests_reviewed_final.py')
ck('16_methods_keep15',len(before)==15 and len(after)==16 and set(before)<=set(after))
ck('14_old_methods_AST_identical',all(before[n]==after[n] for n in before if n!='test_definitions_only_launcher_import'))
intermediate=(D/'offline_tests_reviewed.py').read_text();final=(D/'offline_tests_reviewed_final.py').read_text()
ck('only_new_fixture_escape_fixed',intermediate.replace("\\\\n","\\n")==final)
for name,needle in [('summary-red.log','FAILED (failures=1)'),('summary-green.log','Ran 1 test'),('offline-tests-reviewed.log','FAILED (errors=1)'),('offline-tests-reviewed-final.log','Ran 16 tests')]:ck('recorded_log:'+name,needle in (D/name).read_text())
ck('final_recorded16pass',(D/'offline-tests-reviewed-final.log').read_text().rstrip().endswith('OK'))
ck('no_verbose_env_change','JULIA_TEST_VERBOSE' not in contract['environment'])
ck('prior_budget_unchanged',contract['used_seconds']==527.9604928489425 and contract['remaining_seconds']==1272.0395071510575 and contract['shared_total_seconds']==1800 and [p['accepted'] for p in contract['previous']]==[True,False])
ck('no_runtime_reservation',not Path(contract['output_root']).exists())
F=W/'diagnostics/dual-recovery-devex-green-fixture-preparation/2026-10-30/prepared'
ck('unchanged_driver',sha(F/'green.jl')==contract['driver_sha256'])
ck('unchanged_91prepared',len([p for p in F.rglob('*') if p.is_file()])==91)
for name in ['audit_reviewed.py','launch-reviewed.py','summary_tests.py','offline_tests_reviewed.py','offline_tests_reviewed_final.py']:ast.parse((D/name).read_text())
ck('new_AST_valid',True)
for args in [('diff','HEAD','--name-only'),('diff','--cached','--name-only'),('diff','master','HEAD','--','src','test','Project.toml','.github')]:ck('git:'+str(args),not subprocess.check_output(['git','-C',str(W),*args],text=True).strip())
for p in D.rglob('*'):
 if p.is_file():bindings[str(p)]=sha(p)
result=dict(accepted=True,scope='offline_preparation',runtime_qualified=False,numerical_admission=False,checks=checks,bindings=bindings,findings=[],initial_review_preserved=True,counts=dict(initial_bindings=432,source_bindings=425,prior_published_files=402,fix_bindings=43,prepared_files=91,pure_parser_mutants_rejected=len(mutants),assertions=len(checks)),no_julia=True)
Path('/tmp/devex-green2-review-final-check-result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('checks','bindings')},indent=2));print('Bound input files',len(bindings))
