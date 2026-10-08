"""Audit completed solver checks and retain compact evidence and raw-log hashes."""
from pathlib import Path
import hashlib,json,math,re,shutil,sys,tomllib
root=Path(__file__).resolve().parents[3]; raw=Path(sys.argv[1]).resolve()
out=root/'diagnostics/triangular-stability/results'
initial_attempts=json.loads((raw/'final-results.json').read_text())
assert initial_attempts[-1]['job']=='runtime-ss1600' and initial_attempts[-1]['returncode']==143
assert not (raw/'runtime-ss1600.toml').exists()
retry_attempts=json.loads((raw/'retry-results.json').read_text())
assert retry_attempts[-1]['job']=='runtime-ss1600-v2' and retry_attempts[-1]['returncode']==143
assert not (raw/'runtime-ss1600-v2.toml').exists()
observed_attempts=json.loads((raw/'observed-results.json').read_text())
assert observed_attempts[-1]['job']=='runtime-ss1600-observed' and observed_attempts[-1]['returncode']==143
assert not (raw/'runtime-ss1600-observed.toml').exists()
jobs=initial_attempts[:-1]+retry_attempts[:-1]+json.loads((raw/'warm-results.json').read_text())
expected={'portable-final','semantic','pilotnov-matrix','external','portable-reviewed','precise-replay','runtime-ss1600-warm','runtime-ft1600-warm','project-suite'}
assert len(jobs)==len(expected) and {r['job'] for r in jobs}==expected
assert all(r['sources_unchanged'] for r in jobs)
assert all(r['returncode']==0 for r in jobs if r['job']!='project-suite')
project=next(r for r in jobs if r['job']=='project-suite')
assert project['returncode']==75
project_log=(raw/'project-suite.log').read_text()
assert 'wall-time guard; terminating owned process group' in project_log
assert 'libLLVM.so' in project_log and 'test/primal_initial_tolerance_tests.jl:3' in project_log
assert 'Test Failed' not in project_log and 'Error During Test' not in project_log
project['outcome']='incomplete: wall-time guard, interrupted stack in LLVM compilation'
shutil.copyfile(raw/'project-suite.log',out/'project-suite-interrupted.log')
h=hashlib.sha256()
for p in sorted([root/'Project.toml',*root.glob('src/**/*.jl')]):h.update(str(p.relative_to(root)).encode()+b'\0'+p.read_bytes())
assert all(r['source_sha256']==h.hexdigest() for r in jobs)
read=lambda p:tomllib.loads(p.read_text())
manifest=read(root/'diagnostics/basis-selective-preparation/reproduce/external-inputs.toml')['cases']
external=read(raw/'external.toml')['cases'];managers={'pfi','huangfu_hall','forrest_tomlin','suhl_suhl','bartels_golub'}
expected_keys={(e['id'],a,b,m) for e in manifest for a in ('primal','dual') for b in ('native','markowitz') for m in managers}
assert len(external)==len(expected_keys)==100
assert {(r['id'],r['algorithm'],r['backend'],r['basis_update']) for r in external}==expected_keys
refs={r['id']:r for r in manifest}
for r in external:
 assert r['status']=='OPTIMAL' and r['original_primal_certified'] and r['objective_matches']
 assert r['input_sha256']==refs[r['id']]['sha256']
 assert abs(r['objective']-refs[r['id']]['objective'])<=max(1e-7,1e-8*abs(refs[r['id']]['objective']))
pilotnov=[read(p) for p in sorted((raw/'pilotnov-matrix').glob('*.toml'))]
assert len(pilotnov)==10 and {(r['manager'],r['backend']) for r in pilotnov}=={(m,b) for m in managers for b in ('native','markowitz')}
for r in pilotnov:
 assert r['status']=='OPTIMAL' and r['original_primal_feasible'] and r['reference_matches']
 assert abs(r['objective']+4497.2761882188715)<1e-5
