from pathlib import Path
import sys,json,re,ast,tomllib
E=Path(__file__).resolve().parent;D=E.parent/'DIRECT-BG-DYNAMIC-COST-PREPARATION';sys.path.insert(0,str(D));import control_reviewed as c
r=D/'runs/cost1-300';checks={}
def ck(n,v):
 checks[n]=bool(v)
 if not v:raise RuntimeError(n)
rv=c.rd(r/'result-review.json');actual={str(p) for p in r.rglob('*') if p.is_file() and p.name!='result-review.json'}
ck('result_exact_membership',set(rv['sha256'])==actual and c.bindings(rv) and c.bindings(rv,'evidence_sha256'))
p=c.rd(E/'independent-result-proof-v1.json');su=c.rd(E/'supplement.json');ck('proof_and_supplement',c.bindings(p) and c.bindings(su) and p['all_passed'] and su['all_passed'])
ck('stats_agreement',[z['statistics'] for z in p['cells']]==[z['statistics'] for z in su['cells']])
report=(E/'REPORT.md').read_text();rows=[l for l in report.splitlines() if l.startswith('| sparse') or l.startswith('| dense')]
ck('table_count',len(rows)==8)
for row,z in zip(rows,su['summary']):
 fields=[a.strip() for a in row.strip('|').split('|')]
 ck('table_'+z['fixture']+z['backend'],fields[0]==z['fixture'] and fields[1]==z['backend'] and fields[2]==f"{z['time_ratio']:.4f}" and fields[3]==str(z['faster_pairs'])+'/7' and all(fields[i]==' → '.join(f'{int(a):,}' for a in z[k]) for i,k in [(4,'bytes'),(5,'events'),(6,'final_graph')]))
 failed=[k.replace('_gate','') for k,v in z['gates'].items() if not v]
 ck('failed_'+z['fixture']+z['backend'],fields[7]==(', '.join(failed) if failed else 'none'))
dense=[z for z in su['summary'] if z['fixture']=='dense96'];ck('growth',all(z['max_capacity']==6984 and z['max_live']==4656 and z['probe_counters'][1:4]==[2,65184,651840] for z in dense))
ck('paired_outliers',[[round(t,4) for t in z['ratio_range']] for z in dense]==[[0.2696,2.8582],[0.2036,3.3430]] and [round(z['ratio_mad'],5) for z in dense]==[0.07051,0.12345])
ck('nested_dense96',[[[round(z['nested_seconds'][i][s]['median']*1e6,1) for s in ['reference','candidate']] for i in [3,1,2]] for z in dense]==[[[758.9,173.4],[72.8,152.4],[56.7,95.3]],[[751.8,178.7],[74.3,155.5],[54.7,96.2]]])
ck('process_report',su['process']['resource_samples']==12 and su['process']['min_available_kib']==22160068 and su['process']['max_swap_used_kib']==0 and su['process']['measured_nonzero_gc_windows']==5 and su['process']['child_maxrss_kib']==801764)
ck('scope',su['first_process_cost_viable'] is False and rv['performance_accepted'] is False and rv['no_second_process'] is True and rv['scope']=='dynamic BG first cost diagnostic result' and c.rd(r/'audit.json')['all_passed'] is False)
ck('preserved_draft',(E/'postcheck.py').is_file() and not (E/'postcheck.json').exists())
c.validate_environment();c.validate_sources();c.preparation();ck('clean',not c.git('diff','--name-only') and not c.git('diff','--cached','--name-only'))
S=c.R/'diagnostics/simplex-core-architecture/STATUS.md';ROAD=c.R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md';mapping={S:E/'STATUS.md.before-COST1',ROAD:E/'roadmap.md.before-COST1'}
ck('before_bytes',all(a.read_bytes()==b.read_bytes() for a,b in mapping.items()));maps=[]
for record in [D/'closure.json',D/'publication.json']:
 j=c.rd(record)
 for key,table in [('sha256',j['sha256']),('git_blobs',j.get('git_blobs',{}))]:
  for name,v in table.items():
   dest=c.path(name);old=mapping.get(dest,dest);assert (c.sha(old) if key=='sha256' else c.git('hash-object','--',str(old)))==v
   if dest in mapping:maps.append(dict(record=str(record),field=key,target=str(dest),preserved=str(old),value=v))
ck('six_maps',len(maps)==6)
ck('no_closure_or_publication',not any((E/n).exists() for n in ['closure.json','publication.json','closure-host.json','continuation-map.json']))
for n in ['close.py','publish.py']:ast.parse((E/n).read_text())
ck('python_syntax',True)
ck('no_second_attempt',{x.name for x in (D/'runs').iterdir()}=={'cost1-300'})
h=c.full_host(c.rd(r/'posthost.json')['groups']);ck('host',len(h['groups'])==234 and not h['matches'])
proof=dict(all_passed=True,checks=checks,continuation_maps=maps,host=h,scope='New offline closure review; close.py/publish.py not executed',sha256={str(q):c.sha(q) for q in [E/'REPORT.md',E/'continuation-next.md',E/'close.py',E/'publish.py',E/'supplement.json',E/'independent-result-proof-v1.json',r/'result-review.json']})
c.save(E/'independent-closure-proof-v1.json',proof)
print(json.dumps(dict(all_passed=True,checks=len(checks),maps=len(maps))))
