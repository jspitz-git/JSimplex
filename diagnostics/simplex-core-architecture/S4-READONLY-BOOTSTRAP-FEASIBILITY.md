# S4-V: read-only bootstrap feasibility decision

SOURCE/HOST-READ-ONLY at bdbe6dec / master0eb75c3. No Julia, bubblewrap invocation,
namespace or mount operation, module load, macro execution, compilation, native-library
call, cache copy, permission change, environment mutation or numerical run occurred.
The installed examples are NOT a qualified bootstrap launcher. No launcher is frozen or
approved. Bootstrap remains OPEN; this is not a claim that this host cannot sandbox Julia.
Stop the current bootstrap investigation here rather than substituting another generic
sandbox example or probing imports. Continue independent controller work analysis only.

## What the actual host supports on paper

The installed package metadata identifies bubblewrap0.11.1-1ubuntu0.3 arm64 and
util-linux2.41.3-3ubuntu2.2 arm64. /usr/bin/bwrap is a regular root-owned0755 executable,
not setuid, with no recorded extended attributes. The invoking UID/GID is1000, effective
capabilities zero, NoNewPrivs0 and Seccomp0. These are observations of the metadata-reader
process, not of a prospective sandbox. The installed Debian documentation states that
this unprivileged form requires user namespaces.

The running WSL2 kernel reports6.18.33.2-microsoft-standard-WSL2. Its /proc/config.gz
contains CONFIG_NAMESPACES/USER_NS/PID_NS/NET_NS/IPC_NS/UTS_NS=y; the user namespace limit
is96050. The Debian-specific unprivileged_userns_clone and AppArmor-specific restriction
sysctl paths were absent. Absence is not a permissive policy value. CONFIG_SECURITY_APPARMOR
is enabled; /sys/kernel/security/lsm was unavailable and the reader's attr/current reported
kernel. None of this proves actual namespace admission or a future process's policy.
No trial was made, and no missing tool was installed. bwrap, unshare, mount, nsenter,
systemd-run and setpriv exist; firejail and proot were absent from the inspected PATH.

The installed manpage documents a new empty tmpfs-backed filesystem, read-only bind
mounts, explicit user/PID/IPC/network namespaces, environment clearing, capability drop,
new-session and disable-userns. These are useful construction primitives. They support
plausibility of a purpose-built confined process, not qualification of an existing policy.
The installed README explicitly says that bubblewrap is not a complete ready-made sandbox:
its command-line producer must define the policy. No package-version string or source
hash is substituted for execution evidence or a complete argument/path contract.

## Why the available examples are rejected for this contract

| Available proposal | Concrete mismatch with the requested bootstrap |
|---|---|
| Installed bubblewrap-shell.sh | Retains network with --share-net; creates writable /tmp and other ephemeral directories, inherits environment beyond its few overrides, and does not select/pin the JSimplex depot, project, sysimage or cache graph. Ephemeral writes are not host cache mutation, but permit unaccounted fallback state and do not satisfy the frozen no-cache-creation contract. |
| Installed flatpak-run.sh | Contains prerequisite installation guidance and mkdir operations, writable host application/config binds and an X11 socket bind. Its application/runtime, flags and paths target an unrelated application. It was only read, never run. |
| Generic read-only root/remount shorthand | Does not specify all submounts, aliases, sockets, inherited descriptors or loader environment. The manpage explicitly says --remount-ro changes only the named mount, not its descendants. This does NOT assert that --ro-bind has the same nonrecursive behavior. |

The actual mount snapshot includes writable host mounts and aliases: /run/shm and
/dev/shm share one tmpfs; /mnt/wslg/distro exposes the root filesystem through a separate
read-only mount; /mnt/c is a writable9p mount; /usr also contains separate module/WSL
mounts. Host mount flags do not become a sandbox's flags automatically. A content hash
cannot detect U's cache touch/mtime operation, and a read-only view at one pathname does
not protect an alternate writable view of the same inode. The installed README also
warns that a bound host IPC socket can cause work outside the filesystem sandbox.
A read-only socket pathname is not a complete prohibition of such IPC. No IPC use by
JSimplex is alleged; the complete initializer closure remains unknown.

