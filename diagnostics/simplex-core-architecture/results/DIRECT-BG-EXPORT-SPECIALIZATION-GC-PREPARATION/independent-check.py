"""Fresh reviewer checks. Only Python schema import, text, hashes and read-only host/git.
No Julia command, Julia parser, prior checker, launcher or auditor is invoked.
"""
from pathlib import Path
import ast, copy, hashlib, importlib.util, json, math, os, re, subprocess, sys, time, tomllib
sys.dont_write_bytecode=True
N=Path(__file__).resolve().parent
R=N.parents[3]
D=N.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-DRIVER')
Q=N.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-RED')
checks={}; details={}
def ck(name, value):
    if name in checks: raise RuntimeError('Duplicate check '+name)
    checks[name]=bool(value)
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def full(p):return Path(p) if Path(p).is_absolute() else R/p
def bindings(j):return all(full(p).is_file() and sha(full(p))==h for p,h in j['sha256'].items())
def rejects(name,fn):
    try: fn()
    except ValueError:ck(name,True)
    else:ck(name,False)
canonical=N/'preparation-pins-reviewed.json'; pins=rd(canonical); initial=rd(N/'preparation-pins.json')
ck('canonical_exact_2232',len(pins['sha256'])==2232)
for p,h in pins['sha256'].items():ck('current_binding:'+p,Path(p).is_file() and sha(p)==h)
for p,h in initial['sha256'].items():
    target=N/'PREPARATION.md.before-count-fix' if p==str(N/'PREPARATION.md') else Path(p)
    ck('initial_binding_with_only_report_remap:'+p,target.is_file() and sha(target)==h)
ck('initial_exact_2230',len(initial['sha256'])==2230)
ck('canonical_additions_only_original_report_and_manifest',set(pins['sha256'])-set(initial['sha256'])=={str(N/'PREPARATION.md.before-count-fix'),str(N/'preparation-pins.json')})
ck('canonical_removed_no_paths',set(initial['sha256'])<=set(pins['sha256']))
ck('canonical_only_changed_report', {p for p in initial['sha256'] if initial['sha256'][p]!=pins['sha256'][p]}=={str(N/'PREPARATION.md')})
fix=rd(N/'count-fix.json'); before=(N/'PREPARATION.md.before-count-fix').read_text(); report=(N/'PREPARATION.md').read_text()
ck('count_fix_exact_text',before.replace('exactly18keys','exactly17keys').replace('18-entry dictionary','17-entry dictionary')==report)
ck('count_fix_bound_hashes',fix['original_report_sha256']==sha(N/'PREPARATION.md.before-count-fix') and fix['corrected_report_sha256']==sha(N/'PREPARATION.md'))
ck('count_fix_counts',fix['all_passed'] is True and (fix['original_report_label'],fix['corrected_report_label'],fix['actual_schema_keys'])==(18,17,17))
oldpins=rd(D/'preparation-pins.json');oldreview=rd(D/'review.json')
ck('old_preparation_full_bindings',bindings(oldpins))
ck('old_preparation_exact_required',set(oldpins['sha256'])==set(rd(D/'required-paths.json')['paths']))
ck('old_review_still_accepted',oldreview['accepted'] is True and oldreview['findings']==[] and oldreview['scope']=='BG specialization driver preparation' and oldreview['red_expectation_supported'] is True)
ck('old_review_exact_membership',set(oldreview['sha256'])==set(oldpins['sha256'])|{str(D/'preparation-pins.json')})
ck('old_review_bindings',bindings(oldreview) and oldreview['pins_sha256']==sha(D/'preparation-pins.json'))
for root in (D,Q):
    publication=rd(root/'publication.json')
    ck(root.name+'_publication_bindings',bindings(publication))
    ck(root.name+'_publication_in_canonical',{str(full(p)) for p in publication['sha256']}|{str(root/'publication.json')}<=set(pins['sha256']))
