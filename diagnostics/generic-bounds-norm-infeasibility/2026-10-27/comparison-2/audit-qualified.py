from pathlib import Path
import sys,json,tomllib,statistics as st,math,re
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));import common as c
c.unchanged();p=c.read('output/process.json');co=c.read('contract.json');done=c.read('../correctness-qualification/completed.json');qual=c.read('../correctness-qualification/audit.json');c.need(done['accepted'] and qual['accepted'] and qual['assertions']==15881 and qual['measured_windows']==0 and p['returncode']==1 and p['pins_unchanged'],'qualifiedcostdata/originalexit1')
s=c.read('supervisor.json');gate=c.read('output/gate.json');cur=c.read('output/current.json');permit=c.read('output/permit.json')
c.need(s['accepted'] is False and s['returncode']==1 and not s['soft_timeout'] and not s['hard_timeout'] and 'cleanup_error' not in s and s['elapsed_seconds']<600 and s['guard_identity']==p['runner'] and p['command']==co['command'],'preservedexpectedfailure/supervisor')
c.need(gate['identity']==p['child']==cur['child'] and gate['parent']==p['runner']==cur['runner'],'identities')
c.need(gate['command']==permit['command']==cur['command']==co['command'] and gate['parent_death_signal']==9,'entrycommand/signal')
c.need(gate['current_sha256']==c.sha(D/'output/current.json')==permit['current_sha256'] and gate['permit_sha256']==c.sha(D/'output/permit.json'),'gate links')
c.need(c.sha(D/'output/pins.json')==c.sha(D/'pins.json')==p['pins_sha256'],'actual pins')
c.put('audit-qualified-host.json',c.host([p[k][v] for k in ['runner','child'] for v in ['pgid','sid']]))
log=(D/'output/run.log').read_text();c.need('BOUNDS_NORM_INFEASIBILITY_COMPLETE' not in log and 'Error During Test' not in log,'preservedfailedordinaryrun')
failures=re.findall(r'Test Failed at (.*?):(\d+)',log);c.need(failures==[(str(D/'extra-tests.jl'),'13')]*18,'onlyexact18badexpectedcaps')
row=re.search(r'^Bounds norm infeasibility whole-function comparison\s*\|\s*(\d+)\s+(\d+)\s+(\d+)\s',log,re.M);c.need(row and list(row.groups())==['51891','18','51909'],'originalfailedsummary')
chunks=re.split(r'^CONTEXT (.+)$',log,flags=re.M)
for i in range(1,len(chunks),2):
 label,body=chunks[i],chunks[i+1];wanted=2 if label.startswith('BF') and any(':'+m+'}' in label for m in ['Nearest','Up','FromZero']) else 0
 c.need(body.count('Test Failed at ')==wanted,'failurecontexts')
data=tomllib.loads((D/'output/results.toml').read_text());contexts=[(f'BF{b}_RoundingMode{{:{m}}}()','BigFloat') for b in [64,128,256] for m in ['Nearest','Down','Up','ToZero','FromZero']]+[(t,t) for t in ['Float32','Float64','Rational{BigInt}','Rational{Int64}']];expected=[]
for label,t in contexts:
 for n in [16,64]:
  for den in ['sparse','dense']:
   for shape in (['positive','negative','mixed'] if t=='BigFloat' else ['mixed']):
    for arm,scopes in [('A',['snap','step','ratio']),('B',['norm','init','solve'])]:
     for scope in scopes:expected.append((label,t,n,den,shape,scope,arm,True,'finite'))
 for n in [16,64]:
  for den in ['sparse','dense']:
   for below in [True,False]:
    for mode in ['finite','one_sided','zero_tol']:expected.append((label,t,n,den,'positive','cert','C',below,mode))
c.need(len(data['cells'])==len(expected)==1632,'exact grid length');fields=['seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds'];summary=[];gc=0
for cell,key in zip(data['cells'],expected):
 c.need(tuple(cell[k] for k in ['context','type','n','density','shape','scope','variant','below','mode'])==key,'ordered grid')
 c.need(cell['id']=='/'.join(str(x).lower() if type(x) is bool else str(x) for x in [key[0],*key[2:]]),'exactcellid')
 raw=cell['windows'];c.need(len(raw)==18,'18windows')
 for pair in range(1,10):
  q=raw[(pair-1)*2:pair*2];c.need([w['pair'] for w in q]==[pair,pair] and [w['arm'] for w in q]==(['original',cell['variant']] if pair%2 else [cell['variant'],'original']),'pair order')
  c.need(q[0]['sink']==q[1]['sink'],'consumed outputs')
 for w in raw:
  for f in fields:c.need(type(w[f]) in [int,float] and math.isfinite(w[f]) and w[f]>=0,'finitecost')
  c.need(type(w['bytes']) is type(w['events']) is int and w['compile_seconds']==w['recompile_seconds']==0,'typedcounters/compilezero');gc+=w['gc_seconds']>0
 a=[w for w in raw if w['arm']=='original'];b=[w for w in raw if w['arm']==cell['variant']];q={k:v for k,v in cell.items() if k!='windows'}
 for f in ['seconds','bytes','events']:
  ratios=[b[i][f]/a[i][f] if a[i][f] else 1 if b[i][f]==0 else math.inf for i in range(9)];med=st.median(ratios)
  q[f]=dict(before=st.median(w[f] for w in a),after=st.median(w[f] for w in b),paired_median=med,paired_min=min(ratios),paired_max=max(ratios),paired_MAD=st.median(abs(x-med) for x in ratios))
 summary.append(q)
prep=data['preparation'];c.need(len(prep)==1632+38,'allprep');c.need([x['cell'] for x in prep if 'cell' in x]==[x['id'] for x in data['cells']],'orderedpreplink');c.need([(x['context'],'correctness' if 'correctness' in x else 'GC') for x in prep if 'cell' not in x]==[(label,phase) for label,t in contexts for phase in ['correctness','GC']],'contextpreplink')
for x in prep:
 if 'cell' not in x:continue
 c.need(len(x['cold'])==2 and len(x['warm'])==6 and len(x['resets'])==18,'completeprep')
 for z in [x['fixture'],x['validation'],*x['resets'],*[v for w in x['cold']+x['warm'] for v in [w['cost'],w['reset']]]]:
  for f in fields:c.need(type(z[f]) in [int,float] and math.isfinite(z[f]) and z[f]>=0,'validprep')
resources=[json.loads(l) for l in (D/'output/resources.jsonl').read_text().splitlines()];c.need(resources and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in resources),'resources')
c.put('summary-qualified.json',summary);c.put('audit-qualified.json',dict(accepted=True,original_run_accepted=False,raw_original_failures=18,qualification_assertions=15881,cases=1632,windows=29376,assertions=15881,original_assertions_passed=51891,gc_windows=gc,elapsed_shared_seconds=s['elapsed_seconds'],compiled_zero=True,allprep=True,postexit_auditor_not_launchpin=True,bindings={str(D/n):c.sha(D/n) for n in ['admission.json','contract.json','pins.json','output/process.json','output/results.toml','output/run.log','summary-qualified.json','../correctness-qualification/audit.json','../correctness-qualification/extra-corrected.jl']}))
print('QUALIFIED COSTDATA, originalrunFAILED18oracles;',15881,'qualifiedchecks',1632,'cells',29376,'windows','GC',gc)
