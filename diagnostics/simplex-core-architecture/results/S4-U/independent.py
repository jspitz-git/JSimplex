from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/S4-U';a=json.loads((E/'source-contract.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();checks={}
checks['full627_rehash']=len(a['sha256'])==627 and all(sha(p)==h for p,h in a['sha256'].items())
checks['20_source_checks']=len(a['checks'])==20 and all(a['checks'].values())
m=json.loads((E/'cache-metadata.json').read_text());checks['67_unique_metadata_names']=len(m['entries'])==67 and len({v['name'] for v in m['entries']})==67 and all('sha256' not in v for v in m['entries'])
checks['excerpts_match_actual_source']=all(x['text']=='\n'.join(Path(x['path']).read_text().splitlines()[x['first_line']-1:x['last_line']]) and sha(x['path'])==x['sha256'] for x in json.loads((E/'source-excerpts.json').read_text()))
checks['no_production_test_CI_change']=not subprocess.check_output(['git','diff','master','--','src','test','.github'])
checks['bootstrap_open']=a['bootstrap_qualified'] is False
obj=dict(checks=checks,all_passed=all(checks.values()),scope='Separate author full627 rehash and excerpt/metadata checks; not runtime cache validity or exhaustive initializer closure')
with (E/'independent.json').open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
print(json.dumps(obj));assert obj['all_passed']
