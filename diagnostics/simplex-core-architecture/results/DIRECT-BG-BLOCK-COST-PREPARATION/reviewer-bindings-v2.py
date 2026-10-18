"""Independent offline reviewer: hashes, inventories, exact source inverses only.
No author checker/control imports; no subprocess, Julia, parser, or numeric run.
"""
from pathlib import Path
import hashlib,json,re,tomllib,time
E=Path(__file__).resolve().parent;R=E.parents[3]
checks={};detail={}
def need(v,label):
 checks[label]=bool(v)
 if not v:raise AssertionError(label)
def unique(pairs):
 d={}
 for k,v in pairs:
  if k in d:raise ValueError('duplicate JSON key '+k)
  d[k]=v
 return d
def read(p):return json.loads(Path(p).read_text(),object_pairs_hook=unique)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def digest_map(m):
 bad=[]
 for n,h in m.items():
  p=Path(n) if Path(n).is_absolute() else R/n
  if not p.is_file() or sha(p)!=h:bad.append(n)
 return bad
pins=read(E/'preparation-pins.json');m=pins['sha256'];required=read(E/'required-paths.json')['paths']
need(len(m)==len(required)==1820,'exact1820preparationkeys')
need(len(required)==len(set(required)) and set(m)==set(required),'exactpreparationmembership')
need(not digest_map(m),'all1820freshhashes')
need(str(E/'preparation-pins.json') not in m and str(E/'review.json') not in m,'noncircularpreparation')
need(not (E/'runs').exists(),'no_new_phase_execution_directory')
rt=read(E/'runtime-inputs-complete.json')['inventory']
need(not digest_map({n:v['sha256'] for n,v in rt.items()}),'runtime_hashes')
need(all(str(Path(n).resolve(strict=True))==v['resolved'] for n,v in rt.items()),'runtime_resolved_paths')
need(set(rt)<=set(m),'runtime_bound_in_preparation')
st=read(E/'stages.json')['cost'];S=Path(st['path']);G=Path(st['source'])
actual={str(p.relative_to(S)) for p in S.rglob('*') if p.is_file()}
need(len(actual)==84 and actual==set(st['sha256']),'exact84stagefiles')
need(not S.is_symlink() and not any(p.is_symlink() for p in S.rglob('*')),'ordinary_stage_no_symlinks')
need(all(sha(S/n)==h for n,h in st['sha256'].items()),'all_stage_hashes')
need(all(sha(G/n)==h for n,h in st['baseline_sha256'].items()),'all_GREEN_stage_baseline_hashes')
need(actual-set(st['baseline_sha256'])=={'src/probe-upper.jl','src/probe-bg.jl','src/probe-oracles.jl'},'only_three_probe_files_added')
for n in st['baseline_sha256']:
 b=(S/n).read_bytes();old=(G/n).read_bytes()
 if n=='src/JSimplex.jl':
  inc=st['inserted_includes'].encode();need(b.count(inc)==1,'one_probe_include_block');b=b.replace(inc,b'')
 need(b==old,'stage_inverse_'+n)
for n in ['probe-upper.jl','probe-bg.jl','probe-oracles.jl']:need((E/n).read_bytes()==(S/'src'/n).read_bytes(),'stage_probe_'+n)
inv=read(E/'probe-inverse.json');ren=inv['renames'];need(len(set(ren.values()))==len(ren),'injective_identifier_renames')
def rename(t,m):
 for a,z in sorted(m.items(),key=lambda x:-len(x[0])):
  t=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(a)+r'(?![A-Za-z0-9_!])',z,t)
 return t
C=R/'diagnostics/direct-bg-block-upper/reproduce'
need(not digest_map(inv['sources']),'probe_inverse_sources')
u=(E/'probe-upper.jl').read_text();need(u.startswith(inv['header']),'exact_probe_header');u=u[len(inv['header']):];u=rename(u,{v:k for k,v in ren.items()})
for i,item in enumerate(inv['injections']):
 marker='    # BLOCK_COST_PROBE_BEGIN\n'+item['code']+'\n    # BLOCK_COST_PROBE_END\n'
 full=item['anchor']+'\n'+marker
 need(u.count(full)==1,'anchored_injection_'+str(i));u=u.replace(full,item['anchor'],1)
