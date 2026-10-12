from pathlib import Path
import sys,json,tomllib,hashlib,importlib.util,shutil,re
sys.dont_write_bytecode=True
root=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');d=root/'diagnostics/simplex-core-architecture';o=d/'results/S6-AC';name=sys.argv[1];base=root/'.superpowers/simplex-core-architecture/S6-AC'/name
r=tomllib.loads((base/'report.toml').read_text());p=json.loads((base/'process.json').read_text());pins=json.loads((base/'pins.json').read_text());log=(base/'run.log').read_text();mode=r['mode'];project=Path(r['source']).parents[1];s=(project/'test/native_phase_transfer_tests.jl').read_text();old=(o/'original-test.jl').read_text()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('g',d/'reproduce/guarded_run.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
def extract(s,title):
 marker='@testset "'+title+'" begin';return marker+s.split(marker,1)[1].split('\n@testset',1)[0]
title='Artificial exchanges certify native reconstruction before export';target=extract(s,title)
checks={'exit_expected':p['returncode']==(1 if mode=='red' else 0) and p['reason']=='exit'+str(p['returncode']),'guard_pins':p['pins_unchanged'] and g.pins_match(pins),'independent_pins':all(sha(k)==v['sha256'] and str(Path(k).resolve())==v['resolved'] for k,v in pins['inventory'].items()),'actual_source':project==(Path('/home/jspitz/JSimplex.jl') if mode=='master' else root),'test_hash':r['test_sha256']==sha(project/'test/native_phase_transfer_tests.jl'),'threads':r['julia_threads']==r['blas_threads']==1,'globals':r['globals_preserved'],'native_helper_unchanged':r['native_helper']=='function artificial_exchange_roundoff_fixture'+old.split('function artificial_exchange_roundoff_fixture',1)[1].split('\n@testset',1)[0],'target_actual':r['target']==target}
paths=set(pins['files'])
for t in pins['trees']:paths.update(str(v) for v in Path(t).rglob('*') if v.is_file())
checks['inventory_membership']=paths==set(pins['inventory'])
if mode=='red':
 checks.update({'old_source_exact':s==old,'zero_exchanges':r['selected']=='','two_expected_failures':log.count('Test Failed at')==2 and 'Error During Test' not in log,'adapter_absent':'struct PhaseReconstructionFactor' not in s})
else:
 checks['expected_source']=s==(o/'expected-test.jl').read_text()
 checks['seven_original_assertions']=all(line in target for line in extract(old,title).splitlines() if '@test ' in line) and sum('@test ' in line for line in extract(old,title).splitlines())==7
 checks['all_neighbors_unchanged']=all(extract(s,t)==extract(old,t) for t in re.findall(r'@testset "([^"]+)" begin',old) if t!=title)
 checks['original_prefix_retained']=r['prefix'].startswith(old.split('\n@testset',1)[0])
 selected=target+(''.join('\n'+extract(old,t) for t in ['Artificial exchange recovery preserves cancellation and policy limits','Reliable artificial exchanges need no reconstruction recovery']) if mode=='green' else '')
 checks['actual_selected_oracles']=r['selected']==selected
 checks['target_pass']='|  192    192' in log
 checks['microtests_pass']='Pre-forward attempt accounting' in log and '|   20     20' in log
 checks['all_pass']='Test Failed' not in log and 'Error During Test' not in log
 if mode=='green':checks['neighbors_pass']='|  108    108' in log and '|   16     16' in log
 if mode=='master':checks['green_identity']=s==(o/'green-1-test.jl').read_text()
checks['user_hashes']=all(sha(Path('/home/jspitz/JSimplex.jl')/k)==v for k,v in json.loads(Path('/tmp/jsimplex-main-preserved.json').read_text()).items())
a={'checks':checks,'all_passed':all(checks.values()),'pin_count':len(pins['inventory']),'mode':mode,'summary':[l for l in log.splitlines() if re.search(r'\|\s+\d',l)],'scope':'Structural RED; new-source target/neighbor and wrapper accounting gates only, no historical numerical cause/x64/fullsuite proof.'}
with (o/(name+'-audit.json')).open('x') as f:json.dump(a,f,indent=2);f.write('\n')
for n in ['report.toml','pins.json','process.json','run.log']:shutil.copyfile(base/n,o/(name+'-'+n))
shutil.copyfile(d/'reproduce/phase_reconstruction_repair.jl',o/(name+'-driver.jl'));shutil.copyfile(project/'test/native_phase_transfer_tests.jl',o/(name+'-test.jl'))
print(json.dumps(a,indent=2));assert a['all_passed']
