from pathlib import Path
import tomllib
import sys
paths = [Path(x) for x in sys.argv[1:]]
if not paths:
    paths = sorted((Path(__file__).resolve().parents[1] / 'results/phase-one').glob('*.toml'))
for path in paths:
    r=tomllib.loads(path.read_text())
    trials={};closed=[];overlaps=[];latest_start={}
    for x in r['records']:
        key=x['workspace']; event=x['event']
        if event=='pricing_dantzig':
            assert key not in trials,(path,'unclosed trial',x)
            trials[key]=x
            latest_start[key]=x['iteration']
        if event=='perturbation' and latest_start.get(key)==x['iteration']:
            overlaps.append(x['iteration'])
        if event in ('pricing_progress_return','pricing_trial_expired'):
            start=trials.pop(key)
            duration=x['observations']-start['observations']
            assert duration<=256,(path,duration)
            if event=='pricing_trial_expired': assert duration==256,(path,duration)
            closed.append((event,duration))
        if event=='pricing_phase_reset':
            trials.pop(key,None)
            assert not x.get('temporary',False)
            assert x.get('observations',0)==0
    stable=[x for x in r['records'] if x['event']!='final_observed_workspace']
    print(path.name,'status',r['status'],'closed',len(closed),'open',len(trials),'overlaps',overlaps,
        'last_trace',[(x['iteration'],x['objective']) for x in stable[-1:]])
