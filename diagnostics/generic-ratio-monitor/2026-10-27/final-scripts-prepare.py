from pathlib import Path
import shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-ratio-monitor/2026-10-27');O=D.parents[1]/'generic-interval-stagnation-devex/2026-10-27'
shutil.copyfile(O/'finalization_checks.py',D/'finalization_checks.py')
s=(O/'diagnostic-publish.py').read_text().replace('generic-interval-stagnation-devex','generic-ratio-monitor').replace('import common as c','import common_complete as c').replace('Record interval monitor and Devex scalar savings','Record BigFloat ratio and stagnation scalar savings').replace('Preserve corrected whole-function comparison, rejected original diagnostics, exact RED/GREEN and actual-master qualification, independent reviews and immutable historical mappings.','Preserve the whole-function comparison, offline rejected harness preparations, exact RED/GREEN and actual-master qualification, independent reviews and immutable historical mappings.')
(D/'diagnostic-publish.py').write_text(s)
s=(O/'closure.py').read_text().replace('generic-interval-stagnation-devex','generic-ratio-monitor').replace('import common as c','import common_complete as c')
a=s.index("reviews=[");b=s.index("checks['all_independent_reviews_bound']",a)
s=s[:a]+'''reviews=['admission-complete.json','result-review.json','production-review.json','publication-preparation-reviewed.json','commit-review.json','RED-run/admission.json','RED-run/result-review.json','GREEN-run/admission.json','GREEN-run/result-review.json','MASTER-run/admission.json','MASTER-run/result-review.json','final-review.json']
for n in reviews:
 r=c.read(n);c.need(r['accepted'] is True and r['findings']==[],'review '+n)
 for p,h in r['bindings'].items():before(p,h)
c.need(c.read('admission.json')['accepted'] is False,'initial offline rejected admission preserved')
c.need(c.read('output/process.json')['returncode']==0 and c.read('output/process.json')['pins_unchanged'],'single accepted comparison')
'''+s[b:]
a=s.index('for phase,manifest in [');b=s.index(':\n pins=',a)
s=s[:a]+"for phase,manifest in [(D,n) for n in ['pins.json','pins-reviewed.json','pins-final.json','pins-ready.json','pins-complete.json']]+[(D/'RED-run','pins.json'),(D/'GREEN-run','pins.json'),(D/'MASTER-run','pins.json')]"+s[b:]
a=s.index("red=c.read('RED-run/audit.json')");b=s.index("check('unchanged_old_test'",a)
s=s[:a]+'''red=c.read('RED-run/audit.json');g=c.read('GREEN-run/audit.json');m=c.read('MASTER-run/audit.json');cmp=c.read('audit.json')
check('accepted_numerics',cmp['accepted'] is True and cmp['cases']==1225 and cmp['windows']==22050 and red['accepted'] is True and red['passed']==24721 and red['expected_failures']==4 and g['accepted'] is True and m['accepted'] is True and g['passed']==m['passed']==c.read('MASTER-run/contract.json')['expected_total'] and g['expected_failures']==m['expected_failures']==0)
'''+s[b:]
s=s.replace('measured_assertions=15213','measured_assertions=52721')
(D/'closure.py').write_text(s)
shutil.copyfile(__file__,D/'final-scripts-prepare.py')
print('closure and exactdiagnosticpublication prepared; unexecuted')
