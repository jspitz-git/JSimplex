"""Independent artifact verification and Czech delivery reports; never launches Julia."""
from pathlib import Path
import csv,datetime,fcntl,hashlib,json,math,re,tomllib
root=Path('/home/jspitz/JSimplex.jl')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
js=lambda p:json.loads(Path(p).read_text())
tm=lambda p:tomllib.loads(Path(p).read_text())
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
basekeys=('profile','pricing','mode','input_sha','options','status','original_feasible','primal_sha','objective_bits','iterations','refactors','mode_initial','mode_refactors','steps','entries')
certkeys=('certificate_calls','certificate_true','certificate_last')
metadata={};allprocess=[]
for name,expected_n,expected_b in [('legacy-pricing-check-reuse',143,88),('devex-quality-reset',34,12)]:
 p=root/'diagnostics'/name/'results'; plan=js(p/'plan.json'); assert js(p/'status.json')['state']=='finished';assert js(p/'skipped.json')==[]
 with (p/'suite.lock').open() as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 manifests={}
 for mn in ('sources.json','references.json'):
  if (p/mn).exists():
   pins=js(p/mn)
   for f,h in pins.items():assert sha(f)==h,f
   manifests[mn]=len(pins)
 prov=js(p/'source-provenance.json')
 for rel,h in prov['sources'].items():assert sha(root/rel)==h,rel
 jobs=plan['jobs']; assert len(jobs)==expected_n
 benches=[];audits=[];pcs=[];comps=0;unit_passes=0;red=0
 for profile,group,job in jobs:
  folder=p/profile/group; path=folder/(job+'.toml');d=tm(path);proc=js(folder/(job+'.process.json'));start=js(folder/(job+'.started.json'))
  assert proc['start']==start['start']<proc['end'];assert proc['locks']>=31
  pcs.append((proc['start'],proc['end'],profile,group,job));allprocess.append((proc['start'],proc['end'],name,job))
  if job in ('unit','off-unit','active-unit'):
   log=(folder/(job+'.log')).read_text()
   if job=='off-unit':
    assert proc['exit']==1 and d['expected_original_failure'] is True and d['passed'] is False
    assert d['ordinary_pivot_completed'] is True and d['iterations']==1 and 'Test Failed' in log and 'Error During Test' not in log;red+=1
   else:
    assert proc['exit']==0 and d['passed'] is True
    counts=[int(m[0]) for m in re.findall(r'\|\s*(\d+)\s+(\d+)\s+[0-9.]+s',log)];unit_passes+=sum(counts)
   continue
  assert proc['exit']==0 and proc.get('report_sha256',proc.get('report_sha'))==sha(path)
  assert d['status']=='OPTIMAL' and d['original_feasible'] is True
  assert d['threads']==d['blas_threads']==1 and d['arch']=='aarch64'
  assert math.isfinite(d['seconds']) and 0<d['loop']<=d['seconds']
  assert d['mode_initial']>=1 and d['mode_refactors']==d['refactors']
  expected_input=Path('/home/jspitz/mps/runtime.mps') if name.startswith('legacy') or group=='runtime' else p.parent/'reproduce'/(group+'.mps')
  assert d['input_sha']==sha(expected_input)
  comp=js(folder/(job+'.comparison.json'));assert all(x is True for x in comp.values() if isinstance(x,bool));comps+=1
  if 'report_sha256' in comp:assert comp['report_sha256']==sha(path)
  if 'report_sha' in comp:assert comp['report_sha']==sha(path)
  if name.startswith('legacy'):
   ref=tm(folder/'reference-audit.toml');assert all(d[k]==ref[k] for k in basekeys)
   if job=='shadow':
    a=tm(folder/'reference-audit.toml.audit.toml');b=tm(folder/'shadow.toml.audit.toml')
    assert all(a[k]==b[k] for k in ('sha256','modes','switches'))
    assert all(b['counts'][k]==v for k,v in a['counts'].items())
    assert all(b['pricing_counts'][k]==v for k,v in a['pricing_counts'].items())
   if '.' in job:benches.append((profile,group,job,d))
  else:
   assert d['certificate_last'] is True and d['certificate_true']>0
   ref=tm(folder/(d['arm']+'-audit.toml'))
   assert all(d[k]==ref[k] for k in basekeys+certkeys+('arm','quality_observed','quality_counts'))
   if job=='passive-audit':
    off=tm(folder/'off-audit.toml');a=tm(folder/'off-audit.toml.audit.toml');b=tm(folder/'passive-audit.toml.audit.toml')
    assert all(d[k]==off[k] for k in basekeys+certkeys)
    assert all(a[k]==b[k] for k in ('sha256','counts','modes','sampled_transitions'))
   if group=='runtime' and '.' in job:benches.append((profile,group,job,d))
  if job.endswith('-audit') or job=='shadow':
   a=tm(Path(str(path)+'.audit.toml'));assert len(a['modes'])==d['mode_initial']+d['mode_refactors'];audits.append((profile,group,job,d,a))
 assert len(benches)==expected_b
 assert all(a[1]<=b[0] for a,b in zip(pcs,pcs[1:]));assert [list(x[2:]) for x in sorted(pcs)]==jobs
 first=[(x[0],x[1],x[2].rsplit('.',1)[0]) for x in benches if x[2].endswith('.1')]
 second=[(x[0],x[1],x[2].rsplit('.',1)[0]) for x in benches if x[2].endswith('.2')];assert first[::-1]==second
 record=dict(checked_utc=now,manifests=manifests,production_hashes=sum(x.startswith('src/') for x in prov['sources']),original_hashes=len(prov['sources']),processes=len(pcs),process_exit_zero=len(pcs)-red,expected_original_red_exit_one=red,unit_pass_assertions=unit_passes,comparisons=comps,benchmarks=len(benches),audits=len(audits),all_optimal_original_feasible=True,exact_benchmark_endpoint_own_audit=True,independent_comparisons=True,reverse_second_repeat=True,no_process_overlap=True,no_skips=True,own_lock_free=True,runner_exit_zero_confirmed=True)
 if name.startswith('devex'):record['all_actual_original_certificates_true']=True
 v=js(p/'final-verification.json');v['delivery_verification']=record;(p/'final-verification.json').write_text(json.dumps(v,indent=2)+'\n')
 metadata[name]=(p,record,benches,audits)
