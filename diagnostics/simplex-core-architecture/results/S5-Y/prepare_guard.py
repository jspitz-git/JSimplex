"""Save a separate local guard with atomic exclusive metadata, no old execution."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;s=(H.parent/'S5-U/guard.py').read_text();original=s
helper='''def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.pending')
    with temporary.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.link(temporary, path)  # exclusive publication; never overwrite a prior result
    temporary.unlink()


'''
s=s.replace('def digest(path):\n',helper+'def digest(path):\n',1)
changes={"(out / 'pins.json').write_text(json.dumps(pins, indent=2) + '\\n')":"atomic_json(out / 'pins.json', pins)","(out / 'current.json').write_text(json.dumps(record, indent=2) + '\\n')":"atomic_json(out / 'current.json', record)","(out / 'process.json').write_text(json.dumps(record, indent=2) + '\\n')":"atomic_json(out / 'process.json', record)"}
for a,b in changes.items():assert s.count(a)==1;s=s.replace(a,b)
with (H/'guard.py').open('x') as f:f.write(s)
back=s.replace(helper,'')
for a,b in changes.items():back=back.replace(b,a)
assert back==original
with (H/'guard-source.json').open('x') as f:json.dump(dict(source_sha256=hashlib.sha256(original.encode()).hexdigest(),guard_sha256=hashlib.sha256(s.encode()).hexdigest(),inverse_exact=True,scope='New local guard only; prior U guard not executed'),f,indent=2);f.write('\n')
