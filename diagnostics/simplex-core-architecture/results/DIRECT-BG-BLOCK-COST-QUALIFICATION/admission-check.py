"""New independent exact-stage read-only admission checks. No package script imports or numerical execution."""
from pathlib import Path
import os,json,hashlib,re,tomllib,subprocess,time
Q=Path(__file__).resolve().parent;E=Q.parent/'DIRECT-BG-BLOCK-COST-PREPARATION';R=E.parents[3];RUN=E/'runs/cost1-300';W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl');C=R/'diagnostics/direct-bg-block-upper/reproduce'
checks={};counts={};cache={}
def check(v,n):
 checks[n]=bool(v)
 if not v:raise AssertionError(n)
def unique(items):
 d={}
 for k,v in items:
  if k in d:raise ValueError('duplicate key '+k)
  d[k]=v
 return d
def rd(p):return json.loads(Path(p).read_text(),object_pairs_hook=unique)
def path(p):return Path(p) if Path(p).is_absolute() else R/p
def sha(p):
 p=path(p);st=p.stat();key=(str(p),st.st_size,st.st_mtime_ns,st.st_ino)
 if key not in cache:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):h.update(b)
  cache[key]=h.hexdigest()
 return cache[key]
def bindings(m,n):check(all(sha(p)==h for p,h in m.items()),n)
def inv(j,n):
 paths=set(j['files'])
 for name in j['trees']:
  root=Path(name);check(root.is_dir() and not root.is_symlink(),n+'_root_'+root.name)
  for p in root.rglob('*'):
   check(not (p.is_symlink() and (p.is_dir() or not p.exists())),n+'_link_'+str(p)) if p.is_symlink() else None
   if p.is_file():paths.add(str(p))
 check(paths==set(j['inventory']),n+'_exact_membership')
 check(all(str(Path(p).resolve(strict=True))==v['resolved'] and sha(p)==v['sha256'] for p,v in j['inventory'].items()),n+'_all_paths_and_hashes')
def git(*a,cwd=R):return subprocess.check_output(['/usr/bin/git',*a],cwd=cwd,text=True).strip()
s=rd(RUN/'sealed.json');cfg=s['config'];sp=RUN/'sealed.json'
check(s['phase']=='cost1-300' and cfg==rd(RUN/'config.json')==rd(E/'commands.json')['cost1-300'],'exact_phase_configuration')
check(cfg['seconds']==300 and cfg['process']==1 and cfg['expected_exit']==0,'first_300_only')
check({p.name for p in (E/'runs').iterdir()}=={'cost1-300'} and {p.name for p in RUN.iterdir()}=={'host.json','config.json','sealed.json'},'only_seal_no_reservation_output')
check(len(s['files'])==len(set(s['files']))==1824,'exact1824sealedfiles');inv(s,'sealed');counts['sealed_files']=len(s['files']);counts['sealed_inventory']=len(s['inventory'])
p=rd(E/'preparation-pins.json');v=rd(E/'review.json');required=rd(E/'required-paths.json')['paths']
check(set(p['sha256'])==set(required) and len(required)==len(set(required))==1820,'preparation_membership')
bindings(p['sha256'],'preparation_hashes');check(v['accepted'] is True and v['findings']==[] and v['scope']=='block BG matched cost preparation','preparation_accepted')
check(v['pins_sha256']==sha(E/'preparation-pins.json') and set(v['sha256'])==set(p['sha256'])|{str(E/'preparation-pins.json')},'preparation_review_exact');bindings(v['sha256'],'preparation_review_hashes');bindings(v['evidence_sha256'],'preparation_review_evidence')
rt=rd(E/'runtime-inputs-complete.json')['inventory'];check(set(rt)<=set(s['files']),'runtime_in_seal');check(all(str(Path(n).resolve(strict=True))==x['resolved'] and sha(n)==x['sha256'] for n,x in rt.items()),'runtime_paths_hashes');counts['runtime_entries']=len(rt)
for label,root in [('diagnostic',R),('production',W)]:
 b=rd(E/'baseline.json')[label];check(set(git('ls-files','src','test','.github','Project.toml',cwd=root).splitlines())==set(b),'baseline_membership_'+label);check(all(sha(root/n)==h for n,h in b.items()),'baseline_hashes_'+label)
