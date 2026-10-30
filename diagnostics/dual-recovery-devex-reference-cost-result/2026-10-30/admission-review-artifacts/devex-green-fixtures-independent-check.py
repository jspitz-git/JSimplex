"""New independent read-only offline verifier; does not import submitted helpers."""
from pathlib import Path
import ast, hashlib, json, re
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl')
D=W/'diagnostics/dual-recovery-devex-green-fixture-preparation/2026-10-30'
P=W/'diagnostics/dual-recovery-devex-task4/2026-10-30'
F=W/'diagnostics/dual-recovery-devex-task4-green/2026-10-30'
R=W/'.superpowers/dual-recovery-devex-task4/qualification-1'
root=D/'prepared'; bindings={}; checks={}
def read(p):
 p=Path(p); b=p.read_bytes(); bindings[str(p)]=hashlib.sha256(b).hexdigest(); return b
def sha(p):return hashlib.sha256(read(p)).hexdigest()
def obj(p):return json.loads(read(p))
def require(name,value):
 checks[name]=bool(value)
 if not value:raise AssertionError(name)
s=obj(D/'staging.json'); m=obj(D/'fixture-manifest.json'); c=obj(D/'source-check.json'); f=obj(D/'fixture-check.json')
for p in D.iterdir():
 if p.is_file():read(p)
require('all365_recorded_bindings',len(c['bindings'])==365 and all(sha(p)==h for p,h in c['bindings'].items()))
require('all98_exact_copies',len(s['copies'])==98 and all(sha(p)==sha(v['source'])==v['sha256'] and Path(p).stat().st_size==v['bytes'] for p,v in s['copies'].items()))
require('all255_old_sha256_bindings',len(s['frozen_previous_publications'])==255 and all(sha(p)==h for p,h in s['frozen_previous_publications'].items()))
published=set(); old_blob_count=0
for old in (P,F):
 pub=obj(old/'publication.json'); published.update(str(W/p) for p in pub['expected_names'])
 for p,h in pub['blobs_excluding_publication'].items():
  b=read(W/p);require('old_blob_'+p,hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==h);old_blob_count+=1
