"""One offline correction of literal visible ANSI escapes; original failure preserved."""
from pathlib import Path
import json,re,hashlib
p=Path(__file__).parent;r=json.loads((p/'source-contract.json').read_text());checks={};rows={}
for run,items in r['historical_log_rows'].items():
 rows[run]=[]
 for i,item in enumerate(items):
  t=re.sub(r'\^\[\[[0-9;]*m','',item['text']);nums=list(map(int,re.findall(r'\d+',t.split('|')[1])))[:2];expected=[16,2280,3,12][i];checks[f'{run}_row{i}']=nums==[expected,expected];rows[run].append({'line':item['line'],'cleaned':t,'pass_total':nums})
checks['all_other_original24']=len(r['checks'])==25 and all(v for k,v in r['checks'].items() if k!='historical_four_rows_each') and r['checks']['historical_four_rows_each'] is False
with (p/'log-supplement.json').open('x') as f:json.dump({'checks':checks,'all_passed':all(checks.values()),'rows':rows,'original_sha256':hashlib.sha256((p/'source-contract.json').read_bytes()).hexdigest(),'scope':'original source-contract.json all_passed=false and source preserved; no rerun,only eight stored original log rows normalized'},f,indent=2)
print(checks);assert all(checks.values())
