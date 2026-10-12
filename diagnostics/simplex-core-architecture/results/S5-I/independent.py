"""Independent post-run binding check, exclusive output for each NEW run label."""
from pathlib import Path
import hashlib,json,tomllib,sys,subprocess
I=Path(__file__).resolve().parent;R=I.parents[3];label=sys.argv[1];assert label in ('green-1','master-1')
P=R/'.superpowers/simplex-core-architecture/S5-I'/label;portable=I/label;target=R if label=='green-1' else Path('/home/jspitz/JSimplex.jl')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
pins=json.loads((P/'pins.json').read_text())['inventory'];report=tomllib.loads((P/'raw/report.toml').read_text());a=json.loads((I/(label+'-audit.json')).read_text());e=tomllib.loads((I/'expected.toml').read_text())
files={str(p.relative_to(P)):sha(p) for p in P.rglob('*') if p.is_file()};copied={str(p.relative_to(portable)):sha(p) for p in portable.rglob('*') if p.is_file()}
process=json.loads((P/'process.json').read_text());samples=[json.loads(s) for s in (P/'resources.jsonl').read_text().splitlines()]
checks={'raw_portable_exact':files==copied,'audit_raw_bindings':files==a['raw_sha256'],'full_launch_pins':all(sha(p)==v['sha256'] for p,v in pins.items()),'actual_candidate':sha(target/'test/simplex_precision_state_tests.jl')==e['candidate'],'all_user_files':all(sha(p)==v for p,v in json.loads((I/'host-before.json').read_text())['user_hashes'].items()),'expected298_plus2_assertions':report['passes']==300 and report['fails']==report['errors']==report['broken']==0,'two_entries_each':report['entry_counts']==[2,2,2] and len(report['cases'])==2,'no_production_or_CI_delta':not subprocess.check_output(['git','diff','master','--','src','.github'],cwd=R),'guard_exit_and_pins':process['reason']=='exit0' and process['returncode']==0 and process['pins_unchanged']}
x={'checks':checks,'all_passed':all(checks.values()),'pins':len(pins),'resource_samples':len(samples),'min_available_kib':min(x['available_kib'] for x in samples),'max_swap_kib':max(x['swap_used_kib'] for x in samples),'inclusive_elapsed_seconds':process['ended']-process['started'],'not_a_benchmark':True,'postrun_checker_sha256':sha(__file__),'raw_sha256':files}
with (I/(label+'-independent.json')).open('x') as f:json.dump(x,f,indent=2);f.write('\n')
print(json.dumps(x));assert x['all_passed']
