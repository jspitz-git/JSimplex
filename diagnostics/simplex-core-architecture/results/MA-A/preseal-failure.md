# Pre-seal failure, no numerical attempt

The inline seal command expected review.json["all_passed"], but the independent
review uses "accepted":true. It raised KeyError before writing allowance.json.
The outer shell lacked fail-fast and continued into launcher.py; that launcher
failed closed on the absent allowance, before host/reservation/guard/Julia.
Original invocation and empty launcher log are preserved byte-for-byte as
invocation.json.before-seal and launcher.log.before-seal. Neither was pinned by
the admission. No output directory, reservation, allowance or Julia existed.
The reviewed numerical driver, scripts and 622 launch pins remain unchanged.
Seal uses the actual accepted field and all review checks. All subsequent seal
and launch operations are separate tool calls (no shell continuation).
