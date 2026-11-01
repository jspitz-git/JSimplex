from pathlib import Path
import sys,json,hashlib,re,importlib.util
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;W=D.parents[2];checks=[];cache={}
def read(p):return json.loads(p.read_text())
def sha(p):
 p=str(p)
 if p not in cache:
  with open(p,'rb') as f:cache[p]=hashlib.file_digest(f,'sha256').hexdigest()
 return cache[p]
def require(v,m):
 checks.append(dict(check=m,passed=bool(v)))
 if not v:raise ValueError(m)
maps=[read(D/n) for n in ('loader-before-map.json','production-before-map.json','source-review-before-map.json','handoff-tests-before-map.json','boundary-before-map.json','task4-before-map.json','cleanup-fixture-before-map.json')]
def historical(n,h):
 p=Path(n)
 if p.is_file() and sha(p)==h:return p
 for mapping in maps:
  v=mapping.get(n)
  if v and v['sha256']==h and sha(v['preserved'])==h:return Path(v['preserved'])
 raise ValueError('missing historical binding '+n)
def summaries(log,allowed_error=None):
 details=[];lines=log.splitlines()
 for i,line in enumerate(lines[:-1]):
  if not line.startswith('Test Summary:') or '|' not in line:continue
  labels=line.split('|',1)[1].split();body=lines[i+1];require('|' in body,'summary row follows header')
  name,raw=body.rsplit('|',1);name=name.strip();values=raw.split()
  require(len(labels)==len(values) and labels[-1]=='Time','ordinary summary schema')
  counts={k:int(v) for k,v in zip(labels[:-1],values[:-1])}
  require(counts.get('Fail',0)==0 and counts.get('Error',0)==(1 if name==allowed_error else 0),'ordinary section expected pass/setup error '+name)
  require(counts['Total']==sum(counts.get(k,0) for k in ('Pass','Fail','Error','Broken')),'ordinary total '+name)
  details.append(dict(name=name,counts=counts,time=values[-1]))
 require(details,'ordinary summary evidence exists');return details
s=importlib.util.spec_from_file_location('task5postdefs',D/'public-run.py');L=importlib.util.module_from_spec(s);s.loader.exec_module(L)
require(L.G.pins_match(read(D/'public-green-pins.json')),'all590 actual completion pins unchanged')
for manifest in [D/'before-loader-review/red-pins.json',D/'red-pins.json',D/'before-source-review/diagnostics/dual-step-experiment/task5/green-pins.json',D/'boundary-red-pins.json',D/'green-pins.json',D/'green2-pins.json']:
 for n,v in read(manifest)['inventory'].items():require(sha(historical(n,v['sha256']))==v['sha256'],'historical '+str(manifest.relative_to(D))+': '+n)
require(read(D/'before-loader-review/admission.json')['accepted'] is False,'original loader alias rejection preserved')
require(read(D/'before-source-review/admission.json')['accepted'] is False,'original source review rejection preserved')
runs={};logs={}
for stage,accepted,exitcode in [('red',True,1),('boundary-red',True,1),('green',False,1),('green2',False,1),('public-green',True,0)]:
 out=D/(stage+'-run');r=read(out/'result.json');pr=read(out/'guard/process.json');cfg=read(D/(stage+'-contract.json'));log=(out/'guard/run.log').read_text();logs[stage]=log
 require(r['accepted'] is accepted and r['exit']==pr['returncode']==exitcode and pr['reason']=='exit'+str(exitcode),stage+' exact actual result')
 require(r['pins_unchanged'] and pr['pins_unchanged'] and r['elapsed_seconds']<=r['limit_seconds']==1800,stage+' unchanged pins and common budget')
 require(pr['command']==cfg['command'],stage+' actual exact command')
 a=read(D/(stage+'-admission.json'));require(a['accepted'] is True and a['pins_sha256']==sha(D/(stage+'-pins.json')),stage+' exact independent admission')
 samples=[json.loads(x) for x in (out/'guard/resources.jsonl').read_text().splitlines()]
 require(samples and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in samples),stage+' sampled memory limits')
 require(pr['terminal_memory']['available_kib']>=6*1024**2 and pr['terminal_memory']['swap_used_kib']<=1024**2,stage+' terminal memory limits')
 h=read(out/'terminal-host.json');require(h['no_julia'] and not h['conflicts'],stage+' full process groupsANDsessions closed')
 runs[stage]=dict(accepted_whole_process=accepted,elapsed_seconds=r['elapsed_seconds'],samples=len(samples),min_available_kib=min(x['available_kib'] for x in samples),max_swap_kib=max(x['swap_used_kib'] for x in samples),child_maxrss_kib=pr['child_maxrss_kib'])