audit=rd(D/'runs/red300/audit.json');review=rd(D/'runs/red300/result-review.json')
ck('old_red_still_rejected_non_timeout',audit['all_passed'] is False and audit['pure_timeout'] is False and 'Measured compilation' in audit['error'] and review['accepted'] is False and review['qualification_accepted'] is False)
ck('old_failed_attempt_review_bindings',bindings(review) and all(sha(p)==h for p,h in review['evidence_sha256'].items()))
old=(D/'driver.jl').read_text();new=(N/'driver.jl').read_text();helper=(N/'preparation.jl').read_text()
edits=[('# UNEXECUTED GC preparation amendment; same lifecycle and gates, separate run admission required.','# UNEXECUTED Task2; ordinary stage, all definitions before main; no runtime include.'),('PHASE in ("redgc300","greengc300")','PHASE in ("red300","green300","red600","green600")'),('include("preparation.jl")\n',''),('            pair == 3 && prepare_gc!(cell,f.name)\n',''),('        require(PREPARATION_CALLS[] == PREPARATION_COMPLETED[] == 3,"Preparation count")\n',''),('        raw["preparation_calls"]=PREPARATION_CALLS[]\n        raw["preparations_completed"]=PREPARATION_COMPLETED[]\n','')]
inverse=new
for i,(a,b) in enumerate(edits):
    ck('edit_unique_'+str(i),inverse.count(a)==1);inverse=inverse.replace(a,b,1)
ck('entire_driver_exact_inverse',inverse==old)
source=rd(N/'source-map.json')
ck('source_map_hashes',source['original_sha256']==sha(D/'driver.jl') and source['new_sha256']==sha(N/'driver.jl') and len(source['changes'])==6)
for name in ('green-kernel.jl','red-kernel.jl','recorder.jl','inputs.toml','expected-tests.toml'):
    ck('byte_exact_copy_'+name,(N/name).read_bytes()==(D/name).read_bytes() and source['copies'][name]==sha(N/name))
