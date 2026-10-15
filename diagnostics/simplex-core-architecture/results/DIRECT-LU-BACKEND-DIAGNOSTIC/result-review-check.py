"""Independent saved-data review; standard library only, no prior auditor imports."""
from pathlib import Path
from fractions import Fraction as F
import hashlib,json,math,struct,subprocess,tomllib,time,os
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
E=Path(__file__).resolve().parent; D=E.parent/'DIRECT-LU-BACKEND-PREPARATION'; C=E.parent/'DIRECT-LU-COST-PREPARATION'
checks={}; bindings={}
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  while b:=f.read(1024*1024):h.update(b)
 return h.hexdigest()
def read(p):
 p=Path(p);bindings[str(p)]=sha(p)
 return json.loads(p.read_text()) if p.suffix=='.json' else tomllib.loads(p.read_text())
def check(name,v):
 checks[name]=bool(v)
 if not v:raise AssertionError(name)
def decode(s):
 assert len(s)==16
 x=struct.unpack('>d',bytes.fromhex(s))[0]; assert math.isfinite(x)
 return F(x)
def vec(v):return [decode(x) for x in v]
def sparse(s):
 n=s['n']; a=[[F(0) for _ in range(n)] for _ in range(n)]
 for j in range(n):
  for k in range(s['colptr'][j]-1,s['colptr'][j+1]-1):a[s['rowval'][k]-1][j]=decode(s['nzval'][k])
 return a
def tr(a):return list(map(list,zip(*a)))
def mv(a,x):return [sum((v*y for v,y in zip(row,x) if v),F(0)) for row in a]
def residual(name,a,b,xt):
 x=vec(xt); b=vec(b); z=[v-w for v,w in zip(mv(a,x),b)]
 norm=max(sum(map(abs,row)) for row in a)
 bound=F(128*len(a),2**52)*max(F(1),norm*max(map(abs,x)),max(map(abs,b)))
 m=max(map(abs,z));return dict(name=name,passed=m<=bound,max_abs=str(m),bound=str(bound),ratio=float(m/bound),residual=list(map(str,z)))
pins=read(D/'probe-launch-pins.json');sealed=read(D/'probe-sealed-pins.json');admit=read(D/'probe-admission.json')
paths=set(pins['files']); tree_counts={}
for tree in pins['trees']:
 root=Path(tree); assert root.is_dir() and not root.is_symlink(); count=0
 for p in root.rglob('*'):
  assert not (p.is_symlink() and (p.is_dir() or not p.exists()))
  if p.is_file():paths.add(str(p));count+=1
 tree_counts[tree]=count
check('launch_inventory_exact_4749',len(paths)==4749 and paths==set(pins['inventory']))
bad=[]
for p in sorted(paths):
 x=pins['inventory'][p]
 if str(Path(p).resolve(strict=True))!=x['resolved'] or sha(p)!=x['sha256']:bad.append(p)
check('all_4749_hashes_and_resolved_targets',not bad)
check('sealed_4747_and_admission_exact_4748',len(sealed['inventory'])==4747 and len(admit['sha256'])==4748 and set(admit['sha256'])==set(sealed['files'])|{str(D/'probe-sealed-pins.json')} and admit['accepted'] and not admit['findings'] and admit['pins_sha256']==sha(D/'probe-sealed-pins.json') and all(sha(p)==s for p,s in admit['sha256'].items()))
check('launch_extends_sealed_exactly',set(pins['inventory'])==set(sealed['inventory'])|{str(D/'probe-sealed-pins.json'),str(D/'probe-admission.json')} and all(pins['inventory'][p]==x for p,x in sealed['inventory'].items()))
for name in ['postcheck','interpretation']:
 obj=read(E/(name+'.json'));check(name+'_ten_and_bindings',obj['all_passed'] and len(obj['checks'])==10 and all(obj['checks'].values()) and all(sha(p)==s for p,s in obj['sha256'].items()))