require('4 passed, 5 failed, 0 errored, 0 broken' in logs['red'],'initial RED4Pass5Fail')
require('4 passed, 2 failed, 0 errored, 0 broken' in logs['boundary-red'] and 'FieldError(Nothing, :progress)' in logs['boundary-red'] and 'actual.iterations == 17' in logs['boundary-red'],'boundary RED actual two defects')
require(logs['green'].count('Test Failed at')==1 and 'r.entries == 0 && r.accepted_pivots == 0' in logs['green'] and 'Error During Test' not in logs['green'],'original single invalid cleanup fixture premise')
require('5 passed, 1 failed, 0 errored, 0 broken' in logs['green'],'original cleanup failure5Pass1Fail')
main=logs['green2'];public=logs['public-green'];error_name='Phase-I refactorization reports the original MAX objective'
require(main.count('Error During Test at')==1 and 'UndefVarError: `RecordingSimplexLogger`' in main and 'Test Failed at' not in main,'sole main GREEN2 missing shared helper error')
require('DUAL_ENGINE_TASK5_COMPLETED' not in main,'failed original main never relabeled complete')
md=summaries(main,error_name);require(md[-1]['name']==error_name and md[-1]['counts']==dict(Error=1,Total=1),'main ends before missing logger assertions')
require('DUAL_ENGINE_TASK5_PUBLIC_COMPLETED' in public and 'Test Failed' not in public and 'Error During Test' not in public,'complete public file ordinary PASS marker')
pd=summaries(public);first='Floating solves use reversible scaling by default';ix=next(i for i,x in enumerate(md) if x['name']==first)
prior_public=md[ix:-1]
require(len(prior_public)==13 and len(pd)>=len(prior_public),'all13 earlier public roots retained')
require(all(x['name']==y['name'] and x['counts']==y['counts'] for x,y in zip(prior_public,pd)),'repeated public prefix agrees exactly')
require(error_name in {x['name'] for x in pd} and pd[len(prior_public)]['name']==error_name,'previously blocked public suffix actually executed')
qualified=md[:ix]+pd
require(len({x['name'] for x in qualified})==len(qualified),'canonical source testsets unique, public prefix deduplicated')
testsets={x['name']:x['counts'].get('Pass',0) for x in qualified};passed=sum(testsets.values());skipped=sum(x['counts'].get('Broken',0) for x in qualified)
old=read(D.parent/'task4/postcheck.json')['runs']['green2']['testsets'];require(sum(old.values())==709 and all(testsets.get(n)==v for n,v in old.items()),'complete unchanged709 prior assertions')
require(sum(v for n,v in testsets.items() if n.startswith('Task5 '))==146,'all146 new Task5 assertions passed')
allowed_skips={'NBST actual FTZ guard and restoration','NBST2 actual FTZ transitions never reuse a local mode decision'}
require(all(x['counts'].get('Broken',0)==0 or (x['name'] in allowed_skips and x['counts']['Broken']==1) for x in qualified),'only preserved source FTZ skips allowed')
if skipped:require('NBST_FTZ_ACTUAL_SUPPORTED false' in main and 'NBST2_FTZ_ACTUAL_SUPPORTED false' in main,'actual unsupported FTZ flags explain skips')
activation=[];corpus=[]
for kind,line in re.findall(r'^TASK5_(ACTIVATION|CORPUS) (.+)$',main,re.M):
 item=dict(token.split('=',1) for token in line.split());(activation if kind=='ACTIVATION' else corpus).append(item)
