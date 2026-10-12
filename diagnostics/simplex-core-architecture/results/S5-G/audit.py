"""Exclusive offline audit: derive acceptance from raw records, retain false gates."""
from pathlib import Path
import hashlib,json,sys,tomllib,re,struct,math
from fractions import Fraction
ROOT=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
HERE=Path(__file__).resolve().parent
RUN=ROOT/'.superpowers/simplex-core-architecture/S5-G/qualification-1'
checks={};details={}
def check(k,v):checks[k]=bool(v)
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def sem(x):
    if isinstance(x,dict):
        if 'kind' in x:return (x['value'],x['negative'])
        if 'payload' in x:return (x['bound'],sem(x['payload']))
        return {k:sem(v) for k,v in x.items()}
    if isinstance(x,list):return [sem(v) for v in x]
    return x
def typed(x,bits):
    if isinstance(x,dict):
        if 'kind' in x:return x['precision']==bits and x['kind']==('Float64' if bits==53 else 'BigFloat')
        return all(typed(v,bits) for v in x.values())
    if isinstance(x,list):return all(typed(v,bits) for v in x)
    return True
def valid_scalar(x):
    if isinstance(x,dict):
        if 'kind' in x:
            v=x['value'];neg=x['negative']
            if x['kind']=='Float64':
                z=struct.unpack('>d',int(x['bits'],2).to_bytes(8,'big'))[0]
                if math.isfinite(z):return Fraction(v.replace('//','/'))==Fraction(z) and neg==(math.copysign(1,z)<0) and x['precision']==53
                return v==('NaN' if math.isnan(z) else '-Inf' if z<0 else 'Inf') and neg==(math.copysign(1,z)<0) and x['precision']==53
            if x['kind']=='BigFloat':
                if v in ('Inf','-Inf','NaN'):return x['bits']=='' and (v=='NaN' or neg==(v=='-Inf'))
                q=Fraction(v.replace('//','/'));den=q.denominator
                return den&(den-1)==0 and (q==0 or neg==(q<0)) and x['bits']==''
            return False
        return all(valid_scalar(v) for v in x.values())
    if isinstance(x,list):return all(valid_scalar(v) for v in x)
    return True
