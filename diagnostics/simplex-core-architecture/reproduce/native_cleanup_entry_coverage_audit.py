"""S6-AO per-attempt exclusive source/log/pin audit; never rerun accepted modes."""
from pathlib import Path
import json,tomllib,hashlib,sys,shutil,re
r=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');d=r/'diagnostics/simplex-core-architecture';o=d/'results/S6-AO';mode=sys.argv[1];project=Path(sys.argv[2]);b=r/'.superpowers/simplex-core-architecture/S6-AO'/mode
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();p=json.loads((b/'process.json').read_text());pins=json.loads((b/'pins.json').read_text());pre=json.loads((o/'preflight.json').read_text());host=json.loads((o/('host-after-'+mode+'.json')).read_text());m=tomllib.loads((b/'report.toml').read_text())['metadata'];log=(b/'run.log').read_text();source=(project/'test/primal_perturbation_integration_tests.jl').read_bytes();old=(o/'original-test.jl.txt').read_bytes();new=source[len(old):].decode().lstrip('\n');driver=d/'reproduce/native_cleanup_entry_coverage.jl';resources=[json.loads(x) for x in (b/'resources.jsonl').read_text().splitlines()]
newsource=new[new.index("# Exercise native cleanup's first public entry"):]
checks={
 'exit0':p['returncode']==0 and p['reason']=='exit0',
 'runtime_test_success':bool(re.search(r'Native entry coverage actual source\s*\|\s+(\d+)\s+\1\s',log)) and 'Test Failed' not in log and 'Error During Test' not in log and m['exception']=='none',
 'guard_and_independent_pins':p['pins_unchanged'] and all(h(Path(k))==v['sha256'] and str(Path(k).resolve())==v['resolved'] for k,v in pins['inventory'].items()),
 'expected_actual_root':m['root']==str(project) and m['source']==str(project/'src/JSimplex.jl'),
 'actual_test_source':m['test_sha256']==hashlib.sha256(source).hexdigest() and source==(o/'green-test.jl.txt').read_bytes(),
 'actual_new_source':m['new_sha256']==hashlib.sha256(newsource.encode()).hexdigest(),
 'original_byte_prefix':source.startswith(old) and hashlib.sha256(old).hexdigest()==pre['original_test_sha256'],
 'original_helpers':m['helper_sha256']==pre['helper_hashes']['shifted_primal_workspace'] and m['monitor_sha256']==pre['helper_hashes']['primal_stalled_monitor'],
 'actual_driver':driver.read_bytes()==(o/'driver.jl.txt').read_bytes(),
 'threads_globals':m['threads']==m['blas_threads']==1 and m['globals_preserved'],
 'contract_production_source':all(h(project/k)==v for k,v in pre['source_hashes'].items() if k!='test/primal_perturbation_integration_tests.jl'),
 'six_user_files':all(h(Path(k))==v for k,v in pre['user_hashes'].items()),
 'host_gone_sameboot':host['boot_id']==p['runner']['boot_id']==p['child']['boot_id'] and not host['julia'] and not any(x['present'] for x in host['processes']),
 'two_cases_source_bound':new.count('for mode in (:stop, :throw)')==1 and new.count('run_from_basis!')==1 and new.count('shifted_primal_workspace()')==1 and new.count('_primal_optimize!')==1 and new.count('SimplexRunBudget(')==1,
 'callback_preforward':new.index('callback_calls[] += 1')<new.index('mode == :throw && throw(sentinel)') and '@test callback_calls[] == 1' in new,
 'whole_work_and_state':all(t in new for t in ['@test d.kernel_calls == before.kernel_calls','@test ws.scratch.perturbations === journal','@test (objectid(ws.lower), objectid(ws.upper)) == before.storage','@test ws.progress.start_ns == budget.start_ns == before.start_ns','before.journal_flags','before.matrix','before.row_scaling']),
 'payload_and_exception':all(t in new for t in ['caught === sentinel && isnothing(run)','isnothing(run.primal) && isnothing(run.objective_value) && isnothing(run.basis)','time limit reached during feasibility recovery']),
 'events_complete':all(t in new for t in ['@test d.next_event == before.next_event +','for k in keys(d.counts)']),
 'no_hidden_full_file_run':'include_string(Main,NEW,' in driver.read_text() and 'include_string(Main,SOURCE' not in driver.read_text(),
 'resource_guard':bool(resources) and min(x['available_kib'] for x in resources)>=6*1024*1024 and max(x['swap_used_kib'] for x in resources)<=1024*1024}
summary=re.search(r'Native entry coverage actual source\s*\|\s+(\d+)\s+(\d+)\s',log)
result={'checks':checks,'all_passed':all(checks.values()),'assertions':int(summary.group(1)) if summary else None,'pin_count':len(pins['inventory']),'resource_samples':len(resources),'min_available_kib':min(x['available_kib'] for x in resources),'max_swap_used_kib':max(x['swap_used_kib'] for x in resources),'scope':'Actual new test source assertions/log binding; not per-case value/clock census, real deadline expiry, historical cause or whole-suite proof.'}
with (o/(mode+'-audit.json')).open('x') as f:json.dump(result,f,indent=2);f.write('\n')
for name in ['report.toml','process.json','pins.json','run.log','resources.jsonl']:shutil.copyfile(b/name,o/(mode+'-'+name))
print(json.dumps(result,indent=2));assert result['all_passed']
