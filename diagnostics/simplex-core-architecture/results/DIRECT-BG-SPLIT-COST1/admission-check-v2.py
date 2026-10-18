"""Fresh independent read-only admission inspection. Never imports author code or Julia.
Writes only this review's new result and host snapshot, exclusively.
"""
from pathlib import Path
import hashlib,json,os,re,subprocess,time,tomllib,traceback
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
D=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-SPLIT-COST-PREPARATION'
E=D.parent/'DIRECT-BG-SPLIT-COST1';run=D/'runs/cost1-300'
C=R/'diagnostics/direct-bg-split-upper/reproduce'
W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl')
HEAD='49b26f913df5497bafa8292529a872070864911c';MASTER='26e2291745999f485a74f643298ca997d65c7205'
checks={};details={};cache={}
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 p=Path(p)
 if str(p) not in cache:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):h.update(b)
  cache[str(p)]=h.hexdigest()
 return cache[str(p)]
def check(v,n):
 checks[n]=bool(v)
 if not v:raise AssertionError(n)
def save(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')
def git(*args,cwd=R):return subprocess.check_output(['git',*args],cwd=cwd,text=True).strip()
def binds(j,k='sha256'):
 return all(sha(Path(n) if Path(n).is_absolute() else R/n)==v for n,v in j[k].items())
def inventory(files,trees):
 paths={Path(n) for n in files}
 for n in trees:
  t=Path(n);check(t.is_dir() and not t.is_symlink(),'tree_root_'+n)
  for p in t.rglob('*'):
   check(not p.is_symlink() or (p.exists() and not p.is_dir()),'tree_entry_'+str(p))
   if p.is_file():paths.add(p)
 return {str(p):{'resolved':str(p.resolve(strict=True)),'sha256':sha(p)} for p in sorted(paths)}
def inverse(t,m):
 for a,b in sorted(m.items(),key=lambda ab:-len(ab[1])):t=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(b)+r'(?![A-Za-z0-9_!])',a,t)
 return t
