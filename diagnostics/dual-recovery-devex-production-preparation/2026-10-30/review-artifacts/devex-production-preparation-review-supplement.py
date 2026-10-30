from pathlib import Path
import hashlib,json,subprocess,difflib
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/dual-recovery-devex-production-preparation/2026-10-30';T=Path('/tmp/devex-production-preparation-20261030');bindings={};checks={}
def data(p):
 p=Path(p);b=p.read_bytes();bindings[str(p)]=hashlib.sha256(b).hexdigest();return b
def read(p):return json.loads(data(p))
def check(k,v):checks[k]=bool(v)
m=read(D/'manifest.json');h=read(D/'host.json');base=read('/tmp/devex-production-preparation-review-check-result.json');script=data(T/'close-publish.py').decode();data(D/'PATCH-FORMAT-NOTE.md');data(W/'diagnostics/dual-recovery-devex-cost-admission/2026-10-30/common.py');data(W/'diagnostics/dual-recovery-devex-cost-admission/2026-10-30/cost_checks.py')
p=D/'production.patch';s=data(p).decode();rebuilt=[]
for rel in m['payload']:
 old=data(D/'baseline'/rel).decode() if (D/'baseline'/rel).exists() else '';new=data(D/'prepared'/rel).decode();rebuilt.append(f'diff --git a/{rel} b/{rel}\n')
 if not (D/'baseline'/rel).exists():rebuilt.append('new file mode 100644\n')
 rebuilt.extend(difflib.unified_diff(old.splitlines(keepends=True),new.splitlines(keepends=True),fromfile='a/'+rel if (D/'baseline'/rel).exists() else '/dev/null',tofile='b/'+rel))
check('canonical_patch',s==''.join(rebuilt));trailing=[l for l in s.splitlines() if l.rstrip()!=l];check('exact_nine_format_markers',len(trailing)==9 and set(trailing)=={' '})
r=subprocess.run(['git','diff','--no-index','--check','--','/dev/null',str(p)],capture_output=True,text=True);check('patch_format_exit3_no_stderr',r.returncode==3 and not r.stderr and r.stdout.count('trailing whitespace.')==9)
check('baseline_mapping_only_four',len(m['baseline_sha256'])==4 and 'for rel,v in m[\'baseline_sha256\'].items():' in script)
check('publication_scope_no_runtime_admission',"review['runtime_qualified'] is False" in script and "review['numerical_admission'] is False" in script and "review['production_admission'] is False" in script)
check('publication_stages_exact_D_names',"names0=sorted(str(p.relative_to(W)) for p in D.rglob('*') if p.is_file())" in script and "git('diff','--cached','--name-only').splitlines()==names" in script)
check('publisher_retains_initial_failure_and_bindings',"a['accepted'] is False" in script and "len(a['bindings'])==353" in script and "all(sha(n)==v for n,v in a['bindings'].items())" in script)
check('publisher_narrow_patch_exception',"len(trailing)==9 and all(line==' ' for line in trailing)" in script and "sha(p)==a['bindings'][str(p)]" in script)
# Fresh independent host snapshot, no historical code imported or executed.
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();groups=set(h['host']['checked_groups']);conflicts=[];identities={}
for p in Path('/proc').glob('[0-9]*'):
 try:
  st=(p/'stat').read_text();f=st[st.rfind(')')+2:].split();a={'pid':int(p.name),'pgid':int(f[2]),'sid':int(f[3]),'start_ticks':int(f[19]),'boot_id':boot,'command':(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')};identities[a['pid']]=a
  if (p/'comm').read_text().strip().lower().startswith('julia') or a['pgid'] in groups or a['sid'] in groups:conflicts.append(a)
 except (FileNotFoundError,ProcessLookupError):pass
check('fresh_same_boot_all742_groups_ANDsessions_noJulia',boot==h['host']['boot_id'] and len(groups)==742 and not conflicts)
owners=[{'original':v['original'],'current':identities.get(v['original']['pid'])} for v in h['previous_owners']]
check('old_owner_identities_retired',all(v['current'] is None or (v['current']['boot_id'],v['current']['start_ticks'])!=(v['original']['boot_id'],v['original']['start_ticks']) for v in owners))
mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()};memory={'available_kib':mem['MemAvailable'],'swap_used_kib':mem['SwapTotal']-mem['SwapFree']};check('memory_safe',memory['available_kib']>=6*1024**2 and memory['swap_used_kib']<=1024**2)
check('main_all_813_actual_booleans',base['accepted'] is True and len(base['checks'])==813 and all(type(v) is bool and v for v in base['checks'].values()))
data(__file__)
result={'accepted':all(checks.values()),'checks':checks,'bindings':bindings,'host':{'boot_id':boot,'checked_group_session_count':len(groups),'conflicts':conflicts,'old_owners':owners,'memory':memory},'patch_format_result':{'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr},'scope':'source_only_new_supplement'}
Path('/tmp/devex-production-preparation-review-supplement-result.json').open('x').write(json.dumps(result,indent=2)+'\n');print(json.dumps({'accepted':result['accepted'],'checks':len(checks),'bindings':len(bindings),'failed':[k for k,v in checks.items() if not v]}))