need(u.count(inv['allocator']['new'])==1,'allocator_instrumentation_unique')
u=u.replace(inv['allocator']['new'],inv['allocator']['old'])
need(u==(C/'block-upper.jl').read_text(),'exact_upper_inverse')
need(rename((E/'probe-bg.jl').read_text(),{v:k for k,v in ren.items()})==(C/'block-bg.jl').read_text(),'exact_manager_inverse')
o=(C/'block-oracles.jl').read_text().split('function _bgu_materialize')[0]
need((E/'probe-oracles.jl').read_text()==o+rename(o,ren),'exact_oracle_prefix_inverse')
need(len(inv['counts'])==len(set(inv['counts']))==29,'exact29metrics')
for n,v in read(E/'reused-files.json').items():need(sha(E/n)==sha(v['source'])==v['sha256'],'unchanged_reused_'+n)
fixtures=read(E/'inputs.json');parsed=tomllib.loads((E/'inputs.toml').read_text())
need(parsed==fixtures,'JSON_TOML_fixture_equality')
need([f['name'] for f in fixtures['fixtures']]==['sparse32','dense32','sparse96','dense96'],'four_fixed_fixtures')
for f in fixtures['fixtures']:
 need(len(f['steps'])==8 and len(f['matrices'])==9,'fixture_lifecycle_'+f['name'])
loaded=read(E/'loaded-paths.json');need(set(loaded)=={'SparseArrays','LinearAlgebra','TOML','PrecompileTools'},'four_library_paths_plus_JSimplex_no_Test')
for n,p in loaded.items():need(str(Path(p).resolve())==p and p in m,'loaded_path_bound_'+n)
line=read(E/'lineage.json')['sha256'];need(not digest_map(line),'fresh_GREEN_lineage_hashes')
GR=E.parent/'DIRECT-BG-BLOCK-DRIVER-PREPARATION/runs/green300';rv=read(GR/'result-review.json')
need(rv['accepted'] is True and rv['findings']==[] and rv['scope']=='block BG GREEN result' and rv['phase']=='green300','GREEN_result_accepted')
need(set(rv['sha256'])=={str(p) for p in GR.rglob('*') if p.is_file() and p!=GR/'result-review.json'},'GREEN_review_exact_membership')
need(not digest_map(rv['sha256']),'GREEN_review_bound_files')
need(not digest_map(rv.get('evidence_sha256',{})),'GREEN_reviewer_evidence_hashes')
need(read(GR/'audit.json')['all_passed'] is True,'GREEN_audit_passed')
for n in ['launch-pins.json','sealed.json']:
 j=read(GR/n);need(not digest_map({p:v['sha256'] for p,v in j['inventory'].items()}),'GREEN_'+n+'_all_inventory_hashes')
for n in ['source-check.json','offline-tests.json','prefix-tests.json','negative-supplement.json']:
 j=read(E/n);need(j['all_passed'] is True,'recorded_not_rerun_'+n);detail[n]=len(j.get('checks',{}))
need(len(read(E/'host.json')['groups'])==238,'recorded238historicalgroups')
for label,root in [('diagnostic',R),('production',Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl'))]:
 b=read(E/'baseline.json')[label];need(all(sha(root/n)==h for n,h in b.items()),'baseline_all_bytes_'+label)
detail.update(preparation_files=len(m),runtime_paths=len(rt),stage_files=len(actual),GREEN_baseline_files=len(st['baseline_sha256']),lineage_files=len(line),fixtures=[f['name'] for f in fixtures['fixtures']],counter_count=len(inv['counts']))
out=dict(all_passed=True,checks=checks,detail=detail,pins_sha256=sha(E/'preparation-pins.json'),checker_sha256=sha(__file__),scope='Independent full offline binding/source inverse verification; no Julia or author checker execution')
with (E/'reviewer-bindings-v2.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=True,checks=len(checks),detail=detail)))
