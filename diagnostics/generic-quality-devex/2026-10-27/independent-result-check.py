from pathlib import Path
import hashlib,json,tomllib,re,statistics,math,itertools,subprocess,os,datetime,sys
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-devex/2026-10-27');M=Path('/home/jspitz/JSimplex.jl');Q=D/'RED-run'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(Path(p).read_text())
def need(v,msg):
 if not v:raise RuntimeError(msg)
def git(*a):return subprocess.check_output(['git','-C',str(M),*a],text=True,env=dict(os.environ,GIT_OPTIONAL_LOCKS='0')).strip()
base='7e306e24f064a8aa214bc88379e059def77661ab'
need(all(git('rev-parse',r)==base for r in ['HEAD','master','origin/master']),'source refs')
need(not git('diff','--name-only','HEAD','--','src','test','Project.toml'),'source dirty')
for root in [D,Q]:
 pins=load(root/'pins.json')
 for p,v in pins['inventory'].items():need(str(Path(p).resolve(strict=True))==v['resolved'] and sha(p)==v['sha256'],'inventory '+p)
 for t in pins['trees']:need({str(p) for p in Path(t).rglob('*') if p.is_file()}=={p for p in pins['inventory'] if Path(p).is_relative_to(t)},'tree '+t)
 protected=load(root/'protected-before.json')
 for p,v in {**protected['files'],**protected['indexes']}.items():need(sha(p)==v,'protected '+p)
 for k in ['JULIA_PROJECT','JULIA_LOAD_PATH','JULIA_BINDIR','JULIA_CPU_TARGET','JULIA_DEPOT_PATH','LD_PRELOAD','LD_LIBRARY_PATH','LD_AUDIT','BASH_ENV','ENV','PYTHONPATH','PYTHONHOME']:
  need(not os.environ.get(k),'override '+k)
 need(load(root/'environment.json')['inherited']=={k:os.environ[k] for k in ['JULIA_NUM_THREADS','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'] if k in os.environ},'environment')
basefiles=load(D/'baseline-tree.json')
for rel,h in basefiles.items():
 need(sha(D/'baseline'/rel)==h,'baseline '+rel)
 need(sha(M/rel)==h,'master baseline '+rel)
for root in ['src','test']:
 need({str(p.relative_to(M)) for p in (M/root).rglob('*') if p.is_file()}=={p for p in basefiles if p.startswith(root+'/')},'master membership')
redfiles={str(p.relative_to(D/'RED')):sha(p) for p in (D/'RED').rglob('*') if p.is_file()}
need(set(redfiles)==set(basefiles)|{'test/generic_quality_devex_tests.jl'},'RED members')
need({p for p in basefiles if redfiles[p]!=basefiles[p]}=={'test/runtests.jl'},'RED differences')
old=(D/'baseline/test/runtests.jl').read_text();new=(D/'RED/test/runtests.jl').read_text()
line='include("generic_quality_devex_tests.jl")'
need(new.count(line)==1 and new.replace('    '+line+'\n','')==old,'runtests inclusion only')
need(sha(D/'RED/test/generic_quality_devex_tests.jl')==sha(D/'new-test.jl'),'RED test identity')
ref=(D/'reference.jl').read_text();cand=(D/'candidate.jl').read_text();changes=load(D/'changes.json')
blocks=re.findall(r'^(?:@inline )?function .*?^end\n',ref,re.M|re.S)
need(len(blocks)==9,'reference blocks')
for b in blocks:need(sum(b in p.read_text() for p in (M/'src').glob('*.jl'))==1,'reference source block')
helper_block=ref[ref.index('_primal_devex_candidate_weight(coefficient::T'):ref.index('function _primal_update_devex!')]
need(helper_block in (M/'src/primal_simplex.jl').read_text(),'all helper reference overloads')
header=ref[:ref.index('function _dual_direction')]
for local in ['_quality_components!','_accumulate_quality_term!','_wide_solve_quality!','solve_quality!','_primal_devex_candidate_weight','_primal_update_devex!']:
 need(re.search(r'(?<![\w])'+re.escape(local)+r'(?![\w!])',header) is None,'local dispatch '+local)
want=ref.replace('module SavingsReference','module SavingsCandidate',1)
for k in ['A1','A2','C']:
 c=changes[k];need(c['old'] in (M/'src'/c['file']).read_text(),'old source '+k);need(want.count(c['old'])==1,'unique replace');want=want.replace(c['old'],c['new'],1)