st=rd(E/'stages.json')['cost'];S=Path(st['path']);G=Path(st['source']);actual={str(p.relative_to(S)) for p in S.rglob('*') if p.is_file()}
check(actual==set(st['sha256']) and len(actual)==84,'stage84membership');check(not S.is_symlink() and not any(p.is_symlink() for p in S.rglob('*')),'stage_no_symlink');check(all(sha(S/n)==h for n,h in st['sha256'].items()),'stage_hashes');check(all(sha(G/n)==h for n,h in st['baseline_sha256'].items()),'GREEN_stage_baseline_hashes')
check(actual-set(st['baseline_sha256'])=={'src/probe-upper.jl','src/probe-bg.jl','src/probe-oracles.jl'},'only_three_probe_additions')
for n in st['baseline_sha256']:
 b=(S/n).read_bytes()
 if n=='src/JSimplex.jl':
  inc=st['inserted_includes'].encode();check(b.count(inc)==1,'one_include_block');b=b.replace(inc,b'')
 check(b==(G/n).read_bytes(),'stage_inverse_'+n)
for n in ['probe-upper.jl','probe-bg.jl','probe-oracles.jl']:check((E/n).read_bytes()==(S/'src'/n).read_bytes(),'probe_stage_'+n)
i=rd(E/'probe-inverse.json');bindings(i['sources'],'probe_sources')
def rename(t,m):
 for a,b in sorted(m.items(),key=lambda x:-len(x[0])):t=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(a)+r'(?![A-Za-z0-9_!])',b,t)
 return t
ren=i['renames'];check(len(set(ren.values()))==len(ren),'injective_renames');u=(E/'probe-upper.jl').read_text();check(u.startswith(i['header']),'probe_header');u=rename(u[len(i['header']):],{b:a for a,b in ren.items()})
for k,x in enumerate(i['injections']):
 t=x['anchor']+'\n    # BLOCK_COST_PROBE_BEGIN\n'+x['code']+'\n    # BLOCK_COST_PROBE_END\n';check(u.count(t)==1,'probe_counter_anchor_'+str(k));u=u.replace(t,x['anchor'],1)
