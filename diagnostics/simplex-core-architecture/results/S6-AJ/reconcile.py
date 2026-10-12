import json,hashlib,subprocess,difflib,collections
from pathlib import Path
ROOT=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl'); OUT=ROOT/'diagnostics/simplex-core-architecture/results/S6-AJ'
def git(*args): return subprocess.check_output(['git',*args],cwd=ROOT)
def sha(b): return hashlib.sha256(b).hexdigest()
def read(p): return (ROOT/p).read_bytes()
base='diagnostics/simplex-core-architecture/'
invpath=base+'results/S6-A/ci-inventory-1.json'; inv=json.loads(read(invpath))
master=git('rev-parse','master').decode().strip(); head=git('rev-parse','HEAD').decode().strip()
repairs={'legacy_primal_direction_price_tests.jl':('W','b9e7cb1'),'legacy_primal_preference_work_tests.jl':('C','a465da5'),'dual_pivot_consistency_tests.jl':('AI','354bb1f'),'native_artificial_row_tests.jl':('G','8516e0d'),'solver_tests.jl':('T','afb37d9'),'bigfloat_integrity_tests.jl':('M','7fea422')}
pins={invpath:sha(read(invpath))}; checks={}; records=[]; loc={}; source={}
for run in inv['records']:
 rows=[]
 for e in run['entries']:
  f=e['file']; old=git('show',f"{run['head']}:{f}"); current=read(f)
  if f not in source:
   source[f]={'current_sha256':sha(current),'master_sha256':sha(git('show',f'{master}:{f}')),'historical_sha256':sha(old)}
   pins[f]=sha(current)
  oldlines=old.decode().splitlines();newlines=current.decode().splitlines()
  ln=e['line']-1; matched=[]
  for a,b,n in difflib.SequenceMatcher(None,oldlines,newlines,autojunk=False).get_matching_blocks():
   if a<=ln<a+n: matched.append(b+ln-a+1)
  if f.endswith('legacy_primal_preference_work_tests.jl') and e['line']==38:
   matched=[i+1 for i,line in enumerate(newlines) if line.strip()=='@test !isnothing(terminal) && terminal.status==NUMERICAL_ERROR']
  assert len(matched)==1,(f,e['line'],matched)
  curline=matched[0]
  assert oldlines[ln]==newlines[curline-1] or (f.endswith('legacy_primal_preference_work_tests.jl') and e['line']==38)
  if Path(f).name=='native_phase_transfer_tests.jl': stage,commit=('AC','3c0af5c') if e['line']==164 else ('AA','74f7835')
  else: stage,commit=repairs.get(Path(f).name,(None,None))
  k=(f,e['line'],e['kind'])
  item={'id':f"{run['run']}:{e['log_line']}",'historical_file':f,'historical_line':e['line'],'kind':e['kind'],'title':e['title'],'current_line':curline,'historical_assertion_start':oldlines[ln],'current_assertion_start':newlines[curline-1],'assertion_start_byte_equal':oldlines[ln]==newlines[curline-1],'inventory_expression':e['details'][0] if e['details'] else None,'repair_stage':stage,'repair_master_commit':git('rev-parse',commit).decode().strip() if commit else None,'coverage':'scoped local test repair; historical cause/platform not proved' if stage else 'unchanged native test; S5-C focused evidence reused; cause unresolved','scalar_scope':'unknown for historical accepted=false phase entries' if f.endswith('native_phase_transfer_tests.jl') else 'see historical inventory and stage report; no new scalar inference'}
  rows.append(item)
  if k not in loc: loc[k]={key:item[key] for key in ('historical_file','historical_line','kind','title','current_line','historical_assertion_start','current_assertion_start','assertion_start_byte_equal','repair_stage','coverage')};loc[k]['runs']={}
  loc[k]['runs'][str(run['run'])]=loc[k]['runs'].get(str(run['run']),0)+1
 c=collections.Counter(e['kind'] for e in rows)
 assert c['Test Failed']==run['counts']['failed'] and c['Error During Test']==run['counts']['errored']
 records.append({'run':run['run'],'head':run['head'],'counts':run['counts'],'rows':rows})
