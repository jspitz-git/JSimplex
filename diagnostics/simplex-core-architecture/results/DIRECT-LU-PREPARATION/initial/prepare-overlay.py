"""Offline preparation only. No Julia, dependency installation, or module loading.

Creates a fresh ordinary checkout overlay from tracked source at the calling
repository. Never accepts an existing output directory; never copies user envs.
An execution admission must separately supply/bind its exact environment.
"""
from pathlib import Path
import argparse, hashlib, json, subprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[3]
    output = args.destination.resolve()
    if output.exists():
        raise SystemExit('Refusing existing destination')
    output.mkdir(parents=True)
    source_names = subprocess.check_output(
        ['git', 'ls-files', 'src', 'Project.toml'], cwd=repo, text=True).splitlines()
    bindings = {}
    for name in source_names:
        source = repo / name
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        bindings[name] = hashlib.sha256(source.read_bytes()).hexdigest()
    implementation = Path(__file__).resolve().parent
    for name in ('factor-export.jl', 'direct-factor.jl'):
        (output / 'src' / name).write_bytes((implementation / name).read_bytes())
        bindings['candidate/' + name] = hashlib.sha256((implementation / name).read_bytes()).hexdigest()
    main_file = output / 'src/JSimplex.jl'
    original = main_file.read_bytes()
    anchor = b'include("huangfu_hall_factorization.jl")\n'
    addition = b'include("factor-export.jl")\ninclude("direct-factor.jl")\n'
    if original.count(anchor) != 1 or addition in original:
        raise SystemExit('Root include inverse is not unique')
    changed = original.replace(anchor, anchor + addition)
    if changed.replace(anchor + addition, anchor) != original:
        raise SystemExit('Root inverse failed')
    main_file.write_bytes(changed)
    manifest = dict(scope='UNEXECUTED ordinary source overlay; no runtime/environment admission',
                    source_root=str(repo), output_root=str(output),
                    source_sha256=bindings, changed_original_files=['src/JSimplex.jl'],
                    added_source_files=['src/factor-export.jl', 'src/direct-factor.jl'],
                    julia_executed=False)
    (output / 'overlay.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'source_files': len(source_names), 'output': str(output), 'julia_executed': False}))


if __name__ == '__main__':
    main()
