from pathlib import Path
import sys,json,ast
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/dual-recovery-devex-cost-admission/2026-10-30';T=Path('/tmp/devex-cost-preparation-20261030')
sys.path.insert(0,str(D));import common as C
pres=C.read(D/'preservation.json');contract=C.read(D/'contract.json');used,facts=C.prior('reference-cost');p=C.ORIGINAL
files=list((p/'overlays/reference').rglob('*'));reference={f.relative_to(p/'overlays/reference').as_posix():f for f in files if f.is_file()}
candidate={f.relative_to(p/'overlays/candidate').as_posix():f for f in (p/'overlays/candidate').rglob('*') if f.is_file()}
diff=sorted(n for n in reference if C.sha(reference[n])!=C.sha(candidate[n]))
checks={
'all526_old_published_files_unchanged':len(pres['frozen_publications'])==526 and all(C.sha(n)==h for n,h in pres['frozen_publications'].items()),
'allfour_guards_binding_copies_exact':len(pres['copies'])==4 and all(C.sha(n)==C.sha(v['source'])==v['sha256'] for n,v in pres['copies'].items()),
'unchanged_original_cost_driver_reference':C.driver_ready(),
'two74file_projects_exact':len(reference)==len(candidate)==74 and set(reference)==set(candidate),
'only_three_canonical_candidate_source_differences':diff==['src/simplex_numerics.jl','src/simplex_pivot.jl','src/simplex_recovery.jl'],
'candidate_matches_tested_GREEN2_project':all(C.sha(f)==C.sha(C.FIX/'prepared/overlays/candidate'/n) for n,f in candidate.items()),
'whole_reference71src_equals_master_checkout':all(C.sha(f)==C.sha(W/n) for n,f in reference.items() if n.startswith('src/')),
'policy_constructor256eps_primary_source':'default_solve = exact ? zero(T) : T(256)*eps(T)' in (W/'src/simplex_numerics.jl').read_text(),
'base_prior_three_outcomes_exact':used==1033.6005972509156 and [f['accepted'] for f in facts]==[True,False,True],
'remaining766_no_reset':contract['initial_remaining_seconds']==1800-used==766.3994027490844,
'two_phases_one_attempt_each':contract['maximum_new_processes']==2 and contract['per_phase_attempts']==1 and contract['sequential'] is True and contract['phases']==list(C.PHASES),
'original_exact_schedule':contract['cost']==C.read(p/'contract.json')['cost'],
'no_cost_runtime_seal_admission':not C.RUN.exists(),
'original_qualification_only_red_green':sorted(f.name for f in (W/'.superpowers/dual-recovery-devex-task4/qualification-1').iterdir() if f.is_dir())==['green','red'],
'new_Python_AST_only':all(ast.parse((D/n).read_text()) is not None for n in ['common.py','cost_checks.py','audit.py','seal.py','launch.py','close.py','offline_tests.py','offline_tests_final.py']),
'final13_methods_pass':'Ran 13 tests' in (D/'offline-tests-final.log').read_text() and (D/'offline-tests-final.log').read_text().rstrip().endswith('OK'),
'initial11_methods_preserved':'Ran 11 tests' in (D/'offline-tests.log').read_text() and (D/'offline-tests.log').read_text().rstrip().endswith('OK'),
'no_guard_imports':'guard_reviewed' not in sys.modules and 'supervisor_reviewed' not in sys.modules,
'head_master_production_tree_unchanged':C.git('rev-parse','HEAD')=='6251dafd8be8f94ba4409f560692a893ced7d6a0' and C.git('rev-parse','master')==C.git('rev-parse','origin/master')==C.MASTER and not C.git('diff','HEAD','--name-only') and not C.git('diff','--cached','--name-only') and not C.git('diff','master','HEAD','--','src','test','Project.toml','.github')}
C.require(all(checks.values()),str(checks))
paths=set(Path(p) for p in pres['frozen_publications'])|{p for p in D.rglob('*') if p.is_file()}|{W/'src/simplex_numerics.jl'}
C.fresh(D/'source-check.json',dict(accepted=True,scope='OFFLINE concrete two-cost preparation; no numerical admission/result',checks=checks,bindings={str(p):C.sha(p) for p in sorted(paths)},base_seconds=used,remaining_seconds=1800-used,case_count_per_side=8,assertions_per_side=272))
with (D/'source-check.py').open('xb') as f:f.write(Path(__file__).read_bytes())
print(json.dumps(dict(accepted=True,checks=len(checks),bindings=len(paths),offline_methods=13,base=used,remaining=1800-used)))
