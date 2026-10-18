"""Independent offline review. New Python only; no Julia or old checker execution."""
from pathlib import Path
import json, hashlib, re, copy, struct, subprocess, os, time, traceback, tomllib
E=Path(__file__).resolve().parent; R=E.parents[3]; C=R/'diagnostics/direct-bg-split-upper/reproduce'
checks={}; cache={}
def rd(p):return json.loads(Path(p).read_text())
def digest(p):
 p=Path(p)
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def require(v,name):
 checks[name]=bool(v)
 if not v:raise AssertionError(name)
def bound(j):return all(digest(p)==h for p,h in j.items())
def reject(name,fn):
 try:fn()
 except (AssertionError,ValueError,RuntimeError,KeyError,TypeError,IndexError):require(True,name)
 else:require(False,name)
def git(*args,cwd=R):return subprocess.check_output(['git',*args],cwd=cwd,text=True).strip()
def inverse(t,m):
 for original,renamed in sorted(m.items(),key=lambda x:-len(x[1])):
  t=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(renamed)+r'(?![A-Za-z0-9_!])',lambda _:original,t)
 return t
try:
 pins=rd(E/'preparation-pins.json');members=set(pins['sha256'])
 require(len(members)==1827 and members==set(rd(E/'required-paths.json')['paths']),'1827_exact_required_members')
 require(bound(pins['sha256']),'all_1827_current_hashes')
 # Reconstruct categories independently; preparation-local files are explicitly fixed.
 local_names='ADMISSION.md MEMORY-WORK.md REPORT.md analysis.py audit.py author-host.json authorization.json baseline.json commands.json control.py cost.jl environment.json evidence.py extend.py freeze.py guard.py host.json inputs.json inputs.toml launch.py lineage.json loaded-paths.json negative-supplement-invocation.json negative-supplement.json negative-supplement.py offline-tests-invocation.json offline-tests.json offline-tests.py prefix-tests-invocation.json prefix-tests.json prefix-tests.py prepare-tests.py prepare.py probe-bg.jl probe-inverse.json probe-oracles.jl probe-upper.jl probe.jl required-paths.json reused-files.json runtime-inputs-complete.json seal.py source-check-invocation.json source-check.json source-check.py split-tests-invocation.json split-tests.json split-tests.py stages.json supervisor.py synthetic.py'.split()
 expected={str(E/n) for n in local_names}|{str(p) for p in C.rglob('*') if p.is_file()}
 lineage=rd(E/'lineage.json');expected|=set(lineage['sha256'])
 reused=rd(E/'reused-files.json');expected|={v['source'] for v in reused.values()}
 runtime=rd(E/'runtime-inputs-complete.json')['inventory'];expected|=set(runtime)
 require(all(str(Path(p).resolve(strict=True))==v['resolved'] and digest(p)==v['sha256'] for p,v in runtime.items()),'609_runtime_hashes_and_resolutions')
 stage=rd(E/'stages.json')['cost'];S=Path(stage['path']);expected|={str(S/n) for n in stage['sha256']}
 baseline=rd(E/'baseline.json');W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl')
 for label,root in [('diagnostic',R),('production',W)]:
  expected|={str(root/n) for n in baseline[label]}
  require(set(git('ls-files','src','test','.github','Project.toml',cwd=root).splitlines())==set(baseline[label]),label+'_baseline_membership')
 expected|={str(R/n) for n in ['AGENTS.md','docs/superpowers/plans/2026-10-18-direct-bg-split-free-blocks.md','docs/superpowers/specs/2026-10-18-direct-bg-split-free-blocks.md']}
 base=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/base')
 expected|={str(base/n) for n in ['array.jl','boot.jl','summarysize.jl']}
 require(expected==members,'independently_reconstructed_manifest_membership')
 require(not S.is_symlink() and not any(p.is_symlink() for p in S.rglob('*')),'stage_no_symlinks')
 require({str(p.relative_to(S)) for p in S.rglob('*') if p.is_file()}==set(stage['sha256']) and len(stage['sha256'])==84,'exact84_stage_files')
 old=rd(E.parent/'DIRECT-BG-SPLIT-DRIVER-PREPARATION/stages.json')['green']
 require(stage['source']==old['path'] and stage['baseline_sha256']==old['sha256'] and len(old['sha256'])==81,'GREEN81_baseline')
 require(set(stage['sha256'])-set(old['sha256'])=={'src/probe-upper.jl','src/probe-bg.jl','src/probe-oracles.jl'},'exact_three_stage_additions')
 for n,h in old['sha256'].items():
  b=(S/n).read_bytes()
  if n=='src/JSimplex.jl':
   mark=b'\ninclude("probe-upper.jl")\ninclude("probe-bg.jl")\ninclude("probe-oracles.jl")\n'
   require(b.count(mark)==1 and stage['inserted_includes'].encode()==mark,'exact_root_insert')
   b=b.replace(mark,b'')
  require(hashlib.sha256(b).hexdigest()==h==digest(Path(old['path'])/n),'stage_inverse_'+n)
 j=rd(E/'probe-inverse.json');require(len(j['counts'])==len(set(j['counts']))==83,'83_distinct_counters')
 for n in ['upper','bg','oracles']:
  require((E/f'probe-{n}.jl').read_bytes()==(S/f'src/probe-{n}.jl').read_bytes(),'probe_stage_'+n)
 u=(E/'probe-upper.jl').read_text();require(u.startswith(j['header']),'probe_header')
 u=inverse(u[len(j['header']):],j['renames'])
 marks=re.findall(r'\n    # SPLIT_COST_PROBE_BEGIN\n(.*?)\n    # SPLIT_COST_PROBE_END\n',u,re.S)
 require(len(marks)==len(j['injections']) and sorted(marks)==sorted(v['code'] for v in j['injections']),'injection_exact_membership')
 require(all(re.sub(r'_split_(?:count|max)!\([^\n]*\)','',line).strip() in ('',';') for code in marks for line in code.splitlines()),'injections_only_counter_calls')
 u=re.sub(r'\n    # SPLIT_COST_PROBE_BEGIN\n.*?\n    # SPLIT_COST_PROBE_END\n','',u,flags=re.S)
 require(len(j['replacements'])==3,'three_explicit_bookkeeping_replacements')
 for item in reversed(j['replacements']):
  require(u.count(item['new'])==1,'replacement_'+str(len(checks)));u=u.replace(item['new'],item['old'])
 require(u==(C/'split-upper.jl').read_text(),'exact_upper_byte_inverse')
 require(inverse((E/'probe-bg.jl').read_text(),j['renames'])==(C/'split-bg.jl').read_text(),'exact_adapter_byte_inverse')
 a=(C/'split-oracles.jl').read_text();checker=a[:a.index('function _sbu_materialize')];helpers=a[a.index('function _sbu_test_free('):a.index('function _sbu_test_handles(')]
 require(j['helper']==helpers and (E/'probe-oracles.jl').read_text().startswith(checker) and inverse((E/'probe-oracles.jl').read_text()[len(checker):],j['renames'])==checker+helpers,'exact_oracle_and_helper_inverses')
 require('split-oracles.jl' not in (S/'src/JSimplex.jl').read_text(),'no_duplicate_checker_module_include')
 G=E.parent/'DIRECT-BG-SPLIT-DRIVER-PREPARATION/runs/green300';v=rd(G/'result-review.json')
 require(v['accepted'] is True and v['findings']==[] and v['scope']=='split BG GREEN result' and v['phase']=='green300','GREEN_accepted_scope')
 require(set(v['sha256'])=={str(p) for p in G.rglob('*') if p.is_file() and p.name!='result-review.json'} and bound(v['sha256']) and bound(v['evidence_sha256']),'GREEN_review_exact_current_bindings')
 require(set(lineage['sha256'])==set(v['sha256'])|set(v['evidence_sha256'])|{str(G/'result-review.json')},'GREEN_lineage_exact_membership')
 ga=rd(G/'audit.json');require(ga['all_passed'] is True and ga['result']['assertions']==15929 and len(ga['result']['groups'])==34,'GREEN_15929_34_saved_only')
 for p in ['sealed.json','launch-pins.json']:
  prior=rd(G/p);require(all(digest(n)==x['sha256'] and str(Path(n).resolve(strict=True))==x['resolved'] for n,x in prior['inventory'].items()),'GREEN_'+p+'_current_inventory')
 require(tomllib.loads((E/'inputs.toml').read_text())==rd(E/'inputs.json'),'fixture_json_toml_identity')
 require(all(digest(E/n)==x['sha256']==digest(x['source']) for n,x in reused.items()),'all_reused_bytes')
 require(git('rev-parse','HEAD')=='fae75df5b4b998a768fbee0608695e5b3930174e' and git('rev-parse','master')=='26e2291745999f485a74f643298ca997d65c7205','local_refs_unchanged')
 require(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'tracked_and_index_unchanged')
 require(not (E/'runs').exists(),'no_new_seal_reservation_output')
 # Only new modules containing definitions are imported; no author checker is run.
 import analysis as A, evidence as V
 require(len(V.expected_names())==199,'199_output_members')
 cmds=rd(E/'commands.json')
 require(all(V.config(k)==v for k,v in cmds.items()),'four_exact_commands')
 require(all(V.config(k)['seconds']-8==n for k,n in [('cost1-300',292),('cost2-300',292),('cost1-600',592),('cost2-600',592)]),'fixed_deadlines')
 def tok(x):return struct.pack('>d',x).hex()
 m=dict(n=2,colptr=[1,2,4],rowval=[1,1,2],nzval=list(map(tok,[2.,3.,4.])))
 require(A.residual(A.matrix(m),list(map(tok,[1.,2.])),list(map(tok,[8.,8.]))) and A.residual(A.matrix(m,True),list(map(tok,[1.,2.])),list(map(tok,[2.,11.]))),'independent_nonsymmetric_exact_residuals')
 require(not A.residual(A.matrix(m,True),list(map(tok,[1.,2.])),list(map(tok,[8.,8.]))),'transpose_norm_orientation_negative')
 c=dict.fromkeys(j['counts'],0);require(V.counters_ok(c),'zero_counter_schema')
 c.update(target_calls=8,reserve_requests=8,target_4=8,target_comparisons=24,bin_inspections=120,free_splits=7,exact_fit_requests=1,split_descriptors=7)
 for r in range(4,29,4):c['remainder_'+str(r)]=1
 require(V.counters_ok(c),'independent_repeated4_counts')
 for key,val in [('target_comparisons',23),('remainder_32',1),('free_splits',8),('append_descriptors',8),('descriptor_copied_payload',28),('bin_inspections',0),('relocations',1)]:
  bad=dict(c);bad[key]=val;reject('counter_reject_'+key,lambda:V.counters_ok(bad))
 fixtures=rd(E/'inputs.json')['fixtures']
 cells=[dict(fixture=f['name'],manager='BG',backend=b,policy='threshold_one' if b=='native' else 'default',statistics=dict(time_median_gate=True,allocation_gate=True,memory_gate=True,probe_memory_gate=True,faster_pairs=3)) for f in fixtures for b in ['native','markowitz']]
 good=dict(all_passed=True,pure_timeout=False,cells=cells);require(A.first_process_viable(good,fixtures),'all8_first_gate_positive')
 for i in range(8):
  for key in ['time_median_gate','allocation_gate','memory_gate','probe_memory_gate','faster_pairs']:
   bad=copy.deepcopy(good);bad['cells'][i]['statistics'][key]=2 if key=='faster_pairs' else False
   require(not A.first_process_viable(bad,fixtures),f'gate_reject_cell{i}_{key}')
 p=dict(returncode=-15,reason='wall_time',pins_unchanged=True);s=dict(returncode=1,hard_timeout=False,child_kill=False,guard_term=False,guard_kill=False)
 require(V.timeout_ok(p,s,'BEGIN matched policy cost cost1-300',292,300),'timeout_positive_only')
 for msg in ['WARNING','warning','wArNiNg','world-age','World Age','FATAL COST:','ERROR:','Traceback']:
  require(not V.timeout_ok(p,s,'BEGIN matched policy cost '+msg,292,300),'timeout_reject_'+msg)
 require(not V.timeout_ok(p,s,'BEGIN matched policy cost ',301,300),'timeout_late_cleanup_reject')
 for name in ['offline-tests','prefix-tests','negative-supplement','split-tests','source-check']:
  saved=rd(E/(name+'.json'));require(saved['all_passed'] is True and all(saved['checks'].values()),name+'_saved_pass')
 require(bound(rd(E/'source-check.json')['sha256']),'source_check_saved_byte_bindings')
 require('patch.object(e,\'schedules_ok\'' in (E/'prefix-tests.py').read_text(),'prefix_schedule_mock_explicit')
 # Host snapshot is read only and is not run admission.
 groups=set(rd(E/'host.json')['groups']);matches=[];unreadable=[]
 for proc in Path('/proc').glob('[0-9]*'):
  try:
   z=(proc/'stat').read_text().rsplit(')',1)[1].split();comm=(proc/'comm').read_text().strip();exe=''
   try:exe=str((proc/'exe').resolve(strict=True))
   except PermissionError:unreadable.append(int(proc.name))
   except FileNotFoundError:pass
   if int(z[2]) in groups or int(z[3]) in groups or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):
    matches.append(dict(pid=int(proc.name),pgid=int(z[2]),sid=int(z[3]),start_ticks=int(z[19]),command=(proc/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
  except (FileNotFoundError,ProcessLookupError):pass
 require(len(groups)==244 and not matches,'fresh244_groups_AND_sessions_no_visible_Julia')
 host=dict(groups=sorted(groups),matches=matches,unreadable_exe_pids=unreadable,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),time=time.time(),scope='Review-only host snapshot; not numerical admission')
 with (E/'reviewer-host.json').open('x') as f:json.dump(host,f,indent=2);f.write('\n')
 outcome=dict(all_passed=True,checks=checks,scope='Independent offline source/hash and fresh Python predicates; no Julia or old checker execution',full_Julia_structural_schedules_executed=False,inspection_error_preserved='An earlier read-only inspection attempted absent green300/result-review.md, raised FileNotFoundError, then read the actual JSON review and DIRECT-BG-SPLIT-GREEN/result-review.md. No check or artifact was changed.')
except BaseException:
 outcome=dict(all_passed=False,checks=checks,error=traceback.format_exc())
with (E/'reviewer-check.json').open('x') as f:json.dump(outcome,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=outcome['all_passed'],checks=len(checks),error=outcome.get('error',''))))
if not outcome['all_passed']:raise SystemExit(1)
