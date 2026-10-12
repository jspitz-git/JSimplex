"""New W-only offline verification; exclusive output, never rerun after acceptance."""
import hashlib,json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[4]
r=Path(__file__).resolve().parent
s=json.loads((r/'source-contract.json').read_text())
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
checks={}
checks['full_556_readtime_hashes']=len(s['sha256'])==556 and all(sha(p)==v for p,v in s['sha256'].items())
e=json.loads((r/'source-excerpts.json').read_text())
checks['sixteen_fullfile_hashes']=len(e)==16 and all(sha(root/x['file'])==x['file_sha256'] for x in e)
checks['sixteen_exact_line_ranges']=all(''.join((root/x['file']).read_text().splitlines(keepends=True)[x['first_line']-1:x['last_line']])==x['text'] for x in e)
l=json.loads((r/'attempt-ledger.json').read_text())
checks['twentysix_unique_rows']=len(l['rows'])==26 and len({x['id'] for x in l['rows']})==26
checks['aggregate_explicitly_unqualified']=l['complete_attempt_caps_qualified'] is False
checks['literal_checks_preserved']=len(s['checks'])==22 and all(s['checks'].values()) and s['all_passed'] is True
h=json.loads((r/'host-before.json').read_text())
checks['six_user_hashes']=len(h['user_hashes'])==6 and all(sha(p)==v for p,v in h['user_hashes'].items())
checks['production_test_environment_CI_equal_master']=not subprocess.check_output(['git','diff','master','--','src','test','.github','Project.toml'],cwd=root,text=True)
out={'checks':checks,'all_passed':all(checks.values()),'scope':'Author independent full pins/excerpts/schema/source preservation; not runtime or independent review','bound_sha256':{str(p.relative_to(root)):sha(p) for p in r.iterdir() if p.is_file()}}
with (r/'independent.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'all_passed':out['all_passed']}))
raise SystemExit(0 if out['all_passed'] else 1)
