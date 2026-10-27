from pathlib import Path
import sys,json,re
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));import common as c
c.unchanged();co=c.read('contract.json');p=c.read('output/process.json');s=c.read('supervisor.json');done=c.read('completed.json');log=(D/'output/run.log').read_text()
c.need(p['returncode']==0 and p['pins_unchanged'] and s['accepted'] and done['accepted'],'guard/exit/pins')
c.need(p['command']==co['command'] and p['pins_sha256']==c.sha(D/'pins.json') and s['guard_identity']==p['runner'],'command/runner')
g=c.read('output/gate.json');cur=c.read('output/current.json');pm=c.read('output/permit.json');c.need(g['identity']==p['child']==cur['child'] and g['parent']==p['runner']==cur['runner'],'entryidentities');c.need(g['command']==pm['command']==cur['command']==co['command'] and g['parent_death_signal']==9,'entrycommand');c.need(g['current_sha256']==c.sha(D/'output/current.json')==pm['current_sha256'] and g['permit_sha256']==c.sha(D/'output/permit.json'),'entrylinks')
c.need(c.sha(D/'output/pins.json')==c.sha(D/'pins.json'),'copiedpins')
c.need('Test Failed at ' not in log and 'Error During Test' not in log and log.count('BNI_CORRECTNESS_QUALIFICATION_COMPLETE')==1,'ordinarysuccess')
row=re.search(r'^Bounds norm certificate correctness qualification\s*\|\s*(\d+)\s+(\d+)\s',log,re.M);c.need(row and row[1]==row[2]=='15881','exactordinary15881')
c.need(co['cases']==co['measured_windows']==0 and len(co['command'])==9,'no measurement driver/windowargument')
resources=[json.loads(l) for l in (D/'output/resources.jsonl').read_text().splitlines()];c.need(resources and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in resources),'resources')
c.put('audit-host.json',c.host([p[k][v] for k in ['runner','child'] for v in ['pgid','sid']]))
c.put('audit.json',dict(accepted=True,assertions=15881,measured_windows=0,elapsed_shared_seconds=done['elapsed_shared_seconds'],original_comparison_remains_failed=True,bindings={str(D/n):c.sha(D/n) for n in ['admission.json','pins.json','driver.jl','extra-corrected.jl','oracle-correction.json','output/process.json','output/run.log']}))
print('PASS15881 correctnessonly/no measuredwindows')