LENGTHS=dict(costs=3,lower=3,upper=3,original_costs=3,active_costs=3,original_lower=3,original_upper=3,active_lower=3,active_upper=3,primal=3,reduced_costs=3,weights=3,basis=1,states=3,devex=3,colptr=3,rowval=2,nzval=2,objective=2,row_lower=1,row_upper=1,column_lower=2,column_upper=2,progress_objective=2,row_scaling=1,column_scaling=2)
CK=dict(checkpoint_basis=1,checkpoint_states=3,checkpoint_costs=3,checkpoint_lower=3,checkpoint_upper=3)
J='original_costs active_costs original_lower original_upper active_lower active_upper'.split()
OWN='basis states colptr rowval nzval objective row_lower row_upper column_lower column_upper progress_objective row_scaling column_scaling'.split()
PREC='costs lower upper original_costs active_costs original_lower original_upper active_lower active_upper nzval objective row_lower row_upper column_lower column_upper progress_objective row_scaling column_scaling'.split()
def case(mode,s):
    r=tomllib.loads((RUN/'raw'/f'{mode}.toml').read_text());prefix=mode+'.'
    def c(k,v):check(prefix+k,v)
    c('mode',r['mode']==mode)
    b,a,f=r['before'],r['after'],r['fresh'];ba,fa=b['arrays'],f['arrays'];bm,fm=b['metadata'],f['metadata']
    c('source_exact',b==a)
    c('schema',all(set(x['arrays'])==set(LENGTHS)| (set(CK) if i<2 else set()) and all(len(v['values'])==(LENGTHS|CK)[k] for k,v in x['arrays'].items()) for i,x in enumerate((b,a,f))))
    c('scalar_encoding',valid_scalar([b,a,f]))
    c('source_type',bm['scalar_type']=='Float64' and typed(b,53))
    c('source_owner',bm['owner']==bm['workspace'])
    c('source_detached',all(ba[x]['identity']!=ba[y]['identity'] and ba[x]['values']==ba[y]['values'] for x,y in [('costs','active_costs'),('lower','active_lower'),('upper','active_upper')]))
    c('fresh_owner',fm['scalar_type']=='BigFloat' and fm['owner']==fm['workspace']!=bm['owner'] and all(fm[k]!=bm[k] for k in ('workspace','journal','bounds','factor','model')))
    c('aliases',all(fa[x]['identity']==fa[y]['identity'] and fa[x]['values']==fa[y]['values'] for x,y in [('costs','active_costs'),('lower','active_lower'),('upper','active_upper')]))
    c('owned_containers',all(fa[k]['identity']!=ba[k]['identity'] for k in J+OWN) and fa[J[0]]['identity']!=fa[J[1]]['identity'] and len({fa[k]['identity'] for k in J[2:]})==4)
    c('values_preserved',all(sem(fa[k]['values'])==sem(ba[k]['values']) for k in J+OWN))
    c('history',all(fm[k]=='nothing' for k in ('monitor','bound_monitor','stagnation')) and fm['observation']==fm['bound_observation']==0 and bm['observation']==9 and bm['bound_observation']==8 and bm['monitor']==bm['bound_monitor']!='nothing')
    hist='active bound_active original_perturbed perturbed level bound_level cooldown bound_cooldown'.split()
    c('activity',all(fm[k]==bm[k] for k in hist) and bm['active'] and bm['bound_active'] and bm['perturbed'] and (bm['level'],bm['bound_level'],bm['cooldown'],bm['bound_cooldown'])==(2,1,11,13))
    c('constants_options',all(sem(fm[k])==sem(bm[k]) for k in ('objective_constant','progress_constant','objective_sense','options','policy')))
    c('stored_precision',all(typed(fa[k]['values'],128) for k in PREC) and all(typed(fm[k],128) for k in ('objective_constant','progress_constant')) and all(typed(fm['options'][k],128) for k in ('primal_tolerance','dual_tolerance','zero_tolerance')) and all(typed(fm['policy'][k],128) for k in ('solve_tolerance','pivot_error_tolerance')))
    c('time_limit_float64',fm['options']['time_limit']==bm['options']['time_limit'] and typed(fm['options']['time_limit'],53))
    c('native_policy',bm['policy']['solve_refinement']=='false' and bm['policy']['recovery']=='false' and bm['policy']['max_refinements']=='3' and bm['options']['basis_update']=='pfi' and bm['options']['pricing']=='steepest_edge')
    c('empty_new_history_cache',fm['updates']==0 and fm['cache']==fm['cache_model']=='nothing' and fm['checkpoint_count']==0 and fm['checkpoint']=='nothing' and bm['checkpoint_count']==1 and bm['cache']!='nothing' and bm['cache_model']==bm['model'])
    c('checkpoint_preserved',b['metadata']['checkpoint']==a['metadata']['checkpoint'] and all(ba[k]==a['arrays'][k] for k in CK))
    w0,w1=r['setup_work'],r['final_work'];o=r['observed_outcome']
    c('ambient',r['ambient']==r['ambient_after'])
    c('callback',r['hits']==1 and o['returned_type']=='Nothing' and o['returned_identity']=='nothing')
    if mode=='stop':
        c('outcome',o['stop_flag'] is True and r['true_stop_calls']>0 and o['caught_type']=='Nothing' and o['caught_identity']=='nothing' and o['cause_type']==o['cause_identity']=='none')
    else:
        c('outcome',o['stop_flag'] is False and r['true_stop_calls']==0 and 'DiagnosticObserverFailure{' in o['caught_type'] and o['caught_identity']!='nothing' and o['cause_identity']==o['sentinel_identity'] and o['cause_type']==o['sentinel_type']=='SingularException')
    c('shared_progress',fm['diagnostics']==bm['diagnostics'] and fm['start']==bm['start']==w0['budget_start']==w1['budget_start'] and all(fm[k]==bm[k] for k in ('iteration_offset','refactorization_offset')))
    c('work_budget',w1['iterations']==w0['iterations'] and w1['refactorizations']==w0['refactorizations']+1 and w1['budget_iterations']==bm['iteration_offset']+w1['iterations'] and w1['budget_refactorizations']==bm['refactorization_offset']+w1['refactorizations'] and w1['budget_limit']==w0['budget_limit'])
    kd=dict(zip(s['kernel_keys'],[y-x for x,y in zip(w0['kernel_calls'],w1['kernel_calls'])]));ed=dict(zip(s['event_keys'],[y-x for x,y in zip(w0['event_counts'],w1['event_counts'])]))
    c('work_shapes',len(w0['kernel_calls'])==len(w1['kernel_calls'])==len(s['kernel_keys']) and len(w0['event_counts'])==len(w1['event_counts'])==len(s['event_keys']))
    c('kernels',kd['ftran']==1 and 1<=kd['btran']<=4 and kd['refactorization']==1 and all(v==0 for k,v in kd.items() if k not in ('ftran','btran','refactorization')))
    c('events',ed['refactor_other']==1 and ed['correction_attempt']==kd['btran']-1 and 0<=ed['correction']<=ed['correction_attempt'] and all(v==0 for k,v in ed.items() if k not in ('refactor_other','correction_attempt','correction')))
    c('driver_crosscheck',r['all_passed'] is True and bool(r['checks']) and all(v is True for v in r['checks'].values()))
    details[mode]={'kernel_deltas':kd,'event_deltas':ed,'arrays':sum(len(x['arrays']) for x in (b,a,f)),'entries':sum(len(y['values']) for x in (b,a,f) for y in x['arrays'].values())}
