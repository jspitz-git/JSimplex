"""Independent final offline SHA/AST checker; no reviewed module is executed."""
from pathlib import Path
import ast,hashlib,json,subprocess
E=Path(__file__).resolve().parent;R=E.parents[3]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True).strip()
def path(n):return Path(n) if Path(n).is_absolute() else R/n
checks={}
def ck(n,b):
 checks[n]=bool(b)
 if not b:raise AssertionError(n)
m=E/'preparation-pins-reviewed.json';new=rd(m);old=rd(E/'preparation-pins.json');rej=rd(E/'review-rejected-v1.json')
ck('1855_membership',len(new['sha256'])==1855 and set(new['sha256'])==set(rd(E/'required-paths-reviewed.json')['paths']))
ck('all1855_sha256',all(sha(path(n))==h for n,h in new['sha256'].items()))
ck('1826_preserved',len(old['sha256'])==1826 and all(new['sha256'].get(n)==h and sha(path(n))==h for n,h in old['sha256'].items()))
ck('original_manifest_preserved',rej['pins_sha256']==sha(E/'preparation-pins.json'))
ck('rejected_review_preserved',sha(E/'review-rejected-v1.json')=='8b281d7070d2e8380551b45eb3db8edf91e4ce8913a7bf06cacccda38a7d88d9' and all(sha(path(n))==h for n,h in rej['evidence_sha256'].items()))
ck('v1_complete_review_bound',rd(E/'independent-review-proof-v1.json')['all_checks_passed'] is True and len(rd(E/'independent-review-proof-v1.json')['checks'])==46)
ck('head_master_unchanged',git('rev-parse','HEAD')=='0601df628f30ee3f226066d5ace9ab16928193aa' and git('rev-parse','master')=='26e2291745999f485a74f643298ca997d65c7205')
ck('no_tracked_diff',not git('diff','--name-only') and not git('diff','--cached','--name-only'))
ck('no_runs_or_phase_files',not (E/'runs').exists() and all(not (E/n).exists() for n in ['sealed.json','reservation.json','closure.json','publication.json','review.json']))
# Canonical utility changes are exact, so prior review remains applicable.
for n in ['audit','seal','launch','publish']:
 before=(E/(n+'.py')).read_text()
 for a,b in [('from control import','from control_reviewed import'),('from evidence import','from evidence_reviewed import'),('from analysis import','from analysis_reviewed import'),('from audit import','from audit_reviewed import')]:before=before.replace(a,b)
 ck('exact_wiring_'+n,before==(E/(n+'_reviewed.py')).read_text())