runtime=[]
for name in ('runtime-ss1600-warm','runtime-ft1600-warm'):
 r=read(raw/(name+'.toml'))
 assert r['status']=='OPTIMAL' and r['original_primal_feasible'] and r['objective_matches']
 assert r['input_sha256']=='d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68'
 assert abs(r['objective']-51425691.76210454)<=1e-4
 assert r['interval']==1600 and r['algorithm']=='dual' and r['backend']=='native'
 assert r['julia_threads']==r['blas_threads']==1
 assert r['manager']==('suhl_suhl' if name.startswith('runtime-ss') else 'forrest_tomlin')
 assert r['events'].get('precision_boost',0)==0
 runtime.append(r)
 shutil.copyfile(raw/(name+'.toml'),out/(name+'.toml'))
 lines=(raw/(name+'.log')).read_text().splitlines()
 (out/(name+'-summary.log')).write_text('\n'.join(l for l in lines if not l.startswith('[ Info: iter='))+'\n')
interrupted=[initial_attempts[-1],retry_attempts[-1],observed_attempts[-1]]
for r in jobs+interrupted:
 text=(raw/(r['job']+'.log')).read_text();r['log_sha256']=hashlib.sha256(text.encode()).hexdigest()
 match=re.search(r'Maximum resident set size \(kbytes\): (\d+)',text)
 r['peak_rss_kib']=int(match[1]) if match else None
 r['wall_seconds']=r['ended']-r['started']
for name in ('targeted-v2','portable-reviewed','semantic','project-suite'):
 lines=(raw/(name+'.log')).read_text().splitlines()
 (out/(name+'-summary.log')).write_text('\n'.join(l for l in lines if l.startswith(('TEST ','Test Summary:','Triangular ','Row swaps','A zero','Native terminal','JSimplex','\t')))+'\n')
precise=read(raw/'precise-replay.toml')
assert precise['interval']==320 and precise['arm']=='direct-suhl_suhl-native'
assert precise['records'][-1]['step']==640
checks=[c for r in precise['records'] for c in r['checks']]
assert all(math.isfinite(c[k]) for c in checks for k in ('residual','reference_residual','difference'))
assert all(max(c['residual'],c['reference_residual'])<=1e-10 and c['difference']<=1e-6 for c in checks)
precise_residual=precise['records'][-1]['precise_factor_dense_residual']
assert math.isfinite(precise_residual) and precise_residual<=1e-10
precise_summary={k:v for k,v in precise.items() if k!='records'}
precise_summary.update(final_step=640,probes=len(checks),
 maximum_native_residual=max(c['residual'] for c in checks),
 precise_factor_dense_residual=precise_residual,
 raw_report_sha256=hashlib.sha256((raw/'precise-replay.toml').read_bytes()).hexdigest())
(out/'precise-replay.json').write_text(json.dumps(precise_summary,indent=2)+'\n')
shutil.copyfile(raw/'external.toml',out/'external.toml')
(out/'pilotnov.json').write_text(json.dumps(pilotnov,indent=2)+'\n')
files=[root/'src/triangular_factorization.jl',root/'src/triangular_rows.jl',root/'src/hypersparse_updates.jl',root/'test/triangular_stability_tests.jl',root/'test/runtests.jl',root/'diagnostics/numerical-guard-repair/reproduce/ss_replay_probe.jl',*Path(__file__).parent.glob('*.jl'),*Path(__file__).parent.glob('*.py')]
followup=json.loads((raw/'initial-tolerance-semantic.process.json').read_text())
assert followup['returncode']==0 and followup['source_sha256']==h.hexdigest()
followup['log_sha256']=hashlib.sha256((raw/'initial-tolerance-semantic.log').read_bytes()).hexdigest()
shutil.copyfile(raw/'initial-tolerance-semantic.log',out/'initial-tolerance-semantic.log')
report=dict(project_suite_passed=False,initial_tolerance_followup=followup,source_sha256=h.hexdigest(),source_hash_order='Python Path order',external_unique_combinations=100,pilotnov_unique_combinations=10,
 external_all_original_feasible=True,external_all_reference_matches=True,jobs=jobs,interrupted_attempts=interrupted,startup_interruptions=[json.loads((raw/n).read_text()) for n in ('ss-startup-interruption.json','ss-startup-interruption-v2.json','ss-startup-interruption-observed.json')],
 files_sha256={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
(out/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('Verified 100 external combinations, 10 pilotnov combinations and both full runtime solves; project suite incomplete at LLVM wall-time guard')
