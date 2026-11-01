# Task4 publication review fix

Independent result review found a fail-closed gap in the unexecuted publication draft: it checked closure.accepted, then newly hashed/staged current files without comparing closure.bindings. A changed source/raw/script after closure could therefore enter the staged set under a stale closure. Preserve the original draft under before-publication-review; no stage/commit occurred.

The corrected publication verifies every closure binding, every367 current launch file/hash/resolved path and exact inventory membership before writing publication.json or staging anything. A local hash cache avoids rereading the same path across closure and launch inventories. Existing exact staged names/blobs and diff checks stay unchanged. This is offline publication-only work; no numerical/source/test/guard changes or Julia rerun.
