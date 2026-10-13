"""New exclusive post-attempt evidence check and portable raw preservation."""
from common import *
import sys,tomllib,shutil,subprocess,time
label,=sys.argv[1:];assert label in ('green-1','master-1');out=B/label;p=read(out/'process.json');a=read(H/(label+'-audit.json'));pins=read(out/'pins.json')
assert not absent([p['runner']['pgid'],p['child']['pgid']])['matches']
s=read(H/'schema.json');target=R if label=='green-1' else MAIN
raw=tomllib.loads((out/'raw/case.toml').read_text());report=tomllib.loads((out/'raw/report.toml').read_text())
historical=read(H.parent/'S5-N/evidence.json')['sha256']
checks={'audit_PASS':a['all_passed'] is True and all(v is True for v in a['checks'].values()),
 'full_pins':all(sha(f)==v['sha256'] for f,v in pins['inventory'].items()),
 'historical_N789_exact_original_mapping':all(sha(H/'original-test.jl' if f==str(R/REL) else f)==v for f,v in historical.items()),
 'exact_actual_candidate':sha(target/REL)==s['candidate_sha256'],
 'raw_predicates':set(raw['checks'])==set(s['checks']) and all(v is True for v in raw['checks'].values()),
 'actual_results':report['passes']==42 and report['fails']==report['errors']==report['broken']==0 and report['entry_counts']==[1,1,1],
 'raw_identity':all(sha(out/f)==v for f,v in a['raw_sha256'].items()),
 'user6':all(sha(f)==v for f,v in read(H/'host-before.json')['user_hashes'].items()),
 'production_CI_equal_master':subprocess.check_output(['git','diff','master','--','src','.github'],cwd=R)==b''}
if label=='master-1':checks['master_source_identity']=all(sha(MAIN/f)==sha(R/f)==v for f,v in read(H/'master-source-comparison.json')['sha256'].items())
assert all(checks.values()),checks
shutil.copytree(out,H/label)
dump(H/(label+'-postcheck.json'),{'all_passed':True,'checks':checks,'sha256':{str(H/(label+'-audit.json')):sha(H/(label+'-audit.json')),str(out/'pins.json'):sha(out/'pins.json'),str(out/'process.json'):sha(out/'process.json')},'time_ns':time.time_ns()})
print(json.dumps({'label':label,'checks':checks,'pin_count':len(pins['inventory'])}))
