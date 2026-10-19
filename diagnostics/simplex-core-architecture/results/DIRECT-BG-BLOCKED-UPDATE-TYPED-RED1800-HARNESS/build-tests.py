from pathlib import Path
import json
D=Path(__file__).resolve().parent;P=D.with_name('DIRECT-BG-BLOCKED-UPDATE-TYPED-HARNESS')
s=(P/'tests.py').read_text();edits=[]
def sub(old,new,count=None):
 global s
 n=s.count(old)
 if count is not None and n!=count:raise RuntimeError(repr(old)+' '+str(n))
 if not n:raise RuntimeError('Missing '+repr(old))
 s=s.replace(old,new);edits.append(dict(old=old,new=new,count=n))
sub("('red300','green300')","('red1800',)",2)
sub("phase=='red300'","phase=='red1800'")
sub('o.validate(p,S,LOADED,phase)',"o.validate(p,S,LOADED,'red300')",1)
sub('fixture(phase)',"fixture('red300')")
sub('logfile(phase,p)',"logfile('red300',p)",1)
sub('logfile(phase,fixture_data)',"logfile('red300',fixture_data)",1)
sub('o.warning_log(log,p,phase)',"o.warning_log(log,p,'red300')",1)
sub('o.warning_log(log+bad,p,phase)',"o.warning_log(log+bad,p,'red300')",1)
sub("'ABSENT 28'),p,phase)","'ABSENT 28'),p,'red300')",1)
sub("validate(q,phase))\n  check('red_missing_failure_log'","validate(q,phase))\n  check('red_missing_failure_log'",1)
sub("'REMOVED'),p,phase)","'REMOVED'),p,'red300')",1)
sub("cfg['payload'],cfg['stage'],phase]","cfg['payload'],cfg['stage'],'red300']",1)
sub("cfg['seconds']==300","cfg['seconds']==1800",1)
sub("('p011-red300','p011-green300','red600','',None)","('red300','green300','green1800','p011-red300','p011-green300','red600','',None)",1)
sub('seconds=300','seconds=1800',2)
sub("('elapsed_including_launch',293)","('elapsed_including_launch',1793)",1)
sub("('elapsed_seconds',301)","('elapsed_seconds',1801)",1)
sub("with patch.object(c,'rd',lambda _: {'all_passed':False}):refuse('green_missing_accepted_red',lambda:c.predecessor('green300'))\ncheck('red_no_predecessor',c.predecessor('red300')==([],[]))", "refuse('green_not_prepared',lambda:c.predecessor('green300'))\npf,pg=c.predecessor('red1800');check('timeout_lineage_81_full289',len(pf)==81 and len(pg)==289)\nwith patch.object(c,'rd',lambda _: {'sha256':{},'review':'prior'}):refuse('malformed_timeout_receipt',lambda:c.validate_timeout_record())",1)
sub("scope='BG blocked typed exact-run admission',phase='red300'","scope='BG blocked typed RED repeat exact-run admission',phase='red1800'",1)
anchor="result=dict(all_passed=True,count=len(checks),checks=checks,"
extra="""# New time-only boundary cases preserve numerical predicates and strict schemas.
for value in (300.5,1792.0,1800.0):
 p=fixture('red300')
 for n in o.PREPARATION:
  for k in o.METRICS-{'bytes','events'}:p[n][k]=value
 check('extended_cost_valid_'+str(value),validate(p,'red1800')['expected_failures']==6)
for value in (1800.000001,True,float('inf'),float('nan')):
 p=fixture('red300');p['cost-2.toml']['seconds']=value
 refuse('extended_cost_invalid_'+repr(value),lambda p=p:validate(p,'red1800'))
mem=dict(available_kib=8*1024**2,swap_used_kib=0)
check('resource1792boundary',a.resource_records([dict(mem,elapsed=1792.)],mem,1792.))
refuse('resource1792exceeded',lambda:a.resource_records([dict(mem,elapsed=1792.1)],mem,1792.1))
# Actual process success can extend beyond300, with all unchanged accounting gates.
def long_success(run,out,payload):
 edit(out/'process.json','elapsed_including_launch',1792.)
 edit(run/'invocation.json','elapsed_seconds',1800.)
 p=run/'invocation.json';v=json.loads(p.read_text());v['supervisor']['elapsed_seconds']=1800.;p.write_text(json.dumps(v))
 (out/'resources.jsonl').write_text(json.dumps(dict(mem,elapsed=1792.))+'\\n')
full_case('red1800','long_boundary_success',long_success,success=True)
"""
sub(anchor,extra+anchor,1)
with (D/'tests.py').open('x') as f:f.write(s)
with (D/'test-transform.json').open('x') as f:json.dump(dict(source=str(P/'tests.py'),edits=edits),f,indent=2);f.write('\n')
print('New standard-library synthetic tests prepared')
