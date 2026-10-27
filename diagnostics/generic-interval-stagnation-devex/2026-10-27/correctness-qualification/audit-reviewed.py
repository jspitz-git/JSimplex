from pathlib import Path
import json,re,sys
sys.path.insert(0,str(Path(__file__).resolve().parent));import common_reviewed as c
D=c.D;p=c.read('output/process.json');s=c.read('supervisor.json');co=c.read('contract.json');done=c.read('completed.json');gate=c.read('output/gate.json');cur=c.read('output/current.json');permit=c.read('output/permit.json');res=c.read('reservation.json');log=(D/'output/run.log').read_text()
c.need(p['returncode']==0 and p['pins_unchanged'] is True and s['accepted'] is True and done['accepted'] is True,'successful complete qualification')
c.need(not s['soft_timeout'] and not s['hard_timeout'] and 'cleanup_error' not in s and s['returncode']==0,'supervised normal exit')
c.need(p['command']==co['command'] and p['pins_sha256']==c.sha(D/'pins-reviewed.json')==c.sha(D/'output/pins.json'),'command/pins')
c.need(s['guard_identity']==p['runner']==gate['parent']==cur['runner'] and gate['identity']==p['child']==cur['child'],'entry full identities')
c.need(gate['command']==permit['command']==cur['command']==co['command'] and gate['parent_death_signal']==9,'entry command/signal')
c.need(gate['current_sha256']==permit['current_sha256']==c.sha(D/'output/current.json') and gate['permit_sha256']==c.sha(D/'output/permit.json'),'entry hash links')
c.need(res['guard_deadline']==res['started_monotonic']+592 and res['outer_deadline']==res['started_monotonic']+600 and done['elapsed_shared_seconds']<=600 and s['elapsed_seconds']<=600,'shared deadline')
a=re.search(r'^Corrected exact oracle and active precision qualification\s*\|\s*(\d+)\s+(\d+)\s+',log,re.M)
c.need(a and int(a[1])==int(a[2])==15213,'exact all-pass ordinary count')
header=next(x for x in log.splitlines() if x.startswith('Test Summary:') and '|' in x);c.need(header.split('|',1)[1].split()==['Pass','Total','Time'],'no broken/errors/skips')
c.need('ISD_CORRECTNESS_QUALIFICATION_COMPLETE' in log and 'Test Failed at ' not in log and 'Error During Test' not in log and not re.search(r'^ERROR:',log,re.M),'ordinary completion without failures')
resources=[json.loads(x) for x in (D/'output/resources.jsonl').read_text().splitlines()];c.need(resources and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in resources),'all resources');c.need(p['terminal_memory']['available_kib']>=6*1024**2 and p['terminal_memory']['swap_used_kib']<=1024**2,'terminal memory')
c.unchanged();extra=[p[k][v] for k in ['runner','child'] for v in ['pgid','sid']];c.put('audit-host.json',c.host(extra));c.put('audit.json',dict(accepted=True,assertions=15213,comparison_measurement_rerun=False,elapsed_seconds=done['elapsed_shared_seconds'],bindings={str(D/n):c.sha(D/n) for n in ['output/run.log','output/process.json','pins-reviewed.json','audit-reviewed.py','fixtures.jl','tests.jl']}));print('PASS',15213,'all ordinary correctness checks; no cost remeasurement')
