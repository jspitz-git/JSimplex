"""Fresh exact-stage admission inspection; no Julia or runtime-control entrypoints."""
from pathlib import Path
import hashlib,json,re,sys,time,tomllib
H=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-HARNESS')
D=H.with_name('DIRECT-BG-BLOCKED-UPDATE-RED');R=H.parents[3];C=R/'diagnostics/direct-bg-blocked-update/reproduce'
sys.path.insert(0,str(H))
import control as c
checks={}
def ck(k,v):
 checks[k]=bool(v)
 if not v:raise RuntimeError(k)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def save(p,v):
 with Path(p).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
run=H/'runs/red300';sp=run/'sealed.json';s=rd(sp);cfg=c.config('red300')
ck('exact_config',s['config']==rd(run/'config.json')==cfg and cfg['seconds']==300 and cfg['expected_exit']==1)
ck('phase',s['phase']=='red300')
ck('fixed_refs',s['head']=='6900c4473a39411b074109fb6362fd8753ca10d0' and s['master']=='26e2291745999f485a74f643298ca997d65c7205')
ck('no_launch_artifacts',set(p.name for p in run.iterdir())=={'sealed.json','config.json','host.json'} and set(p.name for p in (H/'outers/red300').iterdir())=={'outer-ready.json'})
env=rd(H/'environment.json');outer_env={k.decode():v.decode() for item in Path('/proc/163746/environ').read_bytes().split(b'\0') if item for k,v in [item.split(b'=',1)]};ck('waiting_outer_loading_environment',{k:outer_env.get(k) for k in env}==env)
c.validate_sources();ck('source_runtime_stages_fresh',True)
c.verify_seal(cfg,s);ck('canonical_sealed_membership_inventory',True)
ck('unique_sorted_sealed_files',s['files']==sorted(set(s['files'])) and len(s['files'])==1880)
for n,v in s['inventory'].items():
 ck('sealed_'+n,str(Path(n).resolve(strict=True))==v['resolved'] and sha(n)==v['sha256'])
ck('explicit_file_membership',set(s['files'])==set(s['inventory']))
ck('tracked_clean',not c.git('diff','--name-only') and not c.git('diff','--cached','--name-only'))
i=c.verify_outer('red300',s,live=True);ck('waiting_outer_identity',i['pid']==i['pgid']==i['sid']==163746 and i['start_ticks']==12981792)
ck('outer_wait_not_expired',time.time()-rd(H/'outers/red300/outer-ready.json')['ready_time']<1100)
ck('outer_not_old_group',i['pgid'] not in s['groups'])
h=c.full_host(s['groups']);m=c.guard.memory()
ck('fresh_full_host',c.host_safe(h) and all(h[k]==s[k] for k in ['head','master','boot_id']))
ck('all_268_old_groups_sessions',len(s['groups'])==268 and set(s['groups'])<=set(h['groups']))
ck('available_RAM_swap',m['available_kib']>=6*1024**2 and m['swap_used_kib']<=1024**2)
# Independently reverse the declared substitutions and enumerate every original site.
sites=rd(H/'assertion-sites.json');tr=rd(H/'test-transform.json')
ck('160_site_universe',set(sites)=={f'{p}{k:03d}' for p,n in [('P',94),('N',26),('L',40)] for k in range(1,n+1)})
for name,prefix in [('panel-tests.jl','P'),('numerical-tests.jl','N'),('lifecycle-tests.jl','L')]:
 original=(C/name).read_text();clone=(H/name).read_text();transform=tr[name]
 ck('test_hash_'+name,sha(C/name)==transform['sha256'] and sha(H/name)==transform['clone_sha256'])
 matches=list(re.finditer(r'@test_throws\b|@test\b',original))
 ck('site_count_'+name,len(matches)==len(transform['changes'][0]['sites']))
 for k,match in enumerate(matches,1):
  line=original.count('\n',0,match.start())+1
  ck(f'site_{prefix}{k:03d}',sites[f'{prefix}{k:03d}']==dict(file=name,line=line,kind=match.group(),source_line=original.splitlines()[line-1]))
 for change in reversed(transform['changes'][1:]):
  ck('inverse_substitution_'+name+'_'+str(len(checks)),clone.count(change['new'])==change['count'])
  clone=clone.replace(change['new'],change['old'])
 clone=clone.replace('using ..HarnessRecords: @check, @checkthrows\nimport ..HarnessRecords\nusing Test','using Test')
 clone=re.sub(r'(@checkthrows|@check) "([PNL][0-9]{3})"',lambda x:sites[x.group(2)]['kind'],clone)
 ck('exact_original_inverse_'+name,clone==original)
