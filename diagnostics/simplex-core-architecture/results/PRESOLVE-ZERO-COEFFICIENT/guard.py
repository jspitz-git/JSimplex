#!/usr/bin/env python3
"""Linux diagnostic ownership, immutable attempts, pins and resource guard.

Run outside a PID-restricted sandbox. The global advisory lock coordinates this
runner; the live Julia check also detects older runners. Never unlink the lock.
Pin all transitive launcher/script dependencies explicitly with freeze.
"""
import argparse
from contextlib import contextmanager
import fcntl
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

FORBIDDEN_NAMES = {'big.mps', 'largo.mps', 'anymod.mps'}
DEFAULT_LOCK = Path('/tmp') / f'jsimplex-numerical-{os.getuid()}.lock'


def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.pending')
    with temporary.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.link(temporary, path)  # exclusive publication; never overwrite a prior result
    temporary.unlink()


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def input_digest(path):
    """Compare decompressed MPS bytes too; compressed aliases remain excluded."""
    h = hashlib.sha256()
    opener = gzip.open if str(path).lower().endswith('.gz') else open
    with opener(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def inventory(files, trees):
    paths = {Path(p) for p in files}
    for tree in trees:
        root = Path(tree)
        if not root.is_dir():
            raise ValueError(f'missing pinned tree: {root}')
        if root.is_symlink():
            raise ValueError(f'directory symlink in pinned tree: {root}')
        for p in root.rglob('*'):
            if p.is_symlink() and (p.is_dir() or not p.exists()):
                raise ValueError(f'directory or dangling symlink in pinned tree: {p}')
            if p.is_file():
                paths.add(p)
    return {str(p): {'resolved': str(p.resolve(strict=True)), 'sha256': digest(p)}
            for p in sorted(paths)}


def freeze(args):
    inputs = [Path(p).absolute() for p in args.input]
    forbidden = {input_digest(p) for p in args.forbidden}
    for p in inputs:
        names = {p.name.lower().removesuffix('.gz'),
                 p.resolve(strict=True).name.lower().removesuffix('.gz')}
        if names & FORBIDDEN_NAMES or input_digest(p) in forbidden:
            raise ValueError(f'forbidden input or content alias: {p}')
    files = sorted({str(Path(p).absolute()) for p in
                    [*args.file, *inputs, *args.forbidden, __file__]})
    trees = sorted({str(Path(p).absolute()) for p in args.tree})
    pins = {'files': files, 'trees': trees, 'inventory': inventory(files, trees),
            'inputs': [str(p) for p in inputs], 'created': time.time()}
    with Path(args.pins).open('x') as stream:
        json.dump(pins, stream, indent=2)
        stream.write('\n')


def pins_match(pins):
    try:
        return inventory(pins['files'], pins['trees']) == pins['inventory']
    except (OSError, ValueError):
        return False


def process_identity(pid):
    stat = (Path('/proc') / str(pid) / 'stat').read_text()
    fields = stat[stat.rindex(')') + 2:].split()
    return {'pid': pid, 'pgid': int(fields[2]), 'sid': int(fields[3]), 'start_ticks': int(fields[19]),
            'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
            'command': (Path('/proc') / str(pid) / 'cmdline').read_bytes()
                       .replace(b'\0', b' ').decode(errors='replace')}


def live_julia():
    found = []
    for p in Path('/proc').glob('[0-9]*'):
        try:
            if (p / 'comm').read_text().strip() == 'julia':
                found.append(process_identity(int(p.name)))
        except FileNotFoundError:
            pass  # The process exited between enumeration and inspection.
    return found


def memory():
    fields = {line.split(':')[0]: int(line.split()[1])
              for line in Path('/proc/meminfo').read_text().splitlines()}
    return {'available_kib': fields['MemAvailable'],
            'swap_used_kib': fields['SwapTotal'] - fields['SwapFree']}


def pressure(sample):
    return sample['available_kib'] < 6 * 1024**2 or sample['swap_used_kib'] > 1024**2


@contextmanager
def ownership(path):
    # O_NOFOLLOW prevents following a foreign symlink at the shared lock path.
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'r+') as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError('numerical ownership lock is held') from error
        stream.seek(0)
        stream.truncate()
        json.dump(process_identity(os.getpid()), stream)
        stream.flush()
        yield


