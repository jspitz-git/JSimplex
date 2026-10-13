"""Exclusive OFFLINE S5-O driver preparation. No Julia invocation."""
from pathlib import Path
import hashlib,json,time,subprocess
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');H=Path(__file__).resolve().parent;N=H.parent/'S5-N';M=H.parent/'S5-M'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def write(name,s):
 with (H/name).open('x') as f:f.write(s)
def dump(name,x):write(name,json.dumps(x,indent=2)+'\n')
old=json.loads((N/'evidence.json').read_text())['sha256'];assert len(old)==789
assert all(sha(p)==v for p,v in old.items())
for f in ('independent.json','closure.json'):
 x=json.loads((N/f).read_text());assert x['all_passed'] is True
 assert all(sha(Path(p) if Path(p).is_absolute() else R/p)==v for p,v in x['sha256'].items())
for f in ('audit.json','postcheck.json','closure.json'):
 assert json.loads((M/f).read_text())['all_passed'] is True
mp=json.loads((M/'qualification-1/pins.json').read_text());assert len(mp['inventory'])==756
assert all(sha(p)==v['sha256'] for p,v in mp['inventory'].items())
ma=json.loads((M/'audit.json').read_text());assert all(sha(M/'qualification-1'/p)==v for p,v in ma['raw_sha256'].items())
user=json.loads((N/'host-before.json').read_text())['user_hashes'];assert all(sha(p)==v for p,v in user.items())
groups={23249,23257,49081,49084,52772,52774,53479,53481,60706,60708};matches=[]
for q in Path('/proc').glob('[0-9]*'):
 try:
  s=(q/'stat').read_text();a=s[s.rindex(')')+2:].split()
  if int(a[2]) in groups or (q/'comm').read_text().strip()=='julia':matches.append(str(q))
 except FileNotFoundError:pass
assert not matches
assert subprocess.check_output(['git','diff','master','--','src','test','.github'],cwd=R)==b''
dump('host-before.json',{'time_ns':time.time_ns(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'matches':matches,'groups':sorted(groups),'user_hashes':user,'N789':True,'M756':True,'Mraw6':True,'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'master':subprocess.check_output(['git','rev-parse','master'],cwd=R,text=True).strip()})
original=(R/'test/adaptive_pricing_lifecycle_tests.jl').read_text();write('original-test.jl',original)
x=json.loads((N/'source-inverse.json').read_text());append=(N/'append.jl').read_text();assert (N/'candidate.jl').read_text()==original+append
prov=json.loads((H.parent/'S5-L/source-provenance.json').read_text())
obs=x['L_removed_suffix'].split('    return checks,observations')[0]
patches=[{'anchor':'    ws = JSimplex.initialize_workspace','insert':'    O_COUNTS[1] += 1\n'},{'anchor':'        JSimplex.make_dual_feasible!(ws,()->false)','insert':'        O_COUNTS[2] += 1\n'},{'anchor':'    return checks\n','insert':obs+'    O_COUNTS[3] += 1\n    O_RECORD[] = (checks=checks,observations=observations)\n'}]
executed=append
for p in patches:
 assert executed.count(p['anchor'])==1
 executed=executed.replace(p['anchor'],p['insert']+p['anchor'])
inverse=executed
for p in reversed(patches):inverse=inverse.replace(p['insert']+p['anchor'],p['anchor'])
assert inverse==append
helpers=[]
for p in prov['helpers']:
 text=p['source_text'];assert original.count(text)==1
 helpers.append({'text':text,'sha256':p['sha256']})
q=lambda s:json.dumps(s,ensure_ascii=False)
write('expected.toml','\n'.join([f'candidate = {q(x["candidate_sha256"])}',f'prefix = {q(x["prefix_sha256"])}',f'suffix = {q(x["append_sha256"])}',f'executed = {q(hashlib.sha256(executed.encode()).hexdigest())}',f'checks = {q(x["checks"])}']+[f'\n[[helpers]]\ntext = {q(p["text"])}\nsha256 = {q(p["sha256"])}' for p in helpers])+'\n')
write('insertions.toml','\n'.join(f'[[insertions]]\nanchor = {q(p["anchor"])}\ninsert = {q(p["insert"])}\n' for p in patches))
write('expected-executed.jl',executed)
schema=json.loads((M/'schema.json').read_text());schema['candidate_sha256']=x['candidate_sha256'];schema['prefix_sha256']=x['prefix_sha256'];schema['suffix_sha256']=x['append_sha256'];schema['test_relative']='test/adaptive_pricing_lifecycle_tests.jl';schema['passes']=42
dump('schema.json',schema)
dump('preparation.json',{'all_passed':True,'N789_M756_raw6_user6_verified':True,'prefix_bytes':19080,'inverse_exact':True,'helpers':helpers,'checks':x['checks'],'candidate_sha256':x['candidate_sha256'],'sha256':{str(p):sha(p) for p in [Path(__file__),N/'source-inverse.json',N/'candidate.jl',N/'append.jl',H/'original-test.jl',H/'expected.toml',H/'insertions.toml',H/'expected-executed.jl']}})
print('S5-O offline preparation PASS: N789/M756/raw6, exact actual prefix/helpers and instrumentation inverse; no Julia.')
