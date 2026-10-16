"""Independent exact-stage admission checks; no Julia or legacy checker execution."""
from pathlib import Path
import ast, hashlib, json, os, subprocess, time
R=Path.cwd(); B=R/'diagnostics/simplex-core-architecture/results'
E=B/'NATIVE-PIVOT-INTEGRATION-ENVIRONMENT-AMENDMENT'; P=B/'NATIVE-PIVOT-INTEGRATION-DRIVER-PREPARATION'; K=B/'NATIVE-PIVOT-INTEGRATION-QUALIFICATION'
run=E/'runs/integration'; sp=run/'sealed.json'; stage=R/'.superpowers/native-pivot-integration-env1/integration'
checks={}; details={}
def rd(p): return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''): h.update(b)
 return h.hexdigest()
def ck(n,v): checks[n]=bool(v)
def path(n): return Path(n) if Path(n).is_absolute() else R/n
def git(*a): return subprocess.check_output(['git',*a],text=True).strip()
def binds(d): return all(sha(path(n))==h for n,h in d.items())
def funcs(p): return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_text()).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
try:
 s=rd(sp); inv=s['inventory']; files=s['files']; cfg=s['config']; groups=set(s['groups'])
 ck('1643_exact_sealed_inventory',len(files)==len(set(files))==len(inv)==1643 and set(files)==set(inv))
 ck('all_sealed_absolute_files',all(Path(n).is_absolute() and Path(n).is_file() for n in files))
 ck('1643_full_hash_and_resolved_path_checks',all(sha(n)==v['sha256'] and str(Path(n).resolve(strict=True))==v['resolved'] for n,v in inv.items()))
 ck('sealed_shape',s['phase']=='integration' and s['inputs']==[] and s['trees']==[str(stage)])
 expected=set()
 for root,num,extra in [(P,1503,18),(E,1561,12)]:
  pins=root/'preparation-pins.json'; a=rd(pins); v=rd(root/'review-final.json'); label=root.name
  ck(label+'_pins_and_required',len(a['sha256'])==num and set(a['sha256'])==set(rd(root/'required-paths.json')['paths']) and binds(a['sha256']))
  ck(label+'_accepted_review',v['accepted'] is True and v['findings']==[] and v['scope']=='offline preparation' and v['pins_sha256']==sha(pins))
  ck(label+'_exact_review_hashes',len(v['sha256'])==num+1 and set(v['sha256'])==set(a['sha256'])|{str(pins)} and binds(v['sha256']))
  ck(label+'_supplemental_hashes',len(v['evidence_sha256'])==extra and binds(v['evidence_sha256']))
  actual=rd(root/'actual-baseline.json')['sha256'];ck(label+'_520_actual_baseline_files',len(actual)==520 and binds(actual))
  if root==P:expected|={str(pins),str(root/'review-final.json')}|set(a['sha256'])|set(v['evidence_sha256'])
  else:expected|=set(a['sha256'])|{str(pins),str(root/'review-final.json')}
  for name in ['closure.json','publication.json']:
   z=rd(root/name); adjusted={}
   for n,h in z['sha256'].items():
    q=path(n)
    if root==P and n=='diagnostics/simplex-core-architecture/STATUS.md':q=E/'STATUS.md.before-environment'
    if root==P and n=='docs/superpowers/plans/2026-10-11-simplex-core-architecture.md':q=E/'roadmap.md.before-environment'
    adjusted[str(q)]=h
   ck(label+'_'+name+'_closure_binding',z['all_passed'] is True and binds(adjusted))
   if root==P:expected|=set(adjusted)|{str(root/name)}
 expected.add(str(P/'closure-host.json'))
 manifest=rd(P/'overlay-manifest.json')['candidate']
 members={str(p.relative_to(stage)) for p in stage.rglob('*') if p.is_file()}
 ck('76_exact_stage_members',len(manifest)==len(members)==76 and members=={e['destination'] for e in manifest})
 ck('stage_no_symlinks',not stage.is_symlink() and not any(p.is_symlink() for p in stage.rglob('*')))
 ck('stage_source_and_manifest_identity',all(sha(stage/e['destination'])==sha(e['source'])==e['sha256'] for e in manifest))
 expected|={str(stage/e['destination']) for e in manifest}|{str(run/'host.json'),str(run/'config.json'),str(R/'diagnostics/simplex-core-architecture/STATUS.md'),str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md')}
 ck('independently_derived_exact_sealed_membership',expected==set(files))
 details['required_missing']=sorted(expected-set(files));details['required_extra']=sorted(set(files)-expected)
 ck('fresh_run_has_only_seal_config_host',{p.name for p in run.iterdir()}=={'sealed.json','config.json','host.json'})
 env=rd(E/'environment.json');ck('nine_key_environment_exact_no_normalization',len(env)==9 and {k:os.environ.get(k) for k in env}==env)
 details['environment_different_keys']=[k for k in env if os.environ.get(k)!=env[k]]
 head='052523788b14c84982e4b770804d3b32e5a47a9b'; master='6f68e24e8ddac42b948da8fcc2d636c010751194'; boot='284d2228-1d9a-4c5f-913c-b9f1098b5838'
 ck('exact_current_refs_boot',git('rev-parse','HEAD')==s['head']==head and git('rev-parse','master')==s['master']==master and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==s['boot_id']==boot)
 ck('amendment_baseline_ancestor',subprocess.run(['git','merge-base','--is-ancestor','5fd40966abc84be5bb88a789853273b41f754717','HEAD']).returncode==0)
 ck('tracked_worktree_and_index_clean',git('diff','--name-only')==git('diff','--cached','--name-only')=='')
 for q in [E/'host.json',P/'closure-host.json',K/'host.json',run/'host.json']:
  h=rd(q);ck(str(q.relative_to(R))+'_216groups_boot',len(h['groups'])==216 and set(h['groups'])==groups and h['boot_id']==boot and h['matches']==[])
 matches=[];unreadable=[];seen=0
 for q in Path('/proc').glob('[0-9]*'):
  try:
   st=(q/'stat').read_text().rsplit(')',1)[1].split();comm=(q/'comm').read_text().strip();exe='';seen+=1
   try:exe=str((q/'exe').resolve(strict=True))
   except PermissionError:unreadable.append(int(q.name))
   except FileNotFoundError:pass
   if int(st[2]) in groups or int(st[3]) in groups or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):
    matches.append(dict(pid=int(q.name),pgid=int(st[2]),sid=int(st[3]),start_ticks=int(st[19]),boot_id=boot,comm=comm,exe=exe,command=(q/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
  except (FileNotFoundError,ProcessLookupError):pass
 ck('fresh_full_216_groups_AND_sessions_no_Julia',not matches)
 mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()};available=mem['MemAvailable'];swap=mem['SwapTotal']-mem['SwapFree'];ck('fresh_resources',available>=6*1024**2 and swap<=1024**2)
 details['fresh_host']=dict(time=time.time(),processes_seen=seen,matches=matches,unreadable_exe_pids=unreadable,available_kib=available,swap_used_kib=swap,boot_id=boot,groups=sorted(groups),head=head,master=master,scope='All process stat and comm, all readable exe; inaccessible system exe remain a visibility limit')
 remote=dict(line.split()[::-1] for line in git('ls-remote','origin','refs/heads/codex/simplex-core-architecture','refs/heads/master').splitlines())
 ck('fresh_remote_refs',remote=={'refs/heads/codex/simplex-core-architecture':head,'refs/heads/master':master});details['remote_refs']=remote
 wantcommand=['/bin/bash','/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh','--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+str(stage),str(P/'driver.jl'),str(run/'output'),'integration',str(stage)]
 wantcfg=dict(phase='integration',seconds=60,expected_exit=0,arm='candidate',stage=str(stage),run=str(run),output=str(run/'output'),command=wantcommand)
 ck('exact_command_resource_scope_config',cfg==rd(run/'config.json')==wantcfg)
 sm=rd(E/'source-map.json');ck('eight_byte_identical_infrastructure',len(sm['byte_identical'])==8 and all(sha(E/n)==sha(v['source'])==v['sha256'] for n,v in sm['byte_identical'].items()))
 ck('driver_original_binding',sm['driver']==str(P/'driver.jl') and sha(sm['driver'])==sm['driver_sha256'])
 ef,pf=funcs(E/'control.py'),funcs(P/'control.py');ck('unchanged_other_control_functions',set(ef)==set(pf) and all(ef[n]==pf[n] for n in ef if n not in ['config','predecessor']))
 smp=rd(P/'source-map.json'); seams=rd(smp['observer_seams']);text=(P/'observed-factorization.jl').read_text()
 for i in reversed(seams['application_order']):
  edit=seams['edits'][i];ck('observer_seam_'+str(i),text.count(edit['after'])==edit['count']);text=text.replace(edit['after'],edit['before'])
 ck('six_observer_seams_exact_inverse',len(seams['edits'])==6 and text==Path(smp['observer_source']).read_text())
 ti=rd(P/'test-inverse.json');text=(P/'observed-tests.jl').read_text()
 for i,edit in enumerate(reversed(ti['edits'])):
  ck('test_inverse_fragment_'+str(i),text.count(edit['after'])==1);text=text.replace(edit['after'],edit['before'])
 ck('three_test_fragments_exact_inverse',len(ti['edits'])==3 and text==Path(ti['original']).read_text())
 rec=(P/'recorder.jl').read_text();ck('recorder_inherited_exact',rec in Path(smp['recorder_source']).read_text())
 test=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/stdlib/v1.13/Test/src/Test.jl');ck('Test113_inheritance_pinned',str(test) in files and 'testsettype = :(get_testset_depth() == 0 ? DefaultTestSet : typeof(get_testset()))' in test.read_text())
 base=rd(E/'controls-baseline.json');ck('fixed20_controls_original_raw_binding',len(base['default'])==20 and sha(base['source'])==base['source_sha256'])
 ck('preflight_evidence_bound',rd(K/'preflight.json')['all_passed'] is True and binds(rd(K/'preflight.json')['sha256']))
 details['counts']=dict(sealed_files=len(files),inventory=len(inv),stage=len(manifest),driver_pins=1503,driver_review=1504,driver_supplementary=18,environment_pins=1561,environment_review=1562,environment_supplementary=12,groups=len(groups))
except Exception as error:
 ck('reviewer_exception',False);details['exception']=repr(error)
result=dict(all_passed=all(checks.values()),checks=checks,details=details,scope='Fresh independent exact-stage read-only admission; no Julia or old checker execution',runtime='UNEXECUTED')
with (K/'admission-checks.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=result['all_passed'],checks=len(checks),failed=[k for k,v in checks.items() if not v],details=details if not result['all_passed'] else details.get('counts'))))