require('255_publication_inventory_exact',published==set(s['frozen_previous_publications']))
oldfiles=[P/'green.jl',P/'endpoint.jl']+[p for sub in ('tests','overlays/candidate') for p in (P/sub).rglob('*') if p.is_file()]
oldnames={str(p.relative_to(P)) for p in oldfiles};newnames={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
extra='tests/fixtures/solver/netlib/adlittle.mps'
require('sole_added_fixture',newnames-oldnames=={extra} and not oldnames-newnames and len(newnames)==91)
require('all90_old_equivalent_files_exact',len(oldfiles)==90 and all(sha(p)==sha(root/p.relative_to(P)) for p in oldfiles))
require('no_symlinks',not any(p.is_symlink() for p in root.rglob('*')))
require('all74_candidate_files_exact',sum(p.is_file() for p in (root/'overlays/candidate').rglob('*'))==74)
require('all15_program_hashes',len(m['programs'])==15 and all(sha(root/p)==sha(P/p)==h for p,h in m['programs'].items()))
require('all13_helpers_listed',set(p for p in newnames if p.startswith('tests/') and p.endswith('.jl'))==set(m['programs'])-{'green.jl','endpoint.jl'})
regressions=[]
for p in m['programs']:
 original=W/'test'/Path(p).name
 if p.startswith('tests/') and original.exists():
  require('original_regression_'+p,sha(original)==sha(root/p));regressions.append(p)
require('seven_current_regressions',len(regressions)==7)
edges=[];uses=[];other_io=[];calls={};macros={}
for p in m['programs']:
 text=read(root/p).decode(); calls[p]=sorted(set(re.findall(r'([A-Za-z_][A-Za-z_0-9.!]*)\s*\(',text)));macros[p]=sorted(set(re.findall(r'@[A-Za-z_][A-Za-z_0-9!]*',text)))
 for n,line in enumerate(text.splitlines(),1):
  if line.lstrip().startswith('#'):continue
  inc=re.fullmatch(r'\s*include\("([^"\\]+)"\)\s*',line)
  if inc:edges.append({'program':p,'line':n,'target':str(Path(p).parent/inc[1])})
  if 'read_mps' in line:
   match=re.fullmatch(r'\s*\w+\s*=\s*read_mps\(joinpath\(@__DIR__,((?:"[^"\\]+",?)+)\)\)\s*',line)
   require('literal_input_'+p,bool(match)); parts=re.findall(r'"([^"]+)"',match[1]);target=str(Path(p).parent.joinpath(*parts));uses.append({'program':p,'line':n,'target':target})
  if re.search(r'\b(?:open|read|readlines|eachline|readdlm|deserialize|load|parsefile|include_string|download|ccall)\s*\(',line):other_io.append({'program':p,'line':n,'text':line.strip()})
require('14_independent_include_edges',len(edges)==14 and {(e['program'],e['line'],e['target']) for e in edges}=={(e['program'],e['line'],e['target']) for e in f['includes']})
seen={'green.jl'}
while True:
 new=seen|{e['target'] for e in edges if e['program'] in seen}
 if new==seen:break
 seen=new
require('all15_reachable',seen==set(m['programs']))
require('exact12_ordered_entry_includes',[e['target'] for e in edges if e['program']=='green.jl']==obj(P/'contract.json')['green_includes'])
require('two_complete_fixture_inputs',len(uses)==2 and {x['target'] for x in uses}==set(m['fixtures']) and {(x['program'],x['line'],x['target']) for x in uses}=={(x['program'],x['line'],x['target']) for x in f['fixture_uses']})
require('one_exact_output_open',other_io==[{'program':'endpoint.jl','line':105,'text':'open(path,"w") do io;TOML.print(io,Dict("cases"=>records);sorted=true);end'}])
require('fixture_sources_exact',len(m['original_fixture_sources'])==2 and all(sha(root/p)==sha(v['path'])==v['sha256']==m['fixtures'][p] and (root/p).stat().st_size==v['bytes'] for p,v in m['original_fixture_sources'].items()))
require('known_adlittle_hash',sha(root/extra)=='fec81e24fa91bc545d97239b108b43e6034f37b4bf2455a3f8c179726b44d44c')
red=read(D/'offline-red.log').decode();green=read(D/'offline-green.log').decode()
require('preserved_red_log_expected_only_failure','F........\n' in red and 'Ran 9 tests' in red and red.rstrip().endswith('FAILED (failures=1)') and 'missing fixture '+extra in red)
require('preserved_green_log_nine_pass','.........\n' in green and 'Ran 9 tests' in green and green.rstrip().endswith('OK'))
for p in D.glob('*.py'):ast.parse(read(p).decode())
old=obj(R/'green/completion.json')
require('failed_green_unaccepted',old['supervisor_accepted'] is False and not (R/'green/audit.json').exists())
require('budget_preserved',old['total_inclusive_seconds']==527.9604928489425 and 1800-old['total_inclusive_seconds']==1272.0395071510575==c['remaining_shared_seconds'])
require('only_original_two_reservations',sorted(p.name for p in R.iterdir() if p.is_dir())==['green','red'])
h=obj(D/'host.json');require('recorded_host733_no_conflicts',h['accepted'] and len(h['host']['checked_groups'])==733 and not h['host']['conflicts'] and all(x['current'] is None for x in h['identities']))
payload=sum((root/p).stat().st_size for p in newnames)
require('payload_counts',payload==1237330==c['prepared_payload_bytes'] and (root/extra).stat().st_size==16500 and sum((root/p).stat().st_size for p in m['fixtures'])==20165)
read(W/'AGENTS.md');read(P/'common.py');read(__file__)
result={'accepted':True,'scope':'independent offline preparation verification only','runtime_qualified':False,'numerical_admission':False,'checks':checks,'read_bindings':bindings,'counts':{'recorded_bindings':365,'copies':98,'previous_sha256_bindings':255,'previous_git_blob_bindings':old_blob_count,'prepared_files':91,'unchanged_old_files':90,'candidate_files':74,'programs':15,'include_edges':14,'fixtures':2,'current_regressions':7,'prepared_payload_bytes':payload,'added_fixture_bytes':16500},'independent_includes':edges,'independent_inputs':uses,'other_io':other_io,'call_names_for_manual_audit':calls,'macros_for_manual_audit':macros,'submitted_scripts_executed':False,'submitted_scripts_imported':False}
out=Path('/tmp/devex-green-fixtures-independent-check.json')
with out.open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps({'accepted':True,'checks':len(checks),'read_bindings':len(bindings),'counts':result['counts'],'result':str(out)}))
