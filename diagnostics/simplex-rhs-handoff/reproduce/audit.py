from pathlib import Path
import hashlib,json,subprocess,tomllib,shutil,re
root=Path.cwd();raw=root/'.superpowers/simplex-rhs-handoff'
out=root/'diagnostics/simplex-rhs-handoff/results';out.mkdir(parents=True,exist_ok=True)
load=lambda p:tomllib.loads(p.read_text())
validation=json.loads((raw/'validation-results.json').read_text())
assert len(validation)==7,validation
for j in validation:
 p=json.loads((raw/j['job']/'process.json').read_text())
 assert p['sources_unchanged']
 for pinned_path,digest in json.loads((raw/j['job']/'preflight.json').read_text()).items():
  assert hashlib.sha256(Path(pinned_path).read_bytes()).hexdigest()==digest,pinned_path
 assert p['returncode']==j['returncode']
 if j['job']!='project-suite':assert j['returncode']==0,j
# This audit describes the preserved run, not an arbitrary future suite failure.
suite_log=(raw/'project-suite/run.log').read_text(errors='replace')
assert validation[-1]==dict(job='project-suite',returncode=75)
assert 'wall-time guard; terminating owned process group' in suite_log
assert 'legacy_primal_working_row_scope_tests.jl:25' in suite_log
assert 'Test Failed' not in suite_log and 'Error During Test' not in suite_log
source={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'src').rglob('*.jl')}
comparisons=[]
for case in ('fast','medium','runtime'):
 before=load(root/f'diagnostics/simplex-shared-work/results/{case}-candidate.toml')
 after=load(raw/f'{case}-candidate/result.toml')
 for f,digest in before['source_hashes'].items():
  assert hashlib.sha256(subprocess.check_output(['git','show',f'1557354:{f}'])).hexdigest()==digest
 assert after['source_hashes']==source
 assert len(before['cases'])==len(after['cases'])
 prior_pins=json.loads((root/f'.superpowers/simplex-shared-work/{case}-candidate/preflight.json').read_text())
 new_pins=json.loads((raw/f'{case}-candidate/preflight.json').read_text())
 for rel in ('Project.toml','Manifest.toml','LocalPreferences.toml'):
  assert prior_pins[str(root/rel)]==new_pins[str(root/rel)]
 for a,b in zip(before['cases'],after['cases']):
  keys=set(a)|set(b);keys.remove('seconds_instrumented')
  assert all(a.get(k)==b.get(k) for k in keys),[(k,a.get(k),b.get(k)) for k in keys if a.get(k)!=b.get(k)]
  comparisons.append(dict(case=case,algorithm=b['algorithm'],manager=b['manager'],status=b['status'],
   iterations=b['iterations'],refactorizations=b['refactorizations'],numerically_identical=True,
   before_seconds=a['seconds_instrumented'],after_seconds=b['seconds_instrumented']))
 shutil.copy2(raw/f'{case}-candidate/result.toml',out/f'{case}-candidate.toml')
bench=load(raw/'production-kernel/results.toml')
assert len(bench['results'])==45
assert all(r['equal'] and r['baseline_bytes']==r['unit_bytes']==0 for r in bench['results'])
shutil.copy2(raw/'production-kernel/results.toml',out/'production-kernel.toml')
shutil.copy2(raw/'probe-1/results.toml',out/'prototype-kernel.toml')
logs=[]
for job in ('final-targeted','targeted-2','semantic','project-suite'):
 lines=(raw/job/'run.log').read_text(errors='replace').splitlines()
 summary=[l for l in lines if '|' in l or any(w in l for w in ('TEST ','Maximum resident','Elapsed (wall','ERROR:','Test Failed','Error During','TIME_LIMIT','guard','signal','LLVM','Exit status'))]
 logs.append(job+'\n'+'\n'.join(summary)+'\n')
(out/'test-summaries.txt').write_text('\n'.join(logs))
result=dict(baseline='15573547d12c16838abd1c7b93870ee478f6ff5c',jobs=validation,
 source_hashes=source,comparisons=comparisons,paired_cases=len(comparisons),
 kernel_cases=45,final_targeted_assertions=12154,semantic_assertions=15689,
 project_suite=dict(status="wall_time_guard",limit_seconds=600,returncode=75,
 last_test="legacy_primal_working_row_scope_tests.jl:25",assertion_failures_reported=0,
 complete=False,llvm_cause_confirmed=False),
 limitations=['Kernel measurements use Float64/native only.','Medium checks are fixed iteration prefixes, not full solves.',
 'Instrumented solve timings are single samples, not whole-solver speedup evidence.'])
(out/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(jobs=validation,comparisons=comparisons),indent=2))
