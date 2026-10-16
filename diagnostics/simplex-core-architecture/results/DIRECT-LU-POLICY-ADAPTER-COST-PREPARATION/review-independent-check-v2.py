"""Reviewer-owned read/hash/source/input checks. Never imports or executes author helpers or Julia."""
from pathlib import Path
import hashlib,json,subprocess,struct,tomllib,os,time
from fractions import Fraction
D=Path(__file__).resolve().parent;R=D.parents[3]
W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl')
MASTER='26e2291745999f485a74f643298ca997d65c7205';HEAD='9a2b50b9f0bf6a790ea8b6cdd00904828ae2221a'
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def git(*args,cwd=R):return subprocess.check_output(['git',*args],cwd=cwd)
checks={};counts={}
def ck(name,value):
 checks[name]=bool(value)
 if not value:raise RuntimeError(name)
def bound(mapping,root=None):return all(sha((root/str(n)) if root else Path(n))==v for n,v in mapping.items())
def inv(mapping):return all(str(Path(n).resolve(strict=True))==v['resolved'] and sha(n)==v['sha256'] for n,v in mapping.items())
def inventory_members(j):
 names=set(j['files'])
 for root in j['trees']:
  names|={str(p) for p in Path(root).rglob('*') if p.is_file()}
 return names
m=D/'preparation-pins.json';pins=read(m);required=read(D/'required-paths.json')['paths']
ck('canonical91_exact_membership',len(required)==len(set(required))==91 and set(required)==set(pins['sha256']))
ck('canonical91_sha256',bound(pins['sha256']))
ck('diagnostic_HEAD',git('rev-parse','HEAD').decode().strip()==HEAD)
ck('local_master',git('rev-parse','master').decode().strip()==MASTER)
ck('production_HEAD',git('rev-parse','HEAD',cwd=W).decode().strip()==MASTER)
ck('tracked_and_index_unchanged',not git('diff','--name-only').strip() and not git('diff','--cached','--name-only').strip())
base=read(D/'baseline.json')
for name,root,expected in [('diagnostic',R,514),('production',W,516)]:
 ck(name+'_baseline_membership',len(base[name])==expected and set(git('ls-files','src','test','.github','Project.toml',cwd=root).decode().splitlines())==set(base[name]))
 ck(name+'_baseline_hashes',bound(base[name],root));counts[name+'_source_files']=len(base[name])
st=read(D/'stages.json')['cost'];stage=Path(st['path']);members={str(p.relative_to(stage)) for p in stage.rglob('*') if p.is_file()}
ck('stage75_membership',len(members)==75 and members==set(st['sha256']))
ck('stage75_hashes',bound(st['sha256'],stage))
ck('stage_no_symlink',not stage.is_symlink() and not any(p.is_symlink() for p in stage.rglob('*')))
master_files=git('ls-tree','-r','--name-only',MASTER,'--','src','Project.toml').decode().splitlines()
addition=b'include("factor-export.jl")\ninclude("direct-factor.jl")\n';anchor=b'include("huangfu_hall_factorization.jl")\n'
for name in master_files:
 original=git('show',MASTER+':'+name);actual=(stage/name).read_bytes()
 if name=='src/JSimplex.jl':
  ck('stage_root_exact_two_include_inverse',actual==original.replace(anchor,anchor+addition) and original.count(anchor)==1)
 else:ck('stage_master_inverse_'+name,actual==original)