require(len(activation)==4 and {(int(x['n']),x['dense']) for x in activation}=={(n,b) for n in (16,64) for b in ('false','true')},'four frozen activation inputs retained')
require(all(x['status']=='OPTIMAL' and int(x['entries'])==1 and int(x['commits'])>0 and all(int(x[k])==0 for k in ('fallbacks','original_retries','original_cleanups','original_recoveries')) for x in activation),'real normal commits and zero whole-phase/outer fallback')
require(sum(int(x['sparse_prices']) for x in activation)>0 and sum(int(x['dense_prices']) for x in activation)>0,'actual sparse and dense pricing')
names=('afiro.mps','netlib/adlittle.mps','netlib/sc50a.mps','generated/degenerate-box.mps','generated/phase-one.mps','generated/scaled-diagonal.mps')
require(len(corpus)==12 and {(x['name'],x['presolve']) for x in corpus}=={(n,b) for n in names for b in ('false','true')},'all12 frozen MPS configurations')
require(all(x['reference']==x['candidate']=='OPTIMAL' and int(x['entries'])<=1 and int(x['fallbacks'])<=1 for x in corpus),'all12 actual original-certified optimal outcomes')
coupled=re.findall(r'^TASK5_COUPLED_CLEANUP (.+)$',main,re.M);require(len(coupled)==1,'original coupled helper retained')
coupled=dict(token.split('=',1) for token in coupled[0].split());require(coupled['status']=='OPTIMAL' and int(coupled['entries'])==1 and int(coupled['commits'])>0 and int(coupled['cleanups'])+int(coupled['retries'])>0,'original coupled cleanup truthful activation')
source=Path(read(D/'logger-source.json')['source']);raw=source.read_bytes();prefix=(D/'recording-logger-helpers.jl').read_bytes()
require(raw[:raw.index(b'function test_workspace_type(')]==prefix and b'@testset' not in prefix and b'@test ' not in prefix,'exact original definitions-only logger helper')
require((W/'experimental/dual_engine/test/driver_boundary_tests.jl').read_text()==''.join((W/'experimental/dual_engine/test/task5_boundary_red.jl').read_text().splitlines(keepends=True)[4:]),'new boundary ordinary checks exact frozen RED body')
require((D/'project/src').is_symlink() and (D/'project/src').resolve(strict=True)==(W/'src').resolve(strict=True),'strict staged source alias')
require(L.H.H.git(W,'diff','--name-only','--','src').splitlines()==['src/dual_simplex.jl','src/solver.jl'],'only planned two production files changed')
for n in ('solver.jl','dual_simplex.jl'):require(sha(D/'source-baseline'/n)==sha(Path('/home/jspitz/JSimplex.jl/src')/n),'original baseline/master unchanged '+n)
require(not L.H.H.git(W,'diff','--name-only','--','test','Project.toml','Manifest.toml','.github','diagnostics/dual-step-experiment/task1','diagnostics/dual-step-experiment/task2','diagnostics/dual-step-experiment/task3','diagnostics/dual-step-experiment/task4','docs/superpowers/plans/2026-10-31-experimental-dual-engine.md','docs/superpowers/specs/2026-10-31-experimental-dual-engine-design.md'),'old tests/env/CI/evidence and plan/design frozen')
h=L.host();require(h['no_julia'] and not h['conflicts'],'fresh refs/fullgroupsANDsessions/noJulia')
with (D/'postcheck-host.json').open('x') as f:json.dump(h,f,indent=2)
qualification=dict(accepted=True,mode='explicit composite of passing GREEN2 main/core/sixfiles plus independently admitted complete public file; original GREEN2 remains failed',assertions=passed,skipped=skipped,testsets=testsets,testset_details=qualified,activations=activation,corpus=corpus,coupled_cleanup=coupled,public_repeated_passes=sum(x['counts'].get('Pass',0) for x in prior_public),main_passing_assertions=sum(x['counts'].get('Pass',0) for x in md),public_assertions=sum(x['counts'].get('Pass',0) for x in pd))
with (D/'postcheck.json').open('x') as f:json.dump(dict(accepted=True,checks=checks,runs=runs,qualification=qualification,pins_sha256=sha(D/'public-green-pins.json'),scope='new offline composite evidence only; no Julia/oldauditor rerun/retroactive pins'),f,indent=2)
print(json.dumps(dict(accepted=True,checks=len(checks),qualified_assertions=passed,skipped=skipped,repeated_public_passes=qualification['public_repeated_passes'],source_testsets=len(qualified))))