def main():
    p=json.loads((RUN/'process.json').read_text());pins=json.loads((RUN/'pins.json').read_text())
    check('exit',p['returncode']==0 and p['reason']=='exit0' and p['pins_unchanged'] is True)
    check('pins',all(sha(path)==r['sha256'] and str(Path(path).resolve())==r['resolved'] for path,r in pins['inventory'].items()))
    check('pin_manifest',sha(RUN/'pins.json')==p['pins_sha256'])
    samples=[json.loads(x) for x in (RUN/'resources.jsonl').read_text().splitlines()]
    check('resources',bool(samples) and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 and x['elapsed']<=121 for x in samples))
    try:
        s=tomllib.loads((RUN/'raw/summary.toml').read_text())
        check('summary',s['cases']==2 and s['all_passed'] is True and s['source']==sha(HERE.parent/'S5-F/driver-reviewed.jl'))
        source=(ROOT/'src/simplex_diagnostics.jl').read_text()
        events=re.findall(r':(\w+)',source.split('const SIMPLEX_EVENT_REASONS = (',1)[1].split(')',1)[0])
        kernels=['ftran','btran','pricing','row_index','refactorization','crash','hypersparse_setup','hypersparse_support','hypersparse_base_graph','hypersparse_upper_graph']+[f'hypersparse_{op}_{route}' for op in ('ftran','btran','pricing','bfrt','weight_ftran','weight_btran') for route in ('sparse','dense','empty')]
        check('source_keys',s['event_keys']==events and s['kernel_keys']==kernels)
        check('exact_files',{x.name for x in (RUN/'raw').iterdir()}=={'stop.toml','throw.toml','summary.toml'})
        for mode in ('stop','throw'):
            try:case(mode,s)
            except Exception as e:check(mode+'.complete',False);details[mode+'_error']=repr(e)
    except Exception as e:check('raw_complete',False);details['raw_error']=repr(e)
    payload={'checks':checks,'all_passed':all(checks.values()),'details':details,'pin_count':len(pins['inventory']),'raw_sha256':{str(x):sha(x) for x in RUN.rglob('*') if x.is_file()}}
    with (HERE/'audit.json').open('x') as f:json.dump(payload,f,indent=2);f.write('\n')
    print(json.dumps({'checks':len(checks),'all_passed':payload['all_passed'],'false':[k for k,v in checks.items() if not v]}))
    return 0 if payload['all_passed'] else 1
if __name__=='__main__':sys.exit(main())