check(u.count(i['allocator']['new'])==1,'probe_allocator_once');u=u.replace(i['allocator']['new'],i['allocator']['old']);check(u==(C/'block-upper.jl').read_text(),'upper_exact_inverse');check(rename((E/'probe-bg.jl').read_text(),{b:a for a,b in ren.items()})==(C/'block-bg.jl').read_text(),'manager_exact_inverse');o=(C/'block-oracles.jl').read_text().split('function _bgu_materialize')[0];check((E/'probe-oracles.jl').read_text()==o+rename(o,ren),'oracles_inverse')
line=rd(E/'lineage.json');bindings(line['sha256'],'GREEN_lineage_hashes');GR=E.parent/'DIRECT-BG-BLOCK-DRIVER-PREPARATION/runs/green300';gv=rd(GR/'result-review.json');check(gv['accepted'] is True and gv['findings']==[] and gv['scope']=='block BG GREEN result' and gv['phase']=='green300','GREEN_review_accepted');check(set(gv['sha256'])=={str(p) for p in GR.rglob('*') if p.is_file() and p!=GR/'result-review.json'},'GREEN_review_membership');bindings(gv['sha256'],'GREEN_review_files');bindings(gv.get('evidence_sha256',{}),'GREEN_review_evidence');check(rd(GR/'audit.json')['all_passed'] is True,'GREEN_audit_accepted');inv(rd(GR/'launch-pins.json'),'GREEN_launch_inventory');inv(rd(GR/'sealed.json'),'GREEN_sealed_inventory')
f=rd(E/'inputs.json');check(tomllib.loads((E/'inputs.toml').read_text())==f,'fixtures_json_toml');check([x['name'] for x in f['fixtures']]==['sparse32','dense32','sparse96','dense96'] and all(len(x['steps'])==8 and len(x['matrices'])==9 for x in f['fixtures']),'fixture_schedule');check(set(rd(E/'loaded-paths.json'))=={'SparseArrays','LinearAlgebra','TOML','PrecompileTools'},'loaded_libraries_no_Test')
err=rd(E/'timing-erratum-acceptance.json');check(err['accepted'] is True and err['findings']==[] and err['scope']=='block BG timing-count erratum','timing_erratum_accepted');bindings(err['sha256'],'erratum_all_hashes');ec=rd(E/'timing-erratum-check.json');check(ec['all_passed'] is True and ec['counts']['executed_explicit_time_ns_reads']==70,'erratum70');bindings(ec['source_sha256'],'erratum_sources');bindings(ec['preserved_existing_sha256'],'erratum_preserved_evidence')
t=(E/'cost.jl').read_text();life=t.split('function lifecycle',1)[1].split('# No extra factor solves.',1)[0];check(life.count('time_ns()')==14 and 'for k in 1:8' in life and 'if k==4' in life and 'elseif k==8' in life,'source14sites70reads');counts['explicit_clock_reads_per_lifecycle']=2+8*8+4;counts['explicit_clock_reads_160_windows']=160*70;counts.update(constructors=200,refactors=400,replacements=1472,ftran=2944,btran=1472,factor_copies=0,residual_vectors=4416)
env=rd(E/'environment.json');check(all(os.environ.get(k)==v for k,v in env.items() if k!='PATH'),'nonPATHenvironment');ev=rd(Q/'environment-review.json');check(ev['accepted'] is True and ev['findings']==[],'environment_review_accepted');bindings(ev['sha256'],'environment_review_hashes')
head=git('rev-parse','HEAD');master=git('rev-parse','master');check(head==s['head']=='ffa005e219b2eb4b8f119a24f6c9953214cac8b9' and master==s['master']=='26e2291745999f485a74f643298ca997d65c7205' and git('rev-parse','HEAD',cwd=W)==master,'all_exact_refs');check(master+'\trefs/heads/master' in git('ls-remote','origin','refs/heads/master'),'remote_master');check(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'no_tracked_changes');check(subprocess.run(['/usr/bin/git','merge-base','--is-ancestor','2642947bc35143bbd72c1c4b9509a4a3e3bcc86d','HEAD'],cwd=R).returncode==0,'accepted_ancestor')
groups=set(s['groups']);check(groups==set(rd(E/'host.json')['groups']) and len(groups)==238,'all238groups');boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();hs=rd(RUN/'host.json');check(not hs['matches'] and all(hs[k]==s[k] for k in ('head','master','boot_id','groups')) and boot==s['boot_id'],'sealed_host')
matches=[];unreadable=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  a=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip();exe=''
  try:exe=str((p/'exe').resolve(strict=True))
  except PermissionError:unreadable.append(int(p.name))
  except FileNotFoundError:pass
  if int(a[2]) in groups or int(a[3]) in groups or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):matches.append({'pid':int(p.name),'pgid':int(a[2]),'sid':int(a[3]),'start_ticks':int(a[19]),'comm':comm,'exe':exe,'command':(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')})
 except (FileNotFoundError,ProcessLookupError):pass
mem={x.split(':')[0]:int(x.split()[1]) for x in Path('/proc/meminfo').read_text().splitlines()};check(not matches,'fresh_process_and_session_closure');check(mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2,'resources')
counts['unique_files_hashed']=len(cache)
out={'all_passed':True,'checks':checks,'counts':counts,'host':{'time':time.time(),'boot_id':boot,'head':head,'master':master,'groups':sorted(groups),'matches':matches,'unreadable_exe_pids':unreadable,'available_kib':mem['MemAvailable'],'swap_used_kib':mem['SwapTotal']-mem['SwapFree']},'pins_sha256':sha(sp),'checker_sha256':sha(__file__),'scope':'Independent fresh cost1-300 sealed binding/source/host admission checks; package scripts only read, no Julia or historical reruns'}
with (Q/'admission-check.json').open('x') as outstream:json.dump(out,outstream,indent=2);outstream.write('\n')
print(json.dumps({'all_passed':True,'checks':len(checks),'counts':counts,'host':out['host']}))
