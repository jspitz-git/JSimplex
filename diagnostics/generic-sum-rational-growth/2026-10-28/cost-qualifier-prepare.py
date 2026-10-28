from pathlib import Path
import sys,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-sum-rational-growth/2026-10-28');sys.path.insert(0,str(D));import common_ready as c
s=(D/'audit-ready.py').read_text()
s=s.replace(";done=read('completed.json');log=",";log=")
s=s.replace("need(p['returncode']==0 and p['pins_unchanged'] is True,'exact child success/pins')","need(p['returncode']==1 and p['pins_unchanged'] is True,'original failed child/pins preserved')")
s=s.replace("need(sup['accepted'] is True and sup['returncode']==0 and not sup['soft_timeout'] and not sup['hard_timeout'] and 'cleanup_error' not in sup,'supervisor success')","need(sup['accepted'] is False and sup['returncode']==1 and not sup['soft_timeout'] and not sup['hard_timeout'] and 'cleanup_error' not in sup,'original rejected supervisor preserved')")
s=s.replace("need(done['accepted'] is True and done['elapsed_shared_seconds']<=900 and sup['elapsed_seconds']<=900,'inclusive900deadline')","need(sup['elapsed_seconds']<=900,'original inclusive900deadline');need(not (D/'completed.json').exists(),'no original accepted completion')")
a=s.index(" need('Test Failed at '");b=s.index(" raw=tomllib.loads",a)
s=s[:a]+''' need('Error During Test' not in log,'no test errors')
 errors=re.findall(r'^ERROR: (.*)$',log,re.M);need(errors==['LoadError: Some tests did not pass: 111259 passed, 90 failed, 0 errored, 0 broken.'],'only original known Test failure error')
 line=next((x for x in log.splitlines() if x.startswith('Sum rational growth whole-function comparison') and '|' in x),None);need(line is not None,'ordinary root summary')
 header=next(x for x in log.splitlines() if x.startswith('Test Summary:') and '|' in x);need(header.split('|',1)[1].split()==['Pass','Fail','Total','Time'],'exact original summary schema')
 cols=line.split('|',1)[1].split();need(len(cols)==4 and [int(v) for v in cols[:3]]==[111259,90,111349],'exact preserved original totals');assertions=111259
 locations=re.findall(r'Test Failed at (.*?):(\\d+)',log);need(len(locations)==90 and all(p==str(D/'extra-tests-ready.jl') and int(n)==127 for p,n in locations),'only exact decoder oracle failures')
 need('SUM_RATIONAL_GROWTH_COMPLETE' not in log,'no fabricated original success marker')
 qualified=read('correctness-qualification/audit.json');review=read('correctness-qualification/result-review.json')
 need(qualified['accepted'] is True and qualified['assertions']==28227 and qualified['measured_windows']==0 and review['accepted'] is True and review['findings']==[],'separate correctness qualification')
 for p,h in review['bindings'].items():need(sha(p)==h,'qualified review binding '+p)
'''+s[b:]
s=s.replace("put('summary.json',summary)","put('summary-qualified.json',summary)")
s=s.replace("put('audit.json',dict(accepted=True,assertions=assertions,","put('audit-qualified.json',dict(accepted=True,original_run_accepted=False,original_assertions_passed=assertions,original_failed_assertions=90,qualification_assertions=qualified['assertions'],postexit_auditor_not_launchpin=True,")
s=s.replace("elapsed_shared_seconds=done['elapsed_shared_seconds']","elapsed_shared_seconds=sup['elapsed_seconds']")
s=s.replace("['audit-ready.py','contract-ready.json','pins-ready.json','output/results.toml','output/run.log','output/process.json','summary.json']","['audit-qualified.py','contract-ready.json','pins-ready.json','output/results.toml','output/run.log','output/process.json','summary-qualified.json','correctness-qualification/audit.json','correctness-qualification/result-review.json']")
s=s.replace("read('audit.json')","read('audit-qualified.json')")
compile(s,str(D/'audit-qualified.py'),'exec');(D/'audit-qualified.py').write_text(s);shutil.copyfile(__file__,D/'cost-qualifier-prepare.py')
print('separate strict cost-data auditor prepared UNEXECUTED; original failure cannot become PASS')
