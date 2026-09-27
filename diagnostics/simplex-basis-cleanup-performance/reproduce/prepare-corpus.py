"""Prepare hash-checked plain MPS copies; leave the original datasets unchanged."""
import gzip
import hashlib
import json
import pathlib
import sys
import tomllib

source = pathlib.Path(__file__).with_name("quick-inputs.toml")
output = pathlib.Path(sys.argv[1]).resolve()
output.mkdir(parents=True, exist_ok=True)
lines = []
for entry in tomllib.loads(source.read_text())["cases"]:
    original = pathlib.Path(entry["original_path"])
    raw = gzip.decompress(original.read_bytes()) if original.suffix == ".gz" else original.read_bytes()
    if hashlib.sha256(raw).hexdigest() != entry["sha256"]:
        raise ValueError("Input hash mismatch: " + str(original))
    target = output / (entry["id"].replace("/", "-") + ".mps")
    target.write_bytes(raw)
    entry["path"] = str(target)
    lines.append("[[cases]]")
    lines.extend(key + " = " + json.dumps(value) for key, value in entry.items())
manifest = output / "quick-inputs.toml"
manifest.write_text("\n".join(lines) + "\n")
print(manifest)
