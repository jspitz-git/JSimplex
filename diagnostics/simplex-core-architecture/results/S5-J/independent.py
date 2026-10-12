"""Exclusive author-independent S5-J rehash and provenance check; no Julia."""
from pathlib import Path
import hashlib,json,re,subprocess,time
R=Path.cwd();J=R/'diagnostics/simplex-core-architecture/results/S5-J';D=J.parent.parent
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
e=json.loads((J/'evidence.json').read_text());bad=[p for p,v in e['sha256'].items() if sha(p)!=v]
rowbad=[]
for row in e['rows']:
 p=R/f".superpowers/simplex-core-architecture/S6-A/ci-inventory-1/{row['run']}-failed.log";raw=p.read_text().splitlines()[row['line']-1]
 normalized=re.sub(r'(?:\x1b|\^\[)\[[0-9;]*m','',raw);nums=normalized.split('|',1)[1].split()
 if raw!=row['raw'] or normalized!=row['normalized'] or nums[:2]!=[str(row['passed']),str(row['total'])]:rowbad.append(row['name'])
excerpts=[]
for item in e['excerpts']:
 p=J/'excerpts'/(item['name']+'.txt');text=p.read_text();src=(R/item['file']).read_text()
 excerpts.append(sha(p)==item['sha256'] and src.splitlines(keepends=True)[item['start_line']-1:][:len(text.splitlines(keepends=True))]==text.splitlines(keepends=True))
host=json.loads((J/'host-before.json').read_text());I=J.parent/'S5-I';cl=json.loads((I/'closure.json').read_text())
checks={'full97_rehash':len(e['sha256'])==97 and not bad,'literal21_pass':e['all_passed'] and len(e['checks'])==21,'raw16_rows':len(e['rows'])==16 and not rowbad,'six_source_excerpts':len(excerpts)==6 and all(excerpts),'user6_unchanged':len(host['user_hashes'])==6 and all(sha(p)==v for p,v in host['user_hashes'].items()),'I_closure_still_unchanged':all(sha(R/p)==v for p,v in cl['sha256'].items()),'src_test_CI_equal_master':not subprocess.check_output(['git','diff','master','--','src','test','.github']),'master_unchanged':subprocess.check_output(['git','rev-parse','master'],text=True).strip()==host['master']}
files=[J/'evidence.json',J/'source_contract.py',J/'host-before.json',Path(__file__).resolve(),D/'S5-DUAL-AUXILIARY-HANDOFF-OWNERSHIP.md',R/'docs/superpowers/plans/2026-10-13-dual-auxiliary-pending-observer-oracle.md']
x={'checks':checks,'all_passed':all(checks.values()),'time_ns':time.time_ns(),'bad':bad,'rowbad':rowbad,'sha256':{str(p.relative_to(R)):sha(p) for p in files}}
with (J/'independent.json').open('x') as f:json.dump(x,f,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'all_passed':x['all_passed']}));raise SystemExit(0 if x['all_passed'] else 1)
