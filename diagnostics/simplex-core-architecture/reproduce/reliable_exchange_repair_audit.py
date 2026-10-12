from pathlib import Path
import json,tomllib,hashlib,sys,importlib.util,shutil,re
sys.dont_write_bytecode=True
root=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');d=root/'diagnostics/simplex-core-architecture';out=d/'results/S6-AA';name=sys.argv[1];base=root/'.superpowers/simplex-core-architecture/S6-AA'/name
r=tomllib.loads((base/'report.toml').read_text());p=json.loads((base/'process.json').read_text());pins=json.loads((base/'pins.json').read_text());log=(base/'run.log').read_text();mode=r['mode'];project=Path(r['source']).parents[1];source=(project/'test/native_phase_transfer_tests.jl').read_text();original=(out/'original-test.jl').read_text()
spec=importlib.util.spec_from_file_location('g',d/'reproduce/guarded_run.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def extract(s,title):
 marker='@testset "'+title+'" begin';return marker+s.split(marker,1)[1].split('\n@testset',1)[0]
oldtarget=extract(original,'Reliable artificial exchanges need no reconstruction recovery');newtarget=oldtarget.replace('artificial_exchange_roundoff_fixture','reliable_artificial_exchange_fixture')
checks={'exit_expected':p['returncode']==(1 if mode=='red' else 0) and p['reason']=='exit'+str(p['returncode']),'guard_pins':p['pins_unchanged'] and g.pins_match(pins),'independent_pins':all(sha(k)==v['sha256'] and str(Path(k).resolve())==v['resolved'] for k,v in pins['inventory'].items()),'source_project':project==Path('/home/jspitz/JSimplex.jl') if mode=='master' else project==root,'test_hash':r['test_sha256']==sha(project/'test/native_phase_transfer_tests.jl'),'threads':r['julia_threads']==r['blas_threads']==1,'globals':r['globals_preserved'],'native_helper_unchanged':r['native_helper']=='function artificial_exchange_roundoff_fixture'+original.split('function artificial_exchange_roundoff_fixture',1)[1].split('\n@testset',1)[0],'target_actual':r['target']==extract(source,'Reliable artificial exchanges need no reconstruction recovery')}
paths=set(pins['files'])
for t in pins['trees']:paths.update(str(v) for v in Path(t).rglob('*') if v.is_file())
checks['inventory_membership']=paths==set(pins['inventory'])
if mode=='red':
 checks.update({'old_source_exact':source==original,'zero_exchanges':r['selected']=='','two_expected_failures':log.count('Test Failed at')==2 and 'Error During Test' not in log,'helper_absent':r['new_helper']==''})
else:
 expected=(out/'expected-test.jl').read_text();checks['only_intended_source_change']=source==expected;checks['four_original_assertions']=r['target']==newtarget
 z=tomllib.loads((d/'results/S6-Z/qualification-1-report.toml').read_text());checks['helper_matches_qualification']=r['new_helper'].strip()==z['qualified_helper'].replace('reliable_exchange_fixture','reliable_artificial_exchange_fixture').strip()
 selected=newtarget+('\n'+extract(original,'Artificial exchange recovery preserves cancellation and policy limits') if mode=='green' else '')
 checks['actual_selected_oracle']=r['selected']==selected
 checks['all_neighbors_unchanged']=all(extract(source,t)==extract(original,t) for t in re.findall(r'@testset "([^"]+)" begin',original) if t!='Reliable artificial exchanges need no reconstruction recovery')
 checks['all_tests_pass']='Test Failed' not in log and 'Error During Test' not in log and '|   16     16' in log and ('|  108    108' in log if mode=='green' else True)
 if mode=='master':checks['green_source_identity']=source==(out/'green-1-test.jl').read_text()
checks['user_hashes']=all(sha(Path('/home/jspitz/JSimplex.jl')/k)==v for k,v in json.loads(Path('/tmp/jsimplex-main-preserved.json').read_text()).items())
audit={'checks':checks,'all_passed':all(checks.values()),'pin_count':len(pins['inventory']),'mode':mode,'summary':[l for l in log.splitlines() if re.search(r'\|\s+\d',l)],'scope':'Structural RED only; actual new-source selected GREEN/master tests. No original solver/corpus replay or x64/fullsuite proof.'}
with (out/(name+'-audit.json')).open('x') as f:json.dump(audit,f,indent=2);f.write('\n')
for n in ('report.toml','pins.json','process.json','run.log'):shutil.copyfile(base/n,out/(name+'-'+n))
shutil.copyfile(d/'reproduce/reliable_exchange_repair.jl',out/(name+'-driver.jl'));shutil.copyfile(project/'test/native_phase_transfer_tests.jl',out/(name+'-test.jl'))
print(json.dumps(audit,indent=2));assert audit['all_passed']
