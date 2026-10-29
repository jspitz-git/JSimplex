"""Independent saved-results audit. No Julia, solver, old scripts or numerical data regeneration."""
from pathlib import Path
import hashlib,json,tomllib,re,collections,statistics,math,os
D=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl/diagnostics/klu-weight-btran/2026-10-29')
O=Path('/tmp/klu-weight-final-review');O.mkdir(exist_ok=True)
checks=[]
def check(p,label):
    if not p: raise AssertionError(label)
    checks.append(label)
def read(p): return json.loads(Path(p).read_text())
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def timed(s,label):
    check(all(isinstance(s[k],(int,float)) and math.isfinite(s[k]) and s[k]>=0 for k in ('seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds')),label+' finite counters')
    check(s['compile_seconds']==s['recompile_seconds']==0,label+' compilation zero')
    check(s['seconds']>0,label+' positive window')
def med(xs):return statistics.median(xs)
r=tomllib.loads((D/'results-2.toml').read_text());analysis=read(D/'diagnostic-analysis.json')
check(r['completed'] is True,'serialized result complete flag is present')
manifest_counts={}
for name in ['source-pins.json','launch-pins.json','launch-pins-2.json']:
    inv=read(D/name)['inventory'];manifest_counts[name]=len(inv)
    for filename,entry in inv.items():
        p=Path(filename);check(str(p.resolve())==entry['resolved'] and sha(p)==entry['sha256'],'unchanged binding '+filename)
