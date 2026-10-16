"""Independent offline reviewer: stdlib and read-only Git/proc queries only.
Does not import or execute any author helper or Julia source.
Writes only its new checks record in the exact reviewed run directory.
"""
from pathlib import Path
import hashlib,json,os,subprocess,time,tomllib
RUN=Path(__file__).resolve().parent;D=RUN.parents[1];R=D.parents[3]
W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl')
MASTER='26e2291745999f485a74f643298ca997d65c7205';HEAD='1c10d172dcd8d914041f74be2f6d5fd7f6a84d87';ENTRY='924e72e9a05634112dc107d6813f9b3a21e4ff54'
checks={};details={}
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for x in iter(lambda:f.read(1024*1024),b''):h.update(x)
 return h.hexdigest()
def git(*args,root=R):return subprocess.check_output(['git',*args],cwd=root)
def ck(name,value):checks[name]=bool(value)
def bound(v):return all(sha(Path(p) if Path(p).is_absolute() else R/p)==h for p,h in v.items())
s=read(RUN/'sealed.json');cfg=read(RUN/'config.json');host=read(RUN/'host.json')
prep=read(D/'preparation-pins.json');review=read(D/'review.json');runtime=read(D/'runtime-inputs-complete.json')['inventory'];stages=read(D/'stages.json');baseline=read(D/'baseline.json')
ck('sealed_schema',set(s)=={'phase','head','master','boot_id','groups','config','files','trees','inventory','inputs'} and s['inputs']==[])
ck('unique_sorted_files',s['files']==sorted(set(s['files'])))
paths=set(s['files']);treefiles=set();symlinks=[]
for root in s['trees']:
 for p in Path(root).rglob('*'):
  if p.is_symlink():symlinks.append(str(p))
  if p.is_file():treefiles.add(str(p))
ck('tree_no_symlinks',not symlinks and all(not Path(p).is_symlink() for p in s['trees']))
ck('inventory_exact_membership',set(s['inventory'])==paths|treefiles)
mismatches=[]
for p,v in s['inventory'].items():
 if set(v)!={'resolved','sha256'} or str(Path(p).resolve(strict=True))!=v['resolved'] or sha(p)!=v['sha256']:mismatches.append(p)
ck('inventory_all_hashes_and_resolutions',not mismatches);details['inventory_count']=len(s['inventory']);details['inventory_mismatches']=mismatches
expected=set(prep['sha256'])|{str(D/'preparation-pins.json'),str(D/'review.json')}|set(runtime)|{str(root/n) for label,root in [('diagnostic',R),('production',W)] for n in baseline[label]}|{str(Path(cfg['stage'])/n) for n in stages['red']['sha256']}|{str(RUN/'host.json'),str(RUN/'config.json')}
ck('seal_exact_derived_file_membership',paths==expected)
ck('seal_exact_trees',s['trees']==[cfg['stage'],str(R/'diagnostics/direct-lu-policy-adapters/reproduce')])
ck('preparation_exact78',len(prep['sha256'])==78 and set(prep['sha256'])==set(read(D/'required-paths.json')['paths']) and bound(prep['sha256']))
ck('preparation_review_exact79',review['accepted'] is True and review['findings']==[] and review['scope']=='direct adapter driver preparation' and review['pins_sha256']==sha(D/'preparation-pins.json') and set(review['sha256'])==set(prep['sha256'])|{str(D/'preparation-pins.json')} and bound(review['sha256']) and bound(review.get('evidence_sha256',{})))
ck('runtime609',len(runtime)==609 and all(s['inventory'].get(p)==v for p,v in runtime.items()))
original=read(D/'runtime-inputs.json')['inventory'];ck('original_runtime606_preserved',len(original)==606 and all(runtime[p]==v for p,v in original.items()))
for label,root in [('diagnostic',R),('production',W)]:
 tracked=git('ls-files','src','test','.github','Project.toml',root=root).decode().splitlines()
 ck(label+'_baseline_exact',set(tracked)==set(baseline[label]) and all(sha(root/n)==h for n,h in baseline[label].items()))
