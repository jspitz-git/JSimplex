from pathlib import Path
import json,tomllib,hashlib,statistics,subprocess,itertools
root=Path(__file__).resolve().parents[3];main=Path('/home/jspitz/JSimplex.jl');raw=root/'.superpowers/dual-residual-work/final';out=root/'diagnostics/dual-residual-work/results'
expected=['paired','runtime-baseline-1','runtime-candidate-1','runtime-candidate-2','runtime-baseline-2','targeted-external','semantic','project-suite']
records=json.loads((raw/'jobs.json').read_text());assert [r['job'] for r in records]==expected
candidate_pins=None;outcomes={}
for record in records:
 name=record['job'];p=raw/name;process=json.loads((p/'process.json').read_text());assert process['sources_unchanged']
 assert process['returncode']==record['returncode']
 pins=json.loads((p/'preflight.json').read_text());src={k:v for k,v in pins.items() if k.startswith(str(root/'src')+'/')}
 if candidate_pins is None:candidate_pins=src
 assert src==candidate_pins
 for path,digest in src.items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest
 if name!='project-suite':assert process['returncode']==0
 if process['returncode']==0:outcomes[name]='passed'
 else:
  log=(p/'run.log').read_text()
  # A timeout is valid evidence of incomplete coverage, never test success.
  assert 'wall-time guard; terminating owned process group' in log,log[-3000:]
  outcomes[name]='guard_timeout_with_test_failures' if 'Test Failed' in log or 'Error During Test' in log else 'guard_timeout_incomplete'
runtime=[];reference=None
for name in expected[1:5]:
 p=raw/name;d=tomllib.load((p/'results.toml').open('rb'));pins=json.loads((p/'preflight.json').read_text());process=json.loads((p/'process.json').read_text())
 project=main if 'baseline' in name else root
 assert d['source']==str(project/'src/JSimplex.jl') and process['effective_project']==str(project)
 assert d['input_sha256']==pins['/home/jspitz/mps/runtime.mps']=='d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68'
 if project==main:
  for path,digest in pins.items():
   if path.startswith(str(main/'src')+'/'):
    content=subprocess.check_output(['git','show','9c67ab2:'+str(Path(path).relative_to(main))],cwd=main)
    assert hashlib.sha256(content).hexdigest()==digest
 assert d['status']=='OPTIMAL' and d['original_feasible'] and d['iterations']==54591 and d['refactorizations']==194
 assert d['events_hash']=='6330422d394b22e155e2ecd58fb96fd3a89035a8d86ed6b07722c348bd59ccdb'
 assert d['states_hash']=='1af4c4c85c63a500a038b6101718f969d8a0ab11fb5a978ee2ba77e1621eb743'
 if reference is None:reference=d
 assert d['objective']==reference['objective'] and d['events']==reference['events']
 runtime.append(dict(job=name,seconds=d['seconds'],compile_seconds=d['compile_seconds'],gc_seconds=d['gc_seconds'],allocations=d['allocations'],bytes=d['bytes']))
external=tomllib.load((raw/'targeted-external/results.toml').open('rb'))['cases'];manifest=tomllib.load((root/'diagnostics/basis-selective-preparation/reproduce/external-inputs.toml').open('rb'))['cases']
key=lambda r:(r['id'],r['algorithm'],r['backend'],r['basis_update'])
keys=set(itertools.product([r['id'] for r in manifest],['primal','dual'],['native','markowitz'],['pfi','forrest_tomlin','suhl_suhl','bartels_golub','huangfu_hall']))
assert len(external)==100 and {key(r) for r in external}==keys
manifest={r['id']:r for r in manifest}
for r in external:
 assert r['status']=='OPTIMAL' and r['original_primal_certified'] and r['objective_matches']
 assert r['input_sha256']==manifest[r['id']]['sha256'] and r['reference_objective']==manifest[r['id']]['objective']
old_external=tomllib.load((root/'diagnostics/simplex-data-movement/results/external.toml').open('rb'))['cases']
old_external={key(r):r for r in old_external}
assert all(r['iterations']==old_external[key(r)]['iterations'] and r['objective']==old_external[key(r)]['objective'] for r in external)
provenance=json.loads((out/'external-script-provenance.json').read_text());assert hashlib.sha256(Path(provenance['path']).read_bytes()).hexdigest()==provenance['sha256']==provenance['baseline_sha256']
paired=tomllib.load((raw/'paired/results.toml').open('rb'))['cases'];assert len(paired)==23
assert all(all(x==0 for x in r['candidate_batch_bytes']) and all(x==0 for x in r['candidate_batch_allocations']) for r in paired)
summary=dict(runtime=runtime,external_unique_certified=100,external_objectives_and_iterations_match_prior=True,paired_cases=23,all_runtime_fingerprints_and_events_match=True,source_and_input_provenance_checked=True,process_outcomes=outcomes)
summary['baseline_mean']=statistics.mean(r['seconds'] for r in runtime if 'baseline' in r['job']);summary['candidate_mean']=statistics.mean(r['seconds'] for r in runtime if 'candidate' in r['job']);summary['relative_reduction']=1-summary['candidate_mean']/summary['baseline_mean']
print(json.dumps(summary,indent=2));(out/'final-audit.json').write_text(json.dumps(summary,indent=2)+'\n')

# Preserve baseline failures explicitly; a guard exit must never hide assertions.
import re
signatures=[]
for name in ('legacy-triage-baseline','legacy-triage-candidate'):
 p=root/'.superpowers/dual-residual-work'/name
 process=json.loads((p/'process.json').read_text());assert process['returncode']==1 and process['sources_unchanged']
 log=(p/'run.log').read_text()
 assert log.count('Test Failed at')==25 and log.count('Error During Test at')==2
 signatures.append([re.sub(r'/home/jspitz/(?:\.codex/worktrees/simplex-shared-work/)?JSimplex.jl','ROOT',line) for line in log.splitlines() if any(token in line for token in ('Test Failed at','Error During Test at','  Expression:','   Evaluated:','FieldError:'))])
assert signatures[0]==signatures[1]
summary['existing_suite_failures']={'baseline_and_candidate_identical':True,'failures':25,'errors':2,'passed':313}
(out/'final-audit.json').write_text(json.dumps(summary,indent=2)+'\n')
