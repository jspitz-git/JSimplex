"""Exclusive OFFLINE test candidate preparation. Never runs Julia or old scripts."""
from pathlib import Path
import hashlib,json,re,subprocess,time
R=Path.cwd();H=R/'diagnostics/simplex-core-architecture/results/S5-T';S=H.parent/'S5-S';P=H.parent/'S5-R';REL='test/simplex_precision_tests.jl'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def dump(p,v):
 with Path(p).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
groups={23249,23257,49081,49084,52772,52774,53479,53481,60706,60708,63808,63815,64420,64422,71824,71826};matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();v=s[s.rindex(')')+2:].split()
  if int(v[2]) in groups or (p/'comm').read_text().strip()=='julia':matches.append(dict(pid=int(p.name),pgid=int(v[2]),start_ticks=int(v[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except FileNotFoundError:pass
assert not matches
host=dict(boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),groups=sorted(groups),matches=matches,refs=subprocess.check_output(['git','rev-parse','HEAD','master'],text=True).splitlines(),remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'],text=True),user_hashes=read(S/'host-before.json')['user_hashes'],time_ns=time.time_ns())
assert host['refs']==['aebf5de2442abcc9d6e3c996eb0737358b4b25d3','35a6a9f4bb61e204b0c61ec9effe96cd9d2de3ab'];assert all(x in host['remote'] for x in host['refs']);assert all(sha(p)==v for p,v in host['user_hashes'].items());dump(H/'host-before.json',host)
checks={}
for name,key,count in [('launch-pins.json','inventory',856),('closure.json','sha256',100),('postcheck.json','sha256',10)]:
 d=read(S/name)[key];checks[name]=len(d)==count and all(sha(p)==(v['sha256'] if key=='inventory' else v) for p,v in d.items())
for name,n in [('audit.json',19),('postcheck.json',9),('closure.json',14),('publication-check.json',6)]:
 d=read(S/name);checks['gates_'+name]=len(d['checks'])==n and d['all_passed'] is True and all(x is True for x in d['checks'].values())
a=read(S/'audit.json');original=R/'.superpowers/simplex-core-architecture/S5-S/qualification-1';checks['raw6']=len(a['raw_sha256'])==6 and all(sha(original/n)==sha(S/'qualification-1'/n)==v for n,v in a['raw_sha256'].items());checks['invocation3']=all(sha(p)==v for p,v in a['invocation_sha256'].items());assert all(checks.values());dump(H/'entry-checks.json',dict(checks=checks,all_passed=True))
source=(P/'candidate-reviewed.jl').read_text();assert sha(P/'candidate-reviewed.jl')=='d03fcc9c0d2f70a16437ea2412e56c807babccb99f6df25aec82894b67d51950'
names=read(P/'provenance.json')['predicate_names'];assert len(names)==40
core=source[source.index('mutable struct S5RProbe'):source.index('    observations=Dict(')]
renames={'S5RProbe':'_BasisInitializationStopProbe','s5r_selected_work':'_basis_initialization_stop_work','s5r_case(output)':'_basis_initialization_stop_checks()'}
for a,b in renames.items():
 assert b not in (R/REL).read_text();core=core.replace(a,b)
append='\n# The explicit stop interrupts imported-basis checkpoint publication after reconstruction.\n'+core+'    return checks\nend\n\n@testset "Supplied-basis checkpoint stop preserves ownership and consumed work" begin\n    checks=_basis_initialization_stop_checks()\n'+''.join('    @test checks.'+n+'\n' for n in names)+'end\n'
prefix=(R/REL).read_bytes()
with (H/'append.jl').open('x') as f:f.write(append)
with (H/'candidate.jl').open('xb') as f:f.write(prefix+append.encode())
with (H/'original-test.jl').open('xb') as f:f.write(prefix)
paths=set(read(S/'launch-pins.json')['inventory'])|{str(p) for p in S.rglob('*') if p.is_file()}|{str(p) for p in H.iterdir() if p.is_file()}|{str(R/'diagnostics/simplex-core-architecture'/n) for n in ('S5-BASIS-INITIALIZATION-STOP-QUALIFICATION.md','S5-BASIS-INITIALIZATION-STOP-QUALIFICATION-REVIEW.md')}|{str(R/'docs/superpowers/plans/2026-10-13-basis-initialization-stop-test-preparation.md')}
dump(H/'provenance.json',dict(candidate_sha256=sha(H/'candidate.jl'),prefix_sha256=sha(R/REL),prefix_bytes=len(prefix),append_sha256=sha(H/'append.jl'),append_lines=len(append.splitlines()),predicate_names=names,renames=renames,source_core_sha256=hashlib.sha256(source[source.index('mutable struct S5RProbe'):source.index('    observations=Dict(')].encode()).hexdigest(),scope='UNEXECUTED candidate. No Julia parser/import/compile or actual test modification.'))
paths.add(str(H/'provenance.json'));dump(H/'pins.json',dict(sha256={p:sha(p) for p in sorted(paths)},scope='Fresh read-time identities, not execution.',time_ns=time.time_ns()))
print(json.dumps(dict(prefix_bytes=len(prefix),append_lines=len(append.splitlines()),candidate_sha256=sha(H/'candidate.jl'),pins=len(paths))))