A qualifying custom policy would need to bind only audited existing inputs read-only,
exclude writable host aliases and IPC endpoints, control inherited file descriptors,
construct a private process/proc view, remove inherited loader/startup/depot overrides,
and fail before the target on every unmet confinement precondition. The exact binary,
sysimage, project/depot/load paths and dependencies must be identified; no hidden writable
depot or source/cache creation fallback is acceptable. Fresh namespace metadata alone
cannot supply that policy. This task does not implement it or treat a list of desired
flags as an executable fail-closed launcher.

The precise unsupported claim is therefore: “an available installed launcher already
provides the required complete read-only JSimplex bootstrap view.” It does not. Available
kernel/tool primitives are promising but no complete launch/path/descriptor contract or
selected cache/dependency closure has been established. This is a qualification boundary,
not proof of OS impossibility, nor an observed namespace denial. No future experiment is
authorized. We reject reuse of these installed examples and close this bounded route
investigation. No follow-on equivalent sandbox/source audit or import probe is scheduled.

## Independent gates and next useful work

U's actual cache validity, transitive __init__/extension/native initialization and T's
complete controller attempt budget remain OPEN. Even perfect filesystem confinement
would not imply zero setup work, valid caches or safe numerical comparison. Missing
cache failure may follow dependency initialization. T's conditional82 public solves,
4 factors,4 refactors and16 backend solves remain source workload counts, not observed
bootstrap work or a complete internal bound. S's seven root changes plus one candidate
HH keyword remain frozen, as does T's one LP. No inventory or exact LP calculation was
repeated. In particular, no Main.JSimplex residence is silently introduced into S's loader.

ONE next task is SOURCE-ONLY controller attempt accounting for the frozen T LP, independent
of bootstrap: map all setup, phase/crash, ordinary/prepared/unit solves, factor updates,
copies, quality, recovery, cleanup, original-model retry and certification entry paths;
separate finite source bounds from unknown native/exception work. Specify exact prospective
counter placement and inverse requirements only if the source supports them. Do not create
a numerical launcher or reopen bootstrap. This changes the order of independent analysis,
not the execution gate: both bootstrap and controller caps must close before a public pair.
See2026-10-12-hh-public-controller-attempt-contract.md.

## Evidence, work and preservation

read-only-audit.json contains17 checks and656 read-time file hashes. All627 U source pins
were independently read again for current-byte equality; this is a new hash check, not a
rerun of U scripts or inventories. Six user hashes, old full process groups23249/23257,
old leader identities and src/test/.github equality to master were checked. host-before.json
binds the actual refs and boot. kernel-config.txt, mountinfo.txt, host-metadata.json and
installed-documents.json preserve the read-only observations. The source hash inventory
is not cache validity, namespace execution, cache-file mtime protection or current policy
attestation. The ephemeral /proc snapshots have their own saved hashes at closure.

No production computational work, allocation or retained memory was added. This diagnosis
performs bounded source/document/metadata reads and file hashing. A hypothetical future
sandbox adds namespace/mount setup, process supervision, filesystem checks and associated
kernel metadata; Julia adds package/init/JIT/Core.kwcall/module/native-handle retention.
Those costs are not zero and were not benchmarked. There is no speedup or native free-balance
claim. No benchmark is required for this documentation-only change.

U's original failed8/9 closure/all_passed=false and separate7/7 supplement are untouched.
Publication here requires a successful separate closure check before staging/commit/push.
CI remains off; production/test/environment/master unchanged; native HH reuse disabled;
native retention, broaderS4/S6/fullsuite and all prior rejections remain unchanged. Q's
GC dominance and outlier evidence are preserved without rerun.