extra=changes['B']['new'].removesuffix(changes['B']['old']);want=want.replace('function _wide_solve_quality!',extra+'function _wide_solve_quality!',1)
need(want==cand,'declared candidate')
for k in ['A1','A2']:need(changes[k]['new']==changes[k]['old'].replace('abs(','_primal_direction_magnitude('),'A only abs')
need('_primal_direction_magnitude(value::BigFloat) = signbit(value) ? -value : value' in (M/'src/primal_simplex.jl').read_text(),'magnitude helper')
fixtures=(D/'fixtures.jl').read_text();test=(D/'new-test.jl').read_text()
prefix='module GenericQualityDevexTests\nusing Test,JSimplex,SparseArrays,LinearAlgebra\n'+ref+'const SavingsCandidate=JSimplex\n'+fixtures
need(test.startswith(prefix),'test frozen reference/fixtures')
need('all(new["bytes"]<0.97old["bytes"]&&new["events"]<0.97old["events"] for (old,new) in pairs)' in test,'gate bytes and events')
need('for k in 1:3' in test[len(prefix):] and 'for k in 1:9' not in test[len(prefix):],'fixed three pairs')
need('Test.push_testset' not in test and 'record(' not in test,'ordinary tests')
results=tomllib.loads((D/'output/results.toml').read_text());rows=results['cells'];summary=load(D/'summary.json');audit=load(D/'audit.json')
scopes=['direction','row','quality','quality_transposed','devex_shared','devex_solved']
contexts=[('BF%d_RoundingMode{:%s}()'%(bits,mode),'BigFloat') for bits,mode in itertools.product([64,128,256],['Nearest','Down','Up','ToZero','FromZero'])]+[(t,t) for t in ['Float32','Float64','Rational{BigInt}','Rational{Int64}']]
expected=[]
for ctx,t in contexts:
 for n,scope,density,pattern in itertools.product([32,128],scopes if t in ['BigFloat','Float32','Float64'] else scopes[2:],['sparse','dense'],['positive','negative','mixed'] if t=='BigFloat' else ['mixed']):expected.append((ctx,t,n,scope,density,pattern))
need(len(rows)==len(expected)==1160,'cell count');need(len(summary['cases'])==1160,'summary count')
fields=['seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds']
def valid(c):
 need(all(type(c[k]) in [float,int] and math.isfinite(c[k]) and c[k]>=0 for k in fields),'cost finite')
 need(type(c['bytes']) is int and type(c['events']) is int,'integer allocations')
records=[];ngc=0;controls=[];gates=[];byte_noise=[]
for cell,key,reported in zip(rows,expected,summary['cases']):
 need(tuple(cell[k] for k in ['context','type','n','scope','density','pattern'])==key,'ordered matrix')
 need(cell['id']=='/'.join(map(str,[key[0],key[2],*key[3:]])),'id')
 w=cell['windows'];need(len(w)==18,'windows');ratios=[];paired=[]
 for p in range(1,10):
  seq=w[2*p-2:2*p];need([a['arm'] for a in seq]==(['original','candidate'] if p%2 else ['candidate','original']),'alternation')
  for a in seq:
   valid(a);need(a['pair']==p and a['compile_seconds']==a['recompile_seconds']==0,'compilezero');need(type(a['sink']) is int,'typed sink');ngc+=a['gc_seconds']>0
  need(seq[0]['sink']==seq[1]['sink'],'equal sinks')
  arms={a['arm']:a for a in seq};o,c=arms['original'],arms['candidate'];need(o['seconds']>0,'nonzero original')
  ratios.append(c['seconds']/o['seconds']);paired.append((o,c))
 out={k:cell[k] for k in ['context','type','n','scope','density','pattern']}
 med=statistics.median(ratios);out.update(paired_ratio=med,ratio_MAD=statistics.median(abs(r-med) for r in ratios),ratio_min=min(ratios),ratio_max=max(ratios))
 for arm in ['original','candidate']:out[arm]={k:statistics.median(v[k] for v in w if v['arm']==arm) for k in ['seconds','bytes','events']}
 out['all_pairs_lower_bytes']=all(c['bytes']<o['bytes'] for o,c in paired);out['all_pairs_lower_events']=all(c['events']<o['events'] for o,c in paired)
 need(out==reported,'summary raw recomputation '+cell['id']);records.append(out)
 if key[1]!='BigFloat':
  need(all(o['events']==c['events'] for o,c in paired),'control event equality');controls.append(out)
  if out['original']['bytes']!=out['candidate']['bytes']:byte_noise.append(cell['id']);need(key[1].startswith('Rational'),'nonrational byte variation')
 if key[0]=='BF128_RoundingMode{:Nearest}()' and key[2]==32 and key[4:] == ('dense','positive'):
  need(all(c['bytes']<.97*o['bytes'] and c['events']<.97*o['events'] for o,c in paired),'all nine gate support')
  gates.append(dict(scope=key[3],pairs=9,max_byte_ratio=max(c['bytes']/o['bytes'] for o,c in paired),max_event_ratio=max(c['events']/o['events'] for o,c in paired)))