def limits():
    resource.setrlimit(resource.RLIMIT_AS, (8 * 1024**3, 8 * 1024**3))


def child_exited(child):
    # WNOWAIT leaves the leader unreaped, reserving the PGID until cleanup.
    return os.waitid(os.P_PID, child.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is not None


def active_group_members(pgid):
    members = []
    for p in Path('/proc').glob('[0-9]*'):
        try:
            stat = (p / 'stat').read_text()
            fields = stat[stat.rindex(')') + 2:].split()
            if (int(fields[2]) == pgid or int(fields[3]) == pgid) and fields[0] not in ('Z', 'X'):
                members.append(int(p.name))
        except FileNotFoundError:
            pass
    return members


def identity_owned(identity,leader):
    return identity['pgid']==leader or identity['sid']==leader

def same_identity(a,b):
    return all(a[k]==b[k] for k in ('pid','start_ticks','boot_id','command'))

def signal_owned(child, sig):
    # Leader is unreaped, reserving its PID/PGID/SID. pidfd prevents signaling a
    # reused member PID; double-read verifies identity and continued membership.
    for pid in active_group_members(child.pid):
        fd = None
        try:
            before=process_identity(pid)
            fd=os.pidfd_open(pid,0)
            after=process_identity(pid)
            if same_identity(before,after) and identity_owned(after,child.pid):
                signal.pidfd_send_signal(fd,sig,None,0)
        except (FileNotFoundError,ProcessLookupError):
            pass
        finally:
            if fd is not None:os.close(fd)


def stop_owned(child):
    signal_owned(child, signal.SIGTERM)
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline and active_group_members(child.pid):
        time.sleep(0.02)
    signal_owned(child, signal.SIGKILL)
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline and active_group_members(child.pid):
        time.sleep(0.02)
    if active_group_members(child.pid):
        return False  # preserve explicit refusal; never claim closure or launch next
    child.wait()
    return True


def run(args):
    guard_started = time.monotonic()
    if not hasattr(os,'pidfd_open') or not hasattr(signal,'pidfd_send_signal'):
        raise ValueError('pidfd unavailable; no launch')
    if not math.isfinite(args.deadline) or args.deadline <= guard_started:
        raise ValueError('expired absolute deadline')
    if not math.isfinite(args.seconds) or args.seconds <= 0:
        raise ValueError('seconds must be finite and positive')
    pins_path = Path(args.pins)
    pins = json.loads(pins_path.read_text())
    pins_digest = digest(pins_path)
    command = args.command
    if not command:
        raise ValueError('missing child command after --')
    with ownership(args.lock):
        running = live_julia()
        if running:
            raise ValueError(f'live Julia process; refusing launch: {running}')
        if not pins_match(pins):
            raise ValueError('changed pins; refusing launch')
        sample = memory()
        if pressure(sample):
            raise ValueError(f'memory pressure; refusing launch: {sample}')
        out = Path(args.out).resolve()
        out.mkdir(parents=True, exist_ok=False)
        atomic_json(out / 'pins.json', pins)
        env = dict(os.environ, JULIA_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
                   OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
                   JULIA_PKG_PRECOMPILE_AUTO='0', JULIA_PKG_OFFLINE='true',
                   JULIA_NUM_PRECOMPILE_TASKS='1', JULIA_IMAGE_THREADS='1')
        record = {'command': command, 'cwd': str(Path.cwd()), 'started': time.time(),
                  'runner': process_identity(os.getpid()), 'pins_sha256': pins_digest,
                  'reason': 'launch_error', 'returncode': None}
        child = None
        old_handlers = {}
        def interrupted(signum, frame):
            raise InterruptedError(f'signal {signum}')
        try:
            for sig in (signal.SIGTERM, signal.SIGINT):
                old_handlers[sig] = signal.signal(sig, interrupted)
            with (out / 'run.log').open('x') as log, (out / 'resources.jsonl').open('x') as resources:
                started = guard_started
                if time.monotonic() >= min(args.deadline, started + args.seconds):
                    raise ValueError('prelaunch deadline consumed')
                child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                         env=env, start_new_session=True, preexec_fn=limits)
                record['child'] = process_identity(child.pid)
                atomic_json(out / 'current.json', record)
                record['reason'] = 'running'
                while not child_exited(child):
                    sample = memory()
                    sample['elapsed'] = time.monotonic() - started
                    try:
                        status = (Path('/proc') / str(child.pid) / 'status').read_text()
                        sample['child_memory'] = [line for line in status.splitlines()
                                                  if line.startswith(('VmRSS:', 'VmPeak:', 'VmSwap:'))]
                    except FileNotFoundError:
                        pass
                    resources.write(json.dumps(sample) + '\n')
                    resources.flush()
                    if pressure(sample):
                        record['reason'] = 'memory_guard'
                        break
                    if sample['elapsed'] > args.seconds or time.monotonic() >= args.deadline:
                        record['reason'] = 'wall_time'
                        break
                    time.sleep(min(1.0, max(0.01, args.seconds / 10)))
        except BaseException as error:
            record['error'] = repr(error)
            record['reason'] = 'interrupted' if isinstance(error, (KeyboardInterrupt, InterruptedError)) else 'launch_error'
        finally:
            # Ignore further interrupts while cleaning up the owned group.
            for sig in old_handlers:
                signal.signal(sig, signal.SIG_IGN)
            if child is not None:
                record['elapsed_including_launch'] = time.monotonic() - started
                if record['reason'] == 'running' and (record['elapsed_including_launch'] > args.seconds or time.monotonic() >= args.deadline):
                    record['reason'] = 'wall_time'
                if record['reason'] == 'running' and child_exited(child):
                    members = active_group_members(child.pid)
                    if members:
                        record['reason'] = 'unexpected_descendants'
                        record['remaining_group'] = members
                        if not stop_owned(child):
                            record["reason"]="cleanup_incomplete"
                            record["remaining_session"]=active_group_members(child.pid)
                    else:
                        child.wait()
                        record['reason'] = f'exit{child.returncode}'
                else:
                    if not stop_owned(child):
                        record["reason"]="cleanup_incomplete"
                        record["remaining_session"]=active_group_members(child.pid)
                record['returncode'] = child.returncode
            record['terminal_memory'] = memory()
            if record['reason'] == 'exit0' and pressure(record['terminal_memory']):
                record['reason'] = 'terminal_memory_guard'
            record['ended'] = time.time()
            record['pins_unchanged'] = pins_match(pins) and pins_path.is_file() and digest(pins_path) == pins_digest
            atomic_json(out / 'process.json', record)
            for sig, handler in old_handlers.items():
                signal.signal(sig, handler)
        print(json.dumps(record))
        return 0 if record['reason'] == 'exit0' and record['pins_unchanged'] else 1


def main():
    # Split command before argparse so options may follow output path naturally.
    argv = sys.argv[1:]
    command = []
    if '--' in argv:
        cut = argv.index('--')
        argv, command = argv[:cut], argv[cut + 1:]
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest='mode', required=True)
    pin = modes.add_parser('freeze')
    pin.add_argument('pins')
    for name in ('file', 'tree', 'input', 'forbidden'):
        pin.add_argument('--' + name, action='append', default=[])
    execute = modes.add_parser('run')
    execute.add_argument('pins')
    execute.add_argument('out')
    execute.add_argument('--lock', type=Path, default=DEFAULT_LOCK)
    execute.add_argument('--seconds', type=float, required=True)
    execute.add_argument('--deadline', type=float, required=True)
    args = parser.parse_args(argv)
    args.command = command
    try:
        return freeze(args) or 0 if args.mode == 'freeze' else run(args)
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
