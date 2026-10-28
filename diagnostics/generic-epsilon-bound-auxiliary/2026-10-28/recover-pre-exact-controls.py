from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
a=(D/'audit.py').read_text();old="int(cols[0])==con['expected_assertions']";assert a.count(old)==1
a=a.replace(old,'int(cols[0])>1000').encode()
c=json.loads((D/'contract.json').read_text());assert c.pop('expected_assertions')==59053 and c.pop('correctness_assertions')==8897
c=(json.dumps(c,indent=2,sort_keys=True)+'\n').encode()
expected={'audit.py':('625559833b17d93c23847d7031f6da2389d809f06545d472a4e21a52d7a35f1a',a),'contract.json':('46471d57fceea26347af2f30d65c99edb4fc86ae33033a8d2c3182d8cac5e11c',c)}
assert all(sha(raw)==h for h,raw in expected.values()),'exact original historical SHA mismatch'
B=D/'history-reconstructed';B.mkdir(exist_ok=False);mapping={}
for n,(h,raw)in expected.items():
 p=B/(n+'.before-exact-assertions');p.write_bytes(raw);mapping[str(D/n)]={'sha256':h,'reconstruction':str(p)}
x=dict(accepted=True,scope='Hash-verified historical reconstruction ONLY, not contemporaneous beforeimage or launch pin',reason='totals-prepare.py strengthened old auditor assertion and added two contract counts before sealing; earlier review was preserved but these two pre-change files were not then copied.',source_operations='Inverse ONLY the two explicit changes in immutable totals-prepare.py; that script was NOT rerun and no original file was rewritten.',original_review=str(D/'preparation-review-before-exact-assertions.json'),original_review_sha256=sha((D/'preparation-review-before-exact-assertions.json').read_bytes()),inverse_source=str(D/'totals-prepare.py'),inverse_source_sha256=sha((D/'totals-prepare.py').read_bytes()),mapping=mapping,all_exact_hashes_match_frozen_original_review=True,contemporaneous_beforeimages=False,retroactive_launch_pins=False,no_Julia_or_old_script_execution=True)
with(D/'history-reconstruction.json').open('x')as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
print('Exact historical hashes recovered:',len(mapping))