before=(E/'close.py').read_text().replace('from control import','from control_reviewed import').replace("'continuation-next.md'","'continuation-next-reviewed.md'")
ck('exact_close_correction',before==(E/'close_reviewed.py').read_text())
oldanalysis=(E/'analysis.py').read_text();analysis=(E/'analysis_reviewed.py').read_text()
ck('old_analysis_preserved',analysis.startswith(oldanalysis))
control=(E/'control_reviewed.py').read_text()
ck('canonical_preparation_bound',"m=D/'preparation-pins-reviewed.json'" in control and "rd(D/'required-paths-reviewed.json')" in control)
ck('second_process_requires_viability',"require(first_process_viable(a,rd(D/'inputs.json')['fixtures']),'Stop: first-process costs cannot qualify fixed eight-cell second process')" in control)
fn=next(n for n in ast.parse(analysis).body if isinstance(n,ast.FunctionDef) and n.name=='first_process_viable')
expected='''def first_process_viable(a,fixtures):
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
ck('all_eight_identity_four_gates_faster_ast',ast.dump(fn,include_attributes=False)==ast.dump(ast.parse(expected).body[0],include_attributes=False))
# Pair comparison now belongs to a complete-pair loop outside cell completion.
fn=next(n for n in ast.parse((E/'evidence_reviewed.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='output_checks');parents={c:n for n in ast.walk(fn) for c in ast.iter_child_nodes(n)}
calls=[n for n in ast.walk(fn) if isinstance(n,ast.Call) and any(isinstance(x,ast.Constant) and x.value=='Direct bitwise paired outputs/modes' for x in n.args)]
ck('one_pair_oracle',len(calls)==1);n=calls[0];conditions=[];loops=[]
while n in parents:
 n=parents[n]
 if isinstance(n,ast.If):conditions.append(ast.unparse(n.test))
 if isinstance(n,ast.For):loops.append(ast.unparse(n.iter))
ck('pair_oracle_not_completion_conditional','end in names' not in conditions)
ck('all_complete_pairs_loop','range(1, len(rows) // 2 + 1)' in loops)
ck('both_bits_and_modes',ast.unparse(calls[0].args[0])=="a['outputs'] == b['outputs'] and a['modes'] == b['modes']")
red=rd(E/'fix-red.json');green=rd(E/'fix-green.json')
ck('red_three_missing_preserved',red['all_passed'] is False and {n for n,v in red['checks'].items() if not v}=={'partial_reject_outputs','partial_reject_modes','first_process_stop_gate'})
ck('green33_with_regressions',green['all_passed'] is True and len(green['checks'])==33 and all(green['checks'].values()) and green['checks']['partial_reject_outputs'] and green['checks']['partial_reject_modes'])
for n,count in [('offline-tests-reviewed.json',91),('prefix-tests-reviewed.json',23),('review-fix-check.json',10)]:
 j=rd(E/n);ck('saved_'+n,j['all_passed'] is True and len(j['checks'])==count and all(j['checks'].values()))
for p in E.glob('*.py'):ast.parse(p.read_text())
ck('all_python_ast',True)
# Existing approved stage and original direct/candidate files are unchanged via
# initial manifest; verify stage membership and all source hashes freshly too.
s=rd(E/'stages.json')['cost'];S=Path(s['path'])
ck('stage83_exact',len(s['sha256'])==83 and {str(p.relative_to(S)) for p in S.rglob('*') if p.is_file()}==set(s['sha256']) and all(sha(S/n)==h for n,h in s['sha256'].items()))
maps=rd(E/'author-check.json')['maps']
ck('six_GREEN_maps',len(maps)==6 and all(rd(i['record'])[i['field']][i['key']]==i['value'] and (sha(i['preserved']) if i['field']=='sha256' else git('hash-object','--',i['preserved']))==i['value'] for i in maps))
# Fresh host scan, no process signaling. Permission-limited exe reads recorded.
groups=set(rd(E/'host.json')['groups']);matches=[];unreadable=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  fields=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip();exe=''
  try:exe=str((p/'exe').resolve(strict=True))
  except PermissionError:unreadable.append(int(p.name))
  except FileNotFoundError:pass
  if int(fields[2]) in groups or int(fields[3]) in groups or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):matches.append(int(p.name))
 except (FileNotFoundError,ProcessLookupError):pass
ck('232groups_sessions_noJulia',len(groups)==232 and not matches)
ck('all_existing_local_files_bound',all(str(p) in new['sha256'] or p==m or p.name in ['independent-final-check.py','independent-final-review.md'] for p in E.iterdir() if p.is_file()))
proof=dict(all_passed=True,checks=checks,pin_count=1855,pins_sha256=sha(m),initial_pin_count=1826,initial_rejection_sha256=sha(E/'review-rejected-v1.json'),pair_oracle_conditions=conditions,pair_oracle_loops=loops,host=dict(groups=sorted(groups),matches=matches,unreadable_exe_pids=unreadable,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip()),scope='Final offline pin/AST/source review; no reviewed program execution, no Julia, no closure or publication')
with (E/'independent-final-proof.json').open('x') as f:json.dump(proof,f,indent=2);f.write('\n')
print('Independent final',len(checks),'PASS;1855pins; findings corrected; noJulia')
