"""Future standalone post-launch integrity/full-session closure; no Julia."""
import sys
import common as C
def main(phase):
 r=C.out(phase);a=C.read(r/'audit.json');seal=C.read(r/'seal.json');attempt=C.read(r/'attempt.json');ad=C.read(attempt['admission_path'])
 C.require(a['accepted'] is True and a['test_summary']==dict(Pass=272,Total=272),'canonical cost stage not accepted')
 C.require(all(C.sha(p)==h for p,h in a['bindings'].items()),'audited files changed')
 C.check_inventory(C.read(r/'pins.json'),C.required_paths(phase))
 h=C.host();C.require(not h['still_active_current_launcher'] and h['conflicts']==[] and set(h['checked_groups'])==C.expected_groups(phase,h['boot_id'],True),'full postexit group/session closure')
 C.require(h['refs']['HEAD']==seal['head'],'postexit admitted HEAD changed')
 paths={str(p) for p in r.rglob('*') if p.is_file()};paths.update((attempt['admission_path'],ad['review_report']))
 C.fresh(r/'closed.json',dict(accepted=True,phase=phase,head=seal['head'],host=h,bindings={p:C.sha(p) for p in sorted(paths)},scope='standalone evidence integrity/full launcher-guard-child closure; independent result review remains required'))
 print('FULL PHASE CLOSED',phase,len(h['checked_groups']),'groups ANDsessions')
if __name__=='__main__':
 C.require(len(sys.argv)==2,'phase required');main(sys.argv[1])
