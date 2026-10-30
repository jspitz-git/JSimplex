from pathlib import Path
import hashlib,json,re,subprocess,tomllib
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');P=W/'diagnostics/dual-recovery-devex-task4/2026-10-30';D=W/'diagnostics/dual-recovery-devex-task4-green/2026-10-30';R=W/'.superpowers/dual-recovery-devex-task4/qualification-1/green'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
log=(R/'guard/run.log').read_text();proc=json.loads((R/'guard/process.json').read_text());sup=json.loads((R/'supervisor.json').read_text());done=json.loads((R/'completion.json').read_text());pins=json.loads((R/'pins.json').read_text());contract=json.loads((P/'contract.json').read_text())
test=P/'tests/simplex_numerics_tests.jl';original=W/'test/simplex_numerics_tests.jl';missing=P/'tests/fixtures/solver/netlib/adlittle.mps';fixture=W/'test/fixtures/solver/netlib/adlittle.mps';stage=P/'stage.py';text=test.read_text();records=tomllib.loads((R/'result.toml').read_text())['cases']
checks={
'ordinary_exact_result':re.search(r'^TASK4_GREEN\s+\|\s+5772\s+1\s+5773\s+',log,re.M) is not None and '5772 passed, 0 failed, 1 errored, 0 broken' in log,
'sole_error_is_missing_existing_dependency':log.count('Error During Test at')==1 and f'opening file "{missing}": No such file or directory' in log and 'Numerical strategy propagation: Error During Test' in log,
'unchanged_test_literal_requires_fixture':test.read_bytes()==original.read_bytes() and 'read_mps(joinpath(@__DIR__,"fixtures","solver","netlib","adlittle.mps"))' in text,
'fixture_available_only_at_original_path':fixture.is_file() and fixture.stat().st_size==16500 and not missing.exists(),
'fixture_omitted_from_pins_and_staging':'adlittle' not in stage.read_text() and str(missing) not in pins['inventory'] and 'wide-bound129.mps' in stage.read_text(),
'all_twelve_include_markers':re.findall(r'^TASK4_INCLUDED (.+)$',log,re.M)==contract['green_includes'],
'endpoint_all46_pass':re.search(r'^\s+TASK4_POST_FALLBACK\s+\|\s+46\s+46\s+',log,re.M) is not None and len(records)==2,
'endpoint_original_certificates_and_controls':{q['type'] for q in records}=={'Float32','Float64'} and all(all(q[k] is True for k in ['original_primal_certified','original_optimality_certified','invalid_witness_rejected','invalid_row_rejected','trajectory_changed']) and q['point']==q['witness']==[1,0] and q['iterations']==q['factorizations']==q['attempted_weight_rows']==q['avoided_weight_rows']==1 and (q['core_and_weight_ftran'],q['core_and_weight_btran'])==(1,3) for q in records),
'actual_exit_failure_not_timeout':proc['returncode']==sup['returncode']==1 and proc['reason']=='exit1' and all(sup[k] is False for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']),
'failed_not_relabelled_accepted':sup['accepted'] is False and done['supervisor_accepted'] is False and not (R/'audit.json').exists() and 'TASK4_GREEN_COMPLETED' not in log,
'shared_budget_not_exhausted':done['elapsed_inclusive_seconds']==494.6009602919803 and done['total_inclusive_seconds']==527.9604928489425 and done['total_inclusive_seconds']<1800,
'no_cost_or_retry':sorted(p.name for p in R.parent.iterdir() if p.is_dir())==['green','red']}
if not all(checks.values()):raise SystemExit(str(checks))
paths=[test,original,fixture,stage,P/'ADMISSION-PREPARATION.md',P/'contract.json',R/'guard/run.log',R/'guard/process.json',R/'supervisor.json',R/'completion.json',R/'result.toml',D/'postcheck.json']
result=dict(accepted=True,scope='source/raw diagnosis only; GREEN remains NOT ACCEPTED, no rerun or repair',checks=checks,bindings={str(p):sha(p) for p in paths},missing_path=str(missing),original_fixture=dict(path=str(fixture),size_bytes=fixture.stat().st_size,sha256=sha(fixture)),ordinary_summary=dict(Pass=5772,Fail=0,Error=1,Broken=0,Total=5773),expected_unreached_checks=['Numerical strategy propagation: result.status == OPTIMAL','Numerical strategy propagation: !isempty(observed) && all(==(7), observed)'],remaining_shared_seconds=1800-done['total_inclusive_seconds'])
with (D/'cause-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
with (D/'cause-check.py').open('xb') as f:f.write(Path(__file__).read_bytes())
print(json.dumps(dict(accepted=True,checks=len(checks),bindings=len(paths),original_fixture=result['original_fixture'],remaining_shared_seconds=result['remaining_shared_seconds'])))
