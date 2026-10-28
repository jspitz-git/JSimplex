from pathlib import Path
import sys,json,shutil,ast
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-epsilon-bound-auxiliary/2026-10-28');P=D/'MASTER-run';sys.path.insert(0,str(P));import common as c
p=c.read('output/process.json');c.need(p['returncode']==1 and p['pins_unchanged'] is True,'finished failed master');extra=[p[k][v] for k in ['runner','child'] for v in ['pgid','sid']];h=c.host(extra);h['diagnostic_head']=c.git(['rev-parse','HEAD'],c.R);h['master_head']=c.git(['rev-parse','HEAD']);c.put('failed-close-host.json',h);c.unchanged()
s=(P/'audit.py').read_text();s=s.replace("need(p['returncode']==c['expected_exit'] and p['pins_unchanged'] is True,'child exit/pins')","need(p['returncode']==1 and p['pins_unchanged'] is True,'preserved failed actualMASTER exit/pins')")
s=s.replace("done=read('completed.json')","done=dict(accepted=False,elapsed_shared_seconds=s['elapsed_seconds'])")
s=s.replace("need(s['accepted'] is True and s['returncode']==0 and not s['soft_timeout'] and not s['hard_timeout'] and 'cleanup_error' not in s,'supervisor')","need(s['accepted'] is False and s['returncode']==1 and not s['soft_timeout'] and not s['hard_timeout'] and 'cleanup_error' not in s,'honest failed test supervisor')")
s=s.replace("need(done['accepted'] is True and done['elapsed_shared_seconds']<=4500 and s['elapsed_seconds']<=4500,'inclusive4500deadline')","need(not (D/'completed.json').exists() and s['elapsed_seconds']<=4500,'no accepted completion; bounded failed supervisor')")
a=s.index(" fields=header.split('|',1)");b=s.index(" resources=[json.loads",a)
s=s[:a]+''' fields=header.split('|',1)[1].split();need(fields==['Pass','Fail','Total','Time'],'exact failed ordinary summary, no errors/broken/skips')
 columns=line.split('|',1)[1].split();need(columns[:3]==['380370','2','380372'] and len(columns)==4,'exact rejected MASTER root')
 pass_count,fails=380370,2
 need(c['expected_failures']==0 and c['expected_total']==380372,'original all-pass expectation preserved')
 locations=[[path,int(n)] for path,n in re.findall(r'Test Failed at (.*?):(\\d+)',log)]
 need(locations==[[str(Path(c['source_root'])/'test/generic_unit_perturb_residual_tests.jl'),581],[str(Path(c['source_root'])/'test/generic_dual_comparisons_tests.jl'),709]],'only two known oldcost failures')
 need('EBA_COMPLETED MASTER' not in log,'no successful completion marker')
'''+s[b:]
s=s.replace("put('audit-host.json'","put('failure-audit-host.json'").replace("put('audit.json'","put('failure-audit.json'").replace("read('audit.json')","read('failure-audit.json')").replace('dict(accepted=True,arm=',"dict(accepted=False,audit_completed=True,production_qualification_rejected=True,original_expected_failures=0,arm=")
s=s.replace("expected_failures=fails","actual_failures=fails").replace("elapsed_shared_seconds=done['elapsed_shared_seconds']","failed_supervisor_elapsed_seconds=s['elapsed_seconds']").replace("'audit.py','contract.json'","'failure-postcheck.py','audit.py','audit-failure.log','contract.json'")
ast.parse(s);(P/'failure-postcheck.py').write_text(s);shutil.copyfile(__file__,D/'failed-master-close.py');print('Actual685group host closed; original failed audit preserved; strict rejected-result postcheck prepared')