C=R/'diagnostics/direct-lu-policy-adapters/reproduce'
ck('stage_only_two_extra_source_files',{n for n in members if n.startswith('src/')}=={n for n in master_files if n.startswith('src/')}|{'src/factor-export.jl','src/direct-factor.jl'})
ck('candidate_stage_identical',all((stage/'src'/n).read_bytes()==(C/n).read_bytes() for n in ['factor-export.jl','direct-factor.jl']))
runinventory=read(D/'runtime-inputs-complete.json')['inventory'];ck('runtime609_membership',len(runinventory)==609);ck('runtime609_resolved_and_hashes',inv(runinventory));counts['runtime_files']=len(runinventory)
lineage=read(D/'lineage.json');ck('GREEN_lineage_hashes',bound(lineage['sha256']))
ck('GREEN_lineage_exact_files',set(lineage['sha256'])==set(lineage['green_files']))
ck('reused_source_hashes',bound(lineage['reused']))
ck('reused_guard_supervisor_environment_runtime_byteidentical',all((D/Path(n).name).read_bytes()==Path(n).read_bytes() for n in lineage['reused'] if Path(n).name in ['guard.py','supervisor.py','environment.json','runtime-inputs-complete.json']))
ck('old_input_hashes',bound(lineage['inputs']))
ck('fixed_input_copies_byteidentical',all((D/Path(n).name).read_bytes()==Path(n).read_bytes() for n in lineage['inputs']))
G=D.parent/'DIRECT-LU-POLICY-ADAPTER-DRIVER-PREPARATION/runs/green300';rv=read(G/'result-review.json')
ck('GREEN_result_accepted',rv['accepted'] is True and rv['findings']==[] and rv['scope']=='direct adapter GREEN result' and rv['phase']=='green300')
ck('GREEN_result_exact_membership',set(rv['sha256'])=={str(p) for p in G.rglob('*') if p.is_file() and p!=G/'result-review.json'})
ck('GREEN_result_full_hashes',bound(rv['sha256']))
if 'evidence_sha256' in rv:ck('GREEN_result_supplement_hashes',bound(rv['evidence_sha256']))
ck('GREEN_audit_accepted',read(G/'audit.json')['all_passed'] is True)
for name in ['sealed.json','launch-pins.json']:
 j=read(G/name);ck('GREEN_'+name+'_inventory_membership',inventory_members(j)==set(j['inventory']));ck('GREEN_'+name+'_inventory_hashes',inv(j['inventory']));counts['GREEN_'+name+'_entries']=len(j['inventory'])
V=D.parent/'DIRECT-LU-POLICY-ADAPTER-GREEN';mapcount=0
for recname in ['closure.json','publication.json']:
 rec=read(V/recname)
 for name,value in rec['sha256'].items():
  p=R/name
  if name=='diagnostics/simplex-core-architecture/STATUS.md':p=D/'STATUS.md.before-cost';mapcount+=1
  if name=='docs/superpowers/plans/2026-10-11-simplex-core-architecture.md':p=D/'roadmap.md.before-cost';mapcount+=1
  ck('GREEN_'+recname+'_binding_'+name,sha(p)==value)
