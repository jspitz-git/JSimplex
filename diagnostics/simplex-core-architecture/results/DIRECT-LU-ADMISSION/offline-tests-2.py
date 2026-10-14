"""Pure-helper/fake-record tests only. No subprocess/guard/Julia launch."""
from control import *
import guard,copy,tempfile
from unittest.mock import patch
checks={}
def rejects(name,fn):
    try:fn()
    except (ValueError,FileNotFoundError):checks[name]=True
    else:checks[name]=False
cfg=rd(D/'config.json')
for phase in ('red','green'):
    c=phase_config(phase)
    rows=[dict(name=e['name'],**dict(zip(('pass','fail','error','broken'),e['counts'])),expected=e['counts'],counts_match=True) for e in c['groups']]
    raw=dict(phase=phase,completed=True,all_expected=True,fatal='',loaded_path=str(Path(c['project'])/'src/JSimplex.jl'),groups=rows)
    checks[phase+'_valid_raw']=raw_ok(raw,phase,c)
    for key,value in [('completed',False),('all_expected',False),('fatal','unexpected'),('loaded_path','/wrong'),('phase','other')]:
        bad=copy.deepcopy(raw);bad[key]=value;checks[phase+'_reject_'+key]=not raw_ok(bad,phase,c)
    for kind in ('missing','wrong_count','reordered','error'):
        bad=copy.deepcopy(raw)
        if kind=='missing':bad['groups']=[]
        elif kind=='wrong_count':bad['groups'][0]['pass']+=1
        elif kind=='reordered':bad['groups'][0]['name']='wrong'
        else:bad['groups'][0]['error']=1
        checks[phase+'_'+kind]=not raw_ok(bad,phase,c)
rejects('unknown_phase',lambda:phase_config('retry'))
with tempfile.TemporaryDirectory() as td:
    p=Path(td)/'input';p.write_text('bound');pin=Path(td)/'pins';pin.write_text('manifest')
    required=[str(p)];review=dict(accepted=True,findings=[],pins_sha256=sha(pin),sha256={str(p):sha(p)})
    validate_review(review,pin,required);checks['valid_review']=True
    for name,mutate in [('unaccepted',lambda v:v.update(accepted=False)),('finding',lambda v:v.update(findings=['P2'])),('wrong_manifest',lambda v:v.update(pins_sha256='bad')),('missing_required',lambda v:v.update(sha256={})),('extra_binding',lambda v:v['sha256'].update(extra='bad'))]:
        bad=copy.deepcopy(review);mutate(bad);rejects(name,lambda:validate_review(bad,pin,required))
    p.write_text('changed');rejects('changed_required',lambda:validate_review(review,pin,required))
    p.write_text('bound');pins=dict(files=[str(p)],trees=[],inventory=guard.inventory([str(p)],[]))
    checks['pins_valid']=guard.pins_match(pins);p.write_text('change');checks['pins_changed']=not guard.pins_match(pins)
    import audit as auditor
    with patch.object(auditor,'D',Path(td)),patch.object(auditor,'phase_config',return_value=dict(output=str(Path(td)/'absent'))):
        result=auditor.audit('red');checks['missing_raw_process_rejected']=result['all_passed'] is False and result['checks']['complete_records'] is False
    record=Path(td)/'exclusive';save(record,{'first':True})
    try:save(record,{'second':True})
    except FileExistsError:checks['exclusive_record_preserved']=rd(record)=={'first':True}
    else:checks['exclusive_record_preserved']=False
# Validate every prepared selection and candidate overlay inverse using bytes only.
W=Path(rd(D/'staging.json')['root']);a=b'include("huangfu_hall_factorization.jl")\n';b=b'include("factor-export.jl")\ninclude("direct-factor.jl")\n'
checks['overlay_exact_inverse']=(W/'candidate/src/JSimplex.jl').read_bytes().replace(a+b,a)==(W/'reference/src/JSimplex.jl').read_bytes()
checks['focused_exact_slices']=all((D/'focused'/v['output']).read_bytes()==(R/v['source']).read_bytes()[v['start_byte']:v['end_byte']] for v in rd(D/'staging.json')['focused'])
checks['counts_sum']=sum(g['counts'][0] for g in cfg['phases']['green']['groups'])==19527
save(D/'offline-tests.json',dict(all_passed=all(checks.values()),checks=checks,scope='Synthetic Python pure helpers/temporary files only; no Julia or numerical replay'))
print(json.dumps({'passed':sum(checks.values()),'checks':len(checks)}))
req(all(checks.values()),'offline checks failed')