allprocess.sort();assert all(a[1]<=b[0] for a,b in zip(allprocess,allprocess[1:]));print('Both series: no numerical process overlap')

def resources(benches):
 lines=['| Správce / pricing / rameno / repeat | Solve s | Smyčka s | GC s | Compile ms | Alokace | Bytes | Peak RSS MiB |','|---|---:|---:|---:|---:|---:|---:|---:|']
 for p,g,n,d in benches:lines.append(f"| {p} / {g} / {n} | {d['seconds']:.6f} | {d['loop']:.6f} | {d['gc']:.6f} | {d['compile']*1000:.6f} | {d['allocations']} | {d['bytes']} | {d['peak_rss_bytes']/2**20:.3f} |")
 return lines

p,rec,benches,audits=metadata['legacy-pricing-check-reuse'];v=js(p/'final-verification.json');coverage=list(csv.DictReader((p/'coverage.csv').open()))
lines=['# Přebírání kontrol pro Dantzig a DSE — závěrečný výklad','',
'Celá schválená série je dokončená: 11 jednotkových procesů, 44 plných auditů a 88 časovaných řešení runtime.mps. Všech 143 procesů skončilo exit0; 132 numerických comparison bylo znovu přepočteno původním summarizerem i nezávislou kontrolou. Všechna řešení jsou OPTIMAL s původní primal feasibility. 90 připnutých souborů, 76 původních zdrojových referencí včetně 71 produkčních souborů a vstupní SHA souhlasí. Žádný retry ani vyřazení.',
'',f"Jednotkové procesy: {rec['unit_pass_assertions']} úspěšných assertions celkem. Audity přepočítaly každý převzatý výsledek a zachovaly přesné původní event/guard hashe, počty, numerický endpoint, přechody pricingu a skutečný režim faktoru po refaktorizaci. Časované běhy ověřily endpoint, options/input/mode/factory počty proti vlastnímu auditu; nezaznamenávaly všechny mezistavy.",'',
'Všech pět produkčních správců zrychlilo pro oba pricingy v obou opakováních. U přímých režimů je výsledek méně stabilní. Normalizovaný FT s Dantzigem měl +4,08 % a −5,34 %, poměr průměrů −0,78 %: stabilní regresi ani malé zrychlení tento výsledek nedokládá. Přímý FT a přímý SS s Dantzigem také změnily znaménko. Normalizovaný SS s DSE měl −15,96 % a +0,77 %; první velký efekt není reprodukován. Windows jako konkrétní příčina kolísání nebyl prokázán; CPU vzorky nejsou měřením frekvence, teplot ani veškeré konkurence hostitele.','',
'Změna se týká celé duální smyčky včetně recovery, nikoli izolovaného kernelu. Nižší počet iterací zde rychlost nevysvětluje: odpovídající reference a kandidát mají shodnou trajektorii. DSE řádky jsou smíšené DSE→Devex běhy, nikoli čistý DSE po celou dobu.','',
'| Správce / pricing | Ref1 s | Cand1 s | Δ1 % | Ref2 s | Cand2 s | Δ2 % | Δ poměr průměrů % |','|---|---:|---:|---:|---:|---:|---:|---:|']
for key,t in v['verified'].items():
 if not key.endswith('/timing'):continue
 profile,pricing,_=key.split('/');ds={n:d for a,g,n,d in benches if a==profile and g==pricing};r1,c1,r2,c2=[ds[x]['loop'] for x in ('reference.1','candidate.1','reference.2','candidate.2')]
 lines.append(f"| {profile} / {pricing} | {r1:.6f} | {c1:.6f} | {t['deltas'][0]:+.3f} | {r2:.6f} | {c2:.6f} | {t['deltas'][1]:+.3f} | {t['ratio_of_means_percent']:+.3f} |")
