"""Separate author check of frozen L evidence; exclusive output, no Julia."""
from pathlib import Path
import json,hashlib,subprocess,time,struct
from fractions import Fraction
r=Path.cwd();o=r/'diagnostics/simplex-core-architecture/results/S4-L';x=json.loads((o/'source-contract.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks={'full_hash_recheck':all(sha(p)==h for p,h in x['hashes'].items()),'source36':len(x['checks'])==36 and all(x['checks'].values()),'four_input_contracts':len(x['fixture_contract'])==4}
for c in x['fixture_contract']:
 for direction in ['forward','transpose']:
  values=list(map(Fraction,c['rhs_'+direction+'_rational']));bits=c['rhs_'+direction+'_bits'];assert len(values)==len(bits)==96
  checks[c['kind']+str(c['phase'])+direction]=all(Fraction.from_float(struct.unpack('>d',bytes.fromhex(b))[0])==v for b,v in zip(bits,values))
checks['user6']=all(sha(p)==h for p,h in x['user_hashes'].items())
checks['production_test_ci_unchanged']=not subprocess.check_output(['git','diff','master','--','src','test','.github'])
matches=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  stat=(p/'stat').read_text();fields=stat[stat.rindex(')')+2:].split();cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace');exe=(p/'exe').resolve().name
  if int(fields[2]) in [12358,12360] or exe=='julia' or int(p.name) in [12359,12360]:matches.append({'pid':int(p.name),'pgid':int(fields[2]),'start_ticks':fields[19],'cmd':cmd})
 except (OSError,ValueError):pass
checks['full_previous_groups_absent']=not matches
refs=subprocess.check_output(['git','rev-parse','HEAD','master'],text=True).splitlines();remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'],text=True)
checks['refs_unchanged']=refs==['457d4c08adbfd0401608ed85349d15c6a6d6fa94','0eb75c3190096946b0e91e5360230ccd7166f298'] and all(s in remote for s in refs)
result={'checks':checks,'all_passed':all(checks.values()),'rehashed':len(x['hashes']),'matches':matches,'refs':refs,'remote':remote,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'source_contract_sha256':sha(o/'source-contract.json'),'author_not_reviewer':True,'time_ns':time.time_ns()}
with (o/'independent.json').open('x') as f:json.dump(result,f,indent=2)
print({'checks':len(checks),'passed':sum(checks.values()),'rehashed':result['rehashed'],'matches':matches});assert result['all_passed']
