from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[4]
E=Path(__file__).resolve().parent
files=[R/"docs/superpowers/specs/2026-10-16-direct-bg-block-upper.md",R/"docs/superpowers/plans/2026-10-16-direct-bg-block-upper.md",E/"entry.json",Path(__file__)]
checks={}
tables=[]
for n,want in [(32,13136),(96,102224)]:
    m=n*(n+1)//2
    k=sum((d+31)//32 for d in range(1,n+1))
    payload=20*m+28*k+32*n+656
    checks[f"dense{n}_payload"]=payload==want
    tables.append(dict(n=n,m=m,K0=k,C=m,R=m,core_payload=payload,outer_pointer_payload=8*n+24))
checks["dense96_hybrid_lower_bound"]=349080-267632+tables[1]["core_payload"]==183672
checks["headroom_excludes_headers"]=173152*11-183672*10==67952
checks["append_payload"]=256*16==4096
checks["scratch_payload"]=33*(8+4+4)==528
checks["slot_payload_reference"]=56*4656+64*96==266880
checks["handle_limit"]=((2**31-1)//32)*32<=2**31-1<(((2**31-1)//32)+1)*32
entry=json.loads((E/"entry.json").read_text())
checks["entry_pins_unchanged"]=all(Path(k).is_file() and hashlib.sha256(Path(k).read_bytes()).hexdigest()==v for k,v in entry["sha256"].items())
h=json.loads((E/"host.json").read_text())
checks["no_historical_group_or_session"]=all(p["pgid"] not in h["groups"] and p["sid"] not in h["groups"] for p in h["matches"])
checks["foreign_julia_explicit"]=bool(h["matches"])
public={k:v for k,v in h.items() if k!="matches"}
public["matches"]=[{k:v for k,v in p.items() if k not in ("command","exe")} for p in h["matches"]]
public["private_raw_sha256"]=hashlib.sha256((E/"host.json").read_bytes()).hexdigest()
public["redaction"]="command and exe excluded: unrelated user project. Original host.json retained locally, excluded from publication. Entry hash binds private original; no retroactive replacement."
with (E/"host-public.json").open("x") as f:json.dump(public,f,indent=2);f.write("\n")
result=dict(all_passed=all(checks.values()),scope="Offline design arithmetic and read-only identity checks only; no Julia or new measurement",checks=checks,tables=tables,sha256={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},limits="Dense triangular design shapes only, not a newly observed export. Sparse K unknown. Payload excludes headers, spare backing, manager and native memory. Runtime acceptance absent.")
with (E/"budget-check.json").open("x") as f:json.dump(result,f,indent=2);f.write("\n")
print(json.dumps(result,indent=2))
if not result["all_passed"]:raise SystemExit(1)