try:
 s=read(run/'sealed.json');p=read(D/'preparation-pins.json');v=read(D/'review.json');cfg=read(run/'config.json');h=read(run/'host.json');pre=read(E/'preflight.json');a=read(E/'allowance.json')
 check(a['authorized'] is True and (a['phase'],a['max_attempts'],a['max_seconds'])==('cost1-300',1,300),'explicit_one_300_allowance')
 check(s['phase']=='cost1-300' and s['head']==HEAD and s['master']==MASTER,'sealed_refs_phase')
 check(set(s['files'])==set(s['inventory']) and len(s['files'])==len(set(s['files']))==1831,'sealed_exact1831')
 check(inventory(s['files'],s['trees'])==s['inventory'],'complete_sealed_inventory_with_trees')
 check(s['inputs']==[] and s['trees']==[cfg['stage'],str(C)],'trees_inputs_exact')
 check(len(p['sha256'])==1827 and set(p['sha256'])==set(read(D/'required-paths.json')['paths']) and binds(p),'preparation1827_current_membership')
 check(v['accepted'] is True and v['findings']==[] and v['scope']=='split BG matched cost preparation','preparation_review_acceptance')
 check(v['pins_sha256']==sha(D/'preparation-pins.json') and len(v['sha256'])==1828 and set(v['sha256'])==set(p['sha256'])|{str(D/'preparation-pins.json')} and binds(v),'preparation_review1828_exact')
 check(len(v['evidence_sha256'])==8 and binds(v,'evidence_sha256'),'preparation_review8_evidence')
 check(cfg==s['config']==read(D/'commands.json')['cost1-300'],'exact_config_commands')
 expected=['/bin/bash','/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh','--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--history-file=no','--project='+cfg['stage'],str(D/'cost.jl'),'cost1-300',str(run/'output'),cfg['stage']]
 check(cfg==dict(phase='cost1-300',process=1,seconds=300,expected_exit=0,stage=cfg['stage'],run=str(run),output=str(run/'output'),command=expected),'exact_concrete300command')
 check({q.name for q in run.iterdir()}=={'sealed.json','config.json','host.json'} and {q.name for q in (D/'runs').iterdir()}=={'cost1-300'},'no_output_reservation_previous_attempt')
 check(git('rev-parse','HEAD')==HEAD and git('rev-parse','master')==MASTER and git('rev-parse','HEAD',cwd=W)==MASTER,'fresh_git_refs')
 check(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'tracked_index_unchanged')
 remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture');details['remote_refs']=remote
 check(set(remote.splitlines())=={HEAD+'\trefs/heads/codex/simplex-core-architecture',MASTER+'\trefs/heads/master'},'fresh_remote_refs')
 for label,root in [('diagnostic',R),('production',W)]:
  b=read(D/'baseline.json')[label]
  check(set(git('ls-files','src','test','.github','Project.toml',cwd=root).splitlines())==set(b) and all(sha(root/n)==v for n,v in b.items()),'baseline_'+label)
 check({k:os.environ.get(k) for k in read(D/'environment.json')}==read(D/'environment.json'),'exact_loading_environment')
 rt=read(D/'runtime-inputs-complete.json')
 check(len(rt['inventory'])==609 and inventory(rt['inventory'],[])==rt['inventory'],'runtime609_resolved_hashes')
 st=read(D/'stages.json')['cost'];root=Path(st['path']);base=Path(st['source'])
 check(len(st['sha256'])==84 and len(st['baseline_sha256'])==81,'stage84_GREEN81')
 check({str(q.relative_to(root)) for q in root.rglob('*') if q.is_file()}==set(st['sha256']) and not any(q.is_symlink() for q in root.rglob('*')),'stage_exact_no_symlinks')
 for n,hsh in st['sha256'].items():check(sha(root/n)==hsh,'stage_hash_'+n)
 for n,hsh in st['baseline_sha256'].items():
  b=(root/n).read_bytes()
  if n=='src/JSimplex.jl':
   check(b.count(st['inserted_includes'].encode())==1,'root_includes_unique');b=b.replace(st['inserted_includes'].encode(),b'')
  check(hashlib.sha256(b).hexdigest()==hsh==sha(base/n),'GREEN_inverse_'+n)
 check(all((D/n).read_bytes()==(root/'src'/n).read_bytes() for n in ['probe-upper.jl','probe-bg.jl','probe-oracles.jl']),'probe_stage_identity')
 j=read(D/'probe-inverse.json');t=(D/'probe-upper.jl').read_text()
 check(len(j['counts'])==len(set(j['counts']))==83 and all(sha(n)==hsh for n,hsh in j['sources'].items()),'probe83_sources')
 check(t.startswith(j['header']),'probe_header')
 t=inverse(t[len(j['header']):],j['renames'])
 for i,x in enumerate(reversed(j['injections'])):
  full=x['anchor']+'\n    # SPLIT_COST_PROBE_BEGIN\n'+x['code']+'\n    # SPLIT_COST_PROBE_END\n'
  check(t.count(full)==1,'injection_unique_'+str(i));t=t.replace(full,x['anchor'])
 for i,x in enumerate(reversed(j['replacements'])):
  check(t.count(x['new'])==1,'replacement_unique_'+str(i));t=t.replace(x['new'],x['old'])
 check(t==(C/'split-upper.jl').read_text(),'complete_upper_inverse')
 check(inverse((D/'probe-bg.jl').read_text(),j['renames'])==(C/'split-bg.jl').read_text(),'complete_adapter_inverse')
 pure=(C/'split-oracles.jl').read_text().split('function _sbu_materialize')[0];o=(D/'probe-oracles.jl').read_text()
 check(o.startswith(pure) and inverse(o[len(pure):],j['renames'])==pure+j['helper'],'complete_oracles_helper_inverse')
 G=D.parent/'DIRECT-BG-SPLIT-DRIVER-PREPARATION/runs/green300';rv=read(G/'result-review.json');lin=read(D/'lineage.json')
 check(binds(lin),'GREEN_lineage')
 check(rv['accepted'] is True and rv['findings']==[] and rv['phase']=='green300' and rv['scope']=='split BG GREEN result','GREEN_accepted')
 check(set(rv['sha256'])=={str(q) for q in G.rglob('*') if q.is_file() and q!=G/'result-review.json'} and binds(rv),'GREEN_exact_result_membership')
 check('evidence_sha256' not in rv or binds(rv,'evidence_sha256'),'GREEN_supplemental_evidence')
 check(read(G/'audit.json')['all_passed'] is True,'GREEN_audit_pass')
 for n in ['sealed.json','launch-pins.json']:
  q=read(G/n);check(inventory(q['files'],q['trees'])==q['inventory'],'GREEN_'+n+'_complete_inventory')
 expectedfiles=set(p['sha256'])|{str(D/'preparation-pins.json'),str(D/'review.json'),str(D/'lineage.json'),str(run/'host.json'),str(run/'config.json')}|set(lin['sha256'])|set(rt['inventory'])|{str(root/n) for n in st['sha256']}|{str(rt0/n) for label,rt0 in [('diagnostic',R),('production',W)] for n in read(D/'baseline.json')[label]}
 check(set(s['files'])==expectedfiles,'independently_reconstructed_sealed_membership')
 for n,jj in read(D/'reused-files.json').items():check(sha(D/n)==jj['sha256']==sha(jj['source']),'fixed_reuse_'+n)
 fs=read(D/'inputs.json')['fixtures'];check([(f['name'],f['n'],len(f['matrices']),len(f['steps'])) for f in fs]==[(z,n,9,8) for z,n in [('sparse32',32),('dense32',32),('sparse96',96),('dense96',96)]],'fixed_four_inputs')
 check(tomllib.loads((D/'inputs.toml').read_text())==read(D/'inputs.json'),'identical_JSON_TOML_inputs')
 cost=(D/'cost.jl').read_text();probe=(D/'probe.jl').read_text();life=cost[cost.index('function lifecycle'):cost.index('# No extra factor')]
 check('timed=@timed lifecycle' in cost and 'factory(side,F,fixture.matrices[1],backend)' in life,'whole_setup_timed')
 check(all(x not in life for x in ['_split_probe_counts','summarysize','checkpoint(','token.','unchanged(']),'no_timed_diagnostic_scans')
 check('for pair in 1:10' in cost and 'pair>3' in cost and 'isodd(pair) ⊻ startswith(PHASE,"cost2")' in cost,'ten_alternating_pairs')
 check('J._split_bg_factor(B,backend,policy(backend))' in cost and 'J._direct_lu_factor(F,B,backend,policy(backend);normalize=true)' in cost and '_dynamic' not in cost and '_block_bg' not in cost,'only_packed_split_factories')
 check(life.count('time_ns()')==14 and 'for k in 1:8' in life and 'clocks=zeros(UInt64,6)' in life,'clock_source_sites')
 details['budget']={'cells':4*2,'warm_windows':4*2*3*2,'measured_windows':4*2*7*2,'windows':4*2*10*2,'construct':160+8*3+8*2,'refactor':160*2+8*6+8*4,'updates':160*8+8*24,'FTRAN':160*16+8*48,'BTRAN':160*8+8*24,'clocks_per_lifecycle':2+8*8+4,'output_vectors':160*24+8*72,'outputs':5+2+8*4+8*20,'checkpoints':8*(1+8+2)}
 check(list(details['budget'].values())==[8,48,112,160,200,400,1472,2944,1472,70,4416,199,88],'independent_exact_work_output_counts')
 check('getfield(getfield(a,:ref),:mem)' in probe and '16*C+4*R+28*K+32*U.n+656' in probe and '8*U.n+24*D' in probe,'backing_and_payload_source')
 check('"extents"=>[[Int(getfield(U,f)[b])' in probe and '"active_slack"=>C-free-U.live' in probe and '"bin_heads"=>Int.(U.bins)' in probe,'full_partition_serialization')
 check('for c in 1:64' in probe and 'for c in 1:8' in probe and 'for r in 1:32' in probe and 'for cycle in 1:3' in probe and probe.count('        for r in 1:40\n')==2,'fixed_structural_schedules')
 details['structural_budget']={'sets':64+32+1+3*80,'reservations':8+1,'invariants':64+9+33+243,'scalar_value_checks':64+sum(range(1,9))+sum(range(1,33))+3*40,'schedule_snapshots':9+33+9}
 ev=(D/'evidence.py').read_text();an=(D/'analysis.py').read_text();au=(D/'audit.py').read_text();ctrl=(D/'control.py').read_text();guard=(D/'guard.py').read_text();sup=(D/'supervisor.py').read_text();launch=(D/'launch.py').read_text()
 for phrase in ['No overlap/hole','Exact slab partition','All descriptors reachable','No chain cycle/duplicate','Backing Memory capacity','Whole capacity partition','All Vector objects enumerated','Fragmented double growth','Repeated4 work','Monotone relocation work']:
  check(phrase in ev,'audit_'+phrase)
 check('Q(128*n,2**52)' in an and 'row,col=(j,i) if transpose else (i,j)' in an and 'm[\'nzval\']' in an,'exact_dyadic_orientation_bound')
 check("a['outputs']==b['outputs']" in ev and "row['compile_seconds']==0 and row['recompile_seconds']==0" in an,'bitwise_and_zero_compile')
 check("['time_median_gate','allocation_gate','memory_gate','probe_memory_gate']" in an and 'not 3<=faster<=7' in an and 'median\']<=.95' in an and "for k in ('bytes','events')" in an,'all_eight_first_gates')
 check("10*p['candidate']['retained_bytes']<=11*p['reference']['retained_bytes'] for p in pairs" in an and "10*s['graphs'][1]<=11*s['graphs'][0] for s in pr['states']" in ev,'every_final_and_checkpoint_memory')
 check("a['faster_pairs']+b['faster_pairs']>=10" in an and 'first_process_viable' in ctrl,'second_run_two_process_gate')
 check("warning|world[ -]age" in ev and "warning|world[ -]age" in au and "'raw.toml' not in names" in ev and "not sup.get('guard_term')" in ev and "not sup.get('hard_timeout')" in ev,'puretimeout_warning_and_prefix_rules')
 check('seconds=cfg[\'seconds\']-8' in ctrl and 'started+seconds' in ctrl and 'started+limit-6' in sup and 'started+limit-2' in sup and "record['elapsed_seconds']<=limit" in sup,'300_292_inclusive_supervision')
 check('8 * 1024**3' in guard and '6 * 1024**2' in guard and "sample['swap_used_kib'] > 1024**2" in guard and "OPENBLAS_NUM_THREADS='1'" in guard,'VM_RAM_swap_threads')
 check("open('x')" in ctrl and "res=run/'reservation.json';save" in launch and 'main(phase)' in launch and 'seal(' not in launch,'one_shot_launch_no_auto_seal')
 boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();groups=set(read(D/'host.json')['groups']);matches=[];processes=[];unreadable=[]
 for q in Path('/proc').glob('[0-9]*'):
  try:
   fields=(q/'stat').read_text().rsplit(')',1)[1].split();comm=(q/'comm').read_text().strip();exe=''
   try:exe=str((q/'exe').resolve(strict=True))
   except PermissionError:unreadable.append(int(q.name))
   except FileNotFoundError:pass
   ident={'pid':int(q.name),'pgid':int(fields[2]),'sid':int(fields[3]),'start_ticks':int(fields[19]),'boot_id':boot,'command':(q/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'),'comm':comm,'exe':exe};processes.append(ident)
   if ident['pgid'] in groups or ident['sid'] in groups or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):matches.append(ident)
  except (FileNotFoundError,ProcessLookupError):pass
 mem={v.split(':')[0]:int(v.split()[1]) for v in Path('/proc/meminfo').read_text().splitlines()};memory={'available_kib':mem['MemAvailable'],'swap_used_kib':mem['SwapTotal']-mem['SwapFree']}
 snapshot={'time':time.time(),'boot_id':boot,'groups':sorted(groups),'matches':matches,'processes':processes,'unreadable_exe_pids':unreadable,'memory':memory,'head':HEAD,'master':MASTER,'scope':'Fresh full proc process-group AND session/start/command snapshot. Unreadable exe links remain visibility limitation.'}
 save(E/'admission-host-v2.json',snapshot)
 check(len(groups)==244 and groups==set(s['groups'])==set(h['groups'])==set(pre['groups']) and set(read(G/'posthost.json')['groups'])<=groups,'full244_groups_sessions')
 check(boot==s['boot_id']==h['boot_id']==pre['boot_id'] and not matches and not h['matches'] and not pre['matches'],'fresh_boot_no_groups_sessions_Julia')
 check(memory['available_kib']>=6*1024**2 and memory['swap_used_kib']<=1024**2,'fresh_RAM_swap')
 check(all(x['start_ticks']>0 and x['boot_id']==boot for x in processes),'fresh_process_start_identity')
 details['unique_hashed_files']=len(cache)
 save(E/'admission-check-v2.json',{'accepted':True,'checks':checks,'check_count':len(checks),'details':details,'scope':'Fresh exact read-only admission; no Julia or old script execution.'})
 print('PASS',len(checks),'checks;',len(cache),'unique file hashes; host',memory)
except Exception:
 save(E/'admission-check-v2.json',{'accepted':False,'checks':checks,'check_count':len(checks),'details':details,'error':traceback.format_exc()})
 raise