stages=rd(H/'stages.json');stage=Path(cfg['stage']);extra='include("factor-export.jl")\ninclude("direct-factor.jl")\n\n';root_source=(stage/'src/JSimplex.jl').read_text()
ck('same_ordinary_stage',stages['red']==stages['green'])
ck('root_include_inverse',root_source.count(extra)==1 and root_source.replace(extra,'')==(R/'src/JSimplex.jl').read_text())
for p in (stage/'src').rglob('*'):
 if p.is_file() and p.name not in ['JSimplex.jl','factor-export.jl','direct-factor.jl']:ck('stage_original_'+str(p.relative_to(stage)),sha(p)==sha(R/p.relative_to(stage)))
for name in ['direct-factor.jl','factor-export.jl']:ck('original_factory_export_'+name,sha(stage/'src'/name)==sha(R/'diagnostics/direct-lu-policy-adapters/reproduce'/name))
schedule=rd(H/'schedule.json');fixtures=rd(C/'fixtures.json')['fixtures'];toml=tomllib.loads((C/'fixtures.toml').read_text())['fixtures']
ck('fixture_json_toml',toml==fixtures)
ck('fixed_schedule',schedule['fixtures']==[dict(name=f['name'],n=f['n'],updates=len(f['steps']),pivot_agreement=f['pivot_agreement'],minimum_panels=f['minimum_panels']) for f in fixtures])
ck('28_units',schedule['units']==['panel','lifecycle']+[f['name']+'/'+b for f in fixtures for b in ['native','markowitz']] and len(schedule['units'])==28)
expected=[f+'/'+b for f in ['dense96','dense256','dense96-long32'] for b in ['native','markowitz']]
ck('six_expected_coverage_cells',schedule['expected_red_units']==expected)
ck('API_budget_arithmetic',len(fixtures)==13 and sum(len(f['steps']) for f in fixtures)==128)
ck('coverage_site',sites['N026']['line']==156 and sites['N026']['source_line'].strip()=='@test sum(o.panels for o in observed)>=f["minimum_panels"]')
driver=(H/'driver.jl').read_text();num=(H/'numerical-tests.jl').read_text();guard=(H/'guard.py').read_text();launch=(H/'launch.py').read_text();outer=(H/'outer.py').read_text();oracle=(H/'oracle.py').read_text()
ck('top_level_definitions',driver.rfind('include(')<driver.index('function main()'))
ck('scalar_subject_only', 'reference_route=RED' in driver and 'blocked=!reference_route' in num and driver.count('run_task1_tests')==driver.count('run_lifecycle')==1)
ck('named_red_failure_guard',all('"'+n+'"' in driver for n in expected) and 'r["site"]=="N026"' in driver)
ck('raw_before_exit',driver.index('save("raw.toml"')<driver.index('exit(valid'))
ck('unit_finally_preservation','finally\n        save("unit-$index.toml"' in driver)
ck('resource_limits_source','resource.setrlimit(resource.RLIMIT_AS, (8 * 1024**3, 8 * 1024**3))' in guard and "sample['available_kib'] < 6 * 1024**2" in guard and "sample['swap_used_kib'] > 1024**2" in guard)
ck('command_limits','--threads=1' in cfg['command'] and '--gcthreads=1,0' in cfg['command'] and '--heap-size-hint=2G' in cfg['command'] and '--compiled-modules=existing' in cfg['command'])
ck('one_attempt_reservation',"save(res,dict(one_attempt=True" in launch and "require(not Path(cfg['output']).exists()" in launch)
ck('external_release_required',"while not (Q/'release.json').exists()" in outer and "c.verify_review(v,sp,s['files']+[str(sp)]" in outer)
ck('mandatory_completions',"expected=trace_counts(e,2*u)" in oracle and "expected.update(trace_counts(e,3))" in oracle)
# Pure accounting checks do not invoke any numerical algorithm.
import oracle as o
ck('11760_panel_assertions',sum(o.panel_counts().values())==11760)
base=dict(event_begin=1,event_finish=1,finish=1,event_scalar_suffix=1,event_scalar_pivot=1,pivot=1)
ck('pure_scalar_formula',o.trace_counts(base,1)['N001']==1)
for name,change in [('unknown',{'unknown':1}),('finish',{'event_finish':0}),('pivot',{'pivot':2})]:
 try:o.trace_counts(dict(base,**change),1)
 except ValueError:ck('reject_'+name,True)
 else:ck('reject_'+name,False)
# No runtime control mutator or old exclusive checker was called.
record=dict(all_passed=True,checks=checks,check_count=len(checks),host=h,memory=m,outer_identity=i,sealed_sha256=sha(sp),sealed_file_count=len(s['files']),inventory_count=len(s['inventory']),julia_executed=False,scope=__doc__)
save(D/'admission-independent-check.json',record)
print(json.dumps(dict(all_passed=True,checks=len(checks),files=len(s['files']),memory=m,host_matches=h['matches'],unreadable_exe_pids=h['unreadable_exe_pids'],outer_identity=i)))