lines+=['','## Skutečné pokrytí a práce','',
'Ve všech 11 DSE konfiguracích nastal živý přechod na Devex; přímý FT měl dva. Důvody a fáze jsou v původních auditních TOML. Cílené testy navíc vynucují oba důvody přechodu. Počty completed níže jsou dokončené duální pivoty na živém workspace; nemusí se rovnat všem solver iterations včetně dalších fází.',
'', '| Správce / pricing | Dantzig pivoty | DSE pivoty | Devex pivoty | Živé DSE→Devex | Převzatý row residual | Převzatá konečnost* | DSE weight reuse |','|---|---:|---:|---:|---:|---:|---:|---:|']
for c in coverage:lines.append('| '+' | '.join([c['profile']+' / '+c['pricing']]+[c[k] for k in ('completed_dantzig','completed_dse','completed_devex','dse_to_devex_live','row_reused','avoided_finite','common_dse_weight')])+' |')
lines+=['','*Převzatá konečnost je součet finite_reused/from_last_pivot/driver_entry; audity ji pro ověření přepočítávají. Tyto počty nejsou procenta zrychlení celého solveru.','',
'Kontrola práce a paměti: experiment rozšiřuje pouze způsobilost původního přebírání, nepřidává skeny, basis solves ani velké cache v běžném kroku. Mimo ověřenou způsobilost zůstávají původní kontroly, včetně konečnosti po změnách vah a původních podmínek Dantzigu. Nebyla nalezena nepotřebná dodatečná práce ani retenční paměť kandidátní změny. Měřicí factory kontroly/časovače jsou symetrické; instrumentované auditní kopie a hashování nejsou v benchmarku. Produkční integrace Dantzig/DSE touto sérií nebyla provedena.','',
'## Časy a prostředky všech benchmarků','',
'Warmup celé afiro a 100 iterací runtime je mimo měření. Solve zahrnuje setup, iterace, recovery i cleanup; smyčka zahrnuje vstupy do duální optimalizace. GC a kompilace jsou zahrnuté a neodečtené. Peak RSS zahrnuje warmup a následné kontroly, není retained memory samotné smyčky. Dvě opakování na jediném modelu omezují zobecnění.','']+resources(benches)
lines+=['','[Strojové ověření](final-verification.json) · [Páry a prostředky CSV](pairs.csv) · [Pokrytí CSV](coverage.csv)']
(p/'interpretation.md').write_text('\n'.join(lines)+'\n')

