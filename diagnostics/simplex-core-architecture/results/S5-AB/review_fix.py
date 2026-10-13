"""One offline correction of S5-O executed-test binding; all previous records stay intact."""
from pathlib import Path
import json,hashlib,tomllib,copy
R=Path.cwd();H=Path(__file__).resolve().parent;D=H.parent.parent;O=H.parent/'S5-O';pins={}
def rb(p):
 p=Path(p);b=p.read_bytes();pins[str(p)]=hashlib.sha256(b).hexdigest();return b
def js(p):return json.loads(rb(p))
def sh(b):return hashlib.sha256(b).hexdigest()
x=js(H/'reconciliation-2.json');old=next(v for v in x['integrations'] if v['stage']=='S5-O');driver=rb(O/'driver.jl').decode();actual='adaptive_pricing_lifecycle_tests.jl';red=old['test']!=actual
assert red and 'const O_TEST=joinpath(O_ROOT,"test","'+actual+'")' in driver
inv=js(O/'master-1/pins.json')['inventory'];raw=tomllib.loads(rb(O/'master-1/raw/report.toml').decode());b=rb(R/'test'/actual);values=[v['sha256'] for p,v in inv.items() if p.endswith('/test/'+actual)];new=copy.deepcopy(old);new.update(test=actual,current_sha256=sh(b),test_matches_all_launch_entries=bool(values) and all(v==sh(b) for v in values),raw_test_sha256=raw['test_sha256'],raw_suffix_sha256=raw['suffix_sha256'],driver_file_binding=True)
reviewed=copy.deepcopy(x['integrations']);reviewed[reviewed.index(old)]=new
checks=dict(RED_wrong_executed_file=red,GREEN_driver_names_actual_test='const O_TEST=joinpath(O_ROOT,"test","'+actual+'")' in driver,GREEN_actual_test_launch_identity=new['test_matches_all_launch_entries'],GREEN_raw_actual_test_identity=raw['test_sha256']==sh(b),GREEN_suffix_identity=raw['suffix_sha256']==sh(b[19080:]),GREEN_raw_passes42=raw['passes']==42 and raw['fails']==raw['errors']==raw['broken']==0,GREEN_other_five_records_unchanged=all(a==z for a,z in zip(x['integrations'],reviewed) if a['stage']!='S5-O'),GREEN_all_six_scoped_bindings=all(v['test_matches_all_launch_entries'] and all(z['matched'] for z in v['source']) for v in reviewed))
report=D/'S5-HANDOFF-COVERAGE-RECONCILIATION.md';before=rb(report)
with (H/(report.name+'.before-review')).open('xb') as f:f.write(before)
text=before.decode();text=text.replace('Current tests for I/O/U/AA/AC/AO match their actual-master launch inventories, as do','With the separate reviewed S5-O binding correction below, current tests for\nI/O/U/AA/AC/AO match their actual-master launch inventories, as do')
text=text.replace('Pins alone are never treated as execution. See results/S5-AB/reconciliation-2.json.','Pins alone are never treated as execution. See results/S5-AB/reconciliation-2.json\nand its separate review-fix.json amendment.\n\nThe initial independent review rejected one Important provenance error: the new\nS5-O record named adaptive_pricing_tests.jl, although the executed append lives in\nadaptive_pricing_lifecycle_tests.jl. The original ten checks,23 source checks and\neight author checks remain preserved; their O file-identity gate checked the wrong\nfile and is insufficient execution evidence. The before-review report and rejected\nreview are preserved. One new offline RED/GREEN correction binds the actual O driver,\nmaster launch inventory, raw whole-test/suffix hashes and42-pass report to the current\nlifecycle file; the other five records are unchanged. Eight supplemental checks pass.\nThis is no numerical rerun or retroactive change to any historical launch pin.')
assert text!=before.decode();report.write_text(text);rb(report);rb(H/'review_fix.py')
with (H/'review-fix.json').open('x') as f:json.dump(dict(checks=checks,all_passed=all(checks.values()),original_record=old,reviewed_integrations=reviewed,sha256=pins,before_report_sha256=sh(before)),f,indent=2);f.write('\n')
print(json.dumps(dict(checks=checks,bindings=len(pins))));assert all(checks.values())