audit=read(D/'probe-audit.json');check('canonical_twelve_integrity_and_bindings',audit['all_passed'] and len(audit['checks'])==12 and all(audit['checks'].values()) and all(sha(p)==s for p,s in audit['sha256'].items()))
base=read(E.parent/'DIRECT-LU-PREPARATION/baseline.json')['sha256'];check('baseline_514_unchanged',len(base)==514 and all(sha(R/p)==s for p,s in base.items()))
check('tracked_files_unchanged',not subprocess.check_output(['git','diff','--name-only'],cwd=R).strip() and not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=R).strip())
refs=subprocess.check_output(['git','rev-parse','HEAD','master'],cwd=R,text=True).split();check('refs_unchanged',refs==['a892ebd3382473532f36e92c32ad47328a350935','6f68e24e8ddac42b948da8fcc2d636c010751194'])
files=sorted(p.name for p in (D/'probe-run').iterdir());check('eight_portable_raw_files',len(files)==8 and files==sorted(p.name for p in (E/'probe-run').iterdir()) and all(sha(D/'probe-run'/n)==sha(E/'probe-run'/n) for n in files))
for parent in [D,E]:
 for n in files:bindings[str(parent/'probe-run'/n)]=sha(parent/'probe-run'/n)
check('original_cost_false_no_cost2',read(C/'cost1-audit.json')['all_passed'] is False and not list(C.glob('cost2-*')))
cfg=read(D/'config.json')['probe'];inv=read(D/'probe-invocation.json');res=read(D/'probe-reservation.json');proc=read(D/'probe-run/process.json');cur=read(D/'probe-run/current.json')
project=str(R/'.superpowers/direct-lu-markowitz-green-2/candidate')
cmd=['/bin/bash','/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh','--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+project,str(D/'driver.jl'),str(D/'probe-run'),project,str(C/'inputs.toml')]
check('literal_command',all(v['command']==cmd for v in [cfg,inv,res,proc,cur]))
guard=['/usr/bin/python3','-B',str(D/'guard.py'),'run',str(D/'probe-launch-pins.json'),str(D/'probe-run'),'--seconds','39','--deadline',str(inv['monotonic_start']+39),'--']+cmd
check('absolute_deadline_and_reservation',inv['guard_command']==guard and cfg['seconds']==res['max_seconds']==45 and res['one_attempt'] is True and res['phase']=='probe' and inv['reservation_sha256']==sha(D/'probe-reservation.json') and inv['review_sha256']==res['review_sha256']==sha(D/'probe-admission.json') and inv['pins_sha256']==res['pins_sha256']==proc['pins_sha256']==sha(D/'probe-launch-pins.json'))
check('successful_bounded_single_invocation',proc['reason']=='exit0' and proc['returncode']==0 and inv['supervisor']['accepted'] and inv['supervisor']['returncode']==0 and 0<inv['elapsed_seconds']<=45 and not any(inv['supervisor'][k] for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']) and proc['runner']==cur['runner']==inv['supervisor']['guard_identity'] and proc['child']==cur['child'])
rs=[json.loads(s) for s in (D/'probe-run/resources.jsonl').read_text().splitlines()]+[proc['terminal_memory']]
check('resources_six_plus_terminal',len(rs)==7 and min(x['available_kib'] for x in rs)>=6*1024**2 and max(x['swap_used_kib'] for x in rs)<=1024**2)
host=read(E/'post-host.json');oldhost=read(D/'probe-prehost.json');groups=set(host['groups']);check('recorded_206_group_session_closure',len(groups)==206 and not host['matches'] and set(oldhost['groups'])<=groups and all(proc[k][f] in groups for k in ['runner','child'] for f in ['pgid','sid']))
matches=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  st=(p/'stat').read_text(); z=st[st.rindex(')')+2:].split();comm=(p/'comm').read_text().strip(); exe=os.readlink(p/'exe')
  if int(z[2]) in groups or int(z[3]) in groups or comm=='julia' or Path(exe).name=='julia':matches.append(dict(pid=int(p.name),pgid=int(z[2]),sid=int(z[3]),start_ticks=int(z[19]),comm=comm,exe=exe))
 except FileNotFoundError:pass
check('fresh_206_group_session_and_julia_absence',not matches and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==host['boot_id'])
fixture=next(f for f in read(C/'inputs.json')['fixtures'] if f['name']=='sparse96'); tfixture=next(f for f in read(C/'inputs.toml')['fixtures'] if f['name']=='sparse96');check('json_toml_input_tokens_equal',fixture==tfixture)
matrices=[sparse(s) for s in fixture['matrices'][:5]];steps=fixture['steps'][:5];n=fixture['n'];check('fixed_dimension',n==96)
fresh=read(D/'probe-run/fresh.toml');prefix=read(D/'probe-run/prefix.toml');raw=read(D/'probe-run/raw.toml');old=read(C/'cost1-run/window-13-1.toml')
check('raw_counts_inputs_source',raw['completed'] and not raw['fatal'] and raw['inputs_unchanged'] and raw['loaded_path']==project+'/src/JSimplex.jl' and raw['counts']==dict(factorization=3,ftran=13,btran=5,replace=4,refactor=1,snapshot=2))
check('reset_all_sixteen_and_output_preservation',len(prefix['reset'])==16 and all(prefix['reset'].values()) and prefix['ordinary_before_base']==prefix['tail_outputs'][:2] and prefix['fresh_context_retained'])
controls=[fresh['controls_before'],fresh['controls_after'],prefix['controls_before'],prefix['controls_after_refactor'],prefix['controls_after']]
check('controls_five_plus_two_unchanged_zero_irstep',all(c==controls[0] and c['irstep_zero'] and decode(c['tokens'][c['irstep_index']-1])==0 for c in controls) and all(o['factor']['control']==controls[0]['tokens'] for o in [fresh,prefix]))
results=[]
for j,(name,key) in enumerate([('fresh_enter','a'),('fresh_dse','dse'),('fresh_btran','unit')]):results.append(residual(name,tr(matrices[4]) if j==2 else matrices[4],steps[4][key],fresh['outputs'][j]))
for k in range(4):
 for j,(label,key) in enumerate([('enter','a'),('dse','dse'),('btran','unit')]):results.append(residual('prefix'+str(k+1)+'_'+label,tr(matrices[k+1]) if j==2 else matrices[k],steps[k][key],prefix['prefix_outputs'][3*k+j]))
for j,(name,key) in enumerate([('tail_enter','a'),('tail_dse','dse'),('base_dse','dse')]):results.append(residual(name,matrices[4],steps[4][key],prefix['tail_outputs'][j]))
check('all_18_exact_residual_vectors_bounds_and_booleans',results==audit['result']['residuals'])
check('exact_15pass_3fail_reproduction',[r['name'] for r in results if not r['passed']]==['fresh_dse','tail_dse','base_dse'] and fresh['outputs'][1]==prefix['tail_outputs'][1]==prefix['tail_outputs'][2]==old['outputs'][13])
check('factor_fields_identical_except_info',{k:v for k,v in fresh['factor'].items() if k!='info'}=={k:v for k,v in prefix['factor'].items() if k!='info'})
decomps={}
for label,record,xt in [('fresh',fresh,fresh['outputs'][1]),('ordinary',prefix,prefix['tail_outputs'][1]),('base',prefix,prefix['tail_outputs'][2])]:
 f=record['factor'];assert f['n']==96 and f['status']==0 and f['lnz']==234 and f['unz']==248 and f['nzd']==96
 assert sorted(f['p'])==sorted(f['q'])==list(range(1,97));p=[x-1 for x in f['p']];q=[x-1 for x in f['q']]
 assert f['do_recip'] in (0,1);sc=vec(f['Rs']);assert all(x>0 for x in sc)
 if f['do_recip']==0:sc=[1/x for x in sc]
 factors=[]
 for key in ['L','U']:
  s=f[key];assert s['format']==('csr' if key=='L' else 'csc');ptr=s['ptr'];ix=s['indices'];vx=vec(s['values']);assert len(ptr)==97 and ptr[0]==1 and ptr[-1]==len(vx)+1 and len(ix)==len(vx)
  a=[[F(0) for _ in range(n)] for _ in range(n)]
  for i in range(n):
   assert ptr[i]<=ptr[i+1];inds=ix[ptr[i]-1:ptr[i+1]-1];assert inds==sorted(set(inds))
   for k in range(ptr[i]-1,ptr[i+1]-1):
    j=ix[k]-1; assert 0<=j<=i
    if key=='L':a[i][j]=vx[k]
    else:a[j][i]=vx[k]
   assert a[i][i]==1 if key=='L' else a[i][i]!=0
  factors.append(a)
 l,u=factors;product=[[sum((l[i][k]*u[k][j] for k in range(n) if l[i][k] and u[k][j]),F(0)) for j in range(n)] for i in range(n)]
 scaled=[[sc[p[i]]*matrices[4][p[i]][q[j]] for j in range(n)] for i in range(n)]
 delta=[[product[i][j]-scaled[i][j] for j in range(n)] for i in range(n)]
 x=vec(xt);y=[x[j] for j in q];b=vec(steps[4]['dse']);rhs=[sc[i]*b[i] for i in p]
 rep=mv(delta,y);app=[v-w for v,w in zip(mv(product,y),rhs)];orig=[v-w for v,w in zip(mv(scaled,y),rhs)]
 assert orig==[a-b for a,b in zip(app,rep)]
 dec=dict(factor_identity_exact=all(v==0 for row in delta for v in row),factor_identity_max=str(max(abs(v) for row in delta for v in row)),representation_action=list(map(str,rep)),combined_application=list(map(str,app)),scaled_original=list(map(str,orig)))
 expected=audit['result']['decomposition'][label];assert all(expected[k]==v for k,v in dec.items())
 unscaled=[orig[i]/sc[p[i]] for i in range(n)];worst=max(range(n),key=lambda i:abs(unscaled[i]));assert worst==30 and p[worst]==86
 dec['row87_original_units']={k:str(v[worst]/sc[86]) for k,v in [('representation_action',rep),('combined_application',app),('original_residual',orig)]};dec['p']=f['p'];dec['q']=f['q'];dec['do_recip']=f['do_recip'];decomps[label]=dec
 m=fixture['matrices'][4];assert f['native_owned'] and f['native_match'] and [x+1 for x in f['native_colptr']]==m['colptr'] and [x+1 for x in f['native_rowval']]==m['rowval'] and f['native_nzval']==m['nzval']
check('two_snapshot_structure_native_inputs_and_all_three_exact_decompositions',True)
summary=read(E/'interpretation.json')['summary'];terms=decomps['fresh']['row87_original_units']
check('published_row87_exact_terms',terms['representation_action']==summary['unscaled_terms']['representation_action'] and terms['combined_application']==summary['unscaled_terms']['combined_application'] and terms['original_residual']==summary['original_residual'] and summary['permuted_row']==31 and summary['original_row']==87 and all(d['do_recip']==1 for d in decomps.values()))
for p in [Path(__file__),R/'diagnostics/simplex-core-architecture/DIRECT-LU-BACKEND-DIAGNOSTIC.md',R/'docs/superpowers/plans/2026-10-15-direct-lu-reference-backend-diagnostic.md',D/'scaling-contract.md',D/'preparation-review.md',D/'preparation-review.json',E/'stage-review.md',E/'stage-review-check.json',D/'driver.jl',D/'guard.py',D/'supervisor.py',D/'launch.py',E/'interpret.py',E/'postcheck.py',D/'probe-launcher.log',D/'probe-posthost.json',D/'probe-seal-host.json']:
 bindings[str(p)]=sha(p)
out=dict(all_passed=all(checks.values()),checks=checks,scope='Independent standard-library saved-data analysis; no Julia or previous auditor/script execution',summary=dict(launch_entries=len(paths),tree_counts=tree_counts,baseline_count=len(base),elapsed_seconds=inv['elapsed_seconds'],resource_samples=len(rs)-1,min_available_kib=min(x['available_kib'] for x in rs),max_swap_kib=max(x['swap_used_kib'] for x in rs),groups=len(groups),fresh_process_matches=matches,refs=refs,counts=raw['counts']),residuals=results,decompositions=decomps,sha256=bindings)
with (E/'result-review-check.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=out['all_passed'],checks=len(checks),summary=out['summary']),indent=2))
