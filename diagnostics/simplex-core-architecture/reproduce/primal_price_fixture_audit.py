from pathlib import Path
import sys,json,tomllib,hashlib,importlib.util,re,shutil
sys.dont_write_bytecode=True
root=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');d=root/'diagnostics/simplex-core-architecture';name=sys.argv[1];project=Path(sys.argv[2]) if len(sys.argv)>2 else root;base=root/'.superpowers/simplex-core-architecture/S6-W'/name;out=d/'results/S6-W'
r=tomllib.loads((base/'report.toml').read_text());p=json.loads((base/'process.json').read_text());pins=json.loads((base/'pins.json').read_text());log=(base/'run.log').read_text();mode=r['mode'];source=(project/'test/legacy_primal_direction_price_tests.jl').read_text();original=(out/'original-test.jl').read_text()
s=importlib.util.spec_from_file_location('g',d/'reproduce/guarded_run.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
checks={'process_exit':p['returncode']==(1 if mode=='red' else 0) and p['reason']==('exit1' if mode=='red' else 'exit0') and p['pins_unchanged'],'pins_guard':g.pins_match(pins),'pins_independent':all(hashlib.sha256(Path(k).read_bytes()).hexdigest()==v['sha256'] and str(Path(k).resolve())==v['resolved'] for k,v in pins['inventory'].items()),'actual_source':r['source']==str(project/'src/JSimplex.jl'),'test_hash':r['test_sha256']==hashlib.sha256(source.encode()).hexdigest(),'one_thread':r['julia_threads']==r['blas_threads']==1,'globals_preserved':r['globals_preserved']}
paths=set(pins['files'])
for t in pins['trees']:paths.update(str(v) for v in Path(t).rglob('*') if v.is_file())
checks['inventory_membership']=paths==set(pins['inventory'])
marker='@testset "A repeated price disagreement cannot renew the recovery budget" begin'
oldtarget=marker+original.split(marker,1)[1]
target=marker+source.split(marker,1)[1]
checks['actual_target']=r['target']==target
checks['no_test_errors']='Error During Test' not in log
if mode=='red':
 checks['unchanged_old_test']=source==original
 checks['zero_solve_execution']=r['selected']==r['executed']=='' and r['records']==[] and 'Loaded problem:' not in log
 checks['expected_structural_failures']=len(re.findall(r'Test Failed at',log))==2 and 'repeated_price_budget_fixture' in log and 'cost_btrans==1' in log
else:
 checks['native_and_adjacent_byte_identical']=source.split('# Scoped Float64 fixture',1)[0]==original.split(marker,1)[0]
 added=['        @test ws.factorization.cost_btrans==1','        @test ws.factorization.correction_btrans==1','        @test ws.factorization.total_btrans==2','        @test ws.factorization.hits==1']
 restored=target.replace('ws=repeated_price_budget_fixture(manager;diagnostics)','ws=native_price_roundoff_fixture(Float64,manager;diagnostics)')
 for line in added:restored=restored.replace(line+'\n','')
 checks['original_target_byte_identical_except_call_and_additions']=restored==oldtarget and all(line in target for line in added)
 checks['no_failures']='Test Failed' not in log and 'Error During Test' not in log
 checks['four_manager_counts']=len(r['records'])==4 and all(x['cost']==x['correction']==x['hits']==1 and x['total']==2 for x in r['records']) and set(x['manager'] for x in r['records'])=={'pfi','forrest_tomlin','suhl_suhl','bartels_golub'}
 checks['selected_state_unchanged']=all(x['before']==x['after'] and x['after']['iterations']==0 for x in r['records'])
 neighbor='@testset "Native price recovery is atomic and respects policy limits" begin'
 neighborbody=neighbor+source.split(neighbor,1)[1].split('\n@testset',1)[0]
 checks['exact_selection']=r['selected']==target+('\n'+neighborbody if mode=='green' else '')
 before='        before=state(ws)\n'
 after='\n        push!(RECORDS,Dict("manager"=>string(manager),"before"=>before,"after"=>state(ws),"cost"=>ws.factorization.cost_btrans,"correction"=>ws.factorization.correction_btrans,"total"=>ws.factorization.total_btrans,"hits"=>ws.factorization.hits))'
 checks['only_readonly_execution_additions']=r['executed'].replace(before,'').replace(after,'')==r['selected']
 checks['expected_pass_counts']=bool(re.search(r'budget\s+\|\s+36\s+36\s+',log)) and bool(re.search(r'preservation\s+\|\s+5\s+5\s+',log)) and (mode!='green' or bool(re.search(r'policy limits\s+\|\s+68\s+68\s+',log)))
 if mode=='master':checks['same_green_source']=source==(out/'green-1-test.jl').read_text()
audit={'checks':checks,'all_passed':all(checks.values()),'pin_count':len(pins['inventory']),'summary':[line for line in log.splitlines() if re.search(r'\|\s+\d',line)],'mode':mode,'scope':'Test-only bounded new-source checks; selected snapshots do not prove hidden trajectories, x64 or full-suite success.'}
with (out/(name+'-audit.json')).open('x') as f:json.dump(audit,f,indent=2);f.write('\n')
for n in ['report.toml','process.json','pins.json','run.log']:shutil.copyfile(base/n,out/(name+'-'+n))
shutil.copyfile(project/'test/legacy_primal_direction_price_tests.jl',out/(name+'-test.jl'))
shutil.copyfile(d/'reproduce/primal_price_fixture_repair.jl',out/(name+'-driver.jl'))
print(json.dumps(audit,indent=2));assert audit['all_passed']
