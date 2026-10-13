"""Prepared only. Refuses without separately bound numerical allowance."""
from common import *
def main():
 # Logs are reserved before validation so pre-output refusal is preserved.
 with (D/'launcher.log').open('x') as log:
  record={'started_ns':time.time_ns(),'command':guard_command(),'returncode':None}
  try:
   assert sys.argv==[str(D/'launcher.py'),'run']
   a=read(D/'allowance.json');pins=read(D/'launch-pins.json')
   assert allowance_valid(a,sha(D/'launch-pins.json'),current_refs())
   assert 'ACCEPTED S2-D numerical admission.' in (D/'numerical-review.md').read_text()
   assert str(D/'numerical-review.md') in a['sha256'] and sha(D/'numerical-review.md')==a['sha256'][str(D/'numerical-review.md')]
   assert manifest_ok(pins,read(D/'required-paths.json'))
   extra={str(D/n) for n in ('admission-pins.json','review.md','reviewer-check.json')}
   assert extra.issubset(pins['inventory'])
   host=absent();record['host']=host;assert not host['matches'];assert not OUT.exists()
   dump(D/'attempt-reserved.json',dict(time_ns=time.time_ns(),command=command(),output=str(OUT),pins_sha256=sha(D/'launch-pins.json'),allowance_sha256=sha(D/'allowance.json')))
   record['reservation_sha256']=sha(D/'attempt-reserved.json')
   run=subprocess.run(guard_command(),cwd=OVERLAY,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   record['returncode']=run.returncode
  except BaseException as e:record['error']=repr(e)
  finally:record['ended_ns']=time.time_ns();dump(D/'invocation.json',record)
 return 0 if record.get('returncode')==0 and 'error' not in record else 1
if __name__=='__main__':sys.exit(main())