check(list(manifest_counts.values())==[119,126,134],'manifest counts 119/126/134')
processes=[]
for attempt,groups in [(1,721),(2,723)]:
    base=D/f'comparison-{attempt}';p=read(base/'guard/process.json');s=read(base/'supervisor.json');post=read(base/'postflight.json')
    check(p['reason']=='exit1' and p['returncode']==1 and s['accepted'] is False and p['pins_unchanged'],'failed attempt stays rejected '+str(attempt))
    manifest=D/('launch-pins.json' if attempt==1 else 'launch-pins-2.json')
    check(sha(manifest)==p['pins_sha256'] and read(base/'guard/pins.json')==read(manifest),'guard pins match '+str(attempt))
    check(len(post['checked_groups'])==groups and not post['conflicts'],'saved full group/session closure '+str(attempt))
    check(all(not s[k] for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']),'no timeout or signal '+str(attempt))
    check(set(post['refs'].values())=={'c0fa748ffa61ccb7c1caaf248c40324f60bc737b'},'saved master refs '+str(attempt))
    processes.append(dict(attempt=attempt,elapsed=p['elapsed_including_launch'],rss_kib=p['child_maxrss_kib'],groups=groups))
log=(D/'comparison-2/guard/run.log').read_text();fail=collections.Counter()
for block in log.split('Test Failed at ')[1:]:
    match=re.search(r'Expression: ([^\n]+)',block);check(match is not None,'ordinary failure expression');fail[match[1]]+=1
check(dict(fail)=={'weights!(trial, rows, stopper, mode)':18,'t.value':126,'t.value.ok':72,'coldstops[1] == coldstops[2] == coldstops[3]':1},'independent exact 217 failure partition')
check('13816   217  14033' in log and '0 errored' in log,'ordinary Test summary')
check('ParseError' in (D/'comparison-1/guard/run.log').read_text() and not (D/'results-1.toml').exists(),'first attempt parse failure and no numerical result')
strict=read(D/'strict-auditor-rejection.json');check(strict['returncode']==1 and 'guard completed and full host closure' in strict['stderr'],'strict auditor preserved rejection')
check(analysis['whole_experiment_accepted'] is False and analysis['diagnostic_accepted'] is True,'partial analyzer is explicitly bounded')
expected={f'{h}-B{state}' for h in ['runtime-30000','runtime-40000','fast0507-1000'] for state in [0,80,160]}|{'coupled64-forced','dense64-native-only','irreducible64-native-only'}
check(len(r['cases'])==12 and {c['id'] for c in r['cases']}==expected,'case identities complete')
check(sum(c['sample_rows'] for c in r['cases'])==1344,'sample rows total 1344')
anchors_path=D.parent.parent/'klu-block-reach/2026-10-29/results-1.toml'
anchors=tomllib.loads(anchors_path.read_text())['profiles'];anchors={a['history']+'-B'+str(a['state']):a for a in anchors}
case_out=[];totals=collections.Counter();maxima=collections.defaultdict(float)
for c in r['cases']:
    name=c['id'];n=c['n'];count=c['sample_rows'];runtime=name.startswith('runtime');o={'case':name,'runtime':runtime,'memory':{}}
    check(count==min(n,128) and c['rows']==[1+(i*(n-1))//(count-1) for i in range(count)],name+' uniform original row schedule')
    check(c['max_scaled_residual']<=c['tolerance']==min(1e-10,128*n*2**-52) and c['max_native_relative_difference']<=1e-6,name+' saved cold oracles within bounds')
    check(c['direct_UMFPACK_checks']==3,name+' three independent endpoints');totals['references']+=3;totals['cold_kernel_calls']+=6*count
    maxima['residual']=max(maxima['residual'],c['max_scaled_residual']);maxima['difference']=max(maxima['difference'],c['max_native_relative_difference'])
    if runtime:maxima['runtime_residual']=max(maxima['runtime_residual'],c['max_scaled_residual'])
    policy=c['policy'];check(policy['solve_tolerance']==2**-44 and policy['max_refinements']==3 and not policy['solve_refinement'],name+' original solve policy')
    check([sum(p)-p[2] for p in c['cold_paths']]==[1 if runtime else count]*3,name+' cold observed unit count')
    if runtime:
        check(all(all(w==1. for w in arm) for arm in c['cold_weights']),name+' no evidence from initial weights')
        check(c['cold_stops']==([4,2,2] if name=='runtime-40000-B80' else [2]*3),name+' cold stop/correction accounting')
    for category,round_count in [('kernel_samples',5),('samples',5),('inclusive_samples',3)]:
        ss=c[category];check(len(ss)==3*round_count,name+'/'+category+' count');by={arm:sorted([s for s in ss if s['arm']==arm],key=lambda s:s['round']) for arm in ['native','full','local']}
        for arm,armss in by.items():
            check([s['round'] for s in armss]==list(range(1,round_count+1)),name+'/'+category+'/'+arm+' complete rounds')
            for s in armss:
                timed(s,name+'/'+category+'/'+arm);check(s['unit_calls']==count and len(s['paths'])==7,name+' requested field and paths')
                actual=sum(s['paths'])-(s.get('generic_correction_calls',0))
                if category=='kernel_samples':check(actual==count,name+' complete measured kernel');totals['kernel_calls']+=actual
                else:
                    check(s['generic_correction_calls']==s['paths'][2] and actual==(1 if runtime else count),name+' observed handler/correction routes')
                    if runtime:totals['excluded_'+category]+=1
                    else:totals['valid_'+category+'_calls']+=actual
        if category=='kernel_samples':
            o['kernel']={}
            for arm,armss in by.items():
                ratios=[a['seconds']/b['seconds'] for a,b in zip(armss,by['native'])]
                o['kernel'][arm]={'median_ms':med([s['seconds']*1000 for s in armss]),'paired_median':med(ratios),'paired_min':min(ratios),'paired_max':max(ratios),'bytes':sorted({s['bytes'] for s in armss}),'events':sorted({s['events'] for s in armss})}
            if runtime:check(o['kernel']['local']['paired_max']<1 and o['kernel']['native']['bytes']==[0] and o['kernel']['local']['bytes']==[16] and o['kernel']['local']['events']==[1],name+' complete kernel gain/cost')
    m=c['memory'];check(m['local']==m['full'] and len({x['native_reported_bytes'] for x in m.values()})==1,name+' equal per-arm native/full-local memory')
    if name in anchors:
        a=anchors[name];check((a['n'],a['B_nnz'],a['matrix_hash'])==(n,c['B_nnz'],c['matrix_hash']),name+' old dimension/nonzero/hash anchor')
        if m['local']['graph_eligible']:
            nf,nb,lu=a['F_stored'],a['blocks'],a['LU_stored']
            reverse=8*(2*n+1+2*nf+nb)+56
            # Exports: 3 n+1 pointers, paired numeric/index arrays, P/Q/Rs, R.
            exports=8*(3*(n+1)+2*(lu+nf)+3*n+nb+1)
            shared=exports+8*(4*n+2*nb)+4*nb
            check(m['local']['transpose_index_payload_bytes']==reverse and m['local']['shared_export_scratch_payload_bytes']==shared,name+' independently recomputed index and shared payload')
            o['memory']={'n':n,'F_stored':nf,'blocks':nb,'LU_stored':lu,'transpose_index_bytes':reverse,'shared_payload_bytes':shared,'extra_payload_over_native_bytes':shared+reverse-m['native']['shared_export_scratch_payload_bytes']-m['native']['transpose_index_payload_bytes'],'transient_next_pointer_bytes':8*(n+1)}
    case_out.append(o)
check(dict(totals)=={'references':36,'cold_kernel_calls':8064,'kernel_calls':20160,'excluded_samples':90,'excluded_inclusive_samples':54,'valid_samples_calls':8640,'valid_inclusive_samples_calls':5184},'independent complete/partial totals')
check(len(r['setup'])==108,'108 setup totals');prep=[]
for name in expected:
    o={'case':name,'arms':{}};case=next(c for c in r['cases'] if c['id']==name)
    for arm in ['native-staged','shared-staged','original-FTRAN-unsplit']:
        ss=sorted([s for s in r['setup'] if s['case']==name and s['arm']==arm],key=lambda s:s['round']);check([s['round'] for s in ss]==[1,2,3],name+'/'+arm+' setup rounds')
        for s in ss:
            timed(s,name+'/'+arm+' setup');stagekeys=set() if arm=='original-FTRAN-unsplit' else {'factor','scratch','reverse'}|({'extraction','metadata'} if arm=='shared-staged' and case['memory']['local']['graph_eligible'] else set())
            check(set(s['stages'])==stagekeys,name+'/'+arm+' stage layout')
            for k,v in s['stages'].items():timed(v,name+'/'+arm+'/'+k)
            check(sum(v['seconds'] for v in s['stages'].values())<=s['seconds']+1e-6,name+'/'+arm+' nested time containment')
        o['arms'][arm]={'median_ms':med([s['seconds']*1000 for s in ss]),'median_events':med([s['events'] for s in ss]),'stages':{k:{'median_ms':med([s['stages'][k]['seconds']*1000 for s in ss]),'events':sorted({s['stages'][k]['events'] for s in ss})} for k in ss[0]['stages']}}
    prep.append(o)
profiles=tomllib.loads((D/'allocation-profile.toml').read_text())['profiles'];profile_out=[]
for p in profiles:
    check(p['sample_rate']==.01 and sum(g['sampled_events'] for g in p['groups'])==p['sampled_events'] and sum(g['sampled_bytes'] for g in p['groups'])==p['sampled_bytes'],'profile sums '+p['arm'])
    types=collections.Counter();lines=collections.Counter()
    for g in p['groups']:types[g['type']]+=g['sampled_events'];lines[g['first_diagnostic_frame']]+=g['sampled_events']
    loop=sum(num for frame,num in lines.items() if re.search(r'/ftran\.jl:(37|39|40)$',frame))
    profile_out.append(dict(arm=p['arm'],events=p['sampled_events'],sampled_bytes=p['sampled_bytes'],types=dict(types),first_frames=dict(lines),loop_events=loop))
orig=next(p for p in profile_out if p['arm']=='original-FTRAN-unsplit');check(orig['events']==5865 and orig['loop_events']==5864 and orig['types']['Int64']==5159,'independent allocation loop/type grouping')
# Mechanical private-name and unit-producer inverse, using text only.
consumer=(D/'consumer.jl').read_text();source=(D/'consumer-source.txt').read_text().strip()
original=consumer[consumer.index('function original_weights!'):consumer.index('\n\n\nfunction weights!')].strip()
for name in ['SimplexWorkspace','_weight_pricing','transpose_solve!','refine_basis_solve!','_typed_ratio']:original=original.replace('JSimplex.'+name,name)
check(original.replace('original_weights!','_rebuild_recovery_weights!')==source,'exact original consumer qualification inverse')
adapted=consumer[consumer.index('function weights!'):].strip().replace('function weights!(trial::JSimplex.SimplexWorkspace{T},rows,stop,mode::Val)','function original_weights!(trial::JSimplex.SimplexWorkspace{T},stop)').replace('for row in rows','for row in 1:m').replace('        unit_btran!(direction,trial.factorization.ctx,rhs,row,mode)','        fill!(rhs,zero(T))\n        rhs[row] = one(T)\n        JSimplex.transpose_solve!(direction,trial.factorization,rhs)')
check(adapted==consumer[consumer.index('function original_weights!'):consumer.index('\n\n\nfunction weights!')].strip(),'adapted consumer exact row/hook inverse')
resources=[json.loads(line) for line in (D/'comparison-2/guard/resources.jsonl').read_text().splitlines()]
check(len(resources)==46 and min(x['available_kib'] for x in resources)==21669688 and max(x['swap_used_kib'] for x in resources)==0,'46 resource samples bounds')
post=read(D/'comparison-2/postflight.json');groups=set(post['checked_groups']);boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();conflicts=[]
for path in Path('/proc').glob('[0-9]*'):
    try:
        data=(path/'stat').read_text();fields=data[data.rindex(')')+2:].split();pgid,sid=int(fields[2]),int(fields[3]);comm=(path/'comm').read_text().strip()
        if comm.lower().startswith('julia') or pgid in groups or sid in groups:conflicts.append({'pid':int(path.name),'pgid':pgid,'sid':sid,'comm':comm})
    except (FileNotFoundError,ProcessLookupError):pass
check(boot==post['boot'] and not conflicts,'fresh same-boot full723 PGID/session and Julia absence')
# Cross-check derived summaries against the coordinator's already-saved analyzer.
for o in case_out:
    other=next(x for x in analysis['summary'] if x['case']==o['case'])
    for arm,k in o['kernel'].items():
        a=other['kernel_samples'][arm]
        check((k['median_ms'],k['paired_median'],k['paired_min'],k['paired_max'],k['bytes'],k['events'])==(a['median_ms'],a['paired_ratio_median'],a['ratio_min'],a['ratio_max'],a['bytes'],a['events']),o['case']+'/'+arm+' independent kernel summary agrees')
for o in prep:
    other=next(x for x in analysis['setup'] if x['case']==o['case'])
    for arm,k in o['arms'].items():
        a=other['arms'][arm]
        check(k['median_ms']==a['median_ms'] and k['median_events']==med(a['events']),o['case']+'/'+arm+' independent preparation summary agrees')
        for stage,v in k['stages'].items():
            check(v['median_ms']==a['stage_medians'][stage]['ms'] and v['events']==a['stage_medians'][stage]['events'],o['case']+'/'+arm+'/'+stage+' stage summary agrees')
out=dict(decision='accepted diagnostic-only closure of REJECTED experiment',experiment_pass=False,critical_findings=[],important_findings=[],minor_findings=[],checks_count=len(checks),checks=checks,manifest_counts=manifest_counts,failures=dict(fail),totals=dict(totals),maxima=dict(maxima),processes=processes,profiles=profile_out,cases=case_out,setup=sorted(prep,key=lambda p:p['case']),host={'boot':boot,'checked_groups':len(groups),'conflicts':conflicts},old_anchor_sha256=sha(anchors_path))
(O/'review-results-checks.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:out[k] for k in ['decision','checks_count','manifest_counts','failures','totals','maxima','profiles']},indent=2))