red=rd(N/'structural-red.json');generator=(N/'prepare.py').read_text()
markers=['include("preparation.jl")','prepare_gc!(cell,f.name)','raw["preparation_calls"]']
ck('source_red_three_absences',all(m not in old for m in markers) and red['expected_missing']==red['actual_missing']==3 and red['candidate_absent'] is True and red['old_sha256']==sha(D/'driver.jl'))
ck('source_red_generated_before_candidate',generator.index("put('structural-red.json'")<generator.index("put('driver.jl'"))
ck('helper_only_one_gc_call',helper.count('GC.gc(')==helper.count('@timed GC.gc(true)')==1)
ck('helper_two_scalar_refs',helper.count('Ref(0)')==2 and 'function prepare_gc!(cell::Int,fixture)' in helper)
ck('helper_order_and_no_loop',helper.index('require(')<helper.index('PREPARATION_CALLS[] += 1')<helper.index('@timed GC.gc(true)')<helper.index('save_window(')<helper.index('PREPARATION_COMPLETED[] += 1') and not re.search(r'^\s*(for|while|try|catch)\b',helper,re.M))
ck('helper_no_factor_operations',all(t not in helper for t in ('forward_solve!','transpose_solve!','refactorize!','replace_column!','factory(', 'finalize(', 'GC.enable(', 'GC.enable_finalizers(', 'precompile(')))
ck('boundary_after_pair_check_once',new.count('prepare_gc!(cell,f.name)')==1 and '"Paired output/mode mismatch")\n            pair == 3 && prepare_gc!(cell,f.name)' in new)
ck('include_at_top_level',new.index('include("preparation.jl")')<new.index('function exact_tree'))
ck('completion_and_finally_order',new.index('"Preparation count")')<new.index('raw["complete"]=true')<new.index('finally\n')<new.index('raw["preparation_calls"]')<new.index('raw["preparations_completed"]')<new.index('save_window("raw.toml"'))
ck('same_schedule',all(x in new for x in ('for pair in 1:10','pair>3','isodd(pair)','compile_seconds"]==0 && row["recompile_seconds"]==0','median7(cands_events)<=median7(refs_events) && median7(cands_bytes)<=median7(refs_bytes)')))
ck('green_four_original_test_includes',all('include("'+str(R/'diagnostics/direct-bg-export-specialized/reproduce'/name)+'")' in new for name in ('workspace-tests.jl','import-tests.jl','lifecycle-tests.jl','boundary-tests.jl')))
expected=tomllib.loads((N/'expected-tests.toml').read_text())
ck('expected_assertion_totals',expected['red']['assertions']==3 and expected['green']['assertions']==8640 and sum(g['pass'] for g in expected['green']['groups'])==8640)
control=ast.parse((D/'control.py').read_text());config=next(x for x in control.body if isinstance(x,ast.FunctionDef) and x.name=='config')
allowed=ast.literal_eval(config.body[0].value.args[0].comparators[0])
ck('old_launcher_rejects_new_phases','redgc300' not in allowed and 'greengc300' not in allowed)
ck('old_audit_does_not_admit_new_records','preparation-' not in (D/'audit.py').read_text() and 'preparation_calls' not in (D/'oracle.py').read_text())
ck('no_new_launch_artifacts',not any((N/x).exists() for x in ('launch.py','audit.py','reservation.json','sealed.json','runs','admission.json')))
spec=importlib.util.spec_from_file_location('fresh_gc_schema',N/'preparation_schema.py');schema=importlib.util.module_from_spec(spec);spec.loader.exec_module(schema)
ck('schema_exact_17_keys',len(schema.KEYS)==17 and set(re.findall(r'"([a-z_]+)"=>',helper))==schema.KEYS)
base=dict(phase='redgc300',fixture='sparse32',cell=1,after_pair=3,before_pair=4,requested_full_gc=True,calls=1,cumulative_calls=1,returned=True,seconds=.04,bytes=12,events=3,gc_seconds=.02,compile_seconds=.01,recompile_seconds=0.,gc_pauses=1,full_collections=1)
for phase in ('redgc300','greengc300'):
    rows={}
    for i,fixture in enumerate(('sparse32','dense32','sparse96'),1):
        row=dict(base,phase=phase,fixture=fixture,cell=i,cumulative_calls=i); rows[f'preparation-{i}.toml']=row
        ck(f'valid_{phase}_{i}',schema.validate_record(row,i,phase))
    for count in range(4):
        partial=dict(list(rows.items())[:count])
        ck(f'valid_prefix_{phase}_{count}',schema.validate_records(partial,phase,False))
        if count<3:rejects(f'incomplete_{phase}_{count}',lambda partial=partial,phase=phase:schema.validate_records(partial,phase,True))
    ck('complete_'+phase,schema.validate_records(rows,phase,True))
    for key in rows:
        bad={k:v for k,v in rows.items() if k!=key}
        if key!='preparation-3.toml':rejects('gap_'+phase+key,lambda bad=bad,phase=phase:schema.validate_records(bad,phase,False))
    bad=dict(rows);bad['preparation-4.toml']=rows['preparation-3.toml'];rejects('extra_row_'+phase,lambda bad=bad,phase=phase:schema.validate_records(bad,phase,True))
for key in schema.KEYS:
    row=dict(base);del row[key];rejects('missing_'+key,lambda row=row:schema.validate_record(row,1,'redgc300'))
row=dict(base,extra=1);rejects('extra_key',lambda:schema.validate_record(row,1,'redgc300'))
for key in ('cell','after_pair','before_pair','calls','cumulative_calls'):
    for i,value in enumerate((True,False,None,str(base[key]),float(base[key]),base[key]+1)):
        row=dict(base);row[key]=value;rejects(f'schedule_{key}_{i}',lambda row=row:schema.validate_record(row,1,'redgc300'))
for key in ('bytes','events','gc_pauses','full_collections'):
    for i,value in enumerate((-1,True,False,None,'1',1.0)):
        row=dict(base);row[key]=value;rejects(f'counter_{key}_{i}',lambda row=row:schema.validate_record(row,1,'redgc300'))
for key in ('seconds','gc_seconds','compile_seconds','recompile_seconds'):
    for i,value in enumerate((-1.,math.nan,math.inf,-math.inf,True,False,0,None,'0')):
        row=dict(base);row[key]=value;rejects(f'time_{key}_{i}',lambda row=row:schema.validate_record(row,1,'redgc300'))