need(all(v['candidate']['bytes']==v['original']['bytes'] and v['candidate']['events']==v['original']['events'] for v in records if v['type']=='BigFloat' and v['scope']=='row' and not v['all_pairs_lower_bytes']),'row unchanged cases')
need(ngc==490 and len(controls)==80 and len(byte_noise)==15 and len(gates)==6,'totals')
need(summary['measured_windows']==20880 and summary['GC_affected_windows']==ngc,'summary aggregate')
prep=results['preparation'];need(len(prep)==1198,'prep length')
phaseentries=[v for v in prep if 'phase' in v]
need([(v['context'],v['phase']) for v in phaseentries]==[(ctx,phase) for ctx,t in contexts for phase in ['correctness_and_snapshots','context_GC']],'prep contexts')
for v in phaseentries:valid(v)
prepcells=[v for v in prep if 'phase' not in v];need([v['cell'] for v in prepcells]==[v['id'] for v in rows],'prep ids')
for v in prepcells:
 valid(v['fixture']);valid(v['validation_and_snapshots'])
 for k,n in [('cold',2),('warm',6),('resets',18)]:
  need(len(v[k])==n,'prep count')
  for r in v[k]:valid(r)
log=(D/'output/run.log').read_text();need(re.search(r'^Quality and Devex complete comparison\s*\|\s*33807\s+33807\s',log,re.M),'ordinary pass')
need('QUALITY_DEVEX_COMPARISON_COMPLETE cells=1160' in log and 'Test Failed' not in log and 'Error During Test' not in log,'completion')
need(re.findall(r'^CONTEXT (.*)$',log,re.M)==[x for x,t in contexts],'logged contexts')
p=load(D/'output/process.json');sup=load(D/'supervisor.json');done=load(D/'completed.json');con=load(D/'contract.json');reservation=load(D/'reservation.json')
need(p['command']==con['command'] and p['returncode']==0 and p['reason']=='exit0' and p['pins_unchanged'],'process success')
need(p['pins_sha256']==sha(D/'pins.json')==sha(D/'output/pins.json'),'run pins')
need(sup['accepted'] and sup['returncode']==0 and not sup['soft_timeout'] and not sup['hard_timeout'] and 'cleanup_error' not in sup,'supervisor')
need(done['accepted'] and done['elapsed_shared_seconds']<=600 and done['pins_unchanged'],'completion time')
need(sup['guard_identity']==p['runner'],'supervisor owner')
gate=load(D/'output/gate.json');cur=load(D/'output/current.json');permit=load(D/'output/permit.json')
need(gate['identity']==p['child']==cur['child'] and gate['parent']==p['runner']==cur['runner'],'gate identity')
need(gate['command']==permit['command']==cur['command']==con['command'] and gate['parent_death_signal']==9,'gate command')
need(gate['current_sha256']==sha(D/'output/current.json')==permit['current_sha256'] and gate['permit_sha256']==sha(D/'output/permit.json'),'gate hash')
resources=[json.loads(x) for x in (D/'output/resources.jsonl').read_text().splitlines()]
need(resources and all(v['available_kib']>=6*1024**2 and v['swap_used_kib']<=1024**2 for v in resources+[p['terminal_memory']]),'resources')
for n,v in audit['bindings'].items():need(sha(n)==v,'audit binding')
need(all(audit[k]==v for k,v in dict(assertions=33807,cells=1160,windows=20880,GC_affected_windows=490,elapsed_seconds=done['elapsed_shared_seconds']).items()),'audit stats')
red=load(Q/'contract.json');need(red['arm']=='RED' and red['files']==['generic_quality_devex_tests.jl'] and red['attempts']==1 and red['expected_exit']==1 and red['expected_failures']==6 and red['shared_limit_seconds']==1800 and red['guard_limit_seconds']==1792,'RED contract')
lineno=next(i for i,s in enumerate(test.splitlines(),1) if '# RED whole-call cost gate' in s)
need(red['expected_failure_locations']==[[str(D/'RED/test/generic_quality_devex_tests.jl'),lineno]]*6,'failure locations')
need('--project='+str(D/'RED') in red['command'] and red['command'][-1]==str(Q/'tests.jl'),'RED command')
need(not (Q/'output').exists() and not (Q/'reservation.json').exists(),'RED not started')
for guardpath in (D/'guard').glob('*.py'):need(sha(guardpath)==sha(Q/'guard'/guardpath.name),'same reviewed guard')
seed=load(Q/'host-seed.json');groups=set(seed['groups']);need(set(load(D/'host-seed.json')['groups'])<=groups and len(groups)>=579,'historical coverage')
need(all(p[k][v] in groups for k in ['runner','child'] for v in ['pgid','sid']),'latest group coverage')
processes=[]
for proc in Path('/proc').glob('[0-9]*'):
 try:
  st=(proc/'stat').read_text().rsplit(')',1)[1].split();argv=[v.decode(errors='replace') for v in (proc/'cmdline').read_bytes().split(b'\0') if v];comm=(proc/'comm').read_text().strip();pgid,sid=int(st[2]),int(st[3])
  need(pgid not in groups and sid not in groups,'historical process group active')
  need(not any(Path(v).name.lower().startswith('julia') for v in [comm]+argv[:1]),'live Julia')
  processes.append(dict(pid=int(proc.name),pgid=pgid,sid=sid,start_ticks=int(st[19]),command=argv))
 except (FileNotFoundError,ProcessLookupError):pass
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();need(boot==seed['boot_id'],'boot')
mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()};need(mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2,'fresh RAM')
host=dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),boot_id=boot,groups=sorted(groups),processes=processes,no_Julia=True,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree'])
aggregates={}
for scope in scopes:
 r=[v for v in records if v['type']=='BigFloat' and v['scope']==scope]
 aggregates[scope]=dict(cells=len(r),median_paired_ratio=statistics.median(v['paired_ratio'] for v in r),cell_ratio_range=[min(v['paired_ratio'] for v in r),max(v['paired_ratio'] for v in r)],all_pairs_lower_bytes_events=sum(v['all_pairs_lower_bytes'] and v['all_pairs_lower_events'] for v in r),bytes_saved_percent_range=[min(100*(1-v['candidate']['bytes']/v['original']['bytes']) for v in r),max(100*(1-v['candidate']['bytes']/v['original']['bytes']) for v in r)])