ck('four_continuation_mappings',mapcount==4)
ck('live_continuations_unchanged',(R/'diagnostics/simplex-core-architecture/STATUS.md').read_bytes()==(D/'STATUS.md.before-cost').read_bytes() and (R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md').read_bytes()==(D/'roadmap.md.before-cost').read_bytes())
fixtures=read(D/'inputs.json');ck('JSON_TOML_exact_equality',fixtures==tomllib.loads((D/'inputs.toml').read_text()))
ck('four_fixed_fixture_names_dimensions',[(f['name'],f['n']) for f in fixtures['fixtures']]==[('sparse32',32),('dense32',32),('sparse96',96),('dense96',96)])
def value(t):
 assert len(t)==16 and all(c in '0123456789abcdef' for c in t)
 return Fraction(struct.unpack('>d',bytes.fromhex(t))[0])
for f in fixtures['fixtures']:
 n=f['n'];mats=[]
 ck(f['name']+'_nine_bases_eight_steps',len(f['matrices'])==9 and len(f['steps'])==8)
 for m in f['matrices']:
  assert m['n']==n;cp=m['colptr'];ri=m['rowval'];vv=m['nzval'];assert len(cp)==n+1 and cp[0]==1 and cp[-1]==len(ri)+1==len(vv)+1
  a=[[Fraction(0) for _ in range(n)] for _ in range(n)]
  for j in range(n):
   assert 1<=cp[j]<=cp[j+1]<=len(vv)+1
   rows=ri[cp[j]-1:cp[j+1]-1];assert rows==sorted(set(rows)) and all(1<=i<=n for i in rows)
   for k in range(cp[j]-1,cp[j+1]-1):a[ri[k]-1][j]=value(vv[k])
  mats.append(a)
 ck(f['name']+'_all_bases_strict_row_dominance_after_fixed_permutation',all(abs(a[i][n-1-((i+3)%n)])>sum(abs(x) for j,x in enumerate(a[i]) if j!=n-1-((i+3)%n)) for a in mats for i in range(n)))
 for k,s in enumerate(f['steps']):
  j=7*k%n;a=[row[j] for row in mats[k]];a[(j+1)%n]=Fraction(float(a[(j+1)%n]+Fraction(1,32))) # Frozen binary64 addition rounds once.
  ck(f['name']+'_exact_replacement_'+str(k),s['j']==j+1 and list(map(value,s['a']))==a and all(mats[k+1][i][c]==(a[i] if c==j else mats[k][i][c]) for i in range(n) for c in range(n)))
  ck(f['name']+'_rhs_'+str(k),list(map(value,s['unit']))==[int(i==j) for i in range(n)] and list(map(value,s['dse']))==[Fraction(i/n) for i in range(1,n+1)])
ledger=read(D/'work-ledger.json');pp=ledger['per_process'];pre=ledger['separate_preflight_per_process'];co=ledger['combined_per_process']
ck('timed_work_counts',all(pp[k]==v for k,v in dict(cells=24,warm_pairs_per_cell=3,measured_pairs_per_cell=7,windows=480,warm_windows=144,measured_windows=336,constructions=480,explicit_refactors=960,updates=3840,FTRAN=7680,BTRAN=3840,recorded_solution_vectors=11520,recorded_solution_entries=737280,input_full_checks=504,retained_factor_graph_reads=480).items()))
ck('preflight_counts',pre==dict(cases=24,constructions=48,refactors=96,explicit_solves=0,candidate_exports=72,native_control_observations=72,markowitz_observations=72,detached_control_tokens=2880,detached_strategy_tokens=72))
ck('combined_native_bounds',co==dict(backend_setup_refactor_entries=1584,candidate_export_entries=792,native_candidate_exports=396,orientation_solve_upper_bound=396))
ck('both_process_counts',ledger['both_processes']==dict(windows=960,constructions=960,refactors=1920,updates=7680,FTRAN=15360,BTRAN=7680,separate_preflight_backend_entries=288,exact_offline_residual_checks=23040))
ck('output_storage_bound',sum(f['n']*24 for f in fixtures['fixtures'])==6144 and max(f['n']*24 for f in fixtures['fixtures'])==2304)
configs=read(D/'config.json')
ck('four_canonical_phases',set(configs)=={'cost1-300','cost2-300','cost1-600','cost2-600'})
wrapper='/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh'
for phase,cfg in configs.items():
 run=D/'runs'/phase;command=['/bin/bash',wrapper,'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--history-file=no','--project='+str(stage),str(D/'cost.jl'),phase,str(run/'output'),str(stage)]
 ck(phase+'_exact_command',cfg==dict(phase=phase,process=int(phase[4]),seconds=int(phase[-3:]),expected_exit=0,stage=str(stage),run=str(run),output=str(run/'output'),command=command))
for filename,count in [('offline-tests-2.json',91),('prefix-tests.json',17)]:
 j=read(D/filename);ck(filename+'_saved_checks',j['all_passed'] is True and len(j['checks'])==count and all(v is True for v in j['checks'].values()))
old=(D/'offline-tests.py').read_text();new=(D/'offline-tests-2.py').read_text()
new=new.replace('(ValueError,KeyError,TypeError,RuntimeError)','(ValueError,KeyError,TypeError)').replace("next(r for r in rows if r['side']=='candidate')['retained_bytes']=1","rows[1]['retained_bytes']=1").replace("D/'offline-tests-2.json'","D/'offline-tests.json'")
ck('preserved_failed_test_narrow_inverse',new==old)
ck('failure_record_preserved',read(D/'offline-tests-failure.json')['returncode']==1 and not (D/'offline-tests.json').exists())
ck('no_phase_runs_seal_reservation_or_closure',not (D/'runs').exists() and not any((D/n).exists() for n in ['closure.json','publication.json']))
# Fresh /proc stat + readable comm/executable check, no signalling.
groups=set(read(D/'host.json')['groups']);matches=[];unreadable=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  stat=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip();exe=''
  try:exe=str((p/'exe').resolve(strict=True))
  except PermissionError:unreadable.append(int(p.name))
  except FileNotFoundError:pass
  if int(stat[2]) in groups or int(stat[3]) in groups or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):matches.append(dict(pid=int(p.name),pgid=int(stat[2]),sid=int(stat[3]),comm=comm,exe=exe))
 except (FileNotFoundError,ProcessLookupError):pass
ck('fresh226_groups_sessions_and_visible_Julia_clear',len(groups)==226 and not matches)
ck('canonical91_unchanged_at_end',bound(pins['sha256']))
result=dict(all_passed=True,checks=checks,counts=counts,checked_at=time.time(),pins_sha256=sha(m),required_paths_sha256=sha(D/'required-paths.json'),scope='New reviewer-only read/hash/exact fixed-input checks; no author helper import/execution, no Julia/parser/import/compile/native run; no sealing/reservation/closure/publication',host=dict(groups=sorted(groups),matches=matches,unreadable_exe_pids=unreadable,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip()),sha256={**pins['sha256'],str(m):sha(m)})
with (D/'review-independent-checks-v2.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=True,checks=len(checks),counts=counts)))
