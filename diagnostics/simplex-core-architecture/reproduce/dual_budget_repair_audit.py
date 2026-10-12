from pathlib import Path
import sys,json,tomllib,hashlib,importlib.util,shutil,re
sys.dont_write_bytecode=True
root=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');d=root/'diagnostics/simplex-core-architecture';o=d/'results/S6-AI';name=sys.argv[1];base=root/'.superpowers/simplex-core-architecture/S6-AI'/name
r=tomllib.loads((base/'report.toml').read_text());p=json.loads((base/'process.json').read_text());pins=json.loads((base/'pins.json').read_text());log=(base/'run.log').read_text();mode=r['mode'];project=Path(r['source']).parents[1];s=(project/'test/dual_pivot_consistency_tests.jl').read_text();old=(o/'original-test.jl').read_text();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def extract(s,title):
 marker='@testset "'+title+'" begin';return marker+s.split(marker,1)[1].split('\n@testset',1)[0]
titles=['Failed dual pivot recovery remains bounded and unpublished','Cancellation after dual refresh cannot publish a pivot']
checks={'exit0':p['returncode']==0 and p['reason']=='exit0','guard_pins':p['pins_unchanged'],'independent_pins':all(sha(k)==v['sha256'] and str(Path(k).resolve())==v['resolved'] for k,v in pins['inventory'].items()),'actual_source':project==(Path('/home/jspitz/JSimplex.jl') if mode=='master' else root),'test_hash':r['test_sha256']==sha(project/'test/dual_pivot_consistency_tests.jl'),'threads':r['julia_threads']==r['blas_threads']==1,'globals':r['globals_preserved'],'native_helper_unchanged':r['prefix'].startswith(old.split('\n@testset',1)[0]),'expected_source':s==(o/'expected-test.jl').read_text(),'original_assertions':all(line in extract(s,t) for t in titles for line in extract(old,t).splitlines() if '@test' in line),'all_neighbors_unchanged':all(extract(s,t)==extract(old,t) for t in re.findall(r'@testset "([^"]+)" begin',old) if t not in titles),'prefix_actual':r['prefix']==s.split('\n@testset',1)[0]}
selected='\n'.join(extract(s,t) for t in titles)+ ('\n'+extract(old,'Consistent small dual pivots retain the direct path') if mode=='green' else '')
checks['actual_selected']=r['selected']==selected
checks['original_callbacks_preserved']=all(part in s for part in [old.split('        observer=(event,ws)->begin',1)[1].split('        policy=',1)[0],old.split('        observer=(event,ws)->(event==:refactor_pivot',1)[1].split('        diagnostics=',1)[0]])
checks['target_pass']=bool(re.search(r'Failed dual pivot recovery remains bounded and unpublished\s*\|\s*192\s+192',log)) and bool(re.search(r'Cancellation after dual refresh cannot publish a pivot\s*\|\s*56\s+56',log))
checks['all_pass']='Test Failed' not in log and 'Error During Test' not in log
checks['structural_global']=bool(re.search(r'Dual recovery structural contract\s*\|\s*3\s+3',log)) and bool(re.search(r'Ambient state preserved\s*\|\s*1\s+1',log))
if mode=='green':
 checks['neighbor_pass']=bool(re.search(r'Consistent small dual pivots retain the direct path\s*\|\s*60\s+60',log))
 checks['micro27']=bool(re.search(r'Pre-forward recovery accounting\s*\|\s*27\s+27',log))
 checks['micro_actual']=len(r['micro'])==9 and all(x['propagated'] and x['entry_count']==1 and x['subtype'] and x['hits']==(2 if x['kind']=='consumed' else 0) for x in r['micro'])
else:
 checks['no_micro_rerun']=not r['micro'];checks['green_identity']=s==(o/'green-1-test.jl').read_text()
paths=set(pins['files'])
for t in pins['trees']:paths.update(str(v) for v in Path(t).rglob('*') if v.is_file())
checks['inventory_membership']=paths==set(pins['inventory'])
checks['user_hashes']=all(sha(Path('/home/jspitz/JSimplex.jl')/k)==v for k,v in json.loads(Path('/tmp/jsimplex-main-preserved.json').read_text()).items())
a={'checks':checks,'all_passed':all(checks.values()),'pin_count':len(pins['inventory']),'mode':mode,'summary':[l for l in log.splitlines() if re.search(r'\|\s+\d',l)],'scope':'New source recovery tests and scoped accounting only; no AF acceptance, historical CI cause or fullsuite proof.'}
for n in ['report.toml','pins.json','process.json','run.log']:
 with (o/(name+'-'+n)).open('xb') as f:f.write((base/n).read_bytes())
for src,suffix in [(d/'reproduce/dual_budget_repair.jl','driver.jl'),(project/'test/dual_pivot_consistency_tests.jl','test.jl')]:
 with (o/(name+'-'+suffix)).open('xb') as f:f.write(src.read_bytes())
with (o/(name+'-audit.json')).open('x') as f:json.dump(a,f,indent=2);f.write('\n')
print(json.dumps(a,indent=2));assert a['all_passed']
