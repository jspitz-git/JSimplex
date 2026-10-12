from pathlib import Path
import hashlib,json,tomllib,subprocess,time
R=Path.cwd();H=R/'diagnostics/simplex-core-architecture/results/S5-H';G=H.parent/'S5-G'
def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  while True:
   b=f.read(1024*1024)
   if not b:break
   h.update(b)
 return h.hexdigest()
e=json.loads((H/'evidence.json').read_text());bad=[p for p,v in e['sha256'].items() if digest(p)!=v]
s=(H/'append.jl').read_bytes();old=(R/'test/simplex_precision_state_tests.jl').read_bytes()
raw={m:tomllib.loads((G/f'qualification-1/raw/{m}.toml').read_text()) for m in ['stop','throw']}
counts={m:{k:(len(v['arrays']),sum(len(a['values']) for a in v['arrays'].values())) for k,v in x.items() if k in ['before','after','fresh']} for m,x in raw.items()}
checks={'all780_current':len(e['sha256'])==780 and not bad,'candidate_prefix_suffix':(H/'candidate.jl').read_bytes()==old+s,
 'source_copy_schema':all(v['before']==(31,76) for v in counts.values()),
 'copy_payload':e['copies_per_case']==31+3 and e['copied_entries_per_case']==76+3*3,
 'source_test_CI_equal_master':not subprocess.check_output(['git','diff','master','--','src','test','.github']),
 'all_six_user_files':all(digest(p)==v for p,v in json.loads((H/'host-before.json').read_text())['user_hashes'].items()),
 'raw_source_preserved':all(x['before']==x['after'] for x in raw.values()),
 'raw_ambient_preserved':all(x['ambient']==x['ambient_after'] for x in raw.values()),
 'cause_identity':raw['throw']['observed_outcome']['cause_identity']==raw['throw']['observed_outcome']['sentinel_identity'],
 'direct_assertions_not_type_names':b'caught.cause===failure' in s and b'caught isa JSimplex.DiagnosticObserverFailure' in s and b'LinearAlgebra.SingularException"' not in s}
x={'checks':checks,'all_passed':all(checks.values()),'bad':bad,'counts':counts,'evidence_sha256':digest(H/'evidence.json'),'time_ns':time.time_ns()}
with (H/'independent.json').open('x') as f:json.dump(x,f,indent=2);f.write('\n')
print(json.dumps(x));raise SystemExit(0 if x['all_passed'] else 1)