checks['distinct_event_ids']=len({e['id'] for r in records for e in r['rows']})==sum(len(r['rows']) for r in records)==399
checks['run_totals_separate']=[(r['counts']['failed'],r['counts']['errored']) for r in records]==[(197,1),(200,1)]
checks['all_24_locations_mapped']=len(loc)==24
checks['23_byte_equal_starts_plus_explicit_C_guard']=sum(x['assertion_start_byte_equal'] for x in loc.values())==23
checks['current_tests_equal_master']=all(x['current_sha256']==x['master_sha256'] for x in source.values())
checks['unchanged_native_cleanup_test']=source['test/primal_perturbation_integration_tests.jl']['current_sha256']==source['test/primal_perturbation_integration_tests.jl']['historical_sha256']
# Bind each repair to its present master file, or the unchanged AA testset inside AC's later file.
repair_bindings={}
for k,(stage,commit) in repairs.items():
 f='test/'+k; repair_bindings[stage]=sha(read(f))==sha(git('show',commit+':'+f))
f='test/native_phase_transfer_tests.jl';repair_bindings['AC']=sha(read(f))==sha(git('show','3c0af5c:'+f))
def block(text,title):
 start=text.index('@testset "'+title+'"');end=text.find('\n@testset ',start+1);return text[start:end if end!=-1 else len(text)]
title='Reliable artificial exchanges need no reconstruction recovery'
repair_bindings['AA']=block(read(f).decode(),title)==block(git('show','74f7835:'+f).decode(),title)
checks['repair_commits_bind_current_files_or_AA_block']=all(repair_bindings.values())
for stage in ('C','G','M','T','W','AA','AC','AI'):
 p=base+'results/S6-'+stage+'/master-1-audit.json'; d=json.loads(read(p));pins[p]=sha(read(p));checks['saved_'+stage+'_master_checks']=all(d['checks'].values())
 p=base+'results/S6-'+stage+'/master-1-run.log'; pins[p]=sha(read(p))
checks['raw_inventory_hashes']=all(sha((Path(inv['raw_location'])/p).read_bytes())==h for p,h in inv['raw_manifest'].items())
for p in git('ls-files','src','test','.github/workflows').decode().splitlines():
 pins[p]=sha(read(p)); assert read(p)==git('show',f'{master}:{p}'),p
checks['all_current_source_tests_CI_equal_master']=True
for p in (base+'S6-FAILURES.md',base+'S5-COPIES.md',base+'results/S5-C/focused-1-reference.toml',base+'results/S5-C/focused-1-run.log'):
 pins[p]=sha(read(p))
user={}
for root in (ROOT,Path('/home/jspitz/JSimplex.jl')):
 for p in ('Manifest.toml','LocalPreferences.toml','.vscode/settings.json'):
  if (root/p).exists(): user[str(root/p)]=sha((root/p).read_bytes())
checks['main_user_hashes_preserved']=all(user['/home/jspitz/JSimplex.jl/'+p]==h for p,h in json.load(open('/tmp/jsimplex-main-preserved.json')).items())
assert all(checks.values()),checks
OUT.mkdir(exist_ok=True)
for name,obj in [('coverage.json',{'head':head,'master':master,'checks':checks,'repair_bindings':repair_bindings,'source':source,'locations':list(loc.values()),'runs':records,'scope':'Offline reuse of accepted inventory. No original parser or numerical driver executed; no historical CI success or cause asserted.'}),('input-hashes.json',pins),('user-hashes.json',user)]:
 with (OUT/name).open('x') as out: out.write(json.dumps(obj,indent=2)+'\n')
(OUT/'reconcile.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps({'checks':len(checks),'locations':len(loc),'entries':399,'hashes':len(pins),'repair_bindings':repair_bindings}))
for x in loc.values(): print(x['historical_file'],x['historical_line'],'->',x['current_line'],x['runs'])
