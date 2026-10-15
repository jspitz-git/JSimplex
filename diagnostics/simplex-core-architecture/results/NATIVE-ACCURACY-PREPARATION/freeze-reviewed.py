"""Separate manifest for corrected offline preparation; original remains frozen."""
from control import *
import guard
old=rd(D/'preparation-pins.json');fix=rd(D/'review-fix.json')
req(fix['all_passed'] and rd(D/'review-fix-tests.json')['all_passed'],'Fix rejected')
extra=['driver.jl.before-review','guard.py.before-review','evidence.py.before-review','seal.py.before-review','report.before-review','review.json','review.md','reviewer-check.initial.py','reviewer-check.initial.json','reviewer-check.py','reviewer-check.json','review-fix.py','review-fix.json','review-fix-tests.py','review-fix-tests.json','preparation-pins.json','required-paths.json','freeze-reviewed.py']
required=sorted(set(rd(D/'required-paths.json'))|{str(D/n) for n in extra})
save(D/'required-paths-reviewed.json',required)
files=sorted(set(old['files'])|set(required)|{str(D/'required-paths-reviewed.json')})
pins=dict(files=files,trees=[],inventory=guard.inventory(files,[]),inputs=old['inputs'],created=time.time(),scope='Corrected OFFLINE preparation only; exact numerical stage seal and admission still required')
save(D/'preparation-pins-reviewed.json',pins);print(dict(required=len(required),inventory=len(pins['inventory'])))
