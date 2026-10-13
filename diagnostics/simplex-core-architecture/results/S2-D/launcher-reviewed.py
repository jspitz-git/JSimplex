"""Prepared only. Refuses without separately bound numerical allowance."""
from common_reviewed import *
def require(condition,message):
 if not condition:raise ValueError(message)
def main():
 # Logs are reserved before validation so pre-output refusal is preserved.
 with (D/'launcher.log').open('x') as log:
  record={'started_ns':time.time_ns(),'command':guard_command(),'returncode':None}
  try:
   require(sys.argv==[str(D/'launcher-reviewed.py'),'run'], "admission gate rejected")
   a=read(D/'allowance.json');pins=read(D/'launch-pins.json')
   require(allowance_valid(a,sha(D/'launch-pins.json'),current_refs()), "admission gate rejected")
   require('ACCEPTED S2-D numerical admission.' in (D/'numerical-review.md').read_text(), "admission gate rejected")
   require(str(D/'numerical-review.md') in a['sha256'] and sha(D/'numerical-review.md')==a['sha256'][str(D/'numerical-review.md')], "admission gate rejected")
   require(manifest_ok(pins,read(D/'required-paths-reviewed.json')), "admission gate rejected")
   extra={str(D/n) for n in ('admission-pins-reviewed.json','final-review.md','final-review-check.json')}
   require(extra.issubset(pins['inventory']), "admission gate rejected")
   host=absent()
   record['host']=host
   require(not host['matches'], "admission gate rejected")
   require(not OUT.exists(), "admission gate rejected")
   dump(D/'attempt-reserved.json',dict(time_ns=time.time_ns(),command=command(),output=str(OUT),pins_sha256=sha(D/'launch-pins.json'),allowance_sha256=sha(D/'allowance.json')))
   record['reservation_sha256']=sha(D/'attempt-reserved.json')
   run=subprocess.run(guard_command(),cwd=OVERLAY,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   record['returncode']=run.returncode
  except BaseException as e:record['error']=repr(e)
  finally:record['ended_ns']=time.time_ns();dump(D/'invocation.json',record)
 return 0 if record.get('returncode')==0 and 'error' not in record else 1
if __name__=='__main__':sys.exit(main())