p,rec,benches,audits=metadata['devex-quality-reset'];v=js(p/'final-verification.json')
lines=['# Kontrola kvality Devex vah a obnova rámce — závěrečný výklad','',
'Obnova podle experimentálního poměru >9 na runtime.mps nepřinesla zrychlení. Zvýšila počet iterací a celé řešení zpomalila v obou opakováních: HH +16,30/+16,07 % (poměr průměrů +16,19 %), FT +14,10/+16,65 % (poměr průměrů +15,36 %). Tento kandidát se nedoporučuje k produkční integraci. Výsledek nevyvrací všechny možné strategie Devex obnovy; hodnotí pouze zvolený práh, ukazatel vybraného řádku a provedení resetu.',
'',f"34 procesů: dvě očekávaná původní RED selhání exit1, dvě GREEN jednotky ({rec['unit_pass_assertions']} assertions celkem), 12 celých smoke, 6 runtime auditů a 12 benchmarků. Ostatních 32 procesů exit0. Všech 30 numerických comparison znovu ověřeno, 89 source + 91 reference pinů a 71 produkčních zdrojů beze změny. Obě série byly sekvenční, Devex fronta začala až po ukončení legacy pricing měření. Žádný další solve při finalizaci.",
'',
'Off/passive mají přesně shodné původní event/guard/sample/end výsledky. Každý pozorovaný již vypočtený referenční součet byl v auditu samostatně přepočten ze skutečného tableau řádku. Active změnil trajektorii úmyslně; bitová shoda s off nebyla vyžadována. Každý OPTIMAL má samostatně true původní primal feasibility a skutečnou původní optimality certificate (last=true, truecalls>0), bez přidaného certifikačního volání. Benchmarky každého ramene odpovídají vlastnímu auditu v koncovém výsledku, počtech obnov, options/input/factory. Benchmarky neobsahují plnou interní stopu.',
'',
'| Správce / rameno | Ref1 solve s | Kandidát1 s | Δ1 % | Ref2 solve s | Kandidát2 s | Δ2 % | Δ průměr solve % | Δ průměr smyčka % |','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
for t in v['timing']:
 a,b=t['repeats'];lines.append(f"| {t['profile']} / {t['arm']} | {a['reference_seconds']:.6f} | {a['candidate_seconds']:.6f} | {a['solve_delta_percent']:+.3f} | {b['reference_seconds']:.6f} | {b['candidate_seconds']:.6f} | {b['solve_delta_percent']:+.3f} | {t['mean_solve_ratio_percent']:+.3f} | {t['mean_loop_ratio_percent']:+.3f} |")
lines+=['','Passive ukazuje režii samotného sledování bez změny vah. HH −0,09/−0,60 %, FT −2,16/+0,53 %: dvě opakování nedokazují, že režie je nulová nebo že pozorování samo zrychluje. Active zahrnuje WeakKeyDict, reset O(m+n), plnou kontrolu po resetu a všechnu práci změněné trajektorie; náklady se neodečítaly.','',
'## Trajektorie a pozorovaný ukazatel','', '| Správce / rameno | Iterace | Refaktorizace | Pozorování | Bad ratio | Proposals | Resety | Staged vynecháno | Δ objective proti off |','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
for profile,g,n,d,a in audits:
 if g!='runtime':continue
 off=next(e for pr,gr,nm,e,aa in audits if pr==profile and gr=='runtime' and nm=='off-audit');c=d['quality_counts']
 lines.append(f"| {profile} / {d['arm']} | {d['iterations']} | {d['refactors']} | {c['observations']} | {c['bad_ratios']} | {c['eligible_proposals']} | {c['resets']} | {c['staged_skipped']} | {d['objective']-off['objective']:+.12g} |")
lines+=['','HH: iterace 75776→84068 (+10,94 %), refaktorizace 483→543. FT: 75164→85205 (+13,36 %), refaktorizace 479→558. Reset neprovádí nový basis solve přímo, ale změna pricingu vedla k více následné práci. Z tohoto experimentu nelze oddělit veškerou přímou cenu resetů od ceny změněné trajektorie.','',
'Všechna bad ratio pozorování nastala ve fázi generation1; ve fázi0 byla pouze good. Neplatných operandů a blokací authority bylo ve všech runtime ramenech0. Fáze generation je identifikátor pozorované fáze, nikoli detail každého interního zápisu. Off ukazatel nesleduje, jeho nulové čítače nejsou důkazem absence špatných odhadů nebo původních resetů. Kompletní phase counts a prvních nejvýše128 bad samples jsou v auditních TOML.','',
'| Správce / rameno | Row residual volání | Direction guard | Full finite | Události | Původní certificate true/calls |','|---|---:|---:|---:|---:|---:|']
for pr,g,n,d,a in audits:
 if g=='runtime':lines.append(f"| {pr} / {d['arm']} | {a['counts']['row']} | {a['counts']['direction']} | {a['counts']['finite']} | {a['counts']['events']} | {d['certificate_true']}/{d['certificate_calls']} |")
lines+=['','Původní safeguards, tolerance, precision, refaktorizace160 a vstup zůstaly. Uložená Devex váha se porovnává s max(1, stávající reference-frame sum), nikoli s plnou DSE normou. Plošná kvalita všech vah není měřena. Reset až po dokončeném běžném pivotu; staged/retry/refactor/phase invalidace a plný finite guard zůstaly.','',
'## Práce, alokace a paměť','',
'Žádný dodatečný dimension-dependent sken, převod, kopie velkých polí nebo basis solve pro obyčejné pozorování. Hodnota weak-key stavu obsahuje jen skaláry (sizeof56B); ve full výsledcích passive/active jedna metadata položka, off žádná. To není celá velikost slovníku ani měření retained memory. Auditní kopie, streamy a vzorky nejsou v benchmarku. Statická kontrola nenašla nepotřebnou další práci nebo retenční numerická pole; nezbytná práce resetu je však drahá v součtu se změněnou trajektorií.',
'',
'HH active přibližně 110,61 milionu alokací proti 62,87 milionu off; FT 218,54 milionu proti 191,01 milionu. Tento růst nelze připsat samotnému scalar state ani z něj izolovat cenu obnov. Passive má téměř stejné allocation counts jako off. Bytes jsou kumulované alokované bajty, nikoli živá paměť. Peak RSS zahrnuje warmup i následné kontroly. Kompilace je zahrnuta v celém solve a neodečtena; audity nejsou benchmark.','']+resources(benches)
lines+=['','Omezení: jeden model, dvě opakování, pouze produkční HH/FT a fixed Devex/legacy/Float64. Bez garance pro ostatní správce nebo vstupy. Přínos obnovy se nepotvrdil a do produkce nic integrováno nebylo. Další automatické prohledávání prahů ani nové solve nejsou součástí tohoto závěru.','',
'[Strojové ověření](final-verification.json) · [Páry CSV](pairs.csv) · [Pokrytí CSV](coverage.csv)']
(p/'interpretation.md').write_text('\n'.join(lines)+'\n')
for name,(p,rec,_,_) in metadata.items():
 print(name,json.dumps(rec))
