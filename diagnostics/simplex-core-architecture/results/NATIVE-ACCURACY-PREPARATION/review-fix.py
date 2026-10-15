"""One separate offline repair after rejected review; preserve original evidence."""
from common import *
import re,ast
D=F;J=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/stdlib/v1.13/SparseArrays/src/solvers');u=(J/'umfpack.jl').read_text();lib=(J/'LibSuiteSparse.jl').read_text();w=(J/'wrappers.jl').read_text()
req(rd(D/'review.json')['accepted'] is False,'Initial rejection must exist')
names=['driver.jl','guard.py','evidence.py','seal.py'];report=R/'diagnostics/simplex-core-architecture/NATIVE-ACCURACY-PREPARATION.md'
paths=[D/n for n in names]+[report];mapping={}
for p in paths:
 before=D/((p.name if p!=report else 'report')+'.before-review');req(not before.exists(),'Before exists');before.write_bytes(p.read_bytes());mapping[str(p)]=dict(preserved=str(before),sha256=sha(before))
red=dict(namespace='API.UMFPACK_STRATEGY_USED' in (D/'driver.jl').read_text() and 'UMFPACK_STRATEGY_USED,' not in u,resident_highwater="'VmHWM:'" not in (D/'guard.py').read_text() and 'child_maxrss_kib' not in (D/'guard.py').read_text())
req(all(red.values()),'Expected source RED')
p=D/'driver.jl';t=p.read_text().replace('const API=SparseArrays.UMFPACK','const API=SparseArrays.UMFPACK\nconst CAPI=SparseArrays.LibSuiteSparse').replace('API.UMFPACK_','CAPI.UMFPACK_');p.write_text(t)
p=D/'guard.py';t=p.read_text().replace("('VmRSS:', 'VmPeak:', 'VmSwap:')","('VmRSS:', 'VmHWM:', 'VmPeak:', 'VmSwap:')").replace("record['returncode'] = child.returncode","record['returncode'] = child.returncode\n                record['child_maxrss_kib'] = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss");p.write_text(t)
p=D/'evidence.py';t=p.read_text();marker="def phase_checks(phase):"
helper='''def memory_report(resources,p):
 peak=p['child_maxrss_kib'];req(type(peak) in (int,float) and math.isfinite(peak) and peak>0,'Terminal resident highwater')
 rows=[]
 for sample in resources:
  values={}
  for line in sample.get('child_memory',[]):
   name,value,unit=line.split();req(name in ('VmRSS:','VmHWM:','VmPeak:','VmSwap:') and unit=='kB' and name[:-1] not in values,'Memory metadata');values[name[:-1]]=int(value);req(values[name[:-1]]>=0,'Memory nonnegative')
  if values:
   req(set(values)=={'VmRSS','VmHWM','VmPeak','VmSwap'} and values['VmRSS']<=values['VmHWM']<=peak,'RSS/HWM metadata');rows.append(values)
 req(rows,'No sampled process memory')
 return dict(samples=rows,child_maxrss_kib=peak,scope='Fresh guard RUSAGE_CHILDREN after reaping its sole child; sampled VmHWM resident, VmPeak virtual. Not native allocation/free balance.')
'''
t=t.replace('import guard','import guard,math').replace(marker,helper+marker).replace("result=analyze(raw,","mem=memory_report(resources,p)\n result=analyze(raw,").replace(" checks['diagnostic_integrity']=True"," result['process_memory']=mem\n checks['resident_memory']=True\n checks['diagnostic_integrity']=True");p.write_text(t)
p=D/'seal.py';t=p.read_text().replace("D/'preparation-pins.json'","D/'preparation-pins-reviewed.json'").replace("D/'review.json'","D/'review-final.json'").replace("D/'required-paths.json'","D/'required-paths-reviewed.json'");p.write_text(t)
report.write_text(report.read_text()+'''\n## Separate preparation review amendment\n\nInitial independent review rejected two preparation defects: uppercase Info\nconstants were not imported into SparseArrays.UMFPACK, and the reused guard\nrecorded VmPeak (virtual) without resident HWM. Original driver/guard/evidence/\nseal/report and manifest/review remain preserved. The corrected driver obtains\nall constant indices from SparseArrays.LibSuiteSparse, which defines wrappers.jl.\nNo function calls, controls, fixtures or numerical budgets changed. The guard\nadds sampled VmHWM and terminal RUSAGE_CHILDREN.ru_maxrss after reaping its sole\nchild. The auditor reports resident and virtual data separately, validates\nRSS<=HWM<=terminal maxrss and retains all samples. Sampling/terminal reads are\noutside Julia cost regions; no added production work or memory.\n\nCanonical preparation now uses preparation-pins-reviewed.json,\nrequired-paths-reviewed.json and review-final.json; the future seal.py reads\nthose exact artifacts. Original preparation-pins.json/review.json remain\nrejected history, with changed source/report keys mapped only to before-review\ncopies in review-fix.json. Original source20/30+24+31 Python checks are retained,\nbut initial namespace and memory claims are insufficient without this amendment.\nNo Julia/native execution occurred during either preparation or repair.\n''')
checks=dict(source_RED=all(red.values()),constant_owner='include("wrappers.jl")' in lib and all('const '+n+' =' in w for n in re.findall(r'CAPI\.(UMFPACK_\w+)',(D/'driver.jl').read_text())),no_unbound_API_constant='API.UMFPACK_' not in (D/'driver.jl').read_text().replace('CAPI.UMFPACK_',''),same_driver_except_owner=(D/'driver.jl').read_text().replace('\nconst CAPI=SparseArrays.LibSuiteSparse','').replace('CAPI.UMFPACK_','API.UMFPACK_')==(D/'driver.jl.before-review').read_text(),sampled_HWM="'VmHWM:'" in (D/'guard.py').read_text(),terminal_maxrss='resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss' in (D/'guard.py').read_text(),new_seal_paths=all(n in (D/'seal.py').read_text() for n in ('preparation-pins-reviewed.json','required-paths-reviewed.json','review-final.json')),original_before_preserved=all(sha(v['preserved'])==v['sha256'] for v in mapping.values()))
for p in D.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
checks['Python_syntax']=True
save(D/'review-fix.json',dict(all_passed=all(checks.values()),checks=checks,RED=red,mappings=mapping,sha256={str(p):sha(p) for p in paths+[Path(__file__),J/'LibSuiteSparse.jl',J/'wrappers.jl',J/'umfpack.jl']},scope='Source-derived RED/GREEN, not Julia parsing or runtime qualification'))
req(all(checks.values()),'Review fix failed; preserve');print(len(checks),'PASS')
