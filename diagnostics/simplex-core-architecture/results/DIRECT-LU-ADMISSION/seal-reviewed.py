"""Future one-shot stage sealing ONLY. Does not launch Julia or reserve a run."""
from control_reviewed import *
from evidence_reviewed import validate_predecessor
import guard,sys

def main(phase):
    config=phase_config(phase);base=D/'preparation-pins-reviewed.json';pins=rd(base)
    review=D/'preparation-review-final.json'
    validate_review(rd(review),base,rd(D/'required-reviewed.json'))
    req(guard.pins_match(pins),'Preparation pins changed')
    groups=rd(D/'host.json')['groups'];extra=[]
    if phase=='green':
        extra=validate_predecessor()
        groups+=rd(D/'red-posthost.json')['groups']
    fresh=host(groups);req(not fresh['matches'],'Live prior groups/sessions or Julia')
    req(fresh['master']==rd(D/'host.json')['master'],'Master changed')
    req(subprocess.run(['git','merge-base','--is-ancestor',rd(D/'host.json')['head'],'HEAD'],cwd=R).returncode==0,'Unrelated HEAD')
    req(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'Tracked working changes')
    save(D/(phase+'-seal-host.json'),fresh)
    files=sorted(set(pins['files'])|{str(base),str(review),str(D/(phase+'-seal-host.json'))}|{str(p) for p in extra})
    sealed=dict(files=files,trees=pins['trees'],inventory=guard.inventory(files,pins['trees']),inputs=[],created=time.time(),phase=phase,head=fresh['head'],master=fresh['master'],boot_id=fresh['boot_id'])
    save(D/(phase+'-sealed-pins.json'),sealed)
    print('SEALED ONLY: independent stage admission must bind this exact manifest before launch.')
if __name__=='__main__':main(sys.argv[1])