for key in ('requested_full_gc','returned'):
    for i,value in enumerate((False,1,0,'true',None)):
        row=dict(base);row[key]=value;rejects(f'boolean_{key}_{i}',lambda row=row:schema.validate_record(row,1,'redgc300'))
for key,value in (('phase','red300'),('phase','green300'),('fixture','dense32'),('fixture','other')):
    row=dict(base);row[key]=value;rejects('identity_'+key+'_'+value,lambda row=row:schema.validate_record(row,1,'redgc300'))
for i,value in enumerate((False,0,4,'1',None)):
    rejects('expected_cell_'+str(i),lambda value=value:schema.validate_record(base,value,'redgc300'))
for i,value in enumerate((0,1,None,'true')):rejects('expected_complete_'+str(i),lambda value=value:schema.validate_records({},'redgc300',value))
ck('zero_metrics_valid',schema.validate_record(dict(base,seconds=0.,bytes=0,events=0,gc_seconds=0.,compile_seconds=0.,recompile_seconds=0.,gc_pauses=0,full_collections=0),1,'redgc300'))
ck('overlapping_metrics_and_multiple_collections_valid',schema.validate_record(dict(base,seconds=1.,gc_seconds=3.,compile_seconds=2.,recompile_seconds=2.,gc_pauses=3,full_collections=2),1,'redgc300'))
# Pinned installed sources are read as text; Julia is never loaded or queried.
timing=next(Path(p) for p in pins['sha256'] if p.endswith('/base/timing.jl')).read_text()
ck('pinned_timing_interface',all(t in timing for t in ('macro timed(ex)','gcstats=diff','compile_time=compile_elapsedtimes[1]/1e9','recompile_time=compile_elapsedtimes[2]/1e9','new.pause        - old.pause','new.full_sweep   - old.full_sweep')))
ck('document_gc_scope_limits',all(t in report for t in ('NOT a bound on collection work','not proof that every object is unreachable','17-entry dictionary','not a pure-timeout retry base','future300second guard must include preparation')))
host=rd(N/'host-entry.json');groups=set(host['groups']);matches=[];unreadable=[];unreadable_identity=[]
for p in Path('/proc').glob('[0-9]*'):
    try:
        stat=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip();argv0=(p/'cmdline').read_bytes().split(b'\0',1)[0].decode(errors='replace');exe=''
        try:exe=str((p/'exe').resolve(strict=True))
        except PermissionError:unreadable.append(int(p.name))
        except FileNotFoundError:pass
        if int(stat[2]) in groups or int(stat[3]) in groups or any(Path(s).name.lower().startswith('julia') for s in (comm,argv0,exe)):
            matches.append(dict(pid=int(p.name),pgrp=int(stat[2]),session=int(stat[3]),start_ticks=int(stat[19]),comm=comm,argv0=argv0,exe=exe))
    except (FileNotFoundError,ProcessLookupError):pass
    except PermissionError:unreadable_identity.append(int(p.name))
refs=subprocess.check_output(['git','rev-parse','HEAD','master'],cwd=R,text=True).splitlines()
ck('host_259_distinct_groups',len(groups)==259)
ck('fresh_no_matching_group_session_or_julia',matches==[] and unreadable_identity==[])
ck('head_master_unchanged',refs==['509fa509fdd8d3187e5aac6a4229bce707ffe227','26e2291745999f485a74f643298ca997d65c7205'])
details['host']=dict(time=time.time(),groups=sorted(groups),matches=matches,unreadable_exe_pids=unreadable,unreadable_identity_pids=unreadable_identity,refs=refs,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),limitation='Unreadable executable symlinks limit universal executable-identity proof; comm, argv0, stat, groups and sessions inspected.')
details['scope']='Offline independent text/hash/schema review only. No Julia parser/import/query/compilation/numerics and no previous checker execution.'
result=dict(all_passed=all(checks.values()),check_count=len(checks),checks=checks,details=details,pins_sha256=sha(canonical),source_sha256=sha(__file__))
with (N/'independent-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=result['all_passed'],checks=len(checks),failed=[k for k,v in checks.items() if not v])))
if not result['all_passed']:raise SystemExit(1)