regressions=[v for v in records if v['type']=='BigFloat' and v['scope'].startswith('quality') and v['paired_ratio']>1]
need(len(regressions)==3 and all(v['pattern']=='negative' for v in regressions) and sum(v['density']=='dense' and v['n']==128 for v in regressions)==2,'B regressions')
need(all(v['paired_ratio']<1 and v['all_pairs_lower_bytes'] and v['all_pairs_lower_events'] for v in records if v['type']=='BigFloat' and v['scope'].startswith('devex')),'C evidence')
result=dict(accepted=True,findings=[],variants={k:'accepted for local whole-function work/allocation reduction; no universal time claim' for k in ['A','B','C']},assertions=33807,cells=1160,windows=20880,GC_affected_windows=490,elapsed_seconds=done['elapsed_shared_seconds'],native_exact_controls=80,rational_medianbyte_variations=15,gates=gates,aggregates=aggregates,B_timing_regressions=regressions,inventory_counts={str(r):len(load(r/'pins.json')['inventory']) for r in [D,Q]},RED_changed_files=['test/runtests.jl','test/generic_quality_devex_tests.jl'])
Path('/tmp/quality_devex_independent_recomputed.json').write_text(json.dumps(result,indent=2)+'\n')
Path('/tmp/quality_devex_independent_host.json').write_text(json.dumps(host,indent=2)+'\n')
print(json.dumps(result,indent=2))
