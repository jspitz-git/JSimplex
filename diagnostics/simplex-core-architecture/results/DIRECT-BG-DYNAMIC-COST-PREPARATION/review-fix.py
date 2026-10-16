"""One offline fix pass into separate successors; initial manifest stays frozen."""
from pathlib import Path
E=Path(__file__).resolve().parent
def put(n,s):
 with (E/n).open('x') as f:f.write(s)
modules=['analysis','control','evidence','audit','seal','launch','close','publish']
for name in modules:
 s=(E/(name+'.py')).read_text()
 for m in ['control','analysis','evidence','audit']:s=s.replace('from '+m+' import','from '+m+'_reviewed import')
 if name=='analysis':
  s+='''

def first_process_viable(a,fixtures):
 # Conservative stop rule for the fixed ALL-EIGHT-cell second process.
 if a.get('all_passed') is not True or a.get('pure_timeout') is not False:return False
 cells=a.get('cells',[])
 expected=[(f['name'],'BG',b,'threshold_one' if b=='native' else 'default') for f in fixtures for b in ['native','markowitz']]
 if len(cells)!=8 or len(expected)!=8:return False
 for c,identity in zip(cells,expected):
  if tuple(c.get(k) for k in ['fixture','manager','backend','policy'])!=identity:return False
  st=c.get('statistics',{})
  if not all(st.get(k) is True for k in ['time_median_gate','allocation_gate','memory_gate','probe_memory_gate']):return False
  faster=st.get('faster_pairs')
  if type(faster) is not int or not 3<=faster<=7:return False
 return True
'''
 if name=='control':
  s=s.replace('import guard','import guard\nfrom analysis_reviewed import first_process_viable').replace("D/'preparation-pins.json'","D/'preparation-pins-reviewed.json'").replace("D/'required-paths.json'","D/'required-paths-reviewed.json'")
  anchor="require(a.get('all_passed') is True and a.get('pure_timeout') is False,'First cost integrity/numerical/compile gates')"
  if s.count(anchor)!=1:raise RuntimeError('stop anchor')
  s=s.replace(anchor,anchor+"\n  require(first_process_viable(a,rd(D/'inputs.json')['fixtures']),'Stop: first-process costs cannot qualify fixed eight-cell second process')")
 if name=='evidence':
  old="""    if end in names:
     require(len(rows)==20 and tomllib.loads((out/end).read_text())==dict(identity,windows=20),'Cell completion')
     for pair in range(1,11):
      a,b=rows[2*(pair-1):2*pair];require(a['outputs']==b['outputs'] and a['modes']==b['modes'],'Direct bitwise paired outputs/modes')
     visited.add(end);finished+=1"""
  new="""    # Every completed pair is checked even before cell completion/timeout.
    for pair in range(1,len(rows)//2+1):
     a,b=rows[2*(pair-1):2*pair];require(a['outputs']==b['outputs'] and a['modes']==b['modes'],'Direct bitwise paired outputs/modes')
    if end in names:
     require(len(rows)==20 and tomllib.loads((out/end).read_text())==dict(identity,windows=20),'Cell completion')
     visited.add(end);finished+=1"""
  if s.count(old)!=1:raise RuntimeError('pair anchor')
  s=s.replace(old,new)
 if name=='close':s=s.replace("D/'continuation-next.md'","D/'continuation-next-reviewed.md'")
 put(name+'_reviewed.py',s)
s=(E/'REPORT.md').read_text()
s=s.replace('the second primary process completes the prespecified two-process comparison even when the first performance gates are negative, provided integrity/numerical/compile gates and independent result review pass.','the fixed full second primary process is refused unless ALL eight first-process cells pass time/allocation/final-and-probe memory gates and each has at least3/7faster pairs (so10/14remains attainable), alongside accepted integrity/numerical/compile result and independent review. A negative first-process gate stops this candidate; no reduced workload or post-output narrowing is prepared.')
s+='''
## Canonical correction after rejected review

The initial preparation1826pins/report/controls and rejected independent review remain unchanged and SUPERSEDED, UNEXECUTED. Canonical future commands are seal_reviewed.py/launch_reviewed.py, importing control_reviewed.py, evidence_reviewed.py, audit_reviewed.py and analysis_reviewed.py. Canonical inventory is preparation-pins-reviewed.json/required-paths-reviewed.json; closure/publication are close_reviewed.py/publish_reviewed.py. The original cost.jl/probe/stage/inputs are unchanged.

P1: every completed pair is checked even in an unfinished-cell timeout prefix; signed-zero output or allowed-mode mismatch is never pure timeout. P2: fixed all-eight-cell second process requires all first-process gates plus attainable faster-pair count; otherwise stop, with no partial second process or tuning. This conservative all-eight prerequisite may leave a potentially promising individual backend unqualified when another fails; it avoids further work under this fixed protocol and does not prove that other backend cannot improve. New regression RED preserved three expected missing checks before separate fixes. Full new offline tests and independent final amendment review are required before acceptance. This fixes experimental validation/admission only, with no Julia or production/candidate edits.
'''
put('REPORT-reviewed.md',s)
s=(E/'continuation-next.md').read_text().replace('Second primary process reverses order and requires independently accepted first correctness/integrity/compile result; negative cost gates remain evidence, not permission to tune.','Second primary process reverses order and requires independently accepted first correctness/integrity/compile result AND ALL eight first-process time/allocation/final-and-probe-memory gates with at least3/7faster pairs each. Otherwise stop; no partial second process/tuning. Completed pairs are checked even in partial timeout prefixes.')
s+='\nCanonical controls: seal_reviewed.py/launch_reviewed.py with control_reviewed/evidence_reviewed/audit_reviewed/analysis_reviewed; preparation-pins-reviewed.json/required-paths-reviewed.json. Report REPORT-reviewed.md. Initial1826manifest/report/controls/rejectedreview preserved SUPERSEDED UNEXECUTED; never use them for launch.\n'
put('continuation-next-reviewed.md',s)
print('Separate canonical successors written; originals unchanged')
