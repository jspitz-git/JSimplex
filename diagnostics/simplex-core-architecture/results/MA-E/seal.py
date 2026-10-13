"""MA-F-only sealing, no Julia launch. NEVER run in offline MA-E."""
import sys
sys.dont_write_bytecode=True
from control import *
def main():
 require(sys.argv==[str(D/'seal.py'),'seal'],'exact invocation')
 review=read(D/'review.json');require(review['accepted'] is True and review['unresolved_findings']==[],'accepted review required')
 require(review['pins_sha256']==sha(D/'admission-pins.json'),'review pins')
 require(all(sha(p)==h for p,h in review['sha256'].items()),'review inputs')
 pins=read(D/'admission-pins.json');require(inventory_ok(pins,read(D/'required-paths.json')),'pins')
 groups=read(D/'host.json')['groups'];h=host(groups);require(not h['matches'],'live groups/sessions')
 required={str(D/n) for n in ('admission-pins.json','required-paths.json','review.json','review.md','driver.jl','kernels.jl','auditor.py','control.py','guard.py','launcher.py','seal.py','admission.md')}
 save(D/'execution-seal.json',dict(accepted=True,stage='MA-F-attempt-1',attempts=1,refs=refs(),pin_sha256=sha(D/'admission-pins.json'),commands=[command(s) for s in STAGES],output=str(OUT),sha256={p:sha(p) for p in sorted(required)},host=h,human_authorization='User explicitly authorized short numerical attempts without asking again; 750s total, no retries.'))
if __name__=='__main__':main()
