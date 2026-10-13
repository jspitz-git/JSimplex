"""UNEXECUTED: ONE attempt only after recorded human authorization and sealed review."""
from common import *
def main():
 with (D/'launcher.log').open('x') as log:
  record={'started_ns':time.time_ns(),'command':guard_command(),'returncode':None}
  try:
   require(sys.argv==[str(D/'launcher.py'),'run'],'exact launcher invocation required')
   pins=read(D/'launch-pins.json');a=read(D/'allowance.json');ph=sha(D/'launch-pins.json')
   require(allowance_ok(a,ph,refs()),'new numerical allowance or bindings missing')
   review=(D/'numerical-review.md').read_text()
   require('ACCEPTED S4-AB numerical admission.' in review and ph in review,'numerical admission not bound to launch manifest')
   required=read(D/'required-paths.json')
   require(manifest_ok(pins,required),'launch pins differ')
   require({str(D/n) for n in FINAL_NAMES}.issubset(pins['inventory']),'missing final admission dependencies')
   host=absent();record['host']=host
   require(not host['matches'],'prior groups/sessions or Julia alive')
   require(not OUT.exists(),'attempt output already exists')
   dump(D/'attempt-reserved.json',{'time_ns':time.time_ns(),'command':command(),'output':str(OUT),'pins_sha256':ph,'allowance_sha256':sha(D/'allowance.json'),'refs':refs()})
   record['reservation_sha256']=sha(D/'attempt-reserved.json')
   run=subprocess.run(guard_command(),cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   record['returncode']=run.returncode
   if (OUT/'process.json').is_file():
    p=read(OUT/'process.json');extra=[p[k]['pgid'] for k in ('runner','child') if k in p]
    record['post_host']=absent(extra)
    require(not record['post_host']['matches'],'post-run groups/sessions or Julia remain')
  except BaseException as e:record['error']=repr(e)
  finally:record['ended_ns']=time.time_ns();dump(D/'invocation.json',record)
 return 0 if record.get('returncode')==0 and 'error' not in record else 1
if __name__=='__main__':sys.exit(main())
