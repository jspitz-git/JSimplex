from pathlib import Path
import hashlib,json,subprocess,ast
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/dual-recovery-devex-green-fixture-preparation/2026-10-30';P=W/'diagnostics/dual-recovery-devex-task4/2026-10-30';R=W/'.superpowers/dual-recovery-devex-task4/qualification-1';root=D/'prepared'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git','-C',str(W),*a],text=True).strip()
s=json.loads((D/'staging.json').read_text());m=json.loads((D/'fixture-manifest.json').read_text());f=json.loads((D/'fixture-check.json').read_text());old=json.loads((R/'green/completion.json').read_text())
original=[P/'green.jl',P/'endpoint.jl',*sorted((P/'tests').rglob('*')),*sorted((P/'overlays/candidate').rglob('*'))]
expected={str(p.relative_to(P)) for p in original if p.is_file()}|{'tests/fixtures/solver/netlib/adlittle.mps'}
regressions=json.loads((P/'contract.json').read_text())['green_includes']
checks={
'isolated_exact91_file_tree':{str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}==expected and len(expected)==91,
'all98_copies_exact':len(s['copies'])==98 and all(sha(dst)==sha(v['source'])==v['sha256'] for dst,v in s['copies'].items()),
'all255_old_published_files_unchanged':len(s['frozen_previous_publications'])==255 and all(sha(p)==h for p,h in s['frozen_previous_publications'].items()),
'whole_original15_programs_unchanged':len(m['programs'])==15 and all(sha(root/p)==sha(P/p)==h for p,h in m['programs'].items()),
'whole_candidate74_files_unchanged':len([p for p in (root/'overlays/candidate').rglob('*') if p.is_file()])==74 and all(sha(root/p.relative_to(P))==sha(p) for p in (P/'overlays/candidate').rglob('*') if p.is_file()),
'whole_original_regressions_unchanged':all(sha(root/p)==sha(W/'test'/Path(p).name) for p in regressions if (W/'test'/Path(p).name).exists()),
'fixture_sources_two_exact':len(m['fixtures'])==2 and all(sha(root/p)==sha(v['path'])==v['sha256']==m['fixtures'][p] for p,v in m['original_fixture_sources'].items()),
'fixed_adlittle_known_hash':sha(root/'tests/fixtures/solver/netlib/adlittle.mps')=='fec81e24fa91bc545d97239b108b43e6034f37b4bf2455a3f8c179726b44d44c',
'complete15_program14_edge2_input1_output_audit':f['accepted'] and (f['program_count'],f['include_edges'],f['fixture_count'],len(f['classified_outputs']))==(15,14,2,1),
'exact_entry_include_order':[a['target'] for a in f['includes'] if a['program']=='green.jl']==regressions,
'offline_red_expected_missing_fixture':'FAILED (failures=1)' in (D/'offline-red.log').read_text() and 'missing fixture tests/fixtures/solver/netlib/adlittle.mps' in (D/'offline-red.log').read_text(),
'offline_green_nine_rejection_tests':'Ran 9 tests' in (D/'offline-green.log').read_text() and (D/'offline-green.log').read_text().rstrip().endswith('OK'),
'old_failed_green_unchanged_unaccepted':old['supervisor_accepted'] is False and old['total_inclusive_seconds']==527.9604928489425 and not (R/'green/audit.json').exists(),
'no_additional_runtime_reservation':sorted(p.name for p in R.iterdir() if p.is_dir())==['green','red'],
'head_master_tree_index_unchanged':git('rev-parse','HEAD')=='a2f2415fcc6c9a018ae8209e28f517da1b23b688' and git('rev-parse','master')==git('rev-parse','origin/master')=='c0fa748ffa61ccb7c1caaf248c40324f60bc737b' and not git('diff','HEAD','--name-only') and not git('diff','--cached','--name-only'),
'no_symbolic_links_in_preparation':not any(p.is_symlink() for p in root.rglob('*')),
'python_syntax_only':all(ast.parse((D/p).read_text()) is not None for p in ('fixture_check.py','fixture_tests.py','prepare.py','preflight.py'))}
if not all(checks.values()):raise SystemExit(str(checks))
paths={Path(p) for p in s['frozen_previous_publications']}|{Path(p) for p in s['copies']}|{Path(v['source']) for v in s['copies'].values()}|{D/'staging.json',D/'fixture-check.json',D/'offline-green.log',R/'green/completion.json'}
payload=sum(p.stat().st_size for p in root.rglob('*') if p.is_file());extra=(root/'tests/fixtures/solver/netlib/adlittle.mps').stat().st_size
record=dict(accepted=True,scope='offline source/dependency preparation only; no Julia/numerical admission',checks=checks,bindings={str(p):sha(p) for p in sorted(paths)},prepared_payload_bytes=payload,added_fixture_bytes=extra,fixture_total_bytes=sum((root/p).stat().st_size for p in m['fixtures']),consumed_guarded_seconds=old['total_inclusive_seconds'],remaining_shared_seconds=1800-old['total_inclusive_seconds'])
with (D/'source-check.json').open('x') as out:json.dump(record,out,indent=2);out.write('\n')
with (D/'source-check.py').open('xb') as out:out.write(Path(__file__).read_bytes())
print(json.dumps(dict(accepted=True,checks=len(checks),bindings=len(paths),prepared_payload_bytes=payload,added_fixture_bytes=extra,fixture_total_bytes=record['fixture_total_bytes'])))