ck('refs',git('rev-parse','HEAD').decode().strip()==s['head']==HEAD and git('rev-parse','master').decode().strip()==s['master']==MASTER and git('rev-parse','HEAD',root=W).decode().strip()==MASTER)
ck('candidate_ancestor',subprocess.run(['git','merge-base','--is-ancestor',ENTRY,HEAD],cwd=R).returncode==0)
ck('remote_master',git('ls-remote','origin','refs/heads/master').decode().strip()==MASTER+'\trefs/heads/master')
ck('tracked_worktree_index_clean',not git('diff','--name-only') and not git('diff','--cached','--name-only'))
masterfiles=git('ls-tree','-r','--name-only',MASTER,'src','Project.toml').decode().splitlines();ck('master71',len(masterfiles)==71)
for mode,stage in stages.items():
 root=Path(stage['path']);actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
 ck(mode+'_stage75',len(actual)==75 and actual==set(stage['sha256']) and all(sha(root/n)==h for n,h in stage['sha256'].items()))
 source=read(stage['source_manifest'])
 ck(mode+'_accepted_source_manifest',all(sha(root/n)==h for n,h in source['source_sha256'].items()))
 ck(mode+'_master_inverse',all((root/n).read_bytes().replace(b'include("factor-export.jl")\ninclude("direct-factor.jl")\n',b'')==git('show',MASTER+':'+n) if n=='src/JSimplex.jl' else (root/n).read_bytes()==git('show',MASTER+':'+n) for n in masterfiles))
 ck(mode+'_environment',all((root/n).read_bytes()==(W/n).read_bytes() for n in ['Manifest.toml','LocalPreferences.toml']))
 old=R/'diagnostics/direct-lu-markowitz/reproduce';new=R/'diagnostics/direct-lu-policy-adapters/reproduce'
 ck(mode+'_implementation_identity',all((root/'src'/n).read_bytes()==((old if mode=='red' else new)/n).read_bytes() for n in ['factor-export.jl','direct-factor.jl']))
C=R/'diagnostics/direct-lu-policy-adapters/reproduce';P=D.parent/'DIRECT-LU-POLICY-ADAPTER-PREPARATION';cr=read(P/'review.json')
ck('candidate7_commit_bytes_and_review',len(list(C.iterdir()))==7 and cr['accepted'] is True and cr['findings']==[] and all(p.read_bytes()==git('show',ENTRY+':'+str(p.relative_to(R))) and sha(p)==cr['sha256'][str(p)] for p in C.iterdir()))
ck('legacy_export_fixtures_unchanged',all((C/n).read_bytes()==(R/'diagnostics/direct-lu-markowitz/reproduce'/n).read_bytes() for n in ['factor-export.jl','fixtures.jl']))
for n,v in read(D/'reused-helpers.json').items():ck('reused_'+n,(D/n).read_bytes()==Path(v['source']).read_bytes() and sha(D/n)==v['sha256'])
wrapper='/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh'
expectedcommand=['/bin/bash',wrapper,'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--history-file=no','--project='+cfg['stage'],str(D/'driver.jl'),str(RUN/'output'),cfg['stage'],'red300']
ck('exact_red300_config',s['phase']=='red300' and s['config']==cfg and cfg==dict(phase='red300',mode='red',seconds=300,expected_exit=1,stage=stages['red']['path'],run=str(RUN),output=str(RUN/'output'),command=expectedcommand))
ck('no_attempt',not any((RUN/n).exists() for n in ['output','reservation.json','prehost.json','launch-pins.json','invocation.json','audit.json']))
e=read(D/'environment.json');ck('loading_environment',{k:os.environ.get(k) for k in e}==e)
ex=read(D/'expected-tests.json')['red'];et=tomllib.loads((D/'expected-tests.toml').read_text())['red'];ck('red_json_toml7',ex=={'assertions':7,'groups':[['Missing direct policy contract (seven expected failures)',0,7,0,0]]} and et['assertions']==7 and [[g[k] for k in ['name','pass','fail','error','broken']] for g in et['groups']]==ex['groups'])
groups=set(s['groups']);matches=[];unreadable=[];count=0
for p in Path('/proc').glob('[0-9]*'):
 try:
  fields=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip();exe='';count+=1
  try:exe=str((p/'exe').resolve(strict=True))
  except PermissionError:unreadable.append(int(p.name))
  except FileNotFoundError:pass
  if int(fields[2]) in groups or int(fields[3]) in groups or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):
   matches.append(dict(pid=int(p.name),pgid=int(fields[2]),sid=int(fields[3]),start_ticks=int(fields[19]),comm=comm,exe=exe,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,ProcessLookupError):pass
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();mem={x.split(':')[0]:int(x.split()[1]) for x in Path('/proc/meminfo').read_text().splitlines()}
ck('host222_groups_sessions_clear',len(groups)==222 and host['groups']==s['groups'] and host['matches']==[] and not matches and boot==host['boot_id']==s['boot_id'])
ck('fresh_resources',mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2)
details['host']=dict(time=time.time(),boot_id=boot,process_count=count,groups=sorted(groups),matches=matches,unreadable_exe_pids=unreadable,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree'],scope='Fresh all-group/session and comm/readable-exe inspection; inaccessible executable links remain visibility limitation')
record=dict(scope='Independent exact RED300 admission offline checks; no author executable imports/runs and no Julia',all_passed=all(checks.values()),checks=checks,details=details)
with (RUN/'admission-checks.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=record['all_passed'],checks=len(checks),failed=[k for k,v in checks.items() if not v],inventory=len(s['inventory']),files=len(s['files']),host_matches=matches,available_kib=mem['MemAvailable'])))
